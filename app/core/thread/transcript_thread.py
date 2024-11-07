from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal

from ..bk_asr import JianYingASR, KuaiShouASR, BcutASR, WhisperASR
from ..entities import Task, TranscribeModelEnum
from ..utils.video_utils import video2audio


class TranscriptThread(QThread):
    finished = pyqtSignal(Task)
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)

    ASR_MODELS = {
        TranscribeModelEnum.JIANYING: JianYingASR,
        TranscribeModelEnum.KUAISHOU: KuaiShouASR,
        TranscribeModelEnum.BIJIAN: BcutASR,
        TranscribeModelEnum.WHISPER: WhisperASR,
    }

    def __init__(self, task: Task):
        super().__init__()
        self.task = task

    def run(self):
        try:
            # 检查是否已经存在字幕文件
            if Path(self.task.original_subtitle_save_path).exists():
                self.progress.emit(100, self.tr("字幕已存在"))
                self.finished.emit(self.task)
                return

            video_path = Path(self.task.file_path)
            if not video_path:
                raise ValueError(self.tr("视频路径不能为空"))

            self.progress.emit(5, self.tr("转换音频中"))

            # 转换为音频(如果音频不存在则转换)
            audio_save_path = Path(self.task.audio_save_path)
            if not audio_save_path.exists():
                is_success = video2audio(str(video_path), output=str(audio_save_path))
                if not is_success:
                    raise ValueError(self.tr("音频转换失败"))

            self.progress.emit(30, self.tr("语音转录中"))

            # 获取ASR模型
            asr_class = self.ASR_MODELS.get(self.task.transcribe_model)
            if not asr_class:
                raise ValueError(self.tr("无效的转录模型: ") + str(self.task.transcribe_model))  # 检查转录模型是否有效
            # 执行转录
            args = {
                "use_cache": self.task.use_asr_cache,
                "need_word_time_stamp": self.task.need_word_time_stamp,
            }
            if self.task.transcribe_model == TranscribeModelEnum.WHISPER:
                args["language"] = self.task.transcribe_language
            asr = asr_class(self.task.audio_save_path, **args)
            asr_data = asr.run(callback=self.progress_callback)

            # 保存字幕文件
            original_subtitle_path = Path(self.task.original_subtitle_save_path)
            original_subtitle_path.parent.mkdir(parents=True, exist_ok=True)
            asr_data.to_srt(save_path=str(original_subtitle_path))

            self.progress.emit(100, self.tr("转录完成"))
            self.finished.emit(self.task)
        except Exception as e:
            self.error.emit(str(e))
            self.progress.emit(100, self.tr("转录失败"))

    def progress_callback(self, value, message):
        progress = min(30 + (value // 100) * 70, 100)
        self.progress.emit(progress, message)
