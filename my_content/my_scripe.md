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



```
python -m nuitka --module app --output-dir=release/dist --include-package=app
```

python -m nuitka ^
    --standalone ^
    --output-dir=release ^
    --windows-disable-console ^
    --enable-plugin=pyqt5 ^
    --include-package=app ^
    --include-data-dir=resource=resource ^
    --show-progress ^
    --show-memory ^
    --windows-company-name=VideoCaptioner ^
    --windows-product-name=VideoCaptioner ^
    --windows-file-version=1.0.0 ^
    --windows-product-version=1.0.0 ^
    main.py


python -m nuitka --standalone --output-dir=niitka-build --windows-console-mode=disable --enable-plugin=pyqt5 --include-package=app --include-data-dir=resource=resource --show-progress --show-memory --windows-company-name=VideoCaptioner --windows-product-name=VideoCaptioner --windows-file-version=1.0.0 --windows-product-version=1.0.0 main.py

python -m nuitka --standalone --output-dir=release --windows-console-mode=disable --enable-plugin=pyqt5 --include-package=app --nofollow-import-to=yt_dlp --experimental=use_pefile --show-progress --show-memory --windows-company-name=VideoCaptioner --windows-product-name=VideoCaptioner --windows-file-version=1.0.0 --windows-product-version=1.0.0 main.py