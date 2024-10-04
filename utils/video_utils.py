import subprocess
from typing import Literal

import ffmpeg


def video2audio(input_file: str, output:str="") -> bytes:
    """Render audio file using ffmpeg"""
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
            cmd = ['ffmpeg', '-i', input_file, '-i', subtitle_file, '-c:v', 'copy', '-c:a', 'copy', '-c:s', 'mov_text', '-loglevel', 'quiet',output, '-y']
            subprocess.run(cmd)
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