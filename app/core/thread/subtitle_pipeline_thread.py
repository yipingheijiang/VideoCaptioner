import time
from PyQt5.QtCore import QThread, pyqtSignal
from ...core.thread.create_task_thread import CreateTaskThread
from ...core.thread.transcript_thread import TranscriptThread
from ...core.thread.subtitle_optimization_thread import SubtitleOptimizationThread
from ...core.thread.video_synthesis_thread import VideoSynthesisThread
from ...core.entities import Task

from .transcript_thread import TranscriptThread
from .subtitle_optimization_thread import SubtitleOptimizationThread
from .video_synthesis_thread import VideoSynthesisThread


class SubtitlePipelineThread(QThread):
    """字幕处理全流程线程，包含:
    1. 转录生成字幕
    2. 字幕优化/翻译
    3. 视频合成
    """
    progress = pyqtSignal(int, str)  # 进度值, 进度描述
    finished = pyqtSignal(Task)
    error = pyqtSignal(str)
    
    def __init__(self, task: Task):
        super().__init__()
        self.task = task
        self.has_error = False
        
    def run(self):
        try:
            def handle_error(error_msg):
                print(f"[-]pipeline 发生错误: {error_msg}")
                self.has_error = True
                self.error.emit(error_msg)

            # 1. 转录生成字幕
            self.task.status = Task.Status.TRANSCRIBING
            self.progress.emit(0, "开始转录")
            transcript_thread = TranscriptThread(self.task)
            transcript_thread.progress.connect(lambda value, msg: self.progress.emit(int(value * 0.4), msg))
            transcript_thread.error.connect(handle_error)
            transcript_thread.run()

            if self.has_error:
                return
            
            # 2. 字幕优化/翻译
            self.task.status = Task.Status.OPTIMIZING
            self.progress.emit(40, "开始优化字幕")
            optimization_thread = SubtitleOptimizationThread(self.task)
            optimization_thread.progress.connect(lambda value, msg: self.progress.emit(int(40 + value * 0.4), msg))
            optimization_thread.error.connect(handle_error)
            optimization_thread.run()

            if self.has_error:
                return

            # 3. 视频合成
            self.task.status = Task.Status.GENERATING
            self.progress.emit(80, "开始合成视频")
            print(f"[+] 开始合成视频...")
            synthesis_thread = VideoSynthesisThread(self.task)
            synthesis_thread.progress.connect(lambda value, msg: self.progress.emit(int(80 + value * 0.2), msg))
            synthesis_thread.error.connect(handle_error)
            synthesis_thread.run()

            if self.has_error:
                return

            self.task.status = Task.Status.COMPLETED
            self.progress.emit(100, "处理完成")
            self.finished.emit(self.task)
            
        except Exception as e:
            self.task.status = Task.Status.FAILED
            self.error.emit(str(e))