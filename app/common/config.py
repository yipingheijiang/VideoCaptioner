# coding:utf-8
from enum import Enum

from PyQt5.QtCore import QLocale
from PyQt5.QtGui import QColor
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            Theme, FolderValidator, ConfigSerializer, EnumSerializer)

from app.config import WORK_PATH, SETTINGS_PATH
from ..core.entities import TargetLanguageEnum, TranscribeModelEnum, TranscribeLanguageEnum, WhisperModelEnum


class Language(Enum):
    """ 软件语言 """
    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Chinese, QLocale.HongKong)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class SubtitleLayoutEnum(Enum):
    """ 字幕布局 """
    TRANSLATE_ON_TOP = "译文在上"
    ORIGINAL_ON_TOP = "原文在上"
    ONLY_ORIGINAL = "仅原文"
    ONLY_TRANSLATE = "仅译文"


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO



class Config(QConfig):
    """ 应用配置 """
    # LLM CONFIG
    api_key = ConfigItem("LLM", "API_Key", "")
    api_base = ConfigItem("LLM", "API_Base", "")
    model = ConfigItem("LLM", "Model", "gpt-4o-mini")
    batch_size = RangeConfigItem("LLM", "BatchSize", 10, RangeValidator(10, 30))
    thread_num = RangeConfigItem("LLM", "ThreadNum", 10, RangeValidator(1, 30))

    # 转录配置
    transcribe_model = OptionsConfigItem("Transcribe", "TranscribeModel", TranscribeModelEnum.JIANYING.value,
                                         OptionsValidator(TranscribeModelEnum), EnumSerializer(TranscribeModelEnum))
    use_asr_cache = ConfigItem("Transcribe", "UseASRCache", True, BoolValidator())
    transcribe_language = OptionsConfigItem("Transcribe", "TranscribeLanguage", TranscribeLanguageEnum.ENGLISH.value,
                                            OptionsValidator(TranscribeLanguageEnum),
                                            EnumSerializer(TranscribeLanguageEnum))
    # Whisper 配置
    whisper_model = OptionsConfigItem("Whisper", "Model", WhisperModelEnum.TINY.value,
                                      OptionsValidator(WhisperModelEnum), EnumSerializer(WhisperModelEnum))

    # 字幕配置
    need_optimize = ConfigItem("Subtitle", "NeedOptimize", True, BoolValidator())
    need_translate = ConfigItem("Subtitle", "NeedTranslate", False, BoolValidator())
    target_language = OptionsConfigItem("Subtitle", "TargetLanguage", TargetLanguageEnum.CHINESE_SIMPLIFIED.value,
                                        OptionsValidator(TargetLanguageEnum), EnumSerializer(TargetLanguageEnum))
    soft_subtitle = ConfigItem("Subtitle", "SoftSubtitle", False, BoolValidator())


    # 字幕样式配置
    subtitle_style_name = ConfigItem("SubtitleStyle", "StyleName", "default")
    subtitle_layout = ConfigItem("SubtitleStyle", "Layout", "仅译文")
    subtitle_preview_image = ConfigItem("SubtitleStyle", "PreviewImage", "")

    # 保存配置
    work_dir = ConfigItem("Save", "Work_Dir", WORK_PATH, FolderValidator())

    # 软件页面配置
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", False, BoolValidator())
    dpiScale = OptionsConfigItem("MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]),
                                 restart=True)
    language = OptionsConfigItem("MainWindow", "Language", Language.AUTO, OptionsValidator(Language),
                                 LanguageSerializer(), restart=True)

    # 更新
    checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", True, BoolValidator())


cfg = Config()
cfg.themeMode.value = Theme.DARK
cfg.themeColor.value = QColor("#ff28f08b")
qconfig.load(SETTINGS_PATH, cfg)
