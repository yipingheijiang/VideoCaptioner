# coding:utf-8

from PyQt5.QtCore import Qt, QUrl, QStandardPaths, pyqtSignal, QThread, QFile
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget, QLabel, QFileDialog
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, CustomColorSettingCard,
                            setTheme, setThemeColor, RangeSettingCard, SettingCard)

from ..common.config import cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..components.LineEditSettingCard import LineEditSettingCard
from ..core.utils.test_opanai import test_openai


class SettingInterface(ScrollArea):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # 头部的设置标签
        self.settingLabel = QLabel(self.tr("设置"), self)

        # 转录配置
        self.transcribeGroup = SettingCardGroup(self.tr("转录配置"), self.scrollWidget)
        self.transcribeModelCard = ComboBoxSettingCard(
            cfg.transcribe_model,
            FIF.MICROPHONE,
            self.tr('转录模型'),
            self.tr('语音转换文字要使用的转录模型'),
            texts=[model.value for model in cfg.transcribe_model.validator.options],
            parent=self.transcribeGroup
        )

        # LLM 配置
        self.llmGroup = SettingCardGroup(self.tr("LLM 配置"), self.scrollWidget)
        self.apiKeyCard = LineEditSettingCard(
            cfg.api_key,
            FIF.FINGERPRINT,
            self.tr("API Key"),
            self.tr("输入您的 API Key"),
            "sk-",
            self.llmGroup
        )
        self.apiBaseCard = LineEditSettingCard(
            cfg.api_base,
            FIF.LINK,
            self.tr("API Base"),
            self.tr("输入您的 API Base"),
            "https://api.openai.com/v1",
            self.llmGroup
        )
        self.modelCard = LineEditSettingCard(
            cfg.model,
            FIF.ROBOT,
            self.tr("模型"),
            self.tr("输入您的模型"),
            "gpt-4o",
            self.llmGroup
        )
        self.checkLLMConnectionCard = PushSettingCard(
            self.tr("检查连接"),
            FIF.LINK,
            self.tr("检查 LLM 连接"),
            self.tr("点击检查 API 连接是否正常"),
            self.llmGroup
        )
        self.batchSizeCard = RangeSettingCard(
            cfg.batch_size,
            FIF.ALIGNMENT,
            self.tr('批处理大小'),
            self.tr('每批处理字幕的数量，建议为 10 的倍数'),
            parent=self.llmGroup
        )
        self.threadNumCard = RangeSettingCard(
            cfg.thread_num,
            FIF.SPEED_HIGH,
            self.tr('线程数'),
            self.tr('模型并行处理的数量，模型服务商允许的情况下建议尽可能大'),
            parent=self.llmGroup
        )

        # 翻译与优化配置
        self.translateGroup = SettingCardGroup(self.tr("翻译与优化"), self.scrollWidget)
        self.subtitleCorrectCard = SwitchSettingCard(
            FIF.EDIT,
            self.tr('字幕校正'),
            self.tr('是否对生成的字幕进行校正'),
            cfg.need_optimize,
            self.translateGroup
        )
        self.subtitleTranslateCard = SwitchSettingCard(
            FIF.LANGUAGE,
            self.tr('字幕翻译'),
            self.tr('是否对生成的字幕进行翻译'),
            cfg.need_translate,
            self.translateGroup
        )
        self.targetLanguageCard = ComboBoxSettingCard(
            cfg.target_language,
            FIF.LANGUAGE,
            self.tr('目标语言'),
            self.tr('选择字幕的目标语言'),
            texts=[lang.value for lang in cfg.target_language.validator.options],
            parent=self.translateGroup
        )

        # 字幕合成配置
        self.subtitleGroup = SettingCardGroup(self.tr("字幕合成配置"), self.scrollWidget)
        self.subtitleStyleCard = HyperlinkCard(
            "",
            self.tr('修改'),
            FIF.FONT,
            self.tr('字幕样式'),
            self.tr('选择字幕的颜色、大小、字体等'),
            self.subtitleGroup
        )
        self.subtitleLayoutCard = HyperlinkCard(
            "",
            self.tr('修改'),
            FIF.FONT,
            self.tr('字幕布局'),
            self.tr('选择字幕的布局'),
            self.subtitleGroup
        )
        # 开启软字幕
        self.softSubtitleCard = SwitchSettingCard(
            FIF.FONT,
            self.tr('软字幕'),
            self.tr('是否开启软字幕'),
            cfg.soft_subtitle,
            self.subtitleGroup
        )

        # 保存配置
        self.saveGroup = SettingCardGroup(self.tr("保存配置"), self.scrollWidget)
        self.savePathCard = PushSettingCard(
            self.tr('工作文件夹'),
            FIF.SAVE,
            self.tr("工作目录路径"),
            cfg.get(cfg.work_dir),
            self.saveGroup
        )

        # 个性化
        self.personalGroup = SettingCardGroup(
            self.tr('个性化'), self.scrollWidget)
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr('应用主题'),
            self.tr("更改应用程序的外观"),
            texts=[
                self.tr('浅色'), self.tr('深色'),
                self.tr('使用系统设置')
            ],
            parent=self.personalGroup
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            self.tr('主题颜色'),
            self.tr('更改应用程序的主题颜色'),
            self.personalGroup
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("界面缩放"),
            self.tr("更改小部件和字体的大小"),
            texts=["100%", "125%", "150%", "175%", "200%",
            self.tr("使用系统设置")
            ],
            parent=self.personalGroup
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr('语言'),
            self.tr('设置您偏好的界面语言'),
            texts=['简体中文', '繁體中文', 'English', self.tr('使用系统设置')],
            parent=self.personalGroup
        )

        # 应用信息
        self.aboutGroup = SettingCardGroup(self.tr('关于'), self.scrollWidget)
        self.helpCard = HyperlinkCard(
            HELP_URL,
            self.tr('打开帮助页面'),
            FIF.HELP,
            self.tr('帮助'),
            self.tr('发现新功能并了解有关PyQt-Fluent-Widgets的使用技巧'),
            self.aboutGroup
        )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr('提供反馈'),
            FIF.FEEDBACK,
            self.tr('提供反馈'),
            self.tr('通过提供反馈帮助我们改进PyQt-Fluent-Widgets'),
            self.aboutGroup
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr('检查更新'),
            FIF.INFO,
            self.tr('关于'),
            '© ' + self.tr('版权所有') + f" {YEAR}, {AUTHOR}. " +
            self.tr('版本') + " " + VERSION,
            self.aboutGroup
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')

        # StyleSheet.SETTING_INTERFACE.apply(self)
        self.setStyleSheet("""        
            SettingInterface, #scrollWidget {
                background-color: transparent;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QLabel#settingLabel {
                font: 33px 'LXGW WenKai';
                background-color: transparent;
                color: white;
            }
        """)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # 添加卡片到组
        self.transcribeGroup.addSettingCard(self.transcribeModelCard)

        self.llmGroup.addSettingCard(self.apiKeyCard)
        self.llmGroup.addSettingCard(self.apiBaseCard)
        self.llmGroup.addSettingCard(self.modelCard)
        self.llmGroup.addSettingCard(self.checkLLMConnectionCard)
        self.llmGroup.addSettingCard(self.batchSizeCard)
        self.llmGroup.addSettingCard(self.threadNumCard)

        self.translateGroup.addSettingCard(self.subtitleCorrectCard)
        self.translateGroup.addSettingCard(self.subtitleTranslateCard)
        self.translateGroup.addSettingCard(self.targetLanguageCard)

        self.subtitleGroup.addSettingCard(self.subtitleStyleCard)
        self.subtitleGroup.addSettingCard(self.subtitleLayoutCard)
        self.subtitleGroup.addSettingCard(self.softSubtitleCard)
        self.saveGroup.addSettingCard(self.savePathCard)

        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)

        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # 将设置卡片组添加到布局
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.transcribeGroup)
        self.expandLayout.addWidget(self.llmGroup)
        self.expandLayout.addWidget(self.translateGroup)
        self.expandLayout.addWidget(self.subtitleGroup)
        self.expandLayout.addWidget(self.saveGroup)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # 检查 LLM 连接
        self.checkLLMConnectionCard.clicked.connect(self.checkLLMConnection)

        # 保存路径
        self.savePathCard.clicked.connect(self.__onsavePathCardClicked)

        # 字幕样式修改跳转
        self.subtitleStyleCard.linkButton.clicked.connect(lambda: self.window().switchTo(self.window().subtitleStyleInterface))
        self.subtitleLayoutCard.linkButton.clicked.connect(lambda: self.window().switchTo(self.window().subtitleStyleInterface))
        
        # 个性化
        self.themeCard.optionChanged.connect(lambda ci: setTheme(cfg.get(ci)))
        self.themeColorCard.colorChanged.connect(setThemeColor)

        # 关于
        self.feedbackCard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
        
    def __showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            self.tr('Updated successfully'),
            self.tr('Configuration takes effect after restart'),
            duration=1500,
            parent=self
        )

    def __onsavePathCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.save_path) == folder:
            return
        cfg.set(cfg.save_path, folder)
        self.savePathCard.setContent(folder)

    def checkLLMConnection(self):
        """ 检查 LLM 连接 """
        # 检查 API Base 是否属于网址
        api_base = self.apiBaseCard.lineEdit.text()
        if not api_base.startswith("http"):
            InfoBar.error(
                self.tr('错误'),
                self.tr('请输入正确的 API Base'),
                duration=1500,
                parent=self
            )
            return
        
        # 禁用检查按钮，显示加载状态
        self.checkLLMConnectionCard.button.setEnabled(False)
        self.checkLLMConnectionCard.button.setText(self.tr("正在检查..."))
        
        # 创建并启动线程
        self.connection_thread = LLMConnectionThread(
            api_base, 
            self.apiKeyCard.lineEdit.text(), 
            self.modelCard.lineEdit.text()
        )
        self.connection_thread.finished.connect(self.onConnectionCheckFinished)
        self.connection_thread.start()

    def onConnectionCheckFinished(self, result, message):
        # 恢复检查按钮状态
        self.checkLLMConnectionCard.button.setEnabled(True)
        self.checkLLMConnectionCard.button.setText(self.tr("检查连接"))
        
        if not result:
            InfoBar.error(
                self.tr('测试错误'),
                message,
                duration=1500,
                parent=self
            )
        else:
            InfoBar.success(
                self.tr('测试成功'),
                message,
                duration=1500,
                parent=self
            )


class LLMConnectionThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, api_base, api_key, model):
        super().__init__()
        self.api_base = api_base
        self.api_key = api_key
        self.model = model

    def run(self):
        result, message = test_openai(self.api_base, self.api_key, self.model)
        self.finished.emit(result, message)
