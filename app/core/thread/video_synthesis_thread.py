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
            video_file = self.task.file_paths
            result_subtitle_save_path = self.task.result_subtitle_save_path
            video_save_path = self.task.video_save_path
            soft_subtitle = self.task.soft_subtitle
            
            self.progress.emit(5, "正在合成视频...")
            add_subtitles(video_file, result_subtitle_save_path, video_save_path, log='quiet', soft_subtitle=soft_subtitle)
            
            self.progress.emit(100, "视频合成完成")
            self.finished.emit(self.task)
        except Exception as e:
            self.task.status = Task.Status.FAILED
            self.error.emit(str(e))
            self.progress.emit(100, "视频合成失败")
    
    def progress_callback(self, value, message):
        self.progress.emit(int(50 + int(value)//100 * 50), message)
