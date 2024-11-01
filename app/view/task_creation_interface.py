# -*- coding: utf-8 -*-
import os
import sys
from urllib.parse import urlparse
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication, QLabel, QLineEdit, QPushButton, QProgressBar, QFileDialog
from PyQt5.QtGui import QPixmap

from PyQt5.sip import voidptr
from qfluentwidgets import ComboBox, SwitchButton, SimpleCardWidget, CaptionLabel, CardWidget, ToolTipFilter, \
    ToolTipPosition, LineEdit, PrimaryPushButton, ProgressBar, PushButton, InfoBar, InfoBarPosition, BodyLabel

from ..core.entities import TargetLanguageEnum, TranscribeModelEnum, Task, VideoInfo
from ..common.config import cfg
from ..core.thread.create_task_thread import CreateTaskThread
from ..components.SimpleSettingCard import ComboBoxSimpleSettingCard, SwitchButtonSimpleSettingCard
from ..core.entities import SupportedAudioFormats, SupportedVideoFormats

class TaskCreationInterface(QWidget):
    """
    任务创建界面类，用于创建和配置任务。
    """
    finished = pyqtSignal(Task)  # 该信号用于在任务创建完成后通知主窗口

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAcceptDrops(True)
        self.task = None
        self.setup_ui()
        self.setup_values()
        self.setup_signals()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setObjectName("main_layout")
        self.main_layout.setSpacing(20)

        self.setup_config_layout()
        self.setup_logo()
        self.setup_search_layout()
        self.setup_status_layout()
        self.setup_info_label()

    def setup_config_layout(self):
        self.config_layout = QHBoxLayout()
        self.config_layout.setObjectName("config_layout")
        self.config_layout.setSpacing(20)

        # 创建转录模型卡片
        self.transcription_model_card = ComboBoxSimpleSettingCard(
            "转录模型",
            "语音转换的模型",
            [model.value for model in TranscribeModelEnum],
            self
        )
        self.transcription_model_card.valueChanged.connect(
            lambda value: cfg.set(cfg.transcribe_model, TranscribeModelEnum(value))
        )

        # 创建字幕修正卡片
        self.subtitle_optimization_card = SwitchButtonSimpleSettingCard(
            "字幕修正",
            "使用AI大模型进行字幕修正",
            self
        )
        self.subtitle_optimization_card.checkedChanged.connect(self.on_subtitle_optimization_clicked)

        # 创建字幕翻译卡片
        self.subtitle_translation_card = SwitchButtonSimpleSettingCard(
            "字幕翻译",
            "使用AI大模型进行字幕修正和翻译",
            self
        )
        self.subtitle_translation_card.checkedChanged.connect(self.on_subtitle_translation_clicked)

        # 创建目标语言卡片
        self.target_language_card = ComboBoxSimpleSettingCard(
            "目标语言",
            "翻译的目标语言",
            [model.value for model in TargetLanguageEnum],
            self
        )
        self.target_language_card.valueChanged.connect(
            lambda value: cfg.set(cfg.target_language, TargetLanguageEnum(value))
        )

        self.config_layout.addWidget(self.transcription_model_card)
        self.config_layout.addWidget(self.subtitle_optimization_card)
        self.config_layout.addWidget(self.subtitle_translation_card)
        self.config_layout.addWidget(self.target_language_card)
        
        config_container = QWidget()
        config_container.setLayout(self.config_layout)
        config_container.setFixedHeight(70)
        
        self.main_layout.addWidget(config_container)

    def setup_logo(self):
        self.logo_label = QLabel(self)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.abspath(os.path.join(current_dir, "..", "resource", "logo.png"))
        self.logo_pixmap = QPixmap(logo_path)
        self.logo_label.setPixmap(self.logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.logo_label)
        self.main_layout.addSpacing(10)

    def setup_search_layout(self):
        self.search_layout = QHBoxLayout()
        self.search_layout.setContentsMargins(80, 0, 80, 0)
        self.search_input = LineEdit(self)
        self.search_input.setPlaceholderText("选择视频文件")
        self.search_input.setFixedHeight(40)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.focusOutEvent = lambda text: None
        self.start_button = PushButton("选择文件", self)
        self.start_button.setFixedSize(80, 40)
        self.search_layout.addWidget(self.search_input)
        self.search_layout.addWidget(self.start_button)
        self.main_layout.addLayout(self.search_layout)
        self.main_layout.addSpacing(100)

    def setup_status_layout(self):
        self.status_layout = QVBoxLayout()
        self.status_layout.setContentsMargins(50, 0, 30, 5)
        self.status_layout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.status_label = BodyLabel("准备就绪", self)
        self.status_label.setStyleSheet("font-size: 14px; color: #888888;")
        self.status_layout.addWidget(self.status_label, 0, Qt.AlignCenter)
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setFixedWidth(300)
        self.status_layout.addWidget(self.progress_bar, 0, Qt.AlignCenter)

        self.main_layout.addStretch(1)
        self.main_layout.addLayout(self.status_layout)
        self.main_layout.addSpacing(2)

    def setup_info_label(self):
        self.info_label = QLabel("© 2023 VideoCaptioner. 使用前请阅读使用说明", self)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 12px; color: #888888;")
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.info_label)

    def setup_signals(self):
        self.start_button.clicked.connect(self.on_start_clicked)
        self.search_input.textChanged.connect(self.on_search_input_changed)

    def setup_values(self):
        self.transcription_model_card.setValue(cfg.transcribe_model.value)
        self.target_language_card.setValue(cfg.target_language.value.value)
        self.subtitle_optimization_card.setChecked(cfg.need_optimize.value)
        self.subtitle_translation_card.setChecked(cfg.need_translate.value)
        self.target_language_card.setEnabled(self.subtitle_translation_card.isChecked())
        self.search_input.setText("C:/Users/weifeng/Videos/N进制演示器.mp4")

    def on_subtitle_optimization_clicked(self, checked):
        if cfg.api_base.value == "" and checked:
            InfoBar.warning(
                self.tr("警告，将使用自带小模型API"),
                self.tr("为确保字幕修正的准确性，建议到设置中配置自己的API"),
                duration=5000,
                parent=self,
                position=InfoBarPosition.BOTTOM_RIGHT
            )
        if checked and self.subtitle_translation_card.isChecked():
            self.subtitle_translation_card.setChecked(False)
        cfg.set(cfg.need_optimize, checked)
        
    def on_subtitle_translation_clicked(self, checked):
        if cfg.api_base.value == "" and checked:
            InfoBar.warning(
                self.tr("警告，将使用自带小模型API"),
                self.tr("为确保字幕修正的准确性，建议到设置中配置自己的API"),
                duration=10000,
                parent=self,
                position=InfoBarPosition.BOTTOM_RIGHT
            )
        if checked and self.subtitle_optimization_card.isChecked():
            self.subtitle_optimization_card.setChecked(False)

        self.target_language_card.setEnabled(checked)
        cfg.set(cfg.need_translate, checked)

    def on_start_clicked(self):
        if self.start_button.text() == "选择文件":
            desktop_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
            file_dialog = QFileDialog()
            
            # 构建文件过滤器
            video_formats = " ".join(f"*.{fmt.value}" for fmt in SupportedVideoFormats)
            audio_formats = " ".join(f"*.{fmt.value}" for fmt in SupportedAudioFormats)
            filter_str = f"媒体文件 ({video_formats} {audio_formats});;视频文件 ({video_formats});;音频文件 ({audio_formats})"
            
            file_path, _ = file_dialog.getOpenFileName(self, "选择媒体文件", desktop_path, filter_str)
            if file_path:
                self.search_input.setText(file_path)
            return
        
        self.process()

    def on_search_input_changed(self):
        if self.search_input.text():
            self.start_button.setText("开始")
            self.start_button.setStyleSheet("""
                QPushButton {
                    color: white;
                    background-color: #2F8D63;
                    border: none;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2E805C;
                }
                QPushButton:pressed {
                    background-color: #2E905C;
                }
            """)
        else:
            self.start_button.setText("选择文件")
            self.start_button.setStyleSheet("""
                QPushButton {
                    color: #333;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)

    def dragEnterEvent(self, event):
        event.accept() if event.mimeData().hasUrls() else event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file_path in files:
            if not os.path.isfile(file_path):
                continue
                
            file_ext = os.path.splitext(file_path)[1][1:].lower()
            
            # 检查文件格式是否支持
            supported_formats = {fmt.value for fmt in SupportedVideoFormats} | {fmt.value for fmt in SupportedAudioFormats}
            is_supported = file_ext in supported_formats
                        
            if is_supported:
                self.search_input.setText(file_path)
                self.status_label.setText("导入成功")
                InfoBar.success(
                    self.tr("导入成功"), 
                    self.tr("导入媒体文件成功"),
                    duration=1500,
                    parent=self
                )
                break
            else:
                InfoBar.error(
                    self.tr("格式错误"),
                    self.tr("不支持该文件格式"),
                    duration=1500,
                    parent=self
                )

    def create_task(self):
        search_input = self.search_input.text()
        if os.path.isfile(search_input):
            self._process_file(search_input)
        elif self._is_valid_url(search_input):
            self._process_url(search_input)
        else:
            InfoBar.error(
                self.tr("错误"),
                self.tr("请输入有效的文件路径或视频URL"),
                duration=1500,
                parent=self
            )

    def _is_valid_url(self, url):
        try:
            result = urlparse(url)
            return result.scheme in ('http', 'https') and bool(result.netloc)
        except ValueError:
            return False

    def _process_file(self, file_path):
        print(f"正在处理文件: {file_path}")
        self.create_task_thread = CreateTaskThread(file_path, 'file')
        self.create_task_thread.finished.connect(self.on_create_task_finished)
        self.create_task_thread.progress.connect(self.on_create_task_progress)
        self.create_task_thread.start()

    def _process_url(self, url):
        print(f"正在处理URL: {url}")
        self.create_task_thread = CreateTaskThread(url, 'url')
        self.create_task_thread.finished.connect(self.on_create_task_finished)
        self.create_task_thread.progress.connect(self.on_create_task_progress)
        self.create_task_thread.error.connect(self.on_create_task_error)
        self.create_task_thread.start()

    def on_create_task_finished(self, task):
        self.task = task
        if self.task.status == Task.Status.PENDING:
            self.finished.emit(task)
        InfoBar.success(
            self.tr("任务创建成功"),
            self.tr("开始自动处理..."),
            duration=2000,
            position=InfoBarPosition.BOTTOM,
            parent=self.parent()
        )

    def on_create_task_progress(self, value, status):
        self.progress_bar.setValue(value)
        self.status_label.setText(status)

    def on_create_task_error(self, error):
        InfoBar.error(
            self.tr("错误"),
            self.tr(error),
            duration=5000,
            parent=self
        )

    def set_task(self, task):
        self.task = task
        self.update_info()

    def update_info(self):
        if self.task:
            self.search_input.setText(self.task.file_path)

    def process(self):
        search_input = self.search_input.text()
        if os.path.isfile(search_input):
            self._process_file(search_input)
        elif self._is_valid_url(search_input):
            self._process_url(search_input)
        else:
            InfoBar.error(
                self.tr("错误"),
                self.tr("请输入音视频文件路径或URL"),
                duration=1500,
                parent=self
            )


if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = TaskCreationInterface()
    window.show()
    sys.exit(app.exec_())