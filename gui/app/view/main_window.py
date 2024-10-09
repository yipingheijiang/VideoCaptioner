# coding: utf-8
from PyQt5.QtCore import QUrl, QSize
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import (NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,
                            SplashScreen)
from qfluentwidgets import FluentIcon as FIF

# from .gallery_interface import GalleryInterface
from .home_interface import HomeInterface
from .setting_interface import SettingInterface
# from .text_interface import TextInterface
# from .view_interface import ViewInterface
from ..common.config import SUPPORT_URL, cfg
from ..common.icon import Icon
from ..common.signal_bus import signalBus
from ..common.translator import Translator
from ..common import resource


class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()

        # 创建子界面
        self.homeInterface = HomeInterface(self)
        self.settingInterface = SettingInterface(self)

        # 启用亚克力效果
        self.navigationInterface.setAcrylicEnabled(True)

        self.connectSignalToSlot()

        # 向导航界面添加项目
        self.initNavigation()
        self.splashScreen.finish()

    def initNavigation(self):
        """初始化导航栏"""
        # 添加导航项
        t = Translator()
        
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('主页'))
        self.navigationInterface.addSeparator()
        pos = NavigationItemPosition.SCROLL

        # 在底部添加自定义小部件
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=NavigationAvatarWidget('zhiyiYo', ':/gallery/images/shoko.png'),
            onClick=self.onSupport,
            position=NavigationItemPosition.BOTTOM
        )
        self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('Settings'), NavigationItemPosition.BOTTOM)

    def initWindow(self):
        """初始化窗口"""
        self.resize(960, 780)
        self.setMinimumWidth(760)
        self.setWindowIcon(QIcon(':/gallery/images/logo.png'))
        self.setWindowTitle('PyQt-Fluent-Widgets')

        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # 创建启动画面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.desktop().availableGeometry()
        # 设置窗口位置, 居中
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

        self.show()
        QApplication.processEvents()

    def connectSignalToSlot(self):
        """连接信号和槽"""
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)

    def onSupport(self):
        """支持作者"""
        w = MessageBox(
            '支持作者🥰',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')
        if w.exec():
            QDesktopServices.openUrl(QUrl(SUPPORT_URL))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())
