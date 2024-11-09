TEMPLATE = app
TARGET = VideoCaptioner

# Python源文件目录
SOURCES += app/view/batch_process_interface.py \
          app/view/home_interface.py \
          app/view/main_window.py \
          app/view/setting_interface.py \
          app/view/subtitle_optimization_interface.py \
          app/view/subtitle_style_interface.py \
          app/view/task_creation_interface.py \
          app/view/transcription_interface.py \
          app/view/video_synthesis_interface.py \
          app/components/WhisperSettingDialog.py
    
国际化
# 翻译文件
TRANSLATIONS += \
    translations/VideoCaptioner_zh_CN.ts \
    translations/VideoCaptioner_en_US.ts