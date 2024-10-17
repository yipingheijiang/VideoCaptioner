# -*- coding: utf-8 -*-

import datetime
import os
import sys
from urllib.parse import urlparse
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication, QLabel, QLineEdit, QPushButton, QProgressBar, QFileDialog
from PyQt5.QtGui import QPixmap

from PyQt5.sip import voidptr
from qfluentwidgets import ComboBox, SwitchButton, SimpleCardWidget, CaptionLabel, CardWidget, ToolTipFilter, \
    ToolTipPosition, LineEdit, PrimaryPushButton, ProgressBar, PushButton, InfoBar, InfoBarPosition

from ..core.entities import TargetLanguageEnum, TranscribeModelEnum, OutputFormatEnum, Task, VideoInfo
from ..common.config import cfg
from ..core.utils.video_utils import get_video_info
from ..core.thread.create_task_thread import CreateTaskThread

class TaskCreationInterface(QWidget):
    """
    任务创建界面类，用于创建和配置任务。
    """
    finished = pyqtSignal(Task)  # 该信号用于在任务创建完成后通知主窗口


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAcceptDrops(True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setObjectName("main_layout")
        self.main_layout.setSpacing(20)

        # 1. 配置栏
        self.config_layout = QHBoxLayout()
        self.config_layout.setObjectName("config_layout")
        self.config_layout.setSpacing(20)

        self.transcription_model_card = self.create_card("transcription_model_card", "转录模型", ComboBox, "语音转换的模型")
        self.subtitle_optimization_card = self.create_card("subtitle_optimization_card", "字幕修正", SwitchButton, "使用AI大模型进行字幕修正")
        self.subtitle_translation_card = self.create_card("subtitle_translation_card", "字幕翻译", SwitchButton, "使用AI大模型进行字幕修正和翻译")
        self.target_language_card = self.create_card("target_language_card", "目标语言", ComboBox, "翻译的目标语言")

        self.config_layout.addWidget(self.transcription_model_card)
        self.config_layout.addWidget(self.subtitle_optimization_card)
        self.config_layout.addWidget(self.subtitle_translation_card)
        self.config_layout.addWidget(self.target_language_card)
        
        # 创建一个容器widget来包含config_layout
        config_container = QWidget()
        config_container.setLayout(self.config_layout)
        config_container.setFixedHeight(70)
        
        self.main_layout.addWidget(config_container)

        # 2. Logo
        self.logo_label = QLabel(self)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.abspath(os.path.join(current_dir, "..", "resource", "logo.png"))
        self.logo_pixmap = QPixmap(logo_path)
        self.logo_label.setPixmap(self.logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.logo_label)
        self.main_layout.addSpacing(10)

        # 3. 搜索框和开始按钮
        self.search_layout = QHBoxLayout()
        self.search_layout.setContentsMargins(80, 0, 80, 0)  # 设置左右边距
        self.search_input = LineEdit(self)
        self.search_input.setPlaceholderText("选择视频文件")
        self.search_input.setFixedHeight(40)  # 设置固定高度
        self.search_input.setClearButtonEnabled(True)
        self.search_input.focusOutEvent = lambda text: None
        # self.search_input.setReadOnly(True)  # 设置为只读
        self.start_button = PushButton("选择文件", self)
        self.start_button.setFixedSize(80, 40)  # 设置固定大小
        self.search_layout.addWidget(self.search_input)
        self.search_layout.addWidget(self.start_button)
        self.main_layout.addLayout(self.search_layout)
        self.main_layout.addSpacing(100)

        # 4. 状态栏
        self.status_layout = QVBoxLayout()  # 垂直布局
        self.status_layout.setContentsMargins(50, 0, 30, 5)  # 减少上下边距
        self.status_layout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)  # 底部居中对齐
        self.status_label = QLabel("准备就绪", self)
        self.status_label.setStyleSheet("font-size: 14px; color: #888888;")
        self.status_layout.addWidget(self.status_label, 0, Qt.AlignCenter)
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setFixedWidth(300)  # 设置固定宽度
        self.status_layout.addWidget(self.progress_bar, 0, Qt.AlignCenter)  # 设置进度条居中对齐

        self.main_layout.addStretch(1)  # 添加弹性空间，将状态栏推到底部
        self.main_layout.addLayout(self.status_layout)
        self.main_layout.addSpacing(2)  # 在状态栏下方添加一些空间

        # 5. 信息栏
        self.info_label = QLabel("© 2023 VideoCaptioner. 使用前请阅读使用说明", self)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 12px; color: #888888;")
        self.main_layout.addStretch()  # 添加弹性空间
        self.main_layout.addWidget(self.info_label)

        self.setup_values()
        self.setup_signals()


    def create_card(self, objectName, label_text, widget_type, tooltip_text):
        """
        创建一个卡片控件。

        :param objectName: 对象名称
        :param label_text: 标签文本
        :param widget_type: 控件类型
        :param tooltip_text: 工具提示文本
        :return: 创建的卡片控件
        """
        card = CardWidget(self)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 10, 8, 10)
        layout.setSpacing(8)

        label = CaptionLabel(card)
        label.setText(label_text)
        layout.addWidget(label)

        layout.addStretch(1)

        widget = widget_type(card)
        widget.setObjectName(objectName)

        if isinstance(widget, SwitchButton):
            widget.setOnText("开")
            widget.setOffText("关")
            card.clicked.connect(lambda: widget.setChecked(not widget.isChecked()))
        
        layout.addWidget(widget)
        
        # 设置工具提示
        card.setToolTip(tooltip_text)
        card.installEventFilter(ToolTipFilter(card, 300, ToolTipPosition.BOTTOM))

        return card

    def setup_signals(self):
        """
        设置信号连接。
        """
        self.transcription_model_card.findChild(ComboBox).currentIndexChanged.connect(self.on_transcription_model_changed)
        self.subtitle_optimization_card.findChild(SwitchButton).checkedChanged.connect(self.on_subtitle_optimization_clicked)
        self.subtitle_translation_card.findChild(SwitchButton).checkedChanged.connect(self.on_subtitle_translation_clicked)
        self.target_language_card.findChild(ComboBox).currentIndexChanged.connect(self.on_target_language_changed)
        self.start_button.clicked.connect(self.on_start_clicked)
        self.search_input.textChanged.connect(self.on_search_input_changed)

    def setup_values(self):
        """
        设置初始值。
        """
        # 设置转录模型选项
        transcription_model_combo = self.transcription_model_card.findChild(ComboBox)
        transcription_model_combo.addItems([model.value for model in TranscribeModelEnum])
        transcription_model_combo.setCurrentText(cfg.transcribe_model.value)

        # 设置目标语言选项
        target_language_combo = self.target_language_card.findChild(ComboBox)
        target_language_combo.addItems([model.value for model in TargetLanguageEnum])
        target_language_combo.setCurrentText(cfg.target_language.value.value)

        # 设置字幕优化和翻译开关的初始状态
        self.subtitle_optimization_card.findChild(SwitchButton).setChecked(cfg.need_optimize.value)
        self.subtitle_translation_card.findChild(SwitchButton).setChecked(cfg.need_translate.value)

        # 初始化时禁用目标语言选择
        translation_switch = self.subtitle_translation_card.findChild(SwitchButton)
        self.target_language_card.setEnabled(translation_switch.isChecked())
        
        self.search_input.setText("C:/Users/weifeng/Videos/xhs.mp4")

    def on_transcription_model_changed(self, index):
        """
        转录模型改变时的处理函数。

        :param index: 选中的索引
        """
        selected_model = self.transcription_model_card.findChild(ComboBox).currentText()
        cfg.set(cfg.transcribe_model, selected_model)

    def on_subtitle_optimization_clicked(self):
        """
        字幕优化开关点击时的处理函数。
        """
        optimization_switch = self.subtitle_optimization_card.findChild(SwitchButton)
        translation_switch = self.subtitle_translation_card.findChild(SwitchButton)

        if cfg.api_base.value == "" and optimization_switch.isChecked():
            InfoBar.error(
                self.tr("错误"),
                self.tr("请先到设置中配置API"),
                duration=1500,
                parent=self
            )
            optimization_switch.setChecked(False)
            return

        if optimization_switch.isChecked() and translation_switch.isChecked():
            translation_switch.setChecked(False)
            
        cfg.set(cfg.need_optimize, optimization_switch.isChecked())
        
    def on_subtitle_translation_clicked(self):
        """
        字幕翻译开关点击时的处理函数。
        """
        optimization_switch = self.subtitle_optimization_card.findChild(SwitchButton)
        translation_switch = self.subtitle_translation_card.findChild(SwitchButton)
        target_language_combo = self.target_language_card.findChild(ComboBox)

        if cfg.api_base.value == "" and translation_switch.isChecked():
            InfoBar.error(
                self.tr("错误"),
                self.tr("请先到设置中配置API"),
                duration=1500,
                parent=self
            )
            translation_switch.setChecked(False)
            return

        if optimization_switch.isChecked() and translation_switch.isChecked():
            optimization_switch.setChecked(False)

        # 当字幕翻译开启时，目标语言下拉框才可点击
        target_language_combo.setEnabled(translation_switch.isChecked())
        self.target_language_card.setEnabled(translation_switch.isChecked())

        cfg.set(cfg.need_translate, translation_switch.isChecked())

    def on_target_language_changed(self, index):
        """
        目标语言改变时的处理函数。

        :param index: 选中的索引
        """
        target_language_combo = self.target_language_card.findChild(ComboBox)
        selected_language = target_language_combo.currentText()
        cfg.set(cfg.target_language, TargetLanguageEnum(selected_language))

    def on_start_clicked(self):
        """
        开始按钮点击时的处理函数。
        """
        if self.start_button.text() == "选择文件":
            desktop_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
            file_dialog = QFileDialog()
            video_file, _ = file_dialog.getOpenFileName(self, "选择视频文件", desktop_path, "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv)")
            if video_file:
                self.search_input.setText(video_file)
            return
        
        search_input = self.search_input.text()
        if os.path.isfile(search_input):
            self._process_file(search_input)
        elif self._is_valid_url(search_input):
            self._process_url(search_input)
        else:
            # 如果既不是文件也不是有效的URL
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
        # 处理文件的逻辑
        print(f"正在处理文件: {file_path}")
        self.create_task_thread = CreateTaskThread(file_path, 'file')
        self.create_task_thread.finished.connect(self.on_create_task_finished)
        self.create_task_thread.start()

    def _process_url(self, url):
        # 处理URL的逻辑
        print(f"正在处理URL: {url}")

    def on_create_task_finished(self, task):
        # 发出信号，传递创建的任务
        self.finished.emit(task)
        InfoBar.success(
            self.tr("任务创建成功"),
            self.tr("开始自动处理..."),
            duration=2000,
            position=InfoBarPosition.BOTTOM,
            parent=self.parent()
        )

    def on_search_input_changed(self):
        """
        搜索栏内容改变时的处理函数。
        """
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

    # 支持文件拖拽
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file_path in files:
            if os.path.isfile(file_path):
                self.search_input.setText(file_path)
                break
        # 显示导入成功
        self.status_label.setText("导入成功")
        InfoBar.success(
            self.tr("导入成功"),
            self.tr("导入视频文件成功"),
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
