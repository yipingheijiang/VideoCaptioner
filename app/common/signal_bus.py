from PyQt5.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    # 字幕排布信号
    subtitle_layout_changed = pyqtSignal(str)

    def on_subtitle_layout_changed(self, layout: str):
        self.subtitle_layout_changed.emit(layout)


signalBus = SignalBus()