import datetime
import os
from PyQt5.QtCore import QThread, pyqtSignal
from ..entities import Task, VideoInfo
from ..utils.video_utils import get_video_info
from ...common.config import cfg

from pathlib import Path

class CreateTaskThread(QThread):
    finished = pyqtSignal(Task)

    def __init__(self, file_path, task_type):
        super().__init__()
        self.file_path = file_path
        self.task_type = task_type

    def run(self):
        if self.task_type == 'file':
            self.create_task_from_file(self.file_path)
        elif self.task_type == 'url':
            self.create_task_from_url(self.file_path)
        elif self.task_type == 'transcription':
            self.create_transcription_task(self.file_path)
        elif self.task_type == 'optimization':
            self.create_subtitle_optimization_task()
        elif self.task_type == 'synthesis':
            self.create_video_synthesis_task()

    def create_task_from_file(self, file_path):
        video_info = get_video_info(self.file_path, need_thumbnail=True)
        video_info = VideoInfo(**video_info)

        # 使用 Path 对象处理路径
        work_dir = Path(cfg.work_dir.value)
        task_work_dir = work_dir / video_info.file_name

        # 定义各个路径
        audio_save_path = task_work_dir / "audio.mp3"
        original_subtitle_save_path = task_work_dir / "subtitles" / "original.srt"
        result_subtitle_save_path = work_dir / "subtitles" / "result.srt"
        video_save_path = work_dir / "videos" / "generated_video.mp4"

        # 创建 Task 对象
        task = Task(
            id=0,
            queued_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            status=Task.Status.TRANSCRIBING,
            fraction_downloaded=0,
            work_dir=str(task_work_dir),
            file_paths=str(Path(self.file_path)),
            url="",
            source=Task.Source.FILE_IMPORT,
            original_language=None,
            target_language=cfg.target_language.value,
            video_info=video_info,
            audio_format="mp3",
            audio_save_path=str(audio_save_path),
            transcribe_model=cfg.transcribe_model.value,
            use_asr_cache=cfg.use_asr_cache.value,
            original_subtitle_save_path=str(original_subtitle_save_path),
            base_url=cfg.api_base.value,
            api_key=cfg.api_key.value,
            llm_model=cfg.model.value,
            need_translate=cfg.need_translate.value,
            need_optimize=cfg.need_optimize.value,
            result_subtitle_save_path=str(result_subtitle_save_path),
            video_save_path=str(video_save_path),
            soft_subtitle=False
        )
        self.finished.emit(task)

    def create_task_from_url(self, url):
        # 实现从URL创建任务的逻辑
        pass

    def create_transcription_task(self, file_path):
        video_info = get_video_info(self.file_path, need_thumbnail=True)
        video_info = VideoInfo(**video_info)

        # 使用 Path 对象处理路径
        work_dir = Path(cfg.work_dir.value)
        task_work_dir = work_dir / video_info.file_name

        # 定义各个路径
        audio_save_path = task_work_dir / "audio.mp3"
        original_subtitle_save_path = task_work_dir / "subtitles" / "original.srt"
        result_subtitle_save_path = work_dir / "subtitles" / "result.srt"
        video_save_path = work_dir / "videos" / "generated_video.mp4"

        # 创建 Task 对象
        task = Task(
            id=0,
            queued_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            status=Task.Status.TRANSCRIBING,
            fraction_downloaded=0,
            work_dir=str(task_work_dir),
            file_paths=str(Path(self.file_path)),
            url="",
            source=Task.Source.FILE_IMPORT,
            original_language=None,
            target_language=cfg.target_language.value.value,
            video_info=video_info,
            audio_format="mp3",
            audio_save_path=str(audio_save_path),
            transcribe_model=cfg.transcribe_model.value,
            use_asr_cache=cfg.use_asr_cache.value,
            original_subtitle_save_path=str(original_subtitle_save_path),
            base_url=cfg.api_base.value,
            api_key=cfg.api_key.value,
            llm_model=cfg.model.value,
            need_translate=cfg.need_translate.value,
            need_optimize=cfg.need_optimize.value,
            result_subtitle_save_path=str(result_subtitle_save_path),
            video_save_path=str(video_save_path),
            soft_subtitle=False
        )
        self.finished.emit(task)

    def create_subtitle_optimization_task(self):
        # 使用 Path 对象处理路径
        original_subtitle_save_path = Path(self.file_path)
        result_subtitle_save_path = original_subtitle_save_path.parent / f"optimized_subtitle_{cfg.model.value}.srt"

        # 创建 Task 对象
        task = Task(
            id=0,
            queued_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            status=Task.Status.OPTIMIZING,
            target_language=cfg.target_language.value.value,
            original_subtitle_save_path=str(original_subtitle_save_path),
            base_url=cfg.api_base.value,
            api_key=cfg.api_key.value,
            llm_model=cfg.model.value,
            need_translate=cfg.need_translate.value,
            need_optimize=cfg.need_optimize.value,
            result_subtitle_save_path=str(result_subtitle_save_path),
            thread_num=cfg.thread_num.value,
            batch_size=cfg.batch_size.value,
        )
        self.finished.emit(task)
        return task

    def create_video_synthesis_task(subtitle_file, video_file):
        video_save_path = Path(video_file).parent / "generated_video.mp4"
        
        # 创建 Task 对象
        task = Task(
            id=0,
            queued_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            status=Task.Status.OPTIMIZING,
            file_paths=str(Path(video_file)),
            result_subtitle_save_path=str(Path(subtitle_file)),
            video_save_path=str(video_save_path),
            soft_subtitle=cfg.soft_subtitle.value,
        )
        return task
