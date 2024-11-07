import os
from pathlib import Path
from typing import Dict

from PyQt5.QtCore import QThread, pyqtSignal

from ..subtitle_processor.optimizer import SubtitleOptimizer
from ..subtitle_processor.summarizer import SubtitleSummarizer
from ..bk_asr.ASRData import from_subtitle_file
from ..entities import Task
from ..subtitle_processor.spliter import merge_segments
from ..utils.test_opanai import test_openai
from ..utils.logger import setup_logger

# 配置日志
logger = setup_logger("subtitle_optimization_thread")


class SubtitleOptimizationThread(QThread):
    finished = pyqtSignal(Task)
    progress = pyqtSignal(int, str)
    update = pyqtSignal(dict)
    update_all = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, task: Task):
        super().__init__()
        self.task: Task = task
        self.subtitle_length = 0
        self.finished_subtitle_length = 0

    def run(self):
        try:
            logger.info("开始优化字幕任务")
            llm_model = self.task.llm_model
            need_translate = self.task.need_translate
            need_optimize = self.task.need_optimize
            str_path = self.task.original_subtitle_save_path
            result_subtitle_save_path = self.task.result_subtitle_save_path
            thread_num = self.task.thread_num
            batch_size = self.task.batch_size
            target_language = self.task.target_language
            need_summarize = False
            subtitle_style_srt = self.task.subtitle_style_srt
            subtitle_layout = self.task.subtitle_layout
            # TODO: 开启字幕总结功能

            # 检查
            assert str_path is not None, self.tr("字幕文件路径为空")
            assert Path(str_path).exists(), self.tr("字幕文件路径不存在")
            assert Path(str_path).suffix in ['.srt', '.vtt', '.ass'], self.tr("字幕文件格式不支持")

            self.progress.emit(2, self.tr("开始优化字幕..."))
            logger.info("开始优化字幕...")
            # 设置环境变量
            if self.task.base_url:
                base_url = self.task.base_url
                api_key = self.task.api_key
                if not test_openai(base_url, api_key, llm_model)[0]:
                    raise Exception(self.tr("OpenAI API 测试失败, 请检查设置"))
            else:
                # 使用智谱的API
                base_url = "https://open.bigmodel.cn/api/paas/v4"
                api_key = "c96c2f6ce767136cdddc3fef1692c1de.H27sLU4GwuUVqPn5"
                llm_model = "glm-4-flash"
                thread_num = 10
                batch_size = 10

            os.environ['OPENAI_BASE_URL'] = base_url
            os.environ['OPENAI_API_KEY'] = api_key

            asr_data = from_subtitle_file(str_path)

            # 检查是否需要合并重新断句
            if asr_data.is_word_timestamp():
                self.progress.emit(5, self.tr("字幕断句..."))
                logger.info("字幕断句...")
                asr_data = merge_segments(asr_data, model=llm_model, num_threads=thread_num)
                split_path = str(
                    Path(result_subtitle_save_path).parent / f"{Path(result_subtitle_save_path).stem}_split.srt")
                asr_data.save(save_path=split_path)
                self.update_all.emit(asr_data.to_json())

            # 制作成请求llm接口的格式 {"1": {"original_subtitle": "字幕内容"},...}
            subtitle_json = {str(k): v["original_subtitle"] for k, v in asr_data.to_json().items()}
            self.subtitle_length = len(subtitle_json)
            if need_translate or need_optimize:
                summarize_result = ""
                self.progress.emit(20, self.tr("总结字幕..."))
                logger.info("总结字幕...")
                if need_summarize:
                    summarizer = SubtitleSummarizer(model=llm_model)
                    summarize_result = summarizer.summarize(asr_data.to_txt())

                if need_translate:
                    self.progress.emit(30, self.tr("优化+翻译..."))
                    logger.info("优化+翻译...")
                    need_reflect = False if "glm-4-flash" in llm_model.lower() else True
                    self.optimizer = SubtitleOptimizer(summary_content=summarize_result, model=llm_model,
                                                       target_language=target_language, batch_num=batch_size,
                                                       thread_num=thread_num)
                    optimizer_result = self.optimizer.optimizer_multi_thread(subtitle_json, translate=True,
                                                                             reflect=need_reflect,
                                                                             callback=self.callback)
                elif need_optimize:
                    self.progress.emit(30, self.tr("优化字幕..."))
                    logger.info("优化字幕...")
                    self.optimizer = SubtitleOptimizer(summary_content=summarize_result, model=llm_model,
                                                       batch_num=batch_size, thread_num=thread_num)
                    optimizer_result = self.optimizer.optimizer_multi_thread(subtitle_json, callback=self.callback)

                # 保存字幕
                for i, subtitle_text in optimizer_result.items():
                    seg = asr_data.segments[int(i) - 1]
                    seg.text = subtitle_text

                if result_subtitle_save_path.endswith(".ass"):
                    asr_data.to_ass(subtitle_style_srt, subtitle_layout, result_subtitle_save_path)
                else:
                    asr_data.save(save_path=result_subtitle_save_path, ass_style=subtitle_style_srt,
                                  layout=subtitle_layout)
                logger.info(f"字幕优化完成，保存到 {result_subtitle_save_path}")
            else:
                if result_subtitle_save_path.endswith(".ass"):
                    asr_data.to_ass(subtitle_style_srt, subtitle_layout, result_subtitle_save_path)
                else:
                    asr_data.save(save_path=result_subtitle_save_path, ass_style=subtitle_style_srt,
                                  layout=subtitle_layout)
                logger.info(f"无需优化翻译，直接保存 {result_subtitle_save_path}")

            self.progress.emit(100, self.tr("优化完成"))
            logger.info("优化完成")
            self.finished.emit(self.task)
        except Exception as e:
            logger.error(f"优化失败: {str(e)}")
            self.error.emit(str(e))
            self.progress.emit(100, self.tr("优化失败"))

    def callback(self, result: Dict):
        self.finished_subtitle_length += len(result)
        progress_num = int((self.finished_subtitle_length / self.subtitle_length) * 70) + 30
        self.progress.emit(progress_num, self.tr("{0}% 处理字幕").format(progress_num))
        self.update.emit(result)

    def stop(self):
        if hasattr(self, 'optimizer'):
            self.optimizer.stop()
        self.terminate()
