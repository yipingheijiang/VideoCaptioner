import datetime
import os
from pathlib import Path
from queue import Queue
from threading import Lock

from PyQt5.QtCore import *
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication, QLabel, QFileDialog, QMenu
from PyQt5.QtGui import QPixmap, QFont
from qfluentwidgets import ComboBox, SwitchButton, SimpleCardWidget, CaptionLabel, CardWidget, ToolTipFilter, \
    ToolTipPosition, LineEdit, PrimaryPushButton, ProgressBar, PushButton, InfoBar, BodyLabel, PillPushButton, setFont, \
    InfoBadge, InfoBadgePosition, ProgressRing, InfoBarPosition, ScrollArea, Action, RoundMenu, IconInfoBadge, InfoLevel
from qfluentwidgets import FluentIcon as FIF

from ..core.thread.create_task_thread import CreateTaskThread
from ..core.entities import Task, VideoInfo
from ..common.config import cfg
from ..components.ImageLable import ImageLabel
from ..core.thread.transcript_thread import TranscriptThread
from ..core.thread.subtitle_pipeline_thread import SubtitlePipelineThread

class BatchProcessInterface(QWidget):
    """批量处理界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BatchProcessInterface")
        self.setWindowTitle("批量处理")
        self.setAcceptDrops(True)

        self.tasks = []
        self.task_cards = []
        self.processing = False
        self.lock = Lock()
        self.create_threads = []
        self.setup_ui()
        self._initStyle()
        self.setup_signals()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        
        # 顶部操作布局
        self.top_layout = QHBoxLayout()
        self.top_layout.setSpacing(10)
        
        # 添加文件按钮
        self.add_file_button = PushButton("添加视频文件", self)
        self.top_layout.addWidget(self.add_file_button)
        
        # 清空任务按钮
        self.clear_all_button = PushButton("清空任务", self)
        self.top_layout.addWidget(self.clear_all_button)
        
        # 任务类型选择
        self.task_type_combo = ComboBox(self)
        self.task_type_combo.addItems(["视频加字幕", "音视频转录"])
        self.top_layout.addWidget(self.task_type_combo)
        
        self.top_layout.addStretch(1)

        # 添加启动和取消按钮
        self.start_all_button = PrimaryPushButton("开始处理", self)
        self.cancel_button = PushButton("取消", self)
        self.cancel_button.setEnabled(False)
        self.top_layout.addWidget(self.start_all_button)
        self.top_layout.addWidget(self.cancel_button)
        
        self.main_layout.addLayout(self.top_layout)

        # 创建滚动区域
        self.scroll_area = ScrollArea(self)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

    def _initStyle(self):
        """初始化样式"""
        self.scroll_widget.setObjectName("scrollWidget")
        self.setObjectName("BatchProcessInterface")
        self.setStyleSheet("""        
            BatchProcessInterface, #scrollWidget {
                background-color: transparent;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

    def setup_signals(self):
        self.add_file_button.clicked.connect(self.on_add_file)
        self.clear_all_button.clicked.connect(self.clear_all_tasks)
        self.start_all_button.clicked.connect(self.start_batch_process)
        self.cancel_button.clicked.connect(self.cancel_batch_process)

    def clear_all_tasks(self):
        """清空所有任务"""
        # 如果正在处理任务,不允许清空
        if self.processing:
            InfoBar.warning(
                self.tr("无法清空"),
                self.tr("正在处理的任务无法清空"),
                duration=2000,
                position=InfoBarPosition.BOTTOM,
                parent=self
            )
            return
            
        # 清空所有任务卡片
        for task_card in self.task_cards[:]:
            self.remove_task_card(task_card)
            
        InfoBar.success(
            self.tr("已清空"),
            self.tr("已清空所有任务"),
            duration=2000,
            position=InfoBarPosition.BOTTOM,
            parent=self
        )

    def start_batch_process(self):
        """开始批量处理"""
        self.processing = True
        self.start_all_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.add_file_button.setEnabled(False)
        self.clear_all_button.setEnabled(False)

        # 显示开始处理的通知
        InfoBar.success(
            self.tr("开始处理"),
            self.tr("开始批量处理任务"),
            duration=2000,
            position=InfoBarPosition.BOTTOM,
            parent=self
        )

        if not self.task_cards:
            InfoBar.warning(
                self.tr("警告"),
                self.tr("没有可处理的任务"),
                duration=2000,
                parent=self
            )
            return

        # 查找第一个未完成的任务并开始处理
        for task_card in self.task_cards:
            if task_card.task.status not in [Task.Status.COMPLETED, Task.Status.FAILED]:
                task_card.finished.connect(self.on_task_finished)
                task_card.error.connect(self.on_task_finished)
                task_card.start()
                break

    def cancel_batch_process(self):
        """取消批量处理"""
        self.processing = False
        self.start_all_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.add_file_button.setEnabled(True)
        self.clear_all_button.setEnabled(True)

        # 停止所有正在运行的任务
        for task_card in self.task_cards:
            if task_card.task.status in [Task.Status.TRANSCRIBING, Task.Status.PENDING, Task.Status.OPTIMIZING, Task.Status.GENERATING]:
                task_card.stop()

        # 显示取消处理的通知
        InfoBar.warning(
            self.tr("已取消"),
            self.tr("已取消批量处理任务"),
            duration=2000,
            position=InfoBarPosition.BOTTOM,
            parent=self
        )

    def on_task_finished(self, task):
        """单个任务完成的处理"""
        # 显示单个任务完成的通知
        InfoBar.success(
            self.tr("任务完成"),
            self.tr(f"任务已完成"),
            duration=2000,
            position=InfoBarPosition.BOTTOM,
            parent=self
        )

        # 查找下一个未完成的任务
        next_task = None
        for task_card in self.task_cards:
            if task_card.task.status not in [Task.Status.COMPLETED, Task.Status.FAILED]:
                next_task = task_card
                break

        if next_task:
            next_task.finished.connect(self.on_task_finished)
            next_task.start()
        else:
            # 所有任务都完成了
            self.on_batch_finished()

    def on_batch_finished(self):
        """批量处理完成的处理"""
        self.processing = False
        self.start_all_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.add_file_button.setEnabled(True)
        self.clear_all_button.setEnabled(True)

        # 显示所有任务完成的通知
        InfoBar.success(
            self.tr("全部完成"),
            self.tr("所有任务已处理完成"),
            duration=2000,
            position=InfoBarPosition.BOTTOM,
            parent=self
        )

    def on_add_file(self):
        """添加文件按钮点击事件"""
        self.create_task(r"C:\Users\weifeng\Videos\【卡卡】N进制演示器.mp4")
        # files, _ = QFileDialog.getOpenFileNames(self,"选择视频文件","","视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv)")
        # for file_path in files:
        #     self.create_task(file_path)

    def create_task(self, file_path):
        """创建新任务"""
        # 检查文件是否已存在
        for task in self.tasks:
            if task.file_path == file_path:
                InfoBar.warning(
                    self.tr("添加失败"),
                    self.tr("该文件已存在于任务列表中"),
                    duration=2000,
                    position=InfoBarPosition.BOTTOM,
                    parent=self
                )
                return
                
        task_type = 'transcription' if self.task_type_combo.currentText() == "音视频转录" else 'file'
        create_thread = CreateTaskThread(file_path, task_type)
        create_thread.finished.connect(self.add_task_card)
        create_thread.finished.connect(lambda: self.cleanup_thread(create_thread))
        self.create_threads.append(create_thread)
        create_thread.start()

    def cleanup_thread(self, thread):
        """清理完成的线程"""
        if thread in self.create_threads:
            self.create_threads.remove(thread)
            thread.deleteLater()

    def add_task_card(self, task: Task):
        """添加新的任务卡片"""
        task_card = TaskInfoCard(self)
        task_card.set_task(task)
        task_card.remove.connect(self.remove_task_card)
        self.task_cards.append(task_card)
        self.tasks.append(task)
        self.scroll_layout.addWidget(task_card)
        
        # 显示成功提示
        InfoBar.success(
            self.tr("添加成功"),
            self.tr(f"已添加视频: {task.video_info.file_name}"),
            duration=2000,
            position=InfoBarPosition.BOTTOM,
            parent=self
        )

    def remove_task_card(self, task_card):
        """移除任务卡片"""
        if task_card in self.task_cards:
            # 如果任务正在处理中,不允许删除
            if self.processing:
                InfoBar.warning(
                    self.tr("无法删除"),
                    self.tr("正在处理的任务无法删除"),
                    duration=2000,
                    position=InfoBarPosition.BOTTOM,
                    parent=self
                )
                return
                
            self.task_cards.remove(task_card)
            self.tasks.remove(task_card.task)
            self.scroll_layout.removeWidget(task_card)
            task_card.deleteLater()

            # 显示删除成功的通知
            InfoBar.success(
                self.tr("删除成功"),
                self.tr(f"已删除任务: {task_card.task.video_info.file_name}"),
                duration=2000,
                position=InfoBarPosition.BOTTOM,
                parent=self
            )

    def dragEnterEvent(self, event):
        """拖拽进入事件处理"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """拖拽放下事件处理"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')):
                self.create_task(file_path)


