import os
from pathlib import Path
import re
import subprocess
from typing import Literal

import ffmpeg


def video2audio(input_file: str, output:str="") -> bytes:
    """Render audio file using ffmpeg"""
    #  创建output
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output = str(output)
    
    if output:
        ffmpeg.input(input_file).output(output, ac=1, format="mp3", af='aresample=async=1',loglevel="quiet").run(overwrite_output=True, capture_stdout=True)
        out = output
    else:
        out, err = (
            ffmpeg.input(input_file)
            .output("pipe:", ac=1, format="mp3", af='aresample=async=1',loglevel="quiet")
            .run(capture_stdout=True)
        )
    return out


def add_subtitles(
    input_file: str,
    subtitle_file: str,
    output: str,
    log: Literal['error', 'info', 'quiet'] = 'info',            # 日志级别
    font: str = 'MicrosoftYaHei', # 字体名称
    font_size: int = 24,          # 字体大小
    font_color: str = '#FFFFFF',  # 字体颜色
    quality: Literal['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'] = 'ultrafast',
    vcodec: str = 'libx264',     # 视频编码器
    soft_subtitle: bool = False  # 是否添加软字幕
) -> None:
    try:
        if soft_subtitle:
            # 添加软字幕
            cmd = ['ffmpeg', '-i', input_file, '-i', subtitle_file, '-c:v', 'copy', '-c:a', 'copy', '-c:s', 'mov_text',output, '-y']
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            # print(result.stdout)
            # print(result.stderr)
            # print(" ".join(cmd))
        else:
            # 硬字幕
            # 格式化 font_color 为 &HBBGGRR&
            # font_color = font_color.lstrip('#')  # 去掉 '#'
            font_color = f"&H{font_color[5:7]}{font_color[3:5]}{font_color[1:3]}&"

            ffmpeg.input(input_file, hwaccel='cuda').output(
                output,
                vf=f"subtitles={subtitle_file}:force_style='FontName={font},FontSize={font_size},PrimaryColour={font_color},Outline=1,Shadow=0,BackColour=&H9C9C9C&,Bold=-1,Alignment=2'",
                vcodec=vcodec,
                preset=quality,
                loglevel=log,
                acodec='copy',
            ).run(overwrite_output=True)
        print(f'处理完成：{output}')
    except ffmpeg.Error as e:
        print(f'处理失败：{e.stderr}')


def get_video_info(filepath, need_thumbnail=False):
    try:
        cmd = [
            "ffmpeg",
            "-i",
            filepath
        ]
        
        # 执行 FFmpeg 命令
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
        
        # FFmpeg 的信息输出在 stderr
        info = result.stderr
        video_info = {
            'file_name': os.path.splitext(os.path.basename(filepath))[0],
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
        duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', info)
        if duration_match:
            hours = int(duration_match.group(1))
            minutes = int(duration_match.group(2))
            seconds = float(duration_match.group(3))
            video_info['duration_seconds'] = hours * 3600 + minutes * 60 + seconds
        
        # 提取比特率
        bitrate_match = re.search(r'bitrate: (\d+) kb/s', info)
        if bitrate_match:
            video_info['bitrate_kbps'] = int(bitrate_match.group(1))
        
        # 提取视频流信息
        video_stream_match = re.search(r'Stream #\d+:\d+.*Video: (\w+).*?, (\d+)x(\d+).*?, ([\d.]+) (?:fps|tb)', info, re.DOTALL)
        if video_stream_match:
            video_info['video_codec'] = video_stream_match.group(1)
            video_info['width'] = int(video_stream_match.group(2))
            video_info['height'] = int(video_stream_match.group(3))
            video_info['fps'] = float(video_stream_match.group(4))
            if need_thumbnail:
                thumbnail_path = os.path.splitext(filepath)[0] + ".png"
                if extract_thumbnail(filepath, video_info['duration_seconds'] * 0.3, thumbnail_path):
                    video_info['thumbnail_path'] = thumbnail_path
        
        # 提取音频流信息
        audio_stream_match = re.search(r'Stream #\d+:\d+.*Audio: (\w+).* (\d+) Hz', info)
        if audio_stream_match:
            video_info['audio_codec'] = audio_stream_match.group(1)
            video_info['audio_sampling_rate'] = int(audio_stream_match.group(2))
    
        return video_info
    except Exception as e:
        return {
            'file_name': os.path.basename(filepath),
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

def extract_thumbnail(video_path, seek_time, thumbnail_path):
    """
    使用 FFmpeg 提取视频缩略图
    
    :param video_path: 输入视频文件的路径
    :param seek_time: 提取缩略图的时间点（秒）
    :param thumbnail_path: 输出缩略图文件的路径
    :return: True 表示成功，False 表示失败
    """
    if not os.path.isfile(video_path):
        print(f"视频文件不存在: {video_path}")
        return False
    
    try:
        timestamp = f"{int(seek_time//3600):02}:{int((seek_time%3600)//60):02}:{seek_time%60:06.3f}"
        
        cmd = [
            "ffmpeg",
            "-ss", timestamp,
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            "-y",
            thumbnail_path
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace')
        return True
    except subprocess.CalledProcessError as e:
        print(f"提取缩略图时出错: {e.stderr}")
        return False
    except Exception as e:
        print(f"提取缩略图时出错: {e}")
        return False


if __name__ == "__main__":
    # ['-i', 'C:\\Users\\weifeng\\Desktop\\【黑神话沙雕动画】二周目起舞的天命人.mp4', '-f', 'mp3', '-ac', '1', '-af', 'aresample=async=1', '-loglevel', 'quiet', 'E:\\GithubProject\\VideoCaptioner\\app\\work_dir\\【黑神话沙雕动画】二周目起舞的天命人\\audio.mp3']
    video_path = "C:\\Users\\weifeng\\Desktop\\【黑神话沙雕动画】二周目起舞的天命人.mp4"
    video2audio(video_path, "audio.mp3")
    
    # video_path = r"C:\Users\weifeng\Videos\【MrBeast公益】我建了100栋房子然后把他送人了！.mp4"
    # info = get_video_info(video_path, need_thumbnail=True)
    # print(info)

    # thumbnail_file = r"C:\Users\weifeng\Videos\thumbnail.png"  # 替换为你希望保存的缩略图路径
    # success = extract_thumbnail(video_path, 10, thumbnail_file)
    # if not success:
    #     print("提取缩略图失败")
