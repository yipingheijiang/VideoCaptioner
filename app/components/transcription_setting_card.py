from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QScrollArea
from qfluentwidgets import (CardWidget, ComboBox, HyperlinkCard,
                          ComboBoxSettingCard, SwitchSettingCard, SettingCardGroup,
                          FluentIcon as FIF, BodyLabel, RangeSettingCard, SingleDirectionScrollArea)

from .LineEditSettingCard import LineEditSettingCard
from .EditComboBoxSettingCard import EditComboBoxSettingCard
from app.components.SpinBoxSettingCard import DoubleSpinBoxSettingCard
from ..common.config import cfg
from ..core.entities import (TranscribeModelEnum, WhisperModelEnum, 
                           TranscribeLanguageEnum, FasterWhisperModelEnum,
                           VadMethodEnum)
from .FasterWhisperSettingWidget import FasterWhisperSettingWidget
from .WhisperCppSettingWidget import WhisperCppSettingWidget
from .WhisperAPISettingWidget import WhisperAPISettingWidget

class TranscriptionSettingCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # 标题和模型选择布局
        self.header_layout = QHBoxLayout()
        self.title_label = BodyLabel(self.tr("转录设置"), self)
        
        self.model_combo = ComboBox(self)
        self.model_combo.addItems([
            TranscribeModelEnum.WHISPER_CPP.value,
            TranscribeModelEnum.WHISPER_API.value,
            TranscribeModelEnum.FASTER_WHISPER.value
        ])
        self.model_combo.setCurrentText(cfg.transcribe_model.value)
        
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch(1)
        self.header_layout.addWidget(self.model_combo)
        
        # 设置界面堆叠
        self.stacked_widget = QStackedWidget(self)
        
        # 添加各个设置界面
        self.whisper_cpp_widget = WhisperCppSettingWidget(self)
        self.whisper_api_widget = WhisperAPISettingWidget(self)
        self.faster_whisper_widget = FasterWhisperSettingWidget(self)
        
        self.stacked_widget.addWidget(self.whisper_cpp_widget)
        self.stacked_widget.addWidget(self.whisper_api_widget)
        self.stacked_widget.addWidget(self.faster_whisper_widget)
        
        # 将组件添加到主布局
        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addWidget(self.stacked_widget)

    def setup_signals(self):
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        
    def on_model_changed(self, value):
        # 更新配置
        cfg.set(cfg.transcribe_model, TranscribeModelEnum(value))
        
        # 切换对应的设置界面
        if value == TranscribeModelEnum.WHISPER_CPP.value:
            self.stacked_widget.setCurrentWidget(self.whisper_cpp_widget)
        elif value == TranscribeModelEnum.WHISPER_API.value:
            self.stacked_widget.setCurrentWidget(self.whisper_api_widget)
        elif value == TranscribeModelEnum.FASTER_WHISPER.value:
            self.stacked_widget.setCurrentWidget(self.faster_whisper_widget) 