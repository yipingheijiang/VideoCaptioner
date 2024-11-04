# coding:utf-8
from asyncio import Task
import sys

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget, QVBoxLayout, QLabel, QSizePolicy
from qfluentwidgets import SegmentedWidget

from .task_creation_interface import TaskCreationInterface
from .transcription_interface import TranscriptionInterface
from .subtitle_optimization_interface import SubtitleOptimizationInterface
from .video_synthesis_interface import VideoSynthesisInterface
from ..core.entities import Task

class HomeInterface(QWidget):
    finished = pyqtSignal(Task)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName('HomeInterface')
        self.setStyleSheet("""
            HomeInterface{background: white}
        """)

        self.pivot = SegmentedWidget(self)
        self.pivot.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.task_creation_interface = TaskCreationInterface(self)
        self.transcription_interface = TranscriptionInterface(self)
        self.subtitle_optimization_interface = SubtitleOptimizationInterface(self)
        self.video_synthesis_interface = VideoSynthesisInterface(self)

        # 添加子界面
        self.addSubInterface(self.task_creation_interface, 'TaskCreationInterface', self.tr('任务创建'))
        self.addSubInterface(self.transcription_interface, 'TranscriptionInterface', self.tr('语音转录'))
        self.addSubInterface(self.subtitle_optimization_interface, 'SubtitleOptimizationInterface', self.tr('字幕优化与翻译'))
        self.addSubInterface(self.video_synthesis_interface, 'VideoSynthesisInterface', self.tr('字幕视频合成'))

        self.vBoxLayout.addWidget(self.pivot)  # 将pivot居中对齐
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(30, 10, 30, 30)

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.task_creation_interface)
        self.pivot.setCurrentItem('TaskCreationInterface')  # 使用字符串而不是对象名

        self.task_creation_interface.finished.connect(self.switch_to_transcription)
        self.transcription_interface.finished.connect(self.switch_to_subtitle_optimization)
        self.subtitle_optimization_interface.finished.connect(self.switch_to_video_synthesis)
    
    def switch_to_transcription(self, task):
        # 切换到转录界面
        self.transcription_interface.set_task(task)  # 假设TranscriptionInterface有一个set_task方法
        self.stackedWidget.setCurrentWidget(self.transcription_interface)
        self.pivot.setCurrentItem('TranscriptionInterface')
    
    def switch_to_subtitle_optimization(self, task):
        # 切换到字幕优化界面
        self.subtitle_optimization_interface.set_task(task)  # 假设SubtitleOptimizationInterface有一个set_task方法
        self.stackedWidget.setCurrentWidget(self.subtitle_optimization_interface)
        self.pivot.setCurrentItem('SubtitleOptimizationInterface')

    def switch_to_video_synthesis(self, task):
        # 切换到视频合成界面
        self.video_synthesis_interface.set_task(task)  # 假设VideoSynthesisInterface有一个set_task方法
        self.stackedWidget.setCurrentWidget(self.video_synthesis_interface)
        self.pivot.setCurrentItem('VideoSynthesisInterface')

    def addSubInterface(self, widget, objectName, text):
        widget.setObjectName(objectName)
        # widget.setAlignment(Qt.AlignCenter)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        if widget:
            self.pivot.setCurrentItem(widget.objectName())
    
    def closeEvent(self, event):
        self.task_creation_interface.close()
        self.transcription_interface.close()
        self.subtitle_optimization_interface.close()
        self.video_synthesis_interface.close()
        super().closeEvent(event)


if __name__ == '__main__':
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = HomeInterface()
    w.show()
    app.exec_()