class TaskInfoCard(CardWidget):
    finished = pyqtSignal(Task)
    remove = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task: Task = None
        self.setup_ui()
        self.setup_signals()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.installEventFilter(ToolTipFilter(self, 100, ToolTipPosition.BOTTOM))

        self.transcript_thread = None
        self.subtitle_thread = None

    def setup_ui(self):
        self.setFixedHeight(150)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 15, 20, 15)
        self.layout.setSpacing(20)
        
        # 设置缩略图
        self.setup_thumbnail()
        # 设置视频信息
        self.setup_info_layout()
        # 设置按钮
        self.setup_button_layout()

        self.task_state = IconInfoBadge.info(FIF.REMOVE, self, target=self.video_title, position=InfoBadgePosition.TOP_RIGHT)

    def setup_thumbnail(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # TODO: 使用默认缩略图
        default_thumbnail_path = os.path.join(current_dir, "..", "resource", "default_thumbnail.jpg")

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
        
        # 设置视频标题
        self.video_title = BodyLabel("未选择视频", self)
        self.video_title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        self.video_title.setWordWrap(True)
        self.info_layout.addWidget(self.video_title, alignment=Qt.AlignTop)
        
        # 设置视频详细信息
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
        self.remove_button = PushButton("删除", self)
        self.open_folder_button = PushButton("打开文件夹", self)
        self.start_button = PrimaryPushButton("开始转录", self)
        self.button_layout.addWidget(self.remove_button)
        self.button_layout.addWidget(self.open_folder_button)
        self.button_layout.addWidget(self.start_button)

        self.start_button.setDisabled(True)

        button_widget = QWidget()
        button_widget.setLayout(self.button_layout)
        button_widget.setFixedWidth(150)
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
        self.update_tooltip()
    
    def update_tooltip(self):
        """更新tooltip"""
        # 设置整体tooltip
        strategy_text = "无"
        if self.task.need_optimize:
            strategy_text = "字幕优化"
        elif self.task.need_translate:
            strategy_text = f"字幕优化翻译 {self.task.target_language}"
        tooltip = f"转录模型: {self.task.transcribe_model.value}\n"
        if self.task.status == Task.Status.PENDING:
            tooltip += f"字幕策略: {strategy_text}\n"
        tooltip += f"任务状态: {self.task.status.value}"
        self.setToolTip(tooltip)

    def update_thumbnail(self, thumbnail_path):
        """更新视频缩略图"""
        pixmap = QPixmap(thumbnail_path).scaled(
            self.video_thumbnail.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_thumbnail.setPixmap(pixmap)

    def setup_signals(self):
        self.start_button.clicked.connect(self.start)
        self.open_folder_button.clicked.connect(self.on_open_folder_clicked)
        self.remove_button.clicked.connect(lambda: self.remove.emit(self))
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        menu = RoundMenu(parent=self)
        
        # 添加菜单项
        open_folder_action = Action("打开文件夹", self)
        open_folder_action.triggered.connect(self.on_open_folder_clicked)
        menu.addAction(open_folder_action)
        
        delete_action = Action("删除任务", self)
        delete_action.triggered.connect(lambda: self.remove.emit(self))
        menu.addAction(delete_action)
        
        reprocess_action = Action("重新处理", self)
        reprocess_action.triggered.connect(self.start)
        menu.addAction(reprocess_action)

        cancel_action = Action("取消任务", self)
        cancel_action.triggered.connect(self.cancel)
        menu.addAction(cancel_action)
        
        # 显示菜单
        menu.exec_(self.mapToGlobal(pos))

    def cancel(self):
        """修改任务状态"""
        self.update_tooltip()
        self.stop()
        self.task.status = Task.Status.CANCELED
        self.finished.emit(self.task)

    def stop(self):
        """停止转录"""
        if self.transcript_thread and self.transcript_thread.isRunning():
            self.transcript_thread.terminate()
        if self.subtitle_thread and self.subtitle_thread.isRunning():
            self.subtitle_thread.terminate()
        self.reset_ui()
        
        InfoBar.success(
            self.tr("已取消"),
            self.tr("任务已取消"),
            duration=2000,
            parent=self
        )

    def start(self):
        """开始转录按钮点击事件"""
        # 获取任务类型
        if self.task.status == Task.Status.COMPLETED:
            InfoBar.warning(
                self.tr("警告"),
                self.tr("该任务已完成"),
                duration=2000,
                parent=self
            )
            return

        self.progress_ring.show()
        self.progress_ring.setValue(100)
        self.start_button.setDisabled(True)
        self.remove_button.setDisabled(True)
        self.task_state.setLevel(InfoLevel.WARNING)
        self.task_state.setIcon(FIF.SYNC)

        # 开始转录过程
        if self.task.status == Task.Status.TRANSCRIBING:
            self.transcript_thread = TranscriptThread(self.task)
            self.transcript_thread.finished.connect(self.on_finished)
            self.transcript_thread.progress.connect(self.on_progress)
            self.transcript_thread.error.connect(self.on_error)
            self.transcript_thread.start()
        elif self.task.status == Task.Status.PENDING:
            self.subtitle_thread = SubtitlePipelineThread(self.task)
            self.subtitle_thread.finished.connect(self.on_finished)
            self.subtitle_thread.progress.connect(self.on_progress)
            self.subtitle_thread.error.connect(self.on_error)
            self.subtitle_thread.start()
        else:
            InfoBar.warning(
                self.tr("警告"),
                self.tr("任务状态错误"),
                duration=2000,
                parent=self
            )
            self.reset_ui()

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

    def on_progress(self, value, message):
        """更新转录进度"""
        self.start_button.setText(message)
        self.progress_ring.setValue(value)
        self.update_tooltip()

    def on_error(self, error):
        """处理转录错误"""
        self.reset_ui()
        self.task_state.setLevel(InfoLevel.ERROR)
        self.task_state.setIcon(FIF.CLOSE)
        
        self.update_tooltip()
        self.error.emit(error)
        InfoBar.error(
            self.tr("转录失败"),
            self.tr(error),
            duration=1500,
            parent=self
        )
    
    def on_finished(self, task):
        """转录完成处理"""
        self.reset_ui()
        self.task_state.setLevel(InfoLevel.SUCCESS)
        self.task_state.setIcon(FIF.ACCEPT)
        self.update_tooltip()

        self.finished.emit(task)

    def reset_ui(self):
        """重置UI状态"""
        self.start_button.setEnabled(True)
        self.start_button.setText("开始转录")
        self.remove_button.setEnabled(True)
        self.progress_ring.setValue(100)
        self.task_state.setLevel(InfoLevel.INFOAMTION)
        self.task_state.setIcon(FIF.REMOVE)

    def set_task(self, task):
        """设置任务并更新UI"""
        self.task = task
        self.update_info(self.task.video_info)
        self.reset_ui()