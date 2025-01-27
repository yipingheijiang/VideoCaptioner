import datetime
from pathlib import Path
from typing import Optional

from app.common.config import cfg
from app.config import MODEL_PATH, SUBTITLE_STYLE_PATH
from app.core.entities import (
    LANGUAGES,
    FullProcessTask,
    SubtitleConfig,
    SubtitleTask,
    SynthesisConfig,
    SynthesisTask,
    TranscribeConfig,
    TranscribeModelEnum,
    TranscribeTask,
    TranscriptAndSubtitleTask,
)


class TaskFactory:
    """任务工厂类，用于创建各种类型的任务"""

    @staticmethod
    def get_subtitle_style(style_name: str) -> str:
        """获取字幕样式内容

        Args:
            style_name: 样式名称

        Returns:
            str: 样式内容字符串，如果样式文件不存在则返回None
        """
        style_path = SUBTITLE_STYLE_PATH / f"{style_name}.txt"
        if style_path.exists():
            return style_path.read_text(encoding="utf-8")
        return None

    @staticmethod
    def create_transcribe_task(
        file_path: str, need_next_task: bool = False
    ) -> TranscribeTask:
        """创建转录任务"""
        config = TranscribeConfig(
            transcribe_model=cfg.transcribe_model.value,
            transcribe_language=LANGUAGES[cfg.transcribe_language.value.value],
            use_asr_cache=cfg.use_asr_cache.value,
            need_word_time_stamp=cfg.transcribe_model.value
            in [TranscribeModelEnum.JIANYING, TranscribeModelEnum.BIJIAN],
            # Whisper Cpp 配置
            whisper_model=cfg.whisper_model.value,
            # Whisper API 配置
            whisper_api_key=cfg.whisper_api_key.value,
            whisper_api_base=cfg.whisper_api_base.value,
            whisper_api_model=cfg.whisper_api_model.value,
            whisper_api_prompt=cfg.whisper_api_prompt.value,
            # Faster Whisper 配置
            faster_whisper_program=cfg.faster_whisper_program.value,
            faster_whisper_model=cfg.faster_whisper_model.value.value,
            faster_whisper_model_dir=str(MODEL_PATH),
            faster_whisper_device=cfg.faster_whisper_device.value,
            faster_whisper_vad_filter=cfg.faster_whisper_vad_filter.value,
            faster_whisper_vad_threshold=cfg.faster_whisper_vad_threshold.value,
            faster_whisper_vad_method=cfg.faster_whisper_vad_method.value.value,
            faster_whisper_ff_mdx_kim2=cfg.faster_whisper_ff_mdx_kim2.value,
            faster_whisper_one_word=cfg.faster_whisper_one_word.value,
            faster_whisper_prompt=cfg.faster_whisper_prompt.value,
        )
        if need_next_task:
            file_name = Path(file_path).stem
            output_path = str(
                Path(cfg.work_dir.value)
                / file_name
                / "subtitle"
                / f"【原始字幕】{file_name}-{config.transcribe_model.value}.srt"
            )
        else:
            output_path = str(
                Path(file_path).parent
                / f"【原始字幕】{Path(file_path).stem}-{config.transcribe_model.value}.srt"
            )

        return TranscribeTask(
            queued_at=datetime.datetime.now(),
            file_path=file_path,
            output_path=output_path,
            transcribe_config=config,
            need_next_task=need_next_task,
        )

    @staticmethod
    def create_subtitle_task(
        file_path: str, video_path: Optional[str] = None, need_next_task: bool = False
    ) -> SubtitleTask:
        """创建字幕任务"""
        output_name = (
            Path(file_path)
            .stem.replace("【原始字幕】", "")
            .replace(f"【下载字幕】", "")
        )
        if need_next_task:
            output_path = str(
                Path(file_path).parent
                / f"【样式字幕】{output_name}-{cfg.model.value}.ass"
            )
        else:
            output_path = str(
                Path(file_path).parent / f"【字幕】{output_name}-{cfg.model.value}.srt"
            )

        config = SubtitleConfig(
            # LLM配置
            base_url=cfg.api_base.value,
            api_key=cfg.api_key.value,
            llm_model=cfg.model.value,
            # 字幕处理
            need_translate=cfg.need_translate.value,
            need_optimize=cfg.need_optimize.value,
            thread_num=cfg.thread_num.value,
            batch_size=cfg.batch_size.value,
            # 字幕布局、样式
            subtitle_layout=cfg.subtitle_layout.value,
            subtitle_style=TaskFactory.get_subtitle_style(
                cfg.subtitle_style_name.value
            ),
            # 字幕分割
            max_word_count_cjk=cfg.max_word_count_cjk.value,
            max_word_count_english=cfg.max_word_count_english.value,
            need_split=cfg.need_split.value,
            # 字幕翻译
            target_language=cfg.target_language.value.value,
            # 字幕优化
            need_remove_punctuation=cfg.needs_remove_punctuation.value,
        )

        return SubtitleTask(
            queued_at=datetime.datetime.now(),
            subtitle_path=file_path,
            video_path=video_path,
            output_path=output_path,
            subtitle_config=config,
            need_next_task=need_next_task,
        )

    @staticmethod
    def create_synthesis_task(
        video_path: str, subtitle_path: str, need_next_task: bool = False
    ) -> SynthesisTask:
        """创建视频合成任务"""
        if need_next_task:
            output_path = str(
                Path(subtitle_path).parent.parent
                / f"【卡卡】{Path(video_path).stem}.mp4"
            )
        else:
            output_path = str(
                Path(video_path).parent / f"【卡卡】{Path(video_path).stem}.mp4"
            )

        config = SynthesisConfig(
            need_video=cfg.need_video.value,
            soft_subtitle=cfg.soft_subtitle.value,
        )

        return SynthesisTask(
            queued_at=datetime.datetime.now(),
            video_path=video_path,
            subtitle_path=subtitle_path,
            output_path=output_path,
            synthesis_config=config,
            need_next_task=need_next_task,
        )

    @staticmethod
    def create_transcript_and_subtitle_task(
        file_path: str,
        output_path: Optional[str] = None,
        transcribe_config: Optional[TranscribeConfig] = None,
        subtitle_config: Optional[SubtitleConfig] = None,
    ) -> TranscriptAndSubtitleTask:
        """创建转录和字幕任务"""
        if output_path is None:
            output_path = str(
                Path(file_path).parent / f"{Path(file_path).stem}_processed.srt"
            )

        return TranscriptAndSubtitleTask(
            queued_at=datetime.datetime.now(),
            file_path=file_path,
            output_path=output_path,
        )

    @staticmethod
    def create_full_process_task(
        file_path: str,
        output_path: Optional[str] = None,
        transcribe_config: Optional[TranscribeConfig] = None,
        subtitle_config: Optional[SubtitleConfig] = None,
        synthesis_config: Optional[SynthesisConfig] = None,
    ) -> FullProcessTask:
        """创建完整处理任务（转录+字幕+合成）"""
        if output_path is None:
            output_path = str(
                Path(file_path).parent
                / f"{Path(file_path).stem}_final{Path(file_path).suffix}"
            )

        return FullProcessTask(
            queued_at=datetime.datetime.now(),
            file_path=file_path,
            output_path=output_path,
        )
