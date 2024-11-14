import datetime
import os
import re
from pathlib import Path

import requests
import yt_dlp
from PyQt5.QtCore import QThread, pyqtSignal

from ..entities import Task, TranscribeModelEnum, VideoInfo, LANGUAGES
from ..utils.video_utils import get_video_info
from ...common.config import cfg
from ..utils.logger import setup_logger
from ...config import SUBTITLE_STYLE_PATH

logger = setup_logger("create_task_thread")

class CreateTaskThread(QThread):
    finished = pyqtSignal(Task)
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)

    def __init__(self, file_path, task_type):
        super().__init__()
        self.file_path = file_path
        self.task_type = task_type

    def run(self):
        try:
            if self.task_type == 'file':
                self.create_file_task(self.file_path)
            elif self.task_type == 'url':
                self.create_url_task(self.file_path)
            elif self.task_type == 'transcription':
                self.create_transcription_task(self.file_path)
            elif self.task_type == 'optimization':
                self.create_subtitle_optimization_task()
            elif self.task_type == 'synthesis':
                self.create_video_synthesis_task()
        except Exception as e:
            logger.error("创建任务失败: %s", str(e))
            self.progress.emit(0, self.tr("创建任务失败"))
            self.error.emit(str(e))

    def create_file_task(self, file_path):
        logger.info("开始创建文件任务")
        # 使用 Path 对象处理路径
        task_work_dir = Path(cfg.work_dir.value) / Path(file_path).stem

        # 获取 视频/音频 信息
        thumbnail_path = str(task_work_dir / "thumbnail.jpg")
        video_info = get_video_info(file_path, thumbnail_path=thumbnail_path)
        video_info = VideoInfo(**video_info)

        # 定义各个路径
        audio_save_path = task_work_dir / f"{Path(file_path).stem}.mp3"
        original_subtitle_save_path = task_work_dir / "subtitle" / f"【原始字幕】{cfg.transcribe_model.value.value}.srt"
        result_subtitle_save_path = task_work_dir / "subtitle" / "【优化字幕】result.ass"
        video_save_path = task_work_dir / f"【卡卡】{Path(file_path).name}"

        ass_style_name = cfg.subtitle_style_name.value
        ass_style_path = SUBTITLE_STYLE_PATH / f"{ass_style_name}.txt"
        if ass_style_path.exists():
            subtitle_style_srt = ass_style_path.read_text(encoding="utf-8")
        else:
            subtitle_style_srt = None

        if cfg.transcribe_model.value in [TranscribeModelEnum.JIANYING, TranscribeModelEnum.BIJIAN]:
            need_word_time_stamp = True
        else:
            need_word_time_stamp = False

        # 创建 Task 对象
        task = Task(
            id=0,
            queued_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            status=Task.Status.PENDING,
            fraction_downloaded=0,
            work_dir=str(task_work_dir),
            file_path=str(Path(self.file_path)),
            url="",
            source=Task.Source.FILE_IMPORT,
            original_language=None,
            target_language=cfg.target_language.value.value,
            transcribe_language=LANGUAGES[cfg.transcribe_language.value.value],
            whisper_model=cfg.whisper_model.value.value,
            video_info=video_info,
            audio_format="mp3",
            audio_save_path=str(audio_save_path),
            transcribe_model=cfg.transcribe_model.value,
            use_asr_cache=cfg.use_asr_cache.value,
            need_word_time_stamp=need_word_time_stamp,
            original_subtitle_save_path=str(original_subtitle_save_path),
            base_url=cfg.api_base.value,
            api_key=cfg.api_key.value,
            llm_model=cfg.model.value,
            need_translate=cfg.need_translate.value,
            need_optimize=cfg.need_optimize.value,
            result_subtitle_save_path=str(result_subtitle_save_path),
            subtitle_layout=cfg.subtitle_layout.value,
            video_save_path=str(video_save_path),
            soft_subtitle=cfg.soft_subtitle.value,
            subtitle_style_srt=subtitle_style_srt
        )
        self.finished.emit(task)
        self.progress.emit(100, self.tr("创建任务完成"))
        logger.info("文件任务创建完成")

    def create_url_task(self, url):
        logger.info("开始创建URL任务")
        self.progress.emit(5, self.tr("正在获取视频信息"))
        # 下载视频。保存到 cfg.work_dir.value 下
        video_file_path, subtitle_file_path, thumbnail_file_path, info_dict = download(url, cfg.work_dir.value,
                                                                                       self.progress_hook)
        self.progress.emit(100, self.tr("下载视频完成"))

        video_info = VideoInfo(
            file_name=Path(video_file_path).stem,
            width=info_dict.get('width', 0),
            height=info_dict.get('height', 0),
            fps=info_dict.get('fps', 0),
            duration_seconds=info_dict.get('duration', 0),
            bitrate_kbps="",
            video_codec=info_dict.get('vcodec', ''),
            audio_codec=info_dict.get('acodec', ''),
            audio_sampling_rate=info_dict.get('asr', 0),
            thumbnail_path=thumbnail_file_path
        )

        # 使用 Path 对象处理路径
        task_work_dir = Path(video_file_path).parent

        # 定义各个路径
        audio_save_path = task_work_dir / f"{Path(video_file_path).stem}.mp3"
        original_subtitle_save_path = task_work_dir / "subtitle" / f"【原始字幕】{cfg.transcribe_model.value.value}.srt" if not subtitle_file_path else subtitle_file_path
        result_subtitle_save_path = task_work_dir / "subtitle" / f"【优化字幕】result.ass"
        video_save_path = task_work_dir / f"【卡卡】{Path(video_file_path).name}"

        # raise Exception("test")
        if cfg.transcribe_model.value in [TranscribeModelEnum.JIANYING, TranscribeModelEnum.BIJIAN]:
            need_word_time_stamp = True
        else:
            need_word_time_stamp = False

        ass_style_name = cfg.subtitle_style_name.value
        ass_style_path = SUBTITLE_STYLE_PATH / f"{ass_style_name}.txt"
        if ass_style_path.exists():
            subtitle_style_srt = ass_style_path.read_text(encoding="utf-8")
        else:
            subtitle_style_srt = None

        # 创建 Task 对象
        task = Task(
            id=0,
            queued_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            status=Task.Status.PENDING,
            fraction_downloaded=0,
            work_dir=str(task_work_dir),
            file_path=str(Path(video_file_path)),
            url="",
            source=Task.Source.FILE_IMPORT,
            original_language=None,
            target_language=cfg.target_language.value,
            video_info=video_info,
            audio_format="mp3",
            audio_save_path=str(audio_save_path),
            transcribe_model=cfg.transcribe_model.value,
            transcribe_language=LANGUAGES[cfg.transcribe_language.value.value],
            whisper_model=cfg.whisper_model.value.value,
            use_asr_cache=cfg.use_asr_cache.value,
            need_word_time_stamp=need_word_time_stamp,
            original_subtitle_save_path=str(original_subtitle_save_path),
            base_url=cfg.api_base.value,
            api_key=cfg.api_key.value,
            llm_model=cfg.model.value,
            need_translate=cfg.need_translate.value,
            need_optimize=cfg.need_optimize.value,
            result_subtitle_save_path=str(result_subtitle_save_path),
            subtitle_layout=cfg.subtitle_layout.value,
            video_save_path=str(video_save_path),
            soft_subtitle=cfg.soft_subtitle.value,
            subtitle_style_srt=subtitle_style_srt
        )
        self.finished.emit(task)
        logger.info("URL任务创建完成")

    def create_transcription_task(self, file_path):
        logger.info("开始创建转录任务")
        # 使用 Path 对象处理路径
        task_work_dir = Path(file_path).parent

        thumbnail_path = task_work_dir / "thumbnail.jpg"

        video_info = get_video_info(file_path, thumbnail_path=str(thumbnail_path))
        video_info = VideoInfo(**video_info)

        # 定义各个路径
        audio_save_path = task_work_dir / f"{Path(file_path).stem}.mp3"
        original_subtitle_save_path = task_work_dir / f"【原始字幕】{cfg.transcribe_model.value.value}.srt"

        # 创建 Task 对象
        task = Task(
            id=0,
            queued_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            status=Task.Status.TRANSCRIBING,
            fraction_downloaded=0,
            work_dir=str(task_work_dir),
            file_path=str(Path(self.file_path)),
            url="",
            source=Task.Source.FILE_IMPORT,
            original_language=None,
            target_language=cfg.target_language.value.value,
            transcribe_language=LANGUAGES[cfg.transcribe_language.value.value],
            whisper_model=cfg.whisper_model.value.value,
            video_info=video_info,
            audio_format="mp3",
            audio_save_path=str(audio_save_path),
            transcribe_model=cfg.transcribe_model.value,
            use_asr_cache=cfg.use_asr_cache.value,
            original_subtitle_save_path=str(original_subtitle_save_path),
        )
        self.finished.emit(task)
        logger.info("转录任务创建完成")

    def create_subtitle_optimization_task(file_path):
        logger.info("开始创建字幕优化任务")
        task_work_dir = Path(file_path.strip()).parent

        original_subtitle_save_path = task_work_dir / file_path
        result_subtitle_save_path = task_work_dir / f"【优化字幕】result_{cfg.model.value}.srt"

        ass_style_name = cfg.subtitle_style_name.value
        ass_style_path = SUBTITLE_STYLE_PATH / f"{ass_style_name}.txt"
        if ass_style_path.exists():
            subtitle_style_srt = ass_style_path.read_text(encoding="utf-8")
        else:
            subtitle_style_srt = None

        # 创建 Task 对象
        task = Task(
            id=0,
            queued_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            status=Task.Status.OPTIMIZING,
            work_dir=str(task_work_dir),
            target_language=cfg.target_language.value.value,
            original_subtitle_save_path=str(original_subtitle_save_path),
            base_url=cfg.api_base.value,
            api_key=cfg.api_key.value,
            llm_model=cfg.model.value,
            need_translate=cfg.need_translate.value,
            need_optimize=cfg.need_optimize.value,
            result_subtitle_save_path=str(result_subtitle_save_path),
            thread_num=cfg.thread_num.value,
            batch_size=cfg.batch_size.value,
            subtitle_layout=cfg.subtitle_layout.value,
            subtitle_style_srt=subtitle_style_srt
        )
        logger.info("字幕优化任务创建完成")
        return task

    def create_video_synthesis_task(subtitle_file, video_file):
        logger.info("开始创建视频合成任务")
        subtitle_file = Path(subtitle_file.strip()).as_posix()
        video_file = Path(video_file.strip()).as_posix()
        task_work_dir = Path(video_file.strip()).parent
        video_save_path = task_work_dir / f"【卡卡】{Path(video_file).name}"

        # 创建 Task 对象,保存文件夹与原视频路径一样
        task = Task(
            id=0,
            queued_at=datetime.datetime.now(),
            started_at=datetime.datetime.now(),
            completed_at=None,
            status=Task.Status.GENERATING,
            work_dir=str(task_work_dir),
            file_path=str(Path(video_file)),
            result_subtitle_save_path=str(Path(subtitle_file)),
            video_save_path=str(video_save_path),
            soft_subtitle=cfg.soft_subtitle.value,
        )
        logger.info("视频合成任务创建完成")
        return task

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d['_percent_str']
            speed = d['_speed_str']

            # 提取百分比和速度的纯文本
            clean_percent = percent.replace('\x1b[0;94m', '').replace('\x1b[0m', '').strip().replace('%', '')
            clean_speed = speed.replace('\x1b[0;32m', '').replace('\x1b[0m', '').strip()

            self.progress.emit(int(float(clean_percent)),
                               f'{self.tr("下载进度")}: {clean_percent}%  {self.tr("速度")}: {clean_speed}')


