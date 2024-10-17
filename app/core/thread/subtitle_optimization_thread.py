import datetime
import os
from pathlib import Path
from typing import Dict
from PyQt5.QtCore import QThread, pyqtSignal

from app.core.bk_asr import ASRData
from app.core.subtitle_processor.optimizer import SubtitleOptimizer
from app.core.subtitle_processor.summarizer import SubtitleSummarizer
from app.core.utils import optimize_subtitles

from ..bk_asr.ASRData import ASRData, from_srt
from ..entities import Task, TranscribeModelEnum
from ..utils.video_utils import video2audio
from ..utils.optimize_subtitles import optimize_subtitles


class SubtitleOptimizationThread(QThread):
    finished = pyqtSignal(Task)
    progress = pyqtSignal(int, str)
    update = pyqtSignal(dict)

    def __init__(self, task: Task):
        super().__init__()
        self.task = task
        self.subtitle_length = 0
        self.finished_subtitle_length = 0

    def run(self):
        llm_model = self.task.llm_model
        need_translate = self.task.need_translate
        need_optimize = self.task.need_optimize
        str_path = self.task.original_subtitle_save_path
        result_subtitle_save_path = self.task.result_subtitle_save_path
        thread_num = self.task.thread_num
        batch_size = self.task.batch_size
        target_language = self.task.target_language

        assert str_path is not None, "字幕文件路径为空"
        assert Path(str_path).exists(), "字幕文件路径不存在"

        os.environ['OPENAI_BASE_URL'] = self.task.base_url
        os.environ['OPENAI_API_KEY'] = self.task.api_key

        asr_data = from_srt(Path(str_path).read_text(encoding="utf-8"))
        asr_data.segments = asr_data.segments[:50]
        subtitle_json = {str(k): v["original_subtitle"] for k, v in asr_data.to_json().items()}
        self.subtitle_length = len(subtitle_json)
        # print(subtitle_json)
        
        # 总结字幕
        self.progress.emit(10, "正在总结字幕...")
        # summarizer = SubtitleSummarizer(model=llm_model)
        # summarize_result = summarizer.summarize(asr_data.to_txt())
        # print(summarize_result)
        summarize_result = ""


        if need_translate:
            self.progress.emit(30, "正在优化/翻译字幕...")
            optimizer = SubtitleOptimizer(summary_content=summarize_result, model=llm_model)
            optimizer_result = optimizer.optimizer_multi_thread(subtitle_json, batch_num=batch_size, thread_num=thread_num, translate=True, callback=self.callback, target_language=target_language)
            print(optimizer_result)
        elif need_optimize:
            self.progress.emit(30, "正在优化字幕...")
            optimizer = SubtitleOptimizer(summary_content=summarize_result, model=llm_model)
            optimizer_result = optimizer.optimizer_multi_thread(subtitle_json, batch_num=batch_size, thread_num=thread_num, callback=self.callback)
            print(optimizer_result)

        # 保存字幕
        for i, subtitle_text in optimizer_result.items():
            seg = asr_data.segments[int(i)-1]
            seg.text = subtitle_text
        asr_data.to_srt(save_path=result_subtitle_save_path)

        self.progress.emit(100, "优化完成")
        self.finished.emit(self.task)

    def callback(self, result: Dict):
        # print(result)
        self.finished_subtitle_length += len(result)
        progress = (self.finished_subtitle_length / self.subtitle_length)
        self.progress.emit(30 + int(progress * 70), f"{progress}% 处理字幕")
        self.update.emit(result)


