import datetime
import os
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

from app.core.utils import optimize_subtitles

from ..entities import Task, TranscribeModelEnum
from ..utils.video_utils import add_subtitles

class VideoSynthesisThread(QThread):
    finished = pyqtSignal(Task)
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)

    def __init__(self, task: Task):
        super().__init__()
        self.task = task

    def run(self):
        try:
            video_file = self.task.file_path
            result_subtitle_save_path = self.task.result_subtitle_save_path
            video_save_path = self.task.video_save_path
            soft_subtitle = self.task.soft_subtitle
            self.progress.emit(5, "正在合成")
            add_subtitles(video_file, result_subtitle_save_path, video_save_path, soft_subtitle=soft_subtitle, progress_callback=self.progress_callback)
            self.progress.emit(100, "合成完成")
            self.finished.emit(self.task)
        except Exception as e:
            self.error.emit(str(e))
            self.progress.emit(100, "视频合成失败")
    
    def progress_callback(self, value, message):
        print("===",value, message, int(5 + int(value)/100 * 95))
        progress = int(5 + int(value)/100 * 95)
        self.progress.emit(progress, f"{progress}% {message}")
