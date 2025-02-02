import webbrowser

from PyQt5.QtCore import Qt, QThread, QUrl, pyqtSignal
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QFileDialog, QLabel, QWidget
from qfluentwidgets import ComboBoxSettingCard, CustomColorSettingCard, ExpandLayout
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (
    HyperlinkCard,
    InfoBar,
    MessageBox,
    OptionsSettingCard,
    PrimaryPushSettingCard,
    PushSettingCard,
    RangeSettingCard,
    ScrollArea,
    SettingCardGroup,
    SwitchSettingCard,
    setTheme,
    setThemeColor,
)

from app.common.config import cfg
from app.common.signal_bus import signalBus
from app.components.EditComboBoxSettingCard import EditComboBoxSettingCard
from app.components.LineEditSettingCard import LineEditSettingCard
from app.config import AUTHOR, FEEDBACK_URL, HELP_URL, RELEASE_URL, VERSION, YEAR
from app.core.entities import TranscribeModelEnum, TranslatorService
from app.core.utils.test_opanai import get_openai_models, test_openai
from app.thread.version_manager_thread import VersionManager


class SettingInterface(ScrollArea):
    """设置界面"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(self.tr("设置"))

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # 头部的设置标签
        self.settingLabel = QLabel(self.tr("设置"), self)

        # 转录配置
        self.transcribeGroup = SettingCardGroup(self.tr("转录配置"), self.scrollWidget)
        self.transcribeModelCard = ComboBoxSettingCard(
            cfg.transcribe_model,
            FIF.MICROPHONE,
            self.tr("转录模型"),
            self.tr("语音转换文字要使用的转录模型"),
            texts=[model.value for model in cfg.transcribe_model.validator.options],
            parent=self.transcribeGroup,
        )

        # 翻译配置
        self.llmGroup = SettingCardGroup(self.tr("翻译配置"), self.scrollWidget)

        self.translatorServiceCard = ComboBoxSettingCard(
            cfg.translator_service,
            FIF.ROBOT,
            self.tr("翻译器服务"),
            self.tr("选择翻译器服务"),
            texts=[
                service.value for service in cfg.translator_service.validator.options
            ],
            parent=self.llmGroup,
        )

        self.apiKeyCard = LineEditSettingCard(
            cfg.api_key,
            FIF.FINGERPRINT,
            self.tr("API Key"),
            self.tr("输入您的 API Key 令牌"),
            "sk-",
            self.llmGroup,
        )
        self.apiBaseCard = LineEditSettingCard(
            cfg.api_base,
            FIF.LINK,
            self.tr("Base URL"),
            self.tr("输入兼容 OpenAI 格式的 Base URL（需包括 /v1 后缀）"),
            "https://api.openai.com/v1",
            self.llmGroup,
        )
        self.modelCard = EditComboBoxSettingCard(
            cfg.model,
            FIF.ROBOT,
            self.tr("模型"),
            self.tr("输入您的模型，点击下方检查连接后会填充模型列表"),
            ["gpt-4o", "gpt-4o-mini", "点击下方「检查连接」后填充支持模型"],
            self.llmGroup,
        )
        self.checkLLMConnectionCard = PushSettingCard(
            self.tr("检查连接"),
            FIF.LINK,
            self.tr("检查 LLM 连接"),
            self.tr("点击检查 API 连接是否正常，并获取模型列表"),
            self.llmGroup,
        )
        self.needReflectTranslateCard = SwitchSettingCard(
            FIF.EDIT,
            self.tr("需要反思翻译"),
            self.tr("启用反思翻译可以提高翻译质量，但耗费更多时间和token"),
            cfg.need_reflect_translate,
            self.llmGroup,
        )
        self.deeplxEndpointCard = LineEditSettingCard(
            cfg.deeplx_endpoint,
            FIF.LINK,
            self.tr("DeepLx 端点"),
            self.tr("输入 DeepLx 的端点(开启deeplx翻译时必填)"),
            "https://api.deeplx.org/translate",
            self.llmGroup,
        )
        self.batchSizeCard = RangeSettingCard(
            cfg.batch_size,
            FIF.ALIGNMENT,
            self.tr("批处理大小"),
            self.tr("每批处理字幕的数量，建议为 10 的倍数"),
            parent=self.llmGroup,
        )
        self.threadNumCard = RangeSettingCard(
            cfg.thread_num,
            FIF.SPEED_HIGH,
            self.tr("线程数"),
            self.tr("模型并行处理的数量，模型服务商允许的情况下建议尽可能大"),
            parent=self.llmGroup,
        )

        # 翻译与优化配置
        self.translateGroup = SettingCardGroup(self.tr("翻译与优化"), self.scrollWidget)
        self.subtitleCorrectCard = SwitchSettingCard(
            FIF.EDIT,
            self.tr("字幕校正"),
            self.tr("是否对生成的字幕进行校正"),
            cfg.need_optimize,
            self.translateGroup,
        )
        self.subtitleTranslateCard = SwitchSettingCard(
            FIF.LANGUAGE,
            self.tr("字幕翻译"),
            self.tr("是否对生成的字幕进行翻译（包含校正过程）"),
            cfg.need_translate,
            self.translateGroup,
        )
        self.targetLanguageCard = ComboBoxSettingCard(
            cfg.target_language,
            FIF.LANGUAGE,
            self.tr("目标语言"),
            self.tr("选择翻译字幕的目标语言"),
            texts=[lang.value for lang in cfg.target_language.validator.options],
            parent=self.translateGroup,
        )

        # 字幕合成配置
        self.subtitleGroup = SettingCardGroup(
            self.tr("字幕合成配置"), self.scrollWidget
        )
        self.subtitleStyleCard = HyperlinkCard(
            "",
            self.tr("修改"),
            FIF.FONT,
            self.tr("字幕样式"),
            self.tr("选择字幕的样式（颜色、大小、字体等）"),
            self.subtitleGroup,
        )
        self.subtitleLayoutCard = HyperlinkCard(
            "",
            self.tr("修改"),
            FIF.FONT,
            self.tr("字幕布局"),
            self.tr("选择字幕的布局（单语、双语）"),
            self.subtitleGroup,
        )

        self.needVideoCard = SwitchSettingCard(
            FIF.VIDEO,
            self.tr("需要合成视频"),
            self.tr("是否需要合成视频"),
            cfg.need_video,
            self.subtitleGroup,
        )
        # 开启软字幕
        self.softSubtitleCard = SwitchSettingCard(
            FIF.FONT,
            self.tr("软字幕"),
            self.tr("合成视频时是否使用软字幕"),
            cfg.soft_subtitle,
            self.subtitleGroup,
        )
        # 保存配置
        self.saveGroup = SettingCardGroup(self.tr("保存配置"), self.scrollWidget)
        self.savePathCard = PushSettingCard(
            self.tr("工作文件夹"),
            FIF.SAVE,
            self.tr("工作目录路径"),
            cfg.get(cfg.work_dir),
            self.saveGroup,
        )

        # 个性化
        self.personalGroup = SettingCardGroup(self.tr("个性化"), self.scrollWidget)
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr("应用主题"),
            self.tr("更改应用程序的外观"),
            texts=[self.tr("浅色"), self.tr("深色"), self.tr("使用系统设置")],
            parent=self.personalGroup,
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            self.tr("主题颜色"),
            self.tr("更改应用程序的主题颜色"),
            self.personalGroup,
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("界面缩放"),
            self.tr("更改小部件和字体的大小"),
            texts=["100%", "125%", "150%", "175%", "200%", self.tr("使用系统设置")],
            parent=self.personalGroup,
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr("语言"),
            self.tr("设置您偏好的界面语言"),
            texts=["简体中文", "繁體中文", "English", self.tr("使用系统设置")],
            parent=self.personalGroup,
        )

        # 应用信息
        self.aboutGroup = SettingCardGroup(self.tr("关于"), self.scrollWidget)
        self.helpCard = HyperlinkCard(
            HELP_URL,
            self.tr("打开帮助页面"),
            FIF.HELP,
            self.tr("帮助"),
            self.tr("发现新功能并了解有关VideoCaptioner的使用技巧"),
            self.aboutGroup,
        )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr("提供反馈"),
            FIF.FEEDBACK,
            self.tr("提供反馈"),
            self.tr("提供反馈帮助我们改进VideoCaptioner"),
            self.aboutGroup,
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr("检查更新"),
            FIF.INFO,
            self.tr("关于"),
            "© "
            + self.tr("版权所有")
            + f" {YEAR}, {AUTHOR}. "
            + self.tr("版本")
            + " "
            + VERSION,
            self.aboutGroup,
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName("settingInterface")

        # 初始化样式表
        self.scrollWidget.setObjectName("scrollWidget")
        self.settingLabel.setObjectName("settingLabel")

        # 初始化翻译服务配置卡片的显示状态
        self.__onTranslatorServiceChanged(
            self.translatorServiceCard.comboBox.currentText()
        )

        self.setStyleSheet(
            """        
            SettingInterface, #scrollWidget {
                background-color: transparent;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QLabel#settingLabel {
                font: 33px 'Microsoft YaHei';
                background-color: transparent;
                color: white;
            }
        """
        )

        # 初始化布局
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # 添加卡片到组
        self.transcribeGroup.addSettingCard(self.transcribeModelCard)

        self.llmGroup.addSettingCard(self.translatorServiceCard)
        self.llmGroup.addSettingCard(self.apiKeyCard)
        self.llmGroup.addSettingCard(self.apiBaseCard)
        self.llmGroup.addSettingCard(self.modelCard)
        self.llmGroup.addSettingCard(self.checkLLMConnectionCard)
        self.llmGroup.addSettingCard(self.deeplxEndpointCard)
        self.llmGroup.addSettingCard(self.needReflectTranslateCard)
        self.llmGroup.addSettingCard(self.batchSizeCard)
        self.llmGroup.addSettingCard(self.threadNumCard)

        self.translateGroup.addSettingCard(self.subtitleCorrectCard)
        self.translateGroup.addSettingCard(self.subtitleTranslateCard)
        self.translateGroup.addSettingCard(self.targetLanguageCard)

        self.subtitleGroup.addSettingCard(self.subtitleStyleCard)
        self.subtitleGroup.addSettingCard(self.subtitleLayoutCard)
        self.subtitleGroup.addSettingCard(self.needVideoCard)
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
        """连接信号与槽"""
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # 翻译服务切换
        self.translatorServiceCard.comboBox.currentTextChanged.connect(
            self.__onTranslatorServiceChanged
        )

        # 检查 LLM 连接
        self.checkLLMConnectionCard.clicked.connect(self.checkLLMConnection)

        # 保存路径
        self.savePathCard.clicked.connect(self.__onsavePathCardClicked)

        # 字幕样式修改跳转
        self.subtitleStyleCard.linkButton.clicked.connect(
            lambda: self.window().switchTo(self.window().subtitleStyleInterface)
        )
        self.subtitleLayoutCard.linkButton.clicked.connect(
            lambda: self.window().switchTo(self.window().subtitleStyleInterface)
        )

        # 个性化
        self.themeCard.optionChanged.connect(lambda ci: setTheme(cfg.get(ci)))
        self.themeColorCard.colorChanged.connect(setThemeColor)

        # 反馈
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL))
        )

        # 关于
        self.aboutCard.clicked.connect(self.checkUpdate)

        # 全局 signalBus
        self.transcribeModelCard.comboBox.currentTextChanged.connect(
            signalBus.transcription_model_changed
        )
        self.subtitleCorrectCard.checkedChanged.connect(
            signalBus.subtitle_optimization_changed
        )
        self.subtitleTranslateCard.checkedChanged.connect(
            signalBus.subtitle_translation_changed
        )
        self.targetLanguageCard.comboBox.currentTextChanged.connect(
            signalBus.target_language_changed
        )
        self.softSubtitleCard.checkedChanged.connect(signalBus.soft_subtitle_changed)
        self.needVideoCard.checkedChanged.connect(signalBus.need_video_changed)

    def __showRestartTooltip(self):
        """显示重启提示"""
        InfoBar.success(
            self.tr("更新成功"),
            self.tr("配置将在重启后生效"),
            duration=1500,
            parent=self,
        )

    def __onsavePathCardClicked(self):
        """处理保存路径卡片点击事件"""
        folder = QFileDialog.getExistingDirectory(self, self.tr("选择文件夹"), "./")
        if not folder or cfg.get(cfg.work_dir) == folder:
            return
        cfg.set(cfg.work_dir, folder)
        self.savePathCard.setContent(folder)

    def checkLLMConnection(self):
        """检查 LLM 连接"""
        # 检查 API Base 是否属于网址
        api_base = self.apiBaseCard.lineEdit.text()
        if not api_base.startswith("http"):
            InfoBar.error(
                self.tr("错误"),
                self.tr("请输入正确的 API Base, 含有 /v1"),
                duration=3000,
                parent=self,
            )
            return

        # 禁用检查按钮，显示加载状态
        self.checkLLMConnectionCard.button.setEnabled(False)
        self.checkLLMConnectionCard.button.setText(self.tr("正在检查..."))

        # 创建并启动线程
        self.connection_thread = LLMConnectionThread(
            api_base,
            self.apiKeyCard.lineEdit.text(),
            self.modelCard.comboBox.currentText(),
        )
        self.connection_thread.finished.connect(self.onConnectionCheckFinished)
        self.connection_thread.error.connect(self.onConnectionCheckError)
        self.connection_thread.start()

    def onConnectionCheckError(self, message):
        """处理连接检查错误事件"""
        self.checkLLMConnectionCard.button.setEnabled(True)
        self.checkLLMConnectionCard.button.setText(self.tr("检查连接"))
        InfoBar.error(self.tr("LLM 连接测试错误"), message, duration=3000, parent=self)

    def onConnectionCheckFinished(self, is_success, message, models):
        """处理连接检查完成事件"""
        self.checkLLMConnectionCard.button.setEnabled(True)
        self.checkLLMConnectionCard.button.setText(self.tr("检查连接"))
        if models:
            temp = self.modelCard.comboBox.currentText()
            self.modelCard.setItems(models)
            self.modelCard.comboBox.setCurrentText(temp)
            InfoBar.success(
                self.tr("获取模型列表成功:"),
                self.tr("一共") + str(len(models)) + self.tr("个模型"),
                duration=3000,
                parent=self,
            )
        if not is_success:
            InfoBar.error(
                self.tr("LLM 连接测试错误"), message, duration=3000, parent=self
            )
        else:
            InfoBar.success(
                self.tr("LLM 连接测试成功"), message, duration=3000, parent=self
            )

    def checkUpdate(self):
        webbrowser.open(RELEASE_URL)

    def __onTranslatorServiceChanged(self, service):
        """处理翻译服务切换事件"""
        base_url_map = {
            TranslatorService.OPENAI.value: ("https://api.openai.com/v1"),
            TranslatorService.SILICONCLOUD.value: "https://api.siliconflow.cn/v1",
            TranslatorService.DEEPSEEK.value: "https://api.deepseek.com/v1",
            TranslatorService.OLLAMA.value: "http://localhost:11434/v1",
            TranslatorService.GEMINI.value: "https://generativelanguage.googleapis.com/v1beta/openai/",
            TranslatorService.ZHIPU.value: "https://open.bigmodel.cn/api/paas/v4",
        }
        # 隐藏所有配置卡片
        openai_cards = [
            self.apiKeyCard,
            self.apiBaseCard,
            self.modelCard,
            self.checkLLMConnectionCard,
            self.needReflectTranslateCard,
            self.batchSizeCard,
        ]
        deeplx_cards = [self.deeplxEndpointCard]

        all_cards = openai_cards + deeplx_cards
        for card in all_cards:
            card.setVisible(False)

        # 根据选择的服务显示相应的配置卡片
        if service in base_url_map:
            for card in openai_cards:
                card.setVisible(True)
            self.apiBaseCard.lineEdit.setText(base_url_map[service])
        elif service in [TranslatorService.DEEPLX.value]:
            for card in deeplx_cards:
                card.setVisible(True)

        # 更新布局
        self.llmGroup.adjustSize()
        self.expandLayout.update()


class LLMConnectionThread(QThread):
    finished = pyqtSignal(bool, str, list)
    error = pyqtSignal(str)

    def __init__(self, api_base, api_key, model):
        super().__init__()
        self.api_base = api_base
        self.api_key = api_key
        self.model = model

    def run(self):
        """查 LLM 连接并获取模型列表"""
        try:
            is_success, message = test_openai(self.api_base, self.api_key, self.model)
            models = get_openai_models(self.api_base, self.api_key)
            print(models)
            self.finished.emit(is_success, message, models)
        except Exception as e:
            self.error.emit(str(e))
