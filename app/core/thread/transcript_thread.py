import datetime
import os
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

from app.core.utils import optimize_subtitles

from ..entities import Task, TranscribeModelEnum
from ..bk_asr import JianYingASR, KuaiShouASR, BcutASR
from ..utils.video_utils import video2audio

class TranscriptThread(QThread):
    finished = pyqtSignal(Task)
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)

    def __init__(self, task: Task):
        super().__init__()
        self.task = task

    def run(self):
        try:
            if self.task.status != Task.Status.TRANSCRIBING:
                self.progress.emit(100, "任务状态错误")
                self.finished.emit(self.task)
                return

            video_path = self.task.file_paths
            self.progress.emit(5, "转换音频中...")

            # 将视频转换为音频
            if Path(self.task.audio_save_path).exists():
                audio_file = self.task.audio_save_path
            else:
                audio_file = video2audio(video_path, output=self.task.audio_save_path)
            self.progress.emit(30, "转录中...")

            # 调用ASR模型进行转录
            use_cache = self.task.use_asr_cache
            if self.task.transcribe_model == TranscribeModelEnum.JIANYING:
                asr = JianYingASR(audio_file, use_cache=use_cache)
            elif self.task.transcribe_model == TranscribeModelEnum.KUAISHOU:
                asr = KuaiShouASR(audio_file, use_cache=use_cache)
            elif self.task.transcribe_model == TranscribeModelEnum.BCUT:
                asr = BcutASR(audio_file, use_cache=use_cache)
            else:
                raise ValueError(f"Invalid transcribe model: {self.task.transcribe_model}")
            
            asr_data = asr.run(callback=self.progress_callback)
            optimize_subtitles(asr_data)

            Path(self.task.original_subtitle_save_path).parent.mkdir(parents=True, exist_ok=True)
            asr_data.to_srt(save_path=self.task.original_subtitle_save_path)

            self.progress.emit(100, "转录完成")
            self.finished.emit(self.task)
        except Exception as e:
            self.task.status = Task.Status.FAILED
            self.error.emit(str(e))
            self.progress.emit(100, "转录失败")
    
    def progress_callback(self, value, message):
        self.progress.emit(int(30 + int(value)//100 * 70), message)
