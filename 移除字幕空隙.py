import re


def parse_time(time_str):
    hours, minutes, seconds, milliseconds = map(int, re.split(r':|,', time_str))
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000


def format_time(total_seconds):
    hours, remainder = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def adjust_srt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    new_subtitles = []
    prev_end_time = None

    for i in range(0, len(lines), 4):  # SRT文件每4行是一个字幕条目
        if i + 3 < len(lines):  # 确保我们有完整的字幕条目
            subtitle_number = lines[i].strip()
            timecode = lines[i + 1].strip()
            start, end = timecode.split(' --> ')

            # 解析时间
            start_time = parse_time(start)
            end_time = parse_time(end)

            # 调整开始时间
            if prev_end_time is not None:
                adjusted_start_time = prev_end_time + 0.001  # 前一个字幕的结束时间加1毫秒
                adjusted_start = format_time(adjusted_start_time)
                new_timecode = f"{adjusted_start} --> {end}"
            else:
                # 如果是第一个字幕条目，保持原时间
                new_timecode = timecode

            # 更新前一个字幕的结束时间
            prev_end_time = end_time

            # 收集字幕内容
            subtitle_text = lines[i + 2].strip()

            # 构建新的字幕条目
            new_subtitles.extend([
                f"{subtitle_number}\n",
                f"{new_timecode}\n",
                f"{subtitle_text}\n",
                "\n"  # SRT文件每条目间通常有空行
            ])

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(''.join(new_subtitles))


# 使用示例：
adjust_srt(r"C:\Users\A\Desktop\片尾.srt")   