def sanitize_filename(name, replacement="_"):
    """
    清理文件名中不允许的字符，确保文件名在不同操作系统中有效。
    
    参数:
    - name (str): 原始文件名。
    - replacement (str): 用于替换不允许字符的字符串，默认为下划线。
    
    返回:
    - str: 清理后的文件名。
    """
    # 定义不同操作系统中不允许的字符
    # 这些是Windows中常见的不允许字符，其他系统如Linux和macOS允许更多字符
    # 为了跨平台兼容，使用这些较严格的规则
    forbidden_chars = r'<>:"/\\|?*'

    # 替换不允许的字符
    sanitized = re.sub(f"[{re.escape(forbidden_chars)}]", replacement, name)

    # 移除控制字符（0-31）和非打印字符
    sanitized = re.sub(r'[\0-\31]', '', sanitized)

    # 去除文件名末尾的空格和点（Windows 不允许）
    sanitized = sanitized.rstrip(' .')

    # 限制文件名长度（例如，Windows最大255个字符）
    max_length = 255
    if len(sanitized) > max_length:
        # 保留文件扩展名
        base, ext = os.path.splitext(sanitized)
        # 计算基名的最大长度
        base_max_length = max_length - len(ext)
        sanitized = base[:base_max_length] + ext

    # 处理Windows的保留名称
    # 列表来自 https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file
    windows_reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }
    name_without_ext = os.path.splitext(sanitized)[0].upper()
    if name_without_ext in windows_reserved_names:
        sanitized = f"{sanitized}_"

    # 如果文件名为空，返回一个默认名称
    if not sanitized:
        sanitized = "default_filename"

    return sanitized


