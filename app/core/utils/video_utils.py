from pathlib import Path
import re
import subprocess
from typing import Literal

from ..utils.logger import setup_logger

logger = setup_logger("video_utils")


def video2audio(input_file: str, output: str = "") -> bool:
    """使用ffmpeg将视频转换为音频"""
    logger.info(f"开始将视频转换为音频: {input_file}")
    
    # 创建output目录
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output = str(output)

    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-ac', '1',
        '-f', 'mp3',
        '-af', 'aresample=async=1',
        '-y',
        output
    ]
    logger.info(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            check=True, 
            encoding='utf-8', 
            errors='replace', 
            shell=True
            )
        if result.returncode == 0 and Path(output).is_file():
            logger.info("音频转换成功")
            return True
        else:
            logger.error("音频转换失败")
            return False
    except Exception as e:
        logger.error(f"音频转换出错: {str(e)}")
        return False


def check_cuda_available() -> bool:
    """检查CUDA是否可用"""
    logger.info("检查CUDA是否可用")
    try:
        # 首先检查ffmpeg是否支持cuda
        result = subprocess.run(
            ['ffmpeg', '-hwaccels'], 
            capture_output=True, 
            text=True,
            shell=True
        )
        if 'cuda' not in result.stdout.lower():
            logger.info("CUDA不在支持的硬件加速器列表中")
            return False
            
        # 进一步检查CUDA设备信息
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-init_hw_device', 'cuda'], 
            capture_output=True, 
            text=True,
            shell=True
        )
        
        # 如果stderr中包含"Cannot load cuda" 或 "Failed to load"等错误信息，说明CUDA不可用
        if any(error in result.stderr.lower() for error in ['cannot load cuda', 'failed to load', 'error']):
            logger.info("CUDA设备初始化失败")
            return False
            
        logger.info("CUDA可用")
        return True
        
    except Exception as e:
        logger.error(f"检查CUDA出错: {str(e)}")
        return False


def add_subtitles(
        input_file: str,
        subtitle_file: str,
        output: str,
        quality: Literal[
            'ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'] = 'ultrafast',
        vcodec: str = 'libx264',
        soft_subtitle: bool = False,
        progress_callback: callable = None
) -> None:
    logger.info(f"开始添加字幕: 输入文件={input_file}, 字幕文件={subtitle_file}")
    
    assert Path(input_file).is_file(), "输入文件不存在"
    assert Path(subtitle_file).is_file(), "字幕文件不存在"

    # 如果是WebM格式，强制使用硬字幕
    if Path(output).suffix.lower() == '.webm':
        soft_subtitle = False
        logger.info("WebM格式视频，强制使用硬字幕")

    if soft_subtitle:
        logger.info("使用软字幕")
        # 添加软字幕
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-i', subtitle_file,
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-c:s', 'mov_text',
            output,
            '-y'
        ]
        logger.info(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='replace',
            shell=True
            )
    else:
        logger.info("使用硬字幕")
        subtitle_file = Path(subtitle_file).as_posix().replace(':', r'\:')
        vf = f"subtitles='{subtitle_file}'"
        if Path(output).suffix.lower() == '.webm':
            vcodec = 'libvpx-vp9'
            logger.info("WebM格式视频，使用libvpx-vp9编码器")

        # 检查CUDA是否可用
        use_cuda = check_cuda_available()
        cmd = ['ffmpeg']
        if use_cuda:
            logger.info("使用CUDA加速")
            cmd.extend(['-hwaccel', 'cuda'])
        cmd.extend([
            '-i', input_file,
            '-acodec', 'copy',
            '-preset', quality,
            '-vf', vf,
            '-y',  # 覆盖输出文件
            output
        ])

        logger.info(f"执行命令: {' '.join(cmd)}")
        cmd_str = subprocess.list2cmdline(cmd)
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            encoding='utf-8',
            errors='replace',
            shell=True
        )
        # 实时读取输出并调用回调函数
        total_duration = None
        current_time = 0

        while True:
            output_line = process.stderr.readline()
            if not output_line or (process.poll() is not None):
                break
            if not progress_callback:
                continue

            if total_duration is None:
                duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', output_line)
                if duration_match:
                    h, m, s = map(float, duration_match.groups())
                    total_duration = h * 3600 + m * 60 + s
                    logger.info(f"视频总时长: {total_duration}秒")

            # 解析当前处理时间
            time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', output_line)
            if time_match:
                h, m, s = map(float, time_match.groups())
                current_time = h * 3600 + m * 60 + s

            # 计算进度百分比
            if total_duration:
                progress = (current_time / total_duration) * 100
                progress_callback(f"{round(progress)}", "正在合成")

        if progress_callback:
            progress_callback("100", "合成完成")
        # 检查进程的返回码
        return_code = process.wait()
        if return_code != 0:
            logger.error(f"视频合成失败，返回码: {return_code}")
            raise Exception(return_code)
        logger.info("视频合成完成")


