# 国际化

1. 创建翻译文件 .ts

批量提取整个项目需要翻译的字符串，

创建 VideoCaptioner.pro

```
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
          app/view/video_synthesis_interface.py
# 导出的翻译文件
TRANSLATIONS += \
    translations/VideoCaptioner_zh_CN.ts \
    translations/VideoCaptioner_en_US.ts
```
```
pylupdate5 VideoCaptioner.pro
```

2. 编译成二进制翻译文件(.qm)
```
lrelease translations/VideoCaptioner_en_US.ts
```