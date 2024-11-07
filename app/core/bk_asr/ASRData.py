import json
import re
from typing import List
from pathlib import Path

class ASRDataSeg:
    def __init__(self, text, start_time, end_time):
        self.text = text
        self.start_time = start_time
        self.end_time = end_time

    def to_srt_ts(self) -> str:
        """Convert to SRT timestamp format"""
        return f"{self._ms_to_srt_time(self.start_time)} --> {self._ms_to_srt_time(self.end_time)}"


    def to_lrc_ts(self) -> str:
        """Convert to LRC timestamp format"""
        return f"[{self._ms_to_lrc_time(self.start_time)}]"
    
    def to_ass_ts(self) -> tuple[str, str]:
        """Convert to ASS timestamp format"""
        return self._ms_to_ass_ts(self.start_time), self._ms_to_ass_ts(self.end_time)

    def _ms_to_lrc_time(self, ms) -> str:
        seconds = ms / 1000
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes):02}:{seconds:.2f}"
    
    @staticmethod
    def _ms_to_srt_time(ms) -> str:
        """Convert milliseconds to SRT time format (HH:MM:SS,mmm)"""
        total_seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{int(milliseconds):03}"

    @staticmethod
    def _ms_to_ass_ts(ms) -> str:
        """Convert milliseconds to ASS timestamp format (H:MM:SS.cc)"""
        total_seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        # ASS格式使用厘秒(1/100秒)而不是毫秒
        centiseconds = int(milliseconds / 10)
        return f"{int(hours):01}:{int(minutes):02}:{int(seconds):02}.{centiseconds:02}"

    @property
    def transcript(self) -> str:
        """Return segment text"""
        return self.text

    def __str__(self) -> str:
        return f"ASRDataSeg({self.text}, {self.start_time}, {self.end_time})"