def download(url, work_dir, progress_hook):
    logger.info("开始下载视频: %s", url)
    # 设置工作目录
    # 初始化 ydl 选项
    initial_ydl_opts = {
        'outtmpl': {
            'default': '%(title)s.%(ext)s',
            'subtitle': '【原始字幕】.%(ext)s',
            'thumbnail': 'thumbnail',
        },
        # 'format': 'worst',                   # 下载质量最差的视频和音频
        'progress_hooks': [progress_hook],  # 下载进度钩子
        # 'overwrites': True,                   # 覆盖已存在的文件
        'quiet': True,  # 禁用日志输出
        'no_warnings': True,  # 禁用警告信息
        'noprogress': True,
        'writeautomaticsub': True,  # 下载自动生成的字幕
        'writethumbnail': True,  # 下载缩略图
        'thumbnail_format': 'jpg',  # 指定缩略图的格式
    }

    with yt_dlp.YoutubeDL(initial_ydl_opts) as ydl:
        # 提取视频信息（不下载）
        info_dict = ydl.extract_info(url, download=False)

        # 设置动态下载文件夹为视频标题
        video_title = sanitize_filename(info_dict.get('title', 'MyVideo'))
        video_work_dir = Path(work_dir) / sanitize_filename(video_title)
        subtitle_language = info_dict.get('language', None)
        try:
            subtitle_download_link = info_dict['automatic_captions'][subtitle_language][-1]['url']
        except Exception as e:
            subtitle_download_link = None
        
        # 设置 yt-dlp 下载选项
        ydl_opts = {
            'paths': {
                'home': str(video_work_dir),
                'subtitle': str(video_work_dir / "subtitle"),
                'thumbnail': str(video_work_dir),
            },
        }
        # 更新 yt-dlp 的配置
        ydl.params.update(ydl_opts)

        # 使用 process_info 进行下载，避免重复解析
        ydl.process_info(info_dict)

        # 视频文件路径
        video_file_path = Path(ydl.prepare_filename(info_dict))
        if video_file_path.exists():
            video_file_path = str(video_file_path)
        else:
            video_file_path = None

        # 字幕文件路径， video_work_dir 下遍历所有文件寻找字幕文件，包括子文件夹 original.*
        subtitle_file_path = None
        for file in video_work_dir.glob("**/【原始字幕】*"):
            subtitle_file_path = str(file)
            if subtitle_language and subtitle_language not in subtitle_file_path:
                logger.info("字幕语言错误，重新下载字幕: %s", subtitle_download_link)
                os.remove(subtitle_file_path)
                if subtitle_download_link:
                    response = requests.get(subtitle_download_link)
                    subtitle_file_path = video_work_dir / "subtitle" / f"【原始字幕】{subtitle_language}.vtt"
                    with open(subtitle_file_path, 'w', encoding="utf-8") as f:
                        f.write(response.text)
            break
        
        # 缩略图文件路径 video_work_dir 下遍历寻找 thumbnail.jpg
        thumbnail_file_path = None
        for file in video_work_dir.glob("**/thumbnail*"):
            thumbnail_file_path = str(file)
            break

        logger.info("视频下载完成: %s", video_file_path)
        return video_file_path, subtitle_file_path, thumbnail_file_path, info_dict
