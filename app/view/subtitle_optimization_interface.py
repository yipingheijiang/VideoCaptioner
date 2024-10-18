# -*- coding: utf-8 -*-

import datetime
import os
from pathlib import Path
import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication, QLabel, QHeaderView, QFileDialog
from PyQt5.QtGui import QPixmap, QFont, QStandardItemModel, QDragEnterEvent, QDropEvent
from qfluentwidgets import ComboBox, SwitchButton, SimpleCardWidget, CaptionLabel, CardWidget, ToolTipFilter, \
    ToolTipPosition, LineEdit, PrimaryPushButton, ProgressBar, PushButton, InfoBar, BodyLabel, PillPushButton, setFont, \
    InfoBadge, ProgressRing, TableWidget, TableItemDelegate, TableView

from app.core.thread.subtitle_optimization_thread import SubtitleOptimizationThread
from ..core.bk_asr.ASRData import ASRData, from_srt
from ..core.thread.create_task_thread import CreateTaskThread
from PyQt5.QtWidgets import QTableWidgetItem,QAbstractItemView
from ..core.entities import Task, VideoInfo
from ..common.config import cfg
from ..components.ImageLable import ImageLabel
from ..core.thread.transcript_thread import TranscriptThread
# from ..core.thread.subtitle_optimization_thread import SubtitleOptimizationThread


class SubtitleTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return 4

    def data(self, index, role):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            row = index.row()
            col = index.column()
            item = list(self._data.values())[row]
            if col == 0:
                return QTime(0, 0, 0).addMSecs(item['start_time']).toString('hh:mm:ss.zzz')
            elif col == 1:
                return QTime(0, 0, 0).addMSecs(item['end_time']).toString('hh:mm:ss.zzz')
            elif col == 2:
                return item['original_subtitle']
            elif col == 3:
                return item['translated_subtitle']
        return None
    
    def update_data(self, new_data):
        """
        更新字幕数据并刷新表格显示
        
        :param new_data: 新的字幕数据字典
        """
        # 记录更新的行
        updated_rows = set()

        # 更新内部数据
        for key, value in new_data.items():
            if key in self._data:
                if "\n" in value:
                    original_subtitle, translated_subtitle = value.split("\n")
                    self._data[key]['original_subtitle'] = original_subtitle
                    self._data[key]['translated_subtitle'] = translated_subtitle
                else:
                    translated_subtitle = value
                    self._data[key]['translated_subtitle'] = translated_subtitle
                row = list(self._data.keys()).index(key)
                updated_rows.add(row)
        
        # 如果有更新，发出dataChanged信号
        if updated_rows:
            min_row = min(updated_rows)
            max_row = max(updated_rows)
            top_left = self.index(min_row, 2)
            bottom_right = self.index(max_row, 3)
            self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole, Qt.EditRole])

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()
            item = list(self._data.values())[row]
            if col == 0:
                time = QTime.fromString(value, 'hh:mm:ss.zzz')
                item['start_time'] = QTime(0, 0, 0).msecsTo(time)
            elif col == 1:
                time = QTime.fromString(value, 'hh:mm:ss.zzz')
                item['end_time'] = QTime(0, 0, 0).msecsTo(time)
            elif col == 2:
                item['original_subtitle'] = value
            elif col == 3:
                item['translated_subtitle'] = value
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        return False

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if cfg.need_translate:
                    return ["开始时间", "结束时间", "字幕内容", "翻译字幕"][section]
                else:
                    return ["开始时间", "结束时间", "字幕内容", "优化字幕"][section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None

class SubtitleOptimizationInterface(QWidget):
    """
    字幕优化界面类，用于显示和编辑字幕。
    """
    finished = pyqtSignal(Task)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setObjectName("main_layout")
        self.main_layout.setSpacing(20)

        # 顶部配置和操作按钮
        self.top_layout = QHBoxLayout()
        self.start_button = PrimaryPushButton("开始", self)
        self.file_select_button = PushButton("选择SRT文件", self)
        self.top_layout.addWidget(self.file_select_button)
        self.top_layout.addWidget(self.start_button)
        self.top_layout.addStretch(1)

        self.main_layout.addLayout(self.top_layout)

        # 中间字幕表格
        self.subtitle_table = TableView(self)
        self.model = SubtitleTableModel("")
        self.subtitle_table.setModel(self.model)  # 创建并设置模型

        self.subtitle_table.setBorderVisible(True)
        self.subtitle_table.setBorderRadius(8)
        self.subtitle_table.setWordWrap(True)
        self.subtitle_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.subtitle_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.subtitle_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.subtitle_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.subtitle_table.setColumnWidth(0, 120)
        self.subtitle_table.setColumnWidth(1, 120)
        self.subtitle_table.verticalHeader().setDefaultSectionSize(50)
        self.subtitle_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

        self.main_layout.addWidget(self.subtitle_table)

        # 底部进度条和状态信息
        self.bottom_layout = QHBoxLayout()
        self.progress_bar = ProgressBar(self)
        self.status_label = BodyLabel("就绪", self)
        self.status_label.setMinimumWidth(100)  # 设置最小宽度
        self.status_label.setAlignment(Qt.AlignCenter)  # 设置文本居中对齐
        self.bottom_layout.addWidget(self.progress_bar, 1)  # 进度条使用剩余空间
        self.bottom_layout.addWidget(self.status_label)  # 状态标签使用固定宽度
        self.main_layout.addLayout(self.bottom_layout)

        self.setup_signals()
        self.task = None

        # self.load_srt_file("E:\\GithubProject\\VideoCaptioner\\app\\core\\subtitles_llama-3.1-70b-versatile.srt")

    def setup_signals(self):
        """
        设置信号连接。
        """
        self.start_button.clicked.connect(self.on_start_clicked)
        self.file_select_button.clicked.connect(self.on_file_select)

    def on_start_clicked(self):
        """
        开始按钮点击时的处理函数。
        """
        self.start_button.setEnabled(False)
        self.file_select_button.setEnabled(False)

        # 更新 task 的配置为当前配置
        self.task.need_optimize = cfg.need_optimize.value
        self.task.need_translate = cfg.need_translate.value
        self.task.api_key = cfg.api_key.value
        self.task.base_url = cfg.api_base.value
        self.task.llm_model = cfg.model.value
        self.task.batch_size = cfg.batch_size.value
        self.task.thread_num = cfg.thread_num.value
        self.task.target_language = cfg.target_language.value.value

        # 创建字幕优化线程
        self.subtitle_optimization_thread = SubtitleOptimizationThread(self.task)
        self.subtitle_optimization_thread.finished.connect(self.on_subtitle_optimization_finished)
        self.subtitle_optimization_thread.progress.connect(self.on_subtitle_optimization_progress)
        self.subtitle_optimization_thread.update.connect(self.update_data)
        self.subtitle_optimization_thread.error.connect(self.on_subtitle_optimization_error)
        self.subtitle_optimization_thread.start()

        InfoBar.info(
            self.tr("开始优化"),
            self.tr("开始优化字幕"),
            duration=1500,
            parent=self
        )

    def on_file_select(self):
        """
        文件选择按钮点击时的处理函数。
        """
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "选择SRT文件", "", "SRT文件 (*.srt)")
        if file_path:
            self.load_srt_file(file_path)

    def load_srt_file(self, file_path):
        """
        加载SRT文件并更新界面
        """
        self.create_task_thread = CreateTaskThread(file_path, 'subtitle_optimization')
        self.task = self.create_task_thread.create_subtitle_optimization_task()
        asr_data = from_srt(Path(file_path).read_text(encoding="utf-8"))
        self.model._data = asr_data.to_json()
        self.model.layoutChanged.emit()
        self.status_label.setText(f"已加载文件")

    def update_data(self, data):
        """
        更新数据
        """
        self.model.update_data(data)
    
    def on_subtitle_optimization_finished(self, task: Task):
        """
        字幕优化完成时的处理函数。
        """
        self.start_button.setEnabled(True)
        self.file_select_button.setEnabled(True)
        
        # 更新 model 字幕数据
        # file_path = task.result_subtitle_save_path
        # print(file_path)
        # asr_data = from_srt(Path(file_path).read_text(encoding="utf-8"))
        # self.model._data = asr_data.to_json()
        # self.model.layoutChanged.emit()

        self.finished.emit(task)
        InfoBar.success(
            self.tr("优化完成"),
            self.tr("优化完成字幕"),
            duration=1500,
            parent=self
        )
    
    def on_subtitle_optimization_error(self, error):
        """
        字幕优化错误时的处理函数。
        """
        self.start_button.setEnabled(True)
        self.file_select_button.setEnabled(True)
        InfoBar.error(
            self.tr("优化失败"),
            self.tr(error),
            duration=1500,
            parent=self
        )

    def on_subtitle_optimization_progress(self, value, status):
        """
        字幕优化进度更新时的处理函数。
        """
        self.progress_bar.setValue(value)
        self.status_label.setText(status)

    def set_task(self, task: Task):
        """
        设置任务并更新界面
        """
        if task.status == Task.Status.OPTIMIZING:
            self.task = task
            self.load_srt_file(task.original_subtitle_save_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file_path in files:
            if file_path.lower().endswith('.srt'):
                self.load_srt_file(file_path)
                InfoBar.success(
                    self.tr("导入成功"),
                    self.tr("成功导入SRT文件"),
                    duration=1500,
                    parent=self
                )
                break
        event.accept()


if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = SubtitleOptimizationInterface()
    window.show()
    sys.exit(app.exec_())
