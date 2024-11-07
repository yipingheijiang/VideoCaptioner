import os
import re
import shutil
import subprocess
from pathlib import Path

from .ASRData import ASRDataSeg
from .BaseASR import BaseASR


class WhisperASR(BaseASR):
    def __init__(self, audio_path, model_path=None, language="en", whisper_cpp_path="whisper-cpp",
                 use_cache: bool = False, need_word_time_stamp: bool = False):
        super().__init__(audio_path, use_cache)
        if model_path is None:
            model_path = r"E:\GithubProject\VideoCaptioner\app\resource\models\ggml-medium.bin"
        self.model_path = Path(model_path)
        self.whisper_cpp_path = Path(whisper_cpp_path)
        self.need_word_time_stamp = need_word_time_stamp
        self.language = language

    def _make_segments(self, resp_data: str) -> list[ASRDataSeg]:
        return from_srt(resp_data)

    def _run(self, callback=None) -> str:
        if callback is None:
            callback = lambda x, y: None

        """使用 whisper.cpp 生成 SRT 字幕文件"""
        audio_path = Path(self.audio_path)

        temp_dir = Path(os.environ.get('TEMP')) / "bk_asr"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_audio = temp_dir / audio_path.name

        if audio_path.exists():
            shutil.copy(self.audio_path, temp_audio)
        else:
            raise FileNotFoundError(f"音频文件不存在: {self.audio_path}")
        output_path = temp_dir / f"{audio_path.stem}.srt"

        cmd = [str(self.whisper_cpp_path), "-m", str(self.model_path), str(temp_audio), "-l", self.language, "-osrt"]
        try:
            callback(5, "Whisper 转换")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1,
                universal_newlines=True
            )

            total_duration = self.get_audio_duration(str(temp_audio))

            while True:
                try:
                    line = process.stdout.readline()
                except UnicodeDecodeError:
                    continue

                if not line:
                    break

                # 解析时间戳
                if '[' in line and ']' in line:
                    time_str = line.split('[')[1].split(' -->')[0].strip()
                    hours, minutes, seconds = map(float, time_str.split(':'))
                    current_time = hours * 3600 + minutes * 60 + seconds

                    if callback:
                        progress = int(min(current_time / total_duration * 100, 98))
                        callback(progress, f"{progress}% 正在转换")

            callback(100, "转换完成")

            if process.wait() != 0:
                raise RuntimeError(f"生成 SRT 文件失败: {process.stderr.read()}")

        except Exception as e:
            print(f"生成 SRT 文件失败: {str(e)}")
            raise RuntimeError(f"生成 SRT 文件失败: {str(e)}")

        return output_path.read_text(encoding='utf-8')

    def detect_language(self, model_path: Path, whisper_cpp_path: Path) -> str:
        cmd = [str(whisper_cpp_path), "-m", str(model_path), str(self.audio_path), "-dl"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stderr.strip()

    def _get_key(self):
        return f"{self.__class__.__name__}-{self.crc32_hex}-{self.need_word_time_stamp}-{self.model_path}"

    def get_audio_duration(self, filepath: str) -> int:
        try:
            cmd = ["ffmpeg", "-i", filepath]
            print(" ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            info = result.stderr
            # 提取时长
            if duration_match := re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', info):
                hours, minutes, seconds = map(float, duration_match.groups())
                duration_seconds = hours * 3600 + minutes * 60 + seconds
                return int(duration_seconds)
        except Exception as e:
            print(f"获取音频时长时出错: {str(e)}")
            return 600


if __name__ == '__main__':
    # Example usage
    audio_file = r"E:\GithubProject\VideoCaptioner\AppData\work-dir\Speak_16x9_UHD_2997_pr422\audio.mp3"
    model_path = r"E:\GithubProject\VideoCaptioner\app\resource\models\ggml-tiny.bin"
    whisper_cpp_path = r"E:\GithubProject\VideoCaptioner\app\resource\bin\whisper-cpp.exe"

    # 修改这行，使用命名参数或者按照正确的位置参数顺序
    asr = WhisperASR(
        audio_path=audio_file,
        model_path=model_path,
        whisper_cpp_path=whisper_cpp_path,
        language="en",
        need_word_time_stamp=True
    )
    asr_data = asr._run(callback=print)
    # print(asr_data.to_srt())