def get_video_info(filepath: str, thumbnail_path: str = "") -> dict:
    logger.info(f"获取视频信息: {filepath}")
    try:
        cmd = ["ffmpeg", "-i", filepath]
        logger.info(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='replace', 
            shell=True
            )
        info = result.stderr

        video_info = {
            'file_name': Path(filepath).stem,
            'duration_seconds': 0,
            'bitrate_kbps': 0,
            'video_codec': '',
            'width': 0,
            'height': 0,
            'fps': 0,
            'audio_codec': '',
            'audio_sampling_rate': 0,
            'thumbnail_path': '',
        }

        # 提取时长
        if duration_match := re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', info):
            hours, minutes, seconds = map(float, duration_match.groups())
            video_info['duration_seconds'] = hours * 3600 + minutes * 60 + seconds
            logger.info(f"视频时长: {video_info['duration_seconds']}秒")

        # 提取比特率
        if bitrate_match := re.search(r'bitrate: (\d+) kb/s', info):
            video_info['bitrate_kbps'] = int(bitrate_match.group(1))
            logger.info(f"视频码率: {video_info['bitrate_kbps']}kb/s")

        # 提取视频流信息
        if video_stream_match := re.search(r'Stream #\d+:\d+.*Video: (\w+).*?, (\d+)x(\d+).*?, ([\d.]+) (?:fps|tb)',
                                           info, re.DOTALL):
            video_info.update({
                'video_codec': video_stream_match.group(1),
                'width': int(video_stream_match.group(2)),
                'height': int(video_stream_match.group(3)),
                'fps': float(video_stream_match.group(4))
            })
            logger.info(f"视频编码: {video_info['video_codec']}, 分辨率: {video_info['width']}x{video_info['height']}, FPS: {video_info['fps']}")
            
            if thumbnail_path:
                if extract_thumbnail(filepath, video_info['duration_seconds'] * 0.3, thumbnail_path):
                    video_info['thumbnail_path'] = thumbnail_path
        else:
            video_info['thumbnail_path'] = thumbnail_path
            logger.warning("未找到视频流信息")

        # 提取音频流信息
        if audio_stream_match := re.search(r'Stream #\d+:\d+.*Audio: (\w+).* (\d+) Hz', info):
            video_info.update({
                'audio_codec': audio_stream_match.group(1),
                'audio_sampling_rate': int(audio_stream_match.group(2))
            })
            logger.info(f"音频编码: {video_info['audio_codec']}, 采样率: {video_info['audio_sampling_rate']}Hz")

        return video_info
    except Exception as e:
        logger.error(f"获取视频信息时出错: {str(e)}")
        return {k: '' if isinstance(v, str) else 0 for k, v in video_info.items()}


def extract_thumbnail(video_path: str, seek_time: float, thumbnail_path: str) -> bool:
    """
    使用 FFmpeg 提取视频缩略图
    
    :param video_path: 输入视频文件的路径
    :param seek_time: 提取缩略图的时间点（秒）
    :param thumbnail_path: 输出缩略图文件的路径
    :return: True 表示成功，False 表示失败
    """
    logger.info(f"开始提取缩略图")
    
    if not Path(video_path).is_file():
        logger.error(f"视频文件不存在: {video_path}")
        return False

    try:
        timestamp = f"{int(seek_time // 3600):02}:{int((seek_time % 3600) // 60):02}:{seek_time % 60:06.3f}"
        # 确保输出目录存在
        Path(thumbnail_path).parent.mkdir(parents=True, exist_ok=True)

        # 转换路径为合适的格式
        video_path = Path(video_path).as_posix()
        thumbnail_path = Path(thumbnail_path).as_posix()

        cmd = [
            "ffmpeg",
            "-ss", timestamp,
            "-i",
            video_path,
            "-vframes", "1",
            "-q:v", "2",
            "-y",
            thumbnail_path
        ]
        logger.info(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='replace', 
            shell=True
        )
        success = result.returncode == 0
        if success:
            logger.info("缩略图提取成功")
        else:
            logger.error("缩略图提取失败")
        return success

    except Exception as e:
        logger.error(f"提取缩略图时出错: {str(e)}")
        return False


if __name__ == "__main__":
    video_path = r"C:\Users\weifeng\Videos\example_video.mp4"
    thumbnail_path = "e:/example_thumbnail.jpg"
    success = extract_thumbnail(video_path, 2, thumbnail_path)
