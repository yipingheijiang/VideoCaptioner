from dataclasses import dataclass, field
import datetime
from dataclasses import dataclass, field
from enum import Enum
from random import randint
from typing import Optional


class SupportedAudioFormats(Enum):
    """ 支持的音频格式 """
    AAC = "aac"
    AC3 = "ac3"
    AIFF = "aiff"
    AMR = "amr"
    APE = "ape"
    AU = "au"
    FLAC = "flac"
    M4A = "m4a"
    MP2 = "mp2"
    MP3 = "mp3"
    MKA = "mka"
    OGA = "oga"
    OGG = "ogg"
    OPUS = "opus"
    RA = "ra"
    WAV = "wav"
    WMA = "wma"


class SupportedVideoFormats(Enum):
    """ 支持的视频格式 """
    MP4 = "mp4"
    WEBM = "webm"
    OGM = "ogm"
    MOV = "mov"
    MKV = "mkv"
    AVI = "avi"
    WMV = "wmv"
    FLV = "flv"
    M4V = "m4v"
    TS = "ts"
    MPG = "mpg"
    MPEG = "mpeg"
    VOB = "vob"
    ASF = "asf"
    RM = "rm"
    RMVB = "rmvb"
    M2TS = "m2ts"
    MTS = "mts"
    DV = "dv"
    GXF = "gxf"
    TOD = "tod"
    MXF = "mxf"
    F4V = "f4v"


class SupportedSubtitleFormats(Enum):
    """ 支持的字幕格式 """
    SRT = "srt"
    ASS = "ass"
    VTT = "vtt"


class OutputSubtitleFormatEnum(Enum):
    """ 字幕输出格式 """
    SRT = "srt"
    ASS = "ass"
    VTT = "vtt"
    JSON = "json"
    TXT = "txt"


class TranscribeModelEnum(Enum):
    """ 转录模型 """
    JIANYING = "剪映"
    BIJIAN = "必剪"
    KUAISHOU = "快手"
    WHISPER = "Whisper"


class TargetLanguageEnum(Enum):
    """ 目标语言 """
    CHINESE_SIMPLIFIED = "简体中文"
    CHINESE_TRADITIONAL = "繁体中文"
    ENGLISH = "English"
    JAPANESE = "日本語"
    KOREAN = "Korean"
    FRENCH = "French"
    GERMAN = "German"
    SPANISH = "Spanish"
    ITALIAN = "Italian"
    PORTUGUESE = "Portuguese"
    RUSSIAN = "Russian"
    TURKISH = "Turkish"


class TranscribeLanguageEnum(Enum):
    """ 转录语言 """
    ENGLISH = "English"
    CHINESE = "Chinese"
    JAPANESE = "Japanese"
    KOREAN = "Korean"
    SPANISH = "Spanish"
    FRENCH = "French"
    GERMAN = "German"


LANGUAGES = {
    "English": "en",
    "Chinese": "zh",
    "Japanese": "ja",
    "Korean": "ko",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
}

SUPPORTED_AUDIO_FORMATS = "Audio files (*.mp3 *.wav *.m4a *.ogg *.opus *.flac);;\
Video files (*.mp4 *.webm *.ogm *.mov *.mkv *.avi *.wmv);;All files (*.*)"


@dataclass
class VideoInfo:
    """视频信息类"""
    file_name: str
    width: int
    height: int
    fps: float
    duration_seconds: float
    bitrate_kbps: int
    video_codec: str
    audio_codec: str
    audio_sampling_rate: int
    thumbnail_path: str


@dataclass
class Task:
    class Status(Enum):
        """ 任务状态 (下载、转录、优化、翻译、生成) """
        PENDING = "待处理"
        DOWNLOADING = "下载中"
        TRANSCRIBING = "转录中"
        OPTIMIZING = "优化中"
        TRANSLATING = "翻译中"
        GENERATING = "生成视频中"
        COMPLETED = "已完成"
        FAILED = "失败"
        CANCELED = "已取消"

    class Source(Enum):
        FILE_IMPORT = "文件导入"
        URL_IMPORT = "URL导入"

    # 任务信息
    id: int = field(default_factory=lambda: randint(0, 100_000_000))
    queued_at: Optional[datetime.datetime] = None
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    status: Status = Status.PENDING
    fraction_downloaded: float = 0.0
    work_dir: Optional[str] = None

    # 初始输入
    file_path: Optional[str] = None
    url: Optional[str] = None
    source: Source = Source.FILE_IMPORT
    original_language: Optional[str] = None
    target_language: Optional[str] = None
    video_info: Optional[VideoInfo] = None

    # 音频转换
    audio_format: Optional[str] = "mp3"
    audio_save_path: Optional[str] = None

    # 转录（转录模型）
    transcribe_model: Optional[TranscribeModelEnum] = TranscribeModelEnum.JIANYING
    transcribe_language: Optional[TranscribeLanguageEnum] = LANGUAGES[TranscribeLanguageEnum.ENGLISH.value]
    use_asr_cache: bool = True
    need_word_time_stamp: bool = False
    original_subtitle_save_path: Optional[str] = None

    # LLM（优化翻译模型）
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    llm_model: Optional[str] = None
    need_translate: bool = False
    need_optimize: bool = False
    result_subtitle_save_path: Optional[str] = None
    thread_num: int = 10
    batch_size: int = 10
    subtitle_layout: Optional[str] = None

    # 视频生成
    video_save_path: Optional[str] = None
    soft_subtitle: bool = True
    subtitle_style_srt: Optional[str] = None
