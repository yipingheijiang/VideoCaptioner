# -*- coding: utf-8 -*-

import datetime
import os
from pathlib import Path
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
from ..core.thread.transcript_thread import TranscriptThread
from ..core.entities import SupportedVideoFormats, SupportedAudioFormats
from app.config import RESOURCE_PATH


DEFAULT_THUMBNAIL_PATH = RESOURCE_PATH / "assets" / "default_thumbnail.jpg"


class VideoInfoCard(CardWidget):
    finished = pyqtSignal(Task)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task = None
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        self.setFixedHeight(150)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 15, 20, 15)
        self.layout.setSpacing(20)
        
        self.setup_thumbnail()
        self.setup_info_layout()
        self.setup_button_layout()

    def setup_thumbnail(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_thumbnail_path = os.path.join(DEFAULT_THUMBNAIL_PATH)

        self.video_thumbnail = QLabel(self)
        self.video_thumbnail.setFixedSize(208, 117)
        self.video_thumbnail.setStyleSheet("background-color: #1E1F22;")
        self.video_thumbnail.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(default_thumbnail_path).scaled(
            self.video_thumbnail.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_thumbnail.setPixmap(pixmap)
        self.layout.addWidget(self.video_thumbnail, 0, Qt.AlignLeft)

    def setup_info_layout(self):
        self.info_layout = QVBoxLayout()
        self.info_layout.setContentsMargins(3, 8, 3, 8)
        self.info_layout.setSpacing(10)
        
        self.video_title = BodyLabel("未选择视频", self)
        self.video_title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self.video_title.setWordWrap(True)
        self.info_layout.addWidget(self.video_title, alignment=Qt.AlignTop)
        
        self.details_layout = QHBoxLayout()
        self.details_layout.setSpacing(15)
        
        self.resolution_info = self.create_pill_button("画质", 110)
        self.file_size_info = self.create_pill_button("文件大小", 110)
        self.duration_info = self.create_pill_button("时长", 100)

        self.progress_ring = ProgressRing(self)
        self.progress_ring.setFixedSize(20, 20)
        self.progress_ring.setStrokeWidth(4)
        self.progress_ring.hide()

        self.details_layout.addWidget(self.resolution_info)
        self.details_layout.addWidget(self.file_size_info)
        self.details_layout.addWidget(self.duration_info)
        self.details_layout.addWidget(self.progress_ring)
        self.details_layout.addStretch(1)
        self.info_layout.addLayout(self.details_layout)
        self.layout.addLayout(self.info_layout)

    def create_pill_button(self, text, width):
        button = PillPushButton(text, self)
        button.setCheckable(False)
        setFont(button, 11)
        button.setFixedWidth(width)
        return button

    def setup_button_layout(self):
        self.button_layout = QVBoxLayout()
        # self.remove_button = PushButton("删除", self)
        self.open_folder_button = PushButton("打开文件夹", self)
        self.start_button = PrimaryPushButton("开始转录", self)
        # self.button_layout.addWidget(self.remove_button)
        self.button_layout.addWidget(self.open_folder_button)
        self.button_layout.addWidget(self.start_button)

        self.start_button.setDisabled(True)

        button_widget = QWidget()
        button_widget.setLayout(self.button_layout)
        button_widget.setFixedWidth(130)
        self.layout.addWidget(button_widget)

    def update_info(self, video_info: VideoInfo):
        """更新视频信息显示"""
        self.video_title.setText(video_info.file_name.rsplit('.', 1)[0])
        self.resolution_info.setText(f"画质: {video_info.width}x{video_info.height}")
        file_size_mb = os.path.getsize(self.task.file_path) / 1024 / 1024
        self.file_size_info.setText(f"大小: {file_size_mb:.1f} MB")
        duration = datetime.timedelta(seconds=int(video_info.duration_seconds))
        self.duration_info.setText(f"时长: {duration}")
        self.start_button.setDisabled(False)
        self.update_thumbnail(video_info.thumbnail_path)

    def update_thumbnail(self, thumbnail_path):
        """更新视频缩略图"""
        pixmap = QPixmap(thumbnail_path).scaled(
            self.video_thumbnail.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_thumbnail.setPixmap(pixmap)

    def setup_signals(self):
        self.start_button.clicked.connect(self.on_start_button_clicked)
        self.open_folder_button.clicked.connect(self.on_open_folder_clicked)
    
    def on_start_button_clicked(self):
        """开始转录按钮点击事件"""
        self.progress_ring.show()
        self.progress_ring.setValue(100)
        self.start_button.setDisabled(True)
        self.start_transcription()

    def on_open_folder_clicked(self):
        """打开文件夹按钮点击事件"""
        if self.task and self.task.work_dir:
            original_subtitle_save_path = Path(self.task.original_subtitle_save_path)
            if original_subtitle_save_path.exists():
                os.system(f'explorer /select,"{str(original_subtitle_save_path)}"')
            else:
                os.startfile(self.task.work_dir)
        else:
            InfoBar.warning(
                self.tr("警告"),
                self.tr("没有可用的字幕文件夹"),
                duration=2000,
                parent=self
            )

    def start_transcription(self):
        """开始转录过程"""
        self.transcript_thread = TranscriptThread(self.task)
        self.transcript_thread.finished.connect(self.on_transcript_finished)
        self.transcript_thread.progress.connect(self.on_transcript_progress)
        self.transcript_thread.error.connect(self.on_transcript_error)
        self.transcript_thread.start()

    def on_transcript_progress(self, value, message):
        """更新转录进度"""
        self.start_button.setText(message)
        self.progress_ring.setValue(value)

    def on_transcript_error(self, error):
        """处理转录错误"""
        self.start_button.setEnabled(True)
        self.start_button.setText("重新转录")
        InfoBar.error(
            self.tr("转录失败"),
            self.tr(error),
            duration=1500,
            parent=self
        )
    
    def on_transcript_finished(self, task):
        """转录完成处理"""
        self.start_button.setEnabled(True)
        self.start_button.setText("转录完成")
        if self.task.status == Task.Status.PENDING:
            self.finished.emit(task)

    def reset_ui(self):
        """重置UI状态"""
        self.start_button.setDisabled(False)
        self.start_button.setText("开始转录")
        self.progress_ring.setValue(100)

    def set_task(self, task):
        """设置任务并更新UI"""
        self.task = task
        self.update_info(self.task.video_info)
        self.reset_ui()


class TranscriptionInterface(QWidget):
    """转录界面类,用于显示视频信息和转录进度"""
    finished = pyqtSignal(Task)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAcceptDrops(True)
        self.task = None

        self._init_ui()
        self._setup_signals()

    def _init_ui(self):
        """初始化UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setObjectName("main_layout")
        self.main_layout.setSpacing(20)

        self.video_info_card = VideoInfoCard(self)
        self.main_layout.addWidget(self.video_info_card)

        self.file_select_button = PushButton("选择视频文件", self)
        self.main_layout.addWidget(self.file_select_button, alignment=Qt.AlignCenter)

    def _setup_signals(self):
        """设置信号连接"""
        self.file_select_button.clicked.connect(self._on_file_select)
        self.video_info_card.finished.connect(self._on_transcript_finished)

    def _on_transcript_finished(self, task):
        """转录完成处理"""
        self.finished.emit(task)
        InfoBar.success(
            self.tr("转录完成"),
            self.tr("开始字幕优化..."),
            duration=2000,
            position=InfoBarPosition.BOTTOM,
            parent=self.parent()
        )

    def _on_file_select(self):
        """文件选择处理"""
        desktop_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        file_dialog = QFileDialog()
        
        # 构建文件过滤器
        video_formats = " ".join(f"*.{fmt.value}" for fmt in SupportedVideoFormats)
        audio_formats = " ".join(f"*.{fmt.value}" for fmt in SupportedAudioFormats)
        filter_str = f"媒体文件 ({video_formats} {audio_formats});;视频文件 ({video_formats});;音频文件 ({audio_formats})"
        
        file_path, _ = file_dialog.getOpenFileName(self, "选择媒体文件", desktop_path, filter_str)
        if file_path:
            self.create_task(file_path)

    def create_task(self, file_path):
        """创建任务"""
        self.create_task_thread = CreateTaskThread(file_path, 'transcription')
        self.create_task_thread.finished.connect(self.set_task)
        self.create_task_thread.start()

    def set_task(self, task: Task):
        """设置任务并更新UI"""
        self.task = task
        self.update_info()

    def update_info(self):
        """更新页面信息"""
        self.video_info_card.set_task(self.task)

    def process(self):
        """主处理函数"""
        self.video_info_card.start_transcription()

    def dragEnterEvent(self, event):
        """拖拽进入事件处理"""
        event.accept() if event.mimeData().hasUrls() else event.ignore()

    def dropEvent(self, event):
        """拖拽放下事件处理"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file_path in files:
            if not os.path.isfile(file_path):
                continue
                
            file_ext = os.path.splitext(file_path)[1][1:].lower()
            
            # 检查文件格式是否支持
            supported_formats = {fmt.value for fmt in SupportedVideoFormats} | {fmt.value for fmt in SupportedAudioFormats}
            is_supported = file_ext in supported_formats
                        
            if is_supported:
                self.create_task(file_path)
                InfoBar.success(
                    self.tr("导入成功"), 
                    self.tr("开始语音转文字"),
                    duration=1500,
                    parent=self
                )
                break
            else:
                InfoBar.error(
                    self.tr(f"格式错误{file_ext}"),
                    self.tr(f"请拖入音频或视频文件"),
                    duration=1500,
                    parent=self
                )

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = TranscriptionInterface()
    window.show()
    sys.exit(app.exec_())