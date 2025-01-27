import datetime
import os
import time
from pathlib import Path
from typing import Dict

from PyQt5.QtCore import QSettings, QThread, pyqtSignal

from app.common.config import cfg
from app.core.bk_asr.asr_data import from_subtitle_file
from app.core.entities import SubtitleConfig, SubtitleTask, Task
from app.core.subtitle_processor.optimization import SubtitleOptimizer
from app.core.subtitle_processor.splitting import merge_segments
from app.core.subtitle_processor.summarization import SubtitleSummarizer
from app.core.utils.logger import setup_logger
from app.core.utils.test_opanai import test_openai

# 配置日志
logger = setup_logger("subtitle_optimization_thread")

FREE_API_CONFIGS = {
    "ddg": {
        "base_url": "http://ddg.bkfeng.top/v1",
        "api_key": "Hey-man-This-free-server-is-convenient-for-software-beginners-Please-do-not-use-for-personal-use-Server",
        "llm_model": "gpt-4o-mini",
        "thread_num": 5,
        "batch_size": 10
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "api_key": "c96c2f6ce767136cdddc3fef1692c1de.H27sLU4GwuUVqPn5",
        "llm_model": "glm-4-flash",
        "thread_num": 10,
        "batch_size": 10
    }
}

class SubtitleThread(QThread):
    finished = pyqtSignal(str, str)
    progress = pyqtSignal(int, str)
    update = pyqtSignal(dict)
    update_all = pyqtSignal(dict)
    error = pyqtSignal(str)
    MAX_DAILY_LLM_CALLS = 50

    def __init__(self, task: SubtitleTask):
        super().__init__()
        self.task: SubtitleTask = task
        self.subtitle_length = 0
        self.finished_subtitle_length = 0
        self.custom_prompt_text = ""
        self.llm_result_logger = None

    def set_custom_prompt_text(self, text: str):
        self.custom_prompt_text = text

    def _setup_api_config(self) -> SubtitleConfig:
        """设置API配置，返回SubtitleConfig"""
        if self.task.subtitle_config.base_url and self.task.subtitle_config.api_key:
            if not test_openai(self.task.subtitle_config.base_url, 
                             self.task.subtitle_config.api_key, 
                             self.task.subtitle_config.llm_model)[0]:
                raise Exception(self.tr("OpenAI API 测试失败, 请检查设置"))
            return self.task.subtitle_config
        
        logger.info("尝试使用自带的API配置")
        # 遍历配置字典找到第一个可用的API
        for config in FREE_API_CONFIGS.values():
            if not self.valid_limit():
                raise Exception(self.tr("公益服务有限！请配置自己的API!"))
            if test_openai(config["base_url"], config["api_key"], config["llm_model"])[0]:
                self.set_limit()
                # 更新配置
                self.task.subtitle_config.base_url = config["base_url"]
                self.task.subtitle_config.api_key = config["api_key"]
                self.task.subtitle_config.llm_model = config["llm_model"]
                self.task.subtitle_config.thread_num = config["thread_num"]
                self.task.subtitle_config.batch_size = config["batch_size"]
                return self.task.subtitle_config
        
        logger.error("自带的API配置暂时不可用，请配置自己的API")
        raise Exception(self.tr("自带的API配置暂时不可用，请配置自己的大模型API"))

    def run(self):
        try:
            logger.info(f"\n===========字幕优化任务开始===========")
            logger.info(f"时间：{datetime.datetime.now()}")

            # 字幕文件路径检查、对断句字幕路径进行定义
            subtitle_path = self.task.subtitle_path
            output_name = Path(subtitle_path).stem.replace("【原始字幕】", "").replace("【下载字幕】", "")
            split_path = str(Path(subtitle_path).parent / f"【断句字幕】{output_name}.srt")
            assert subtitle_path is not None, self.tr("字幕文件路径为空")

            # 获取API配置，会先检查可用性（优先使用设置的API，其次使用自带的公益API）
            self.progress.emit(2, self.tr("开始验证API配置..."))
            subtitle_config = self._setup_api_config()
            logger.info(f"使用 {subtitle_config.llm_model} 作为LLM模型")
            os.environ['OPENAI_BASE_URL'] = subtitle_config.base_url
            os.environ['OPENAI_API_KEY'] = subtitle_config.api_key

            self.progress.emit(3, self.tr("开始优化字幕..."))

            self.llm_result_logger = setup_logger("llm_result", 
                                                info_fmt="%(message)s",
                                                log_file=str(Path(subtitle_path).parent / '优化日志.log'),
                                                console_output=False)

            asr_data = from_subtitle_file(subtitle_path)

            # 1. 分割成字词级时间戳（对于非断句字幕且开启分割选项）
            if subtitle_config.need_split and not asr_data.is_word_timestamp():
                asr_data.split_to_word_segments()

            # 2. 重新断句（对于字词级字幕）
            if asr_data.is_word_timestamp():
                self.progress.emit(5, self.tr("字幕断句..."))
                logger.info("正在字幕断句...")
                asr_data = merge_segments(asr_data, 
                                        model=subtitle_config.llm_model,
                                        num_threads=subtitle_config.thread_num,
                                        max_word_count_cjk=subtitle_config.max_word_count_cjk,
                                        max_word_count_english=subtitle_config.max_word_count_english)
                asr_data.save(save_path=split_path)
                self.update_all.emit(asr_data.to_json())

            # 3. 翻译、优化字幕
            subtitle_json = {str(k): v["original_subtitle"] for k, v in asr_data.to_json().items()}
            self.subtitle_length = len(subtitle_json)

            if subtitle_config.need_translate or subtitle_config.need_optimize:
                summarize_result = self.custom_prompt_text.strip()
                # self.progress.emit(20, self.tr("总结字幕..."))
                # if not summarize_result:
                #     summarizer = SubtitleSummarizer(model=subtitle_config.llm_model)
                #     summarize_result = summarizer.summarize(asr_data.to_txt())
                # logger.info(f"总结字幕内容:{summarize_result}")
                
                if subtitle_config.need_translate:
                    self.progress.emit(30, self.tr("优化+翻译..."))
                    logger.info("正在优化+翻译...")
                    need_reflect = False if "glm-4-flash" in subtitle_config.llm_model.lower() else True
                    self.optimizer = SubtitleOptimizer(
                        summary_content=summarize_result,
                        model=subtitle_config.llm_model,
                        target_language=subtitle_config.target_language,
                        batch_num=subtitle_config.batch_size,
                        thread_num=subtitle_config.thread_num,
                        llm_result_logger=self.llm_result_logger,
                        need_remove_punctuation=cfg.needs_remove_punctuation.value,
                        cjk_only=True
                    )
                    optimizer_result = self.optimizer.optimizer_multi_thread(
                        subtitle_json, 
                        translate=True,
                        reflect=need_reflect,
                        callback=self.callback
                    )
                elif subtitle_config.need_optimize:
                    self.progress.emit(30, self.tr("优化字幕..."))
                    logger.info("正在优化字幕...")
                    self.optimizer = SubtitleOptimizer(
                        summary_content=summarize_result, 
                        model=subtitle_config.llm_model,
                        batch_num=subtitle_config.batch_size, 
                        thread_num=subtitle_config.thread_num, 
                        llm_result_logger=self.llm_result_logger
                    )
                    optimizer_result = self.optimizer.optimizer_multi_thread(
                        subtitle_json, 
                        callback=self.callback
                    )
                # 替换优化或者翻译后的字幕
                for i, subtitle_text in optimizer_result.items():
                    seg = asr_data.segments[int(i) - 1]
                    seg.text = subtitle_text
            
            # 4. 保存字幕
            asr_data.save(save_path=self.task.output_path, 
                            ass_style=subtitle_config.subtitle_style,
                            layout=subtitle_config.subtitle_layout)

            logger.info(f"字幕保存到 {self.task.output_path}")


            if self.task.need_next_task and self.task.video_path:
                # 保存srt文件到视频目录（对于全流程任务）
                save_srt_path = Path(self.task.video_path).parent / f"{Path(self.task.video_path).stem}.srt"
                asr_data.to_srt(save_path=str(save_srt_path), layout=subtitle_config.subtitle_layout)
            else:
                # 删除断句文件（对于仅字幕任务）
                split_path = str(Path(self.task.subtitle_path).parent / f"【智能断句】{Path(self.task.subtitle_path).stem}.srt")
                if os.path.exists(split_path):
                    os.remove(split_path)

            self.progress.emit(100, self.tr("优化完成"))
            logger.info("优化完成")
            self.finished.emit(self.task.video_path, self.task.output_path)
        except Exception as e:
            logger.exception(f"优化失败: {str(e)}")
            self.error.emit(str(e))
            self.progress.emit(100, self.tr("优化失败"))

    def set_limit(self):
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope,
                                  'VideoCaptioner', 'VideoCaptioner')
        current_date = time.strftime('%Y-%m-%d')
        last_date = self.settings.value('llm/last_date', '')
        if current_date != last_date:
            self.settings.setValue('llm/last_date', current_date)
            self.settings.setValue('llm/daily_calls', 0)
            self.settings.sync()  # 强制写入
    
    def valid_limit(self):
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope,
                                  'VideoCaptioner', 'VideoCaptioner')
        daily_calls = int(self.settings.value('llm/daily_calls', 0))
        if daily_calls >= self.MAX_DAILY_LLM_CALLS:
            return False
        self.settings.setValue('llm/daily_calls', daily_calls + 1)
        self.settings.sync()  # 强制写入
        print(self.settings.value('llm/daily_calls', 0))
        return True

    def callback(self, result: Dict):
        self.finished_subtitle_length += len(result)
        progress_num = int((self.finished_subtitle_length / self.subtitle_length) * 70) + 30
        self.progress.emit(progress_num, self.tr("{0}% 处理字幕").format(progress_num))
        self.update.emit(result)

    def stop(self):
        if hasattr(self, 'optimizer'):
            self.optimizer.stop()
        self.terminate()