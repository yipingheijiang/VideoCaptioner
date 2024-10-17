from typing import Union
from qfluentwidgets import ImageLabel
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import (QPixmap, QPainter, QPainterPath)
from PyQt5.QtWidgets import QLabel

class ImageLabel(ImageLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def setImage(self, image = None):
        """ set the image of label """
        self.image = image.toImage()
        # self.setFixedSize(self.image.size())
        self.update()

    def paintEvent(self, e):
        if self.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        path = QPainterPath()
        w, h = self.width(), self.height()

        # top line
        path.moveTo(self.topLeftRadius, 0)
        path.lineTo(w - self.topRightRadius, 0)

        # top right arc
        d = self.topRightRadius * 2
        path.arcTo(w - d, 0, d, d, 90, -90)

        # right line
        path.lineTo(w, h - self.bottomRightRadius)

        # bottom right arc
        d = self.bottomRightRadius * 2
        path.arcTo(w - d, h - d, d, d, 0, -90)

        # bottom line
        path.lineTo(self.bottomLeftRadius, h)

        # bottom left arc
        d = self.bottomLeftRadius * 2
        path.arcTo(0, h - d, d, d, -90, -90)

        # left line
        path.lineTo(0, self.topLeftRadius)

        # top left arc
        d = self.topLeftRadius * 2
        path.arcTo(0, 0, d, d, -180, -90)

        # draw image
        image = self.image.scaled(
            self.size()*self.devicePixelRatioF(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        painter.setPen(Qt.NoPen)
        painter.setClipPath(path)
        painter.drawImage(self.rect(), image)

        # 计算绘制位置，使图像居中
        x = (self.width() - image.width()) // 2
        y = (self.height() - image.height()) // 2

        painter.setPen(Qt.NoPen)
        painter.setClipPath(path)

        painter.drawImage(QRect(x, y, image.width(), image.height()), image)