class ASRData:
    def __init__(self, segments: List[ASRDataSeg]):
        self.segments = segments

    def __iter__(self):
        return iter(self.segments)
    
    def __len__(self) -> int:
        return len(self.segments)
    
    def has_data(self) -> bool:
        """Check if there are any utterances"""
        return len(self.segments) > 0
    
    def is_word_timestamp(self) -> bool:
        """
        判断是否是字级时间戳
        规则：
        1. 对于英文，每个segment应该只包含一个单词
        2. 对于中文，每个segment应该只包含一个汉字
        3. 允许20%的误差率
        """
        if not self.segments:
            return False
            
        valid_segments = 0
        total_segments = len(self.segments)
        
        for seg in self.segments:
            text = seg.text.strip()
            # 检查是否只包含一个英文单词或一个汉字
            if (len(text.split()) == 1 and text.isascii()) or len(text.strip()) <= 2:
                valid_segments += 1
        print(f"valid_segments: {valid_segments}, total_segments: {total_segments}")
        return (valid_segments / total_segments) >= 0.8


    def save(self, save_path: str, ass_style: str = None, layout: str = "原文在上") -> None:
        """Save the ASRData to a file"""
        # 根据文件后缀名选择保存格式
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        if save_path.endswith('.srt'):
            self.to_srt(save_path=save_path)
        elif save_path.endswith('.txt'):
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(self.to_txt())
        elif save_path.endswith('.json'):
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_json(), f, ensure_ascii=False)
        elif save_path.endswith('.ass'):
            self.to_ass(save_path=save_path, style_str=ass_style, layout=layout)
        else:
            raise ValueError(f"Unsupported file extension: {save_path}")

    def to_txt(self) -> str:
        """Convert to plain text subtitle format (without timestamps)"""
        return "\n".join(seg.transcript for seg in self.segments)

    def to_srt(self, save_path=None) -> str:
        """Convert to SRT subtitle format"""
        srt_text = "\n".join(
            f"{n}\n{seg.to_srt_ts()}\n{seg.transcript}\n"
            for n, seg in enumerate(self.segments, 1))
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(srt_text)
        return srt_text

    def to_lrc(self, save_path=None) -> str:
        """Convert to LRC subtitle format"""
        lrc_text = "\n".join(
            f"{seg.to_lrc_ts()}{seg.transcript}" for seg in self.segments
        )
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(lrc_text)
        return lrc_text

    def to_json(self) -> dict:
        result_json = {}
        for i, segment in enumerate(self.segments, 1):
            # 检查是否有换行符
            if "\n" in segment.text:
                original_subtitle, translated_subtitle = segment.text.split("\n")
            else:
                original_subtitle, translated_subtitle = segment.text, ""

            result_json[str(i)] = {
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "original_subtitle": original_subtitle,
                "translated_subtitle": translated_subtitle
            }
        return result_json

    def to_ass(self, style_str: str = None, layout: str = "原文在上", save_path: str = None) -> str:
        """转换为ASS字幕格式
        
        Args:
            style_str: ASS样式字符串,为空则使用默认样式
            layout: 字幕布局,可选值["译文在上", "原文在上", "仅原文", "仅译文"]
            
        Returns:
            ASS格式字幕内容
        """
        # 默认样式
        if not style_str:
            style_str = (
                "[V4+ Styles]\n"
                "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
                "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
                "Alignment,MarginL,MarginR,MarginV,Encoding\n"
                "Style: Default,微软雅黑,66,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,"
                "0,0,1,2,0,2,10,10,10,1\n"
                "Style: Translate,微软雅黑,40,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,"
                "0,0,1,2,0,2,10,10,10,1"
            )

        # 构建ASS文件头
        ass_content = (
            "[Script Info]\n"
            "; Script generated by VideoCaptioner\n"
            "; https://github.com/weifeng2333\n"
            "ScriptType: v4.00+\n"
            "PlayResX: 1280\n"
            "PlayResY: 720\n\n"
            f"{style_str}\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )

        # 根据布局生成对话内容
        for seg in self.segments:
            start_time = seg.to_ass_ts()[0]
            end_time = seg.to_ass_ts()[1]
            dialogue_template = 'Dialogue: 0,{},{},{},,0,0,0,,{}\n'

            # 检查是否有换行符分隔的原文和译文
            if "\n" in seg.text:
                original, translate = seg.text.split("\n")
                if layout == "译文在上" and translate:
                    ass_content += dialogue_template.format(start_time, end_time, "Secondary", original)
                    ass_content += dialogue_template.format(start_time, end_time, "Default", translate)
                elif layout == "原文在上" and translate:
                    ass_content += dialogue_template.format(start_time, end_time, "Secondary", translate)
                    ass_content += dialogue_template.format(start_time, end_time, "Default", original)
                elif layout == "仅原文":
                    ass_content += dialogue_template.format(start_time, end_time, "Default", original)
                elif layout == "仅译文" and translate:
                    ass_content += dialogue_template.format(start_time, end_time, "Default", translate)
            else:
                original = seg.text
                ass_content += dialogue_template.format(start_time, end_time, "Default", original)
            # 根据布局生成对话行
            
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
        return ass_content

    def merge_segments(self, start_index: int, end_index: int, merged_text: str = None):
            """合并从 start_index 到 end_index 的段（包含）。"""
            if start_index < 0 or end_index >= len(self.segments) or start_index > end_index:
                raise IndexError("无效的段索引。")
            merged_start_time = self.segments[start_index].start_time
            merged_end_time = self.segments[end_index].end_time
            if merged_text is None:
                merged_text = ''.join(seg.text for seg in self.segments[start_index:end_index+1])
            merged_seg = ASRDataSeg(merged_text, merged_start_time, merged_end_time)
            # 替换 segments[start_index:end_index+1] 为 merged_seg
            self.segments[start_index:end_index+1] = [merged_seg]

    def merge_with_next_segment(self, index: int) -> None:
        """合并指定索引的段与下一个段。"""
        if index < 0 or index >= len(self.segments) - 1:
            raise IndexError("索引超出范围或没有下一个段可合并。")
        current_seg = self.segments[index]
        next_seg = self.segments[index + 1]

        # 合并文本
        merged_text = f"{current_seg.text} {next_seg.text}"
        merged_start_time = current_seg.start_time
        merged_end_time = next_seg.end_time
        merged_seg = ASRDataSeg(merged_text, merged_start_time, merged_end_time)

        # 替换当前段为合并后的段
        self.segments[index] = merged_seg
        # 删除下一个段
        del self.segments[index + 1]

    def __str__(self):
        return self.to_txt()