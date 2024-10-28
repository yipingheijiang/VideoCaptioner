from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtGui import QIcon
from qfluentwidgets import SettingCard, CompactSpinBox
from qfluentwidgets.common.config import ConfigItem, qconfig
from typing import Union


class SpinBoxSettingCard(SettingCard):
    """ 数值输入设置卡片 """

    valueChanged = pyqtSignal(int)

    def __init__(self, configItem: ConfigItem, icon: Union[str, QIcon], title: str, content: str = None, 
                 minimum: int = 0, maximum: int = 100, parent=None):
        super().__init__(icon, title, content, parent)
        
        self.configItem = configItem
        
        # 创建SpinBox
        self.spinBox = CompactSpinBox(self)
        self.spinBox.setRange(minimum, maximum)
        self.spinBox.setMinimumWidth(60)
        
        # 添加到布局
        self.hBoxLayout.addWidget(self.spinBox, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(8)

        # 设置初始值和连接信号
        self.setValue(qconfig.get(configItem))
        self.spinBox.valueChanged.connect(self.__onValueChanged)
        configItem.valueChanged.connect(self.setValue)

    def __onValueChanged(self, value: int):
        """ 数值改变时的槽函数 """
        self.setValue(value)
        self.valueChanged.emit(value)

    def setValue(self, value: int):
        """ 设置数值 """
        qconfig.set(self.configItem, value)
        self.spinBox.setValue(value)
