# -*- coding: utf-8 -*-

import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from qfluentwidgets import ComboBox, SwitchButton, SimpleCardWidget, CaptionLabel, CardWidget


class VideoSynthesisInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.label = CaptionLabel(self)
        self.label.setText("视频合成")
        self.label.setObjectName("video_synthesis_label")



if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = VideoSynthesisInterface()
    window.show()
    sys.exit(app.exec_())
