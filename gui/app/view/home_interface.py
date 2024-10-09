# coding:utf-8
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget, QVBoxLayout, QLabel
from qfluentwidgets import SegmentedWidget

from .task_creation_interface import TaskCreationInterface


class HomeInterface(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName('HomeInterface')
        self.setStyleSheet("""
            HomeInterface{background: white}
            TaskCreationInterface{
                background: #F0F0F0;
                border-radius: 10px;
            }
        """)
        # self.resize(800, 600)

        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.task_creation_interface = TaskCreationInterface(self)
        self.transcription_interface = QLabel(self.tr('语音转录'), self)
        self.subtitle_optimization_interface = QLabel(self.tr('字幕优化与翻译'), self)
        self.video_synthesis_interface = QLabel(self.tr('字幕视频合成'), self)

        # 添加子界面
        self.addSubInterface(self.task_creation_interface, 'TaskCreationInterface', self.tr('任务创建'))
        self.addSubInterface(self.transcription_interface, 'transcription', self.tr('语音转录'))
        self.addSubInterface(self.subtitle_optimization_interface, 'subtitle_optimization', self.tr('字幕优化与翻译'))
        self.addSubInterface(self.video_synthesis_interface, 'video_synthesis', self.tr('字幕视频合成'))

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(30, 10, 30, 30)

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.task_creation_interface)
        self.pivot.setCurrentItem('TaskCreationInterface')  # 使用字符串而不是对象名

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


if __name__ == '__main__':
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = HomeInterface()
    w.show()
    app.exec_()
