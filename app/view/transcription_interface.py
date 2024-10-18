# -*- coding: utf-8 -*-

import datetime
import os
import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication, QLabel, QFileDialog
from PyQt5.QtGui import QPixmap, QFont
from qfluentwidgets import ComboBox, SwitchButton, SimpleCardWidget, CaptionLabel, CardWidget, ToolTipFilter, \
    ToolTipPosition, LineEdit, PrimaryPushButton, ProgressBar, PushButton, InfoBar, BodyLabel, PillPushButton, setFont, \
    InfoBadge, IndeterminateProgressRing, ProgressRing, InfoBarPosition
from app.core.thread.create_task_thread import CreateTaskThread

from ..core.entities import Task, VideoInfo
from ..common.config import cfg
from ..components.ImageLable import ImageLabel
from ..core.thread.transcript_thread import TranscriptThread

class VideoInfoCard(CardWidget):
    finished = pyqtSignal(Task)
    
    """
    视频信息卡片组件
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task = None

        self.setFixedHeight(150)  # 设置卡片固定高度
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 15, 20, 15)
        self.layout.setSpacing(20)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_thumbnail_path = os.path.join(current_dir, "..", "resource", "default_thumbnail.jpg")

        # 左侧视频缩略图
        self.video_thumbnail = QLabel(self)
        self.video_thumbnail.setFixedSize(208, 117)  # 设置固定大小
        self.video_thumbnail.setStyleSheet("background-color: #1E1F22;")
        self.video_thumbnail.setAlignment(Qt.AlignCenter)  # 居中对齐
        pixmap = QPixmap(default_thumbnail_path).scaled(
            self.video_thumbnail.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_thumbnail.setPixmap(pixmap)
        self.layout.addWidget(self.video_thumbnail, 0, Qt.AlignLeft)  # 在布局中左对齐

        # 信息布局
        self.info_layout = QVBoxLayout()
        self.info_layout.setContentsMargins(3, 8, 3, 8)
        self.info_layout.setSpacing(10)
        
        # 视频标题
        self.video_title = BodyLabel("未选择视频", self)
        self.video_title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self.video_title.setWordWrap(True)  # 设置可以换行
        self.info_layout.addWidget(self.video_title, alignment=Qt.AlignTop)
        
        # 视频详细信息
        self.details_layout = QHBoxLayout()
        self.details_layout.setSpacing(15)
        
        self.resolution_info = PillPushButton("画质", self)
        self.resolution_info.setCheckable(False)
        setFont(self.resolution_info, 11)
        self.resolution_info.setFixedWidth(110)
        
        self.file_size_info = PillPushButton("文件大小", self)
        self.file_size_info.setCheckable(False)
        setFont(self.file_size_info, 11)
        self.file_size_info.setFixedWidth(110)
        
        self.duration_info = PillPushButton("时长", self)
        self.duration_info.setCheckable(False)
        setFont(self.duration_info, 11)
        self.duration_info.setFixedWidth(100)

        self.progress_ring = ProgressRing(self)
        self.progress_ring.setFixedSize(20, 20)
        self.progress_ring.setStrokeWidth(4)
        self.progress_ring.hide()

        self.details_layout.addWidget(self.resolution_info)
        self.details_layout.addWidget(self.file_size_info)
        self.details_layout.addWidget(self.duration_info)
        self.details_layout.addWidget(self.progress_ring)
        self.details_layout.addStretch(1)  # 添加弹性空间
        self.info_layout.addLayout(self.details_layout)
        self.layout.addLayout(self.info_layout)

        # 按钮布局
        self.button_layout = QVBoxLayout()
        self.remove_button = PushButton("删除", self)
        self.start_button = PrimaryPushButton("开始转录", self)
        self.button_layout.addWidget(self.remove_button)
        self.button_layout.addWidget(self.start_button)
        self.start_button.setDisabled(True)

        button_widget = QWidget()
        button_widget.setLayout(self.button_layout)
        button_widget.setFixedWidth(130)  # 设置固定宽度，可以根据需要调整
        self.layout.addWidget(button_widget)

        self.setup_signals()

    def update_info(self, video_info: VideoInfo):
        """
        更新视频信息
        """
        self.video_title.setText(video_info.file_name.rsplit('.', 1)[0])
        self.resolution_info.setText(f"画质: {video_info.width}x{video_info.height}")
        file_size_mb = video_info.bitrate_kbps * video_info.duration_seconds / 8 / 1024
        self.file_size_info.setText(f"大小: {file_size_mb:.1f} MB")

        duration = datetime.timedelta(seconds=int(video_info.duration_seconds))
        self.duration_info.setText(f"时长: {duration}")
        self.start_button.setDisabled(False)
        # 更新视频缩略图
        pixmap = QPixmap(video_info.thumbnail_path).scaled(
            self.video_thumbnail.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_thumbnail.setPixmap(pixmap)

    def setup_signals(self):
        self.start_button.clicked.connect(self.on_start_button_clicked)
    
    def on_start_button_clicked(self):
        self.progress_ring.show()
        self.progress_ring.setValue(100)
        self.start_button.setDisabled(True)

        self.transcript_thread = TranscriptThread(self.task)
        self.transcript_thread.finished.connect(self.on_transcript_finished)
        self.transcript_thread.progress.connect(self.on_transcript_progress)
        self.transcript_thread.error.connect(self.on_transcript_error)
        self.transcript_thread.start()

    def on_transcript_progress(self, value, message):
        self.start_button.setText(f"{message}")
        self.progress_ring.setValue(value)

    def on_transcript_error(self, error):
        self.start_button.setDisabled(False)
        self.start_button.setText("开始转录")
        self.progress_ring.setValue(100)
        InfoBar.error(
            self.tr("转录失败"),
            self.tr(error),
            duration=1500,
            parent=self
        )
    
    def on_transcript_finished(self, task):
        self.start_button.setDisabled(False)
        self.start_button.setText("开始转录")
        self.progress_ring.setValue(100)
        # 发送任务完成信号
        self.finished.emit(task)


class TranscriptionInterface(QWidget):
    """
    转录界面类，用于显示视频信息和转录进度。
    """
    finished = pyqtSignal(Task)  # 添加新的信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAcceptDrops(True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setObjectName("main_layout")
        self.main_layout.setSpacing(20)

        # 视频信息卡片
        self.video_info_card = VideoInfoCard(self)
        self.main_layout.addWidget(self.video_info_card)

        # 文件选择按钮
        self.file_select_button = PushButton("选择视频文件", self)
        self.main_layout.addWidget(self.file_select_button, alignment=Qt.AlignCenter)

        self.setup_signals()
        self.task = None

    def setup_signals(self):
        """
        设置信号连接。
        """
        self.file_select_button.clicked.connect(self.on_file_select)
        self.video_info_card.finished.connect(self.on_transcript_finished)

    def on_transcript_finished(self, task):
        self.finished.emit(task)
        InfoBar.success(
            self.tr("转录完成"),
            self.tr("开始字幕优化..."),
            duration=2000,
            position=InfoBarPosition.BOTTOM,
            parent=self.parent()
        )

    def on_file_select(self):
        """
        文件选择按钮点击时的处理函数。
        """
        desktop_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "选择视频文件", desktop_path, "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv)")
        if file_path:
            print(f"正在处理文件: {file_path}")
            self.create_task_thread = CreateTaskThread(file_path, 'transcription')
            self.create_task_thread.finished.connect(self.on_create_task_finished)
            self.create_task_thread.start()

    def update_video_info(self, file_path):
        """
        更新视频信息
        """
        self.video_info_card.update_info(file_path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file_path in files:
            if os.path.isfile(file_path):
                print(f"正在处理文件: {file_path}")
                self.create_task_thread = CreateTaskThread(file_path, 'transcription')
                self.create_task_thread.finished.connect(self.on_create_task_finished)
                self.create_task_thread.start()
                InfoBar.success(
                    self.tr("导入成功"),
                    self.tr("开始处理的视频文件"),
                    duration=1500,
                    parent=self
                )
                break
        

    def set_task(self, task: Task):
        """
        设置任务并更新界面
        """
        self.task = task
        self.video_info_card.task = task
        self.update_video_info(task.video_info)

    def on_create_task_finished(self, task):
        """
        创建任务完成时的处理函数
        """
        self.set_task(task)

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = TranscriptionInterface()
    window.show()
    sys.exit(app.exec_())