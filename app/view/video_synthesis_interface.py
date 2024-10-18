# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QApplication, 
                             QFileDialog, QProgressBar, QStatusBar)
from PyQt5.QtGui import QFont
from qfluentwidgets import (ComboBox, SwitchButton, SimpleCardWidget, CaptionLabel, 
                            CardWidget, PrimaryPushButton, LineEdit, BodyLabel,
                            InfoBar, InfoBarPosition, ProgressBar, PushButton)

from app.core.thread.create_task_thread import CreateTaskThread
from app.core.thread.video_synthesis_thread import VideoSynthesisThread

class VideoSynthesisInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)

        # 配置卡片
        self.config_card = CardWidget(self)
        self.config_layout = QVBoxLayout(self.config_card)
        self.config_layout.setSpacing(15)
        self.config_layout.setContentsMargins(20, 10, 20, 10)

        # 字幕文件选择
        self.subtitle_layout = QHBoxLayout()
        self.subtitle_layout.setSpacing(10)
        self.subtitle_label = BodyLabel("字幕文件:", self)
        self.subtitle_input = LineEdit(self)
        self.subtitle_input.setPlaceholderText("选择字幕文件")
        self.subtitle_button = PushButton("浏览", self)
        self.subtitle_layout.addWidget(self.subtitle_label)
        self.subtitle_layout.addWidget(self.subtitle_input)
        self.subtitle_layout.addWidget(self.subtitle_button)
        self.config_layout.addLayout(self.subtitle_layout)

        # 视频文件选择
        self.video_layout = QHBoxLayout()
        self.video_layout.setSpacing(10)
        self.video_label = BodyLabel("视频文件:", self)
        self.video_input = LineEdit(self)
        self.video_input.setPlaceholderText("选择视频文件")
        self.video_button = PushButton("浏览", self)
        self.video_layout.addWidget(self.video_label)
        self.video_layout.addWidget(self.video_input)
        self.video_layout.addWidget(self.video_button)
        self.config_layout.addLayout(self.video_layout)

        self.main_layout.addWidget(self.config_card)

        # 合成按钮和打开文件夹按钮
        self.button_layout = QHBoxLayout()
        self.synthesize_button = PushButton("开始合成", self)
        self.open_folder_button = PushButton("打开视频文件夹", self)
        self.button_layout.addWidget(self.synthesize_button)
        self.button_layout.addWidget(self.open_folder_button)
        self.main_layout.addLayout(self.button_layout)

        self.main_layout.addStretch(1)
        # 底部进度条和状态信息
        self.bottom_layout = QHBoxLayout()
        self.progress_bar = ProgressBar(self)
        self.status_label = BodyLabel("就绪", self)
        self.status_label.setMinimumWidth(100)  # 设置最小宽度
        self.status_label.setAlignment(Qt.AlignCenter)  # 设置文本居中对齐
        self.bottom_layout.addWidget(self.progress_bar, 1)  # 进度条使用剩余空间
        self.bottom_layout.addWidget(self.status_label)  # 状态标签使用固定宽度
        self.main_layout.addLayout(self.bottom_layout)

        self.set_value()
        self.setup_signals()

        self.task = None

    def setup_signals(self):
        self.subtitle_button.clicked.connect(self.choose_subtitle_file)
        self.video_button.clicked.connect(self.choose_video_file)
        self.synthesize_button.clicked.covnnect(self.start_synthesis)
        self.open_folder_button.clicked.connect(self.open_video_folder)

    def set_value(self):
        self.subtitle_input.setText("E:/GithubProject/VideoCaptioner/app/core/subtitles0.srt")
        self.video_input.setText("C:/Users/weifeng/Videos/佛山周末穷游好去处!.mp4")

    def choose_subtitle_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择字幕文件", "", "字幕文件 (*.srt)")
        if file_path:
            self.subtitle_input.setText(file_path)

    def choose_video_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "", "视频文件 (*.mp4 *.avi *.mov)")
        if file_path:
            self.video_input.setText(file_path)

    def start_synthesis(self):
        print("start_synthesis")
        subtitle_file = self.subtitle_input.text()
        video_file = self.video_input.text()
        if not subtitle_file or not video_file:
            InfoBar.error(
                "错误",
                "请选择字幕文件和视频文件",
                duration=2000,
                position=InfoBarPosition.TOP,
                parent=self
            )
            return
        
        if not self.task:
            self.task = CreateTaskThread.create_video_synthesis_task(subtitle_file, video_file)
        # print(self.task)
        self.video_synthesis_thread = VideoSynthesisThread(self.task)
        self.video_synthesis_thread.finished.connect(self.on_video_synthesis_finished)
        self.video_synthesis_thread.progress.connect(self.on_video_synthesis_progress)
        self.video_synthesis_thread.error.connect(self.on_video_synthesis_error)
        self.video_synthesis_thread.start()

    def on_video_synthesis_finished(self, task):
        InfoBar.success(
            "成功",
            "视频合成已完成",
            duration=2000,
            position=InfoBarPosition.TOP,
            parent=self
        )
    
    def on_video_synthesis_progress(self, progress, message):
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)

    def on_video_synthesis_error(self, error):
        InfoBar.error(
            "错误",
            str(error),
            duration=2000,
            position=InfoBarPosition.TOP,
            parent=self
        )
    
    def set_task(self, task):
        self.task = task

    def open_video_folder(self):
        if self.task and self.task.video_save_path:
            folder_path = os.path.dirname(self.task.video_save_path)
            os.startfile(folder_path)
        else:
            InfoBar.warning(
                "警告",
                "没有可用的视频文件夹",
                duration=2000,
                position=InfoBarPosition.TOP,
                parent=self
            )

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = VideoSynthesisInterface()
    window.resize(600, 400)  # 设置窗口大小
    window.show()
    sys.exit(app.exec_())