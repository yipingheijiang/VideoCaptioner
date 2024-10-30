import os
import sys
from urllib.parse import urlparse
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication, QLabel, QLineEdit, QPushButton, QProgressBar, QFileDialog
from PyQt5.QtGui import QPixmap

from PyQt5.sip import voidptr
from qfluentwidgets import ComboBox, SwitchButton, SimpleCardWidget, CaptionLabel, CardWidget, ToolTipFilter, \
    ToolTipPosition, LineEdit, PrimaryPushButton, ProgressBar, PushButton, InfoBar, InfoBarPosition, BodyLabel


class SimpleSettingCard(CardWidget):
    """基础设置卡片类"""
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.title = title
        self.content = content
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 10, 8, 10)
        self.layout.setSpacing(8)
        
        self.label = CaptionLabel(self)
        self.label.setText(self.title)
        self.layout.addWidget(self.label)
        
        self.layout.addStretch(1)
        
        self.setToolTip(self.content)
        self.installEventFilter(ToolTipFilter(self, 100, ToolTipPosition.BOTTOM))

class ComboBoxSimpleSettingCard(SimpleSettingCard):
    """下拉框设置卡片"""
    valueChanged = pyqtSignal(str)
    
    def __init__(self, title, content, items=None, parent=None):
        super().__init__(title, content, parent)
        self.items = items or []
        self.setup_combobox()
        
    def setup_combobox(self):
        self.comboBox = ComboBox(self)
        self.comboBox.addItems(self.items)
        self.comboBox.currentTextChanged.connect(self.valueChanged)
        self.layout.addWidget(self.comboBox)
        
    def setValue(self, value):
        self.comboBox.setCurrentText(value)
        
    def value(self):
        return self.comboBox.currentText()

class SwitchButtonSimpleSettingCard(SimpleSettingCard):
    """开关设置卡片"""
    checkedChanged = pyqtSignal(bool)
    
    def __init__(self, title, content, parent=None):
        super().__init__(title, content, parent)
        self.setup_switch()
        
    def setup_switch(self):
        self.switchButton = SwitchButton(self)
        self.switchButton.setOnText("开")
        self.switchButton.setOffText("关")
        self.switchButton.checkedChanged.connect(self.checkedChanged)
        self.layout.addWidget(self.switchButton)
        
        self.clicked.connect(lambda: self.switchButton.setChecked(not self.switchButton.isChecked()))
        
    def setChecked(self, checked):
        self.switchButton.setChecked(checked)
        
    def isChecked(self):
        return self.switchButton.isChecked()

