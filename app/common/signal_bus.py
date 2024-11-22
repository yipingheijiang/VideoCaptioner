from PyQt5.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    # 字幕排布信号
    subtitle_layout_changed = pyqtSignal(str)
    # 字幕优化信号
    subtitle_optimization_changed = pyqtSignal(bool)
    # 字幕翻译信号
    subtitle_translation_changed = pyqtSignal(bool)
    # 翻译语言
    target_language_changed = pyqtSignal(str)

    def on_subtitle_layout_changed(self, layout: str):
        self.subtitle_layout_changed.emit(layout)

    def on_subtitle_optimization_changed(self, optimization: bool):
        if optimization:
            # 如果开启字幕优化,则关闭字幕翻译
            self.subtitle_translation_changed.emit(False)
        self.subtitle_optimization_changed.emit(optimization)

    def on_subtitle_translation_changed(self, translation: bool):
        if translation:
            # 如果开启字幕翻译,则关闭字幕优化
            self.subtitle_optimization_changed.emit(False)
        self.subtitle_translation_changed.emit(translation)

    def on_target_language_changed(self, language: str):
        self.target_language_changed.emit(language)


signalBus = SignalBus()