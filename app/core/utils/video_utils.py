import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Literal

import ffmpeg


def video2audio(input_file: str, output:str="") -> bool:
    """使用ffmpeg将视频转换为音频"""
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
    result = subprocess.run(cmd, capture_output=True, check=True, encoding='utf-8', errors='replace')

    if result.returncode == 0 and Path(output).is_file():
        return True
    else:
        return False


def add_subtitles(
    input_file: str,
    subtitle_file: str,
    output: str,
    quality: Literal['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'] = 'ultrafast',
    vcodec: str = 'libx264',
    soft_subtitle: bool = False,
    progress_callback: callable = None
) -> None:
    assert Path(input_file).is_file(), "输入文件不存在"
    assert Path(subtitle_file).is_file(), "字幕文件不存在"

    if soft_subtitle:
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
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    else:
        subtitle_file = Path(subtitle_file).as_posix().replace(':', r'\:')
        vf = f"subtitles='{subtitle_file}'"
        # if Path(subtitle_file).suffix == '.srt':
        #     font: str = 'MicrosoftYaHei',
        #     font_size: int = 24,
        #     font_color: str = '#FFFFFF',
        #     font_color = font_color.lstrip('#')
        #     font_color_ass = f"&H00{font_color[4:6]}{font_color[2:4]}{font_color[0:2]}&"
        #     font = Path(font).as_posix().replace(':', r'\:')
        #     force_style = f"FontName={font},FontSize={font_size},PrimaryColour={font_color_ass},Outline=1,Shadow=0,BackColour=&H009C9C9C&,Bold=-1,Alignment=2"
        #     vf = f"subtitles={subtitle_file}:force_style='{force_style}'"
        cmd = [
            'ffmpeg',
            '-hwaccel', 'cuda',
            '-i', input_file,
            '-acodec', 'copy',
            '-preset', quality,
            '-vcodec', vcodec,
            '-vf', vf,
            '-y',  # 覆盖输出文件
            output
        ]
        cmd_str = subprocess.list2cmdline(cmd)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')

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
            raise Exception(return_code)


def get_video_info(filepath: str, thumbnail_path: str = "") -> dict:
    try:
        cmd = ["ffmpeg", "-i", filepath]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
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
        
        # 提取比特率
        if bitrate_match := re.search(r'bitrate: (\d+) kb/s', info):
            video_info['bitrate_kbps'] = int(bitrate_match.group(1))
        
        # 提取视频流信息
        if video_stream_match := re.search(r'Stream #\d+:\d+.*Video: (\w+).*?, (\d+)x(\d+).*?, ([\d.]+) (?:fps|tb)', info, re.DOTALL):
            video_info.update({
                'video_codec': video_stream_match.group(1),
                'width': int(video_stream_match.group(2)),
                'height': int(video_stream_match.group(3)),
                'fps': float(video_stream_match.group(4))
            })
            if thumbnail_path:
                if extract_thumbnail(filepath, video_info['duration_seconds'] * 0.3, thumbnail_path):
                    video_info['thumbnail_path'] = thumbnail_path
        
        # 提取音频流信息
        if audio_stream_match := re.search(r'Stream #\d+:\d+.*Audio: (\w+).* (\d+) Hz', info):
            video_info.update({
                'audio_codec': audio_stream_match.group(1),
                'audio_sampling_rate': int(audio_stream_match.group(2))
            })
    
        return video_info
    except Exception as e:
        print(f"获取视频信息时出错: {str(e)}")
        return {k: '' if isinstance(v, str) else 0 for k, v in video_info.items()}

def extract_thumbnail(video_path: str, seek_time: float, thumbnail_path: str) -> bool:
    """
    使用 FFmpeg 提取视频缩略图
    
    :param video_path: 输入视频文件的路径
    :param seek_time: 提取缩略图的时间点（秒）
    :param thumbnail_path: 输出缩略图文件的路径
    :return: True 表示成功，False 表示失败
    """
    if not Path(video_path).is_file():
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
        print(cmd)
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace')
        print(result)
        return result.returncode == 0
    except Exception as e:
        return False


if __name__ == "__main__":
    # subtitle = "E:/GithubProject/VideoCaptioner/app/core/subtitles0.srt"

    # video_path = "E:\\GithubProject\\VideoCaptioner\\app\\work_dir\\【卡卡】【语文大师】夜宿山寺——唐·李白\\audio.mp3"
    # video2audio(video_path, r"E:\\GithubProject\\VideoCaptioner\\app\\work_dir\\【卡卡】【语文大师】夜宿山寺——唐·李白\\audio.mp3")

    # video_path = r"C:\Users\weifeng\Videos\xhs\08.mp4"
    # # info = get_video_info(video_path, need_thumbnail=True)
    # # print(info)

    # thumbnail_file = r"C:\Users\weifeng\Videos\thumbnail.png"  # 替换为你希望保存的缩略图路径
    # success = extract_thumbnail(video_path, 2, thumbnail_file)
    # if not success:
    #     print("提取缩略图失败")
    # video_path = r"C:\Users\weifeng\Videos\xhs.mp4"
    video_path = r"C:\Users\weifeng\Videos\【卡卡】N进制演示器.mp4"
    srt_subtitle = r"E:\GithubProject\VideoCaptioner\app\work_dir\低视力音乐助人者_mp4\result_subtitle.srt"
    ass_subtitle = r"E:\GithubProject\VideoCaptioner\app\work_dir\低视力音乐助人者_mp4\result_subtitle.ass"
    # font_path = r"E:\GithubProject\VideoCaptioner\app\resource\AlibabaPuHuiTi-Medium.ttf"
    add_subtitles(video_path, srt_subtitle, "output.mp4", progress_callback=print, soft_subtitle=False)
