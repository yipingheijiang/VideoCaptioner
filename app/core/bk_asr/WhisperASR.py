import os
import re
import shutil
import subprocess
from pathlib import Path

from .ASRData import ASRDataSeg, from_srt
from .BaseASR import BaseASR
from ..utils.logger import setup_logger
from ...config import MODEL_PATH

logger = setup_logger("whisper_asr")


class WhisperASR(BaseASR):
    def __init__(self, audio_path, language="en", whisper_cpp_path="whisper-cpp", whisper_model=None,
                 use_cache: bool = False, need_word_time_stamp: bool = False):
        super().__init__(audio_path, False)
        # 如果指定了 whisper_model，则在 models 目录下查找对应模型
        if whisper_model:
            models_dir = Path(MODEL_PATH)
            model_files = list(models_dir.glob(f"*ggml*{whisper_model}*.bin"))
            if not model_files:
                raise ValueError(f"在 {models_dir} 目录下未找到包含 '{whisper_model}' 的模型文件")
            model_path = str(model_files[0])
            logger.info(f"找到模型文件: {model_path}")
        else:
            raise ValueError("whisper_model 不能为空")

        self.model_path = model_path
        self.whisper_cpp_path = Path(whisper_cpp_path)
        self.need_word_time_stamp = need_word_time_stamp
        self.language = language

        self.process = None

    def _make_segments(self, resp_data: str) -> list[ASRDataSeg]:
        asr_data = from_srt(resp_data)
        # 过滤掉纯音乐标记
        filtered_segments = []
        for seg in asr_data.segments:
            text = seg.text.strip()
            # 保留不以【、[、(、（开头的文本
            if not (text.startswith('【') or 
                   text.startswith('[') or 
                   text.startswith('(') or 
                   text.startswith('（')):
                filtered_segments.append(seg)
        
        asr_data.segments = filtered_segments
        return asr_data

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
            logger.error(f"音频文件不存在: {self.audio_path}")
            raise FileNotFoundError(f"音频文件不存在: {self.audio_path}")
        output_path = temp_dir / f"{audio_path.stem}.srt"

        cmd = [str(self.whisper_cpp_path), "-m", str(self.model_path), str(temp_audio), "-l", self.language, "-osrt"]
        try:
            callback(5, "正在 Whisper")
            logger.info("开始执行命令: %s", " ".join(cmd))
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1,
                universal_newlines=True,
                shell=True
            )

            total_duration = self.get_audio_duration(str(temp_audio))
            logger.info("音频总时长: %d 秒", total_duration)

            while True:
                try:
                    line = self.process.stdout.readline()
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
                        logger.info("当前进度: %d%%", progress)

            callback(100, "转换完成")
            logger.info("转换完成")

            if self.process.wait() != 0:
                error_message = self.process.stderr.read()
                logger.error("生成 SRT 文件失败: %s", error_message)
                raise RuntimeError(f"生成 SRT 文件失败: {error_message}")

        except Exception as e:
            logger.exception("生成 SRT 文件失败: %s", str(e))
            raise RuntimeError(f"生成 SRT 文件失败: {str(e)}")

        return output_path.read_text(encoding='utf-8')

    def _get_key(self):
        return f"{self.__class__.__name__}-{self.crc32_hex}-{self.need_word_time_stamp}-{self.model_path}"

    def get_audio_duration(self, filepath: str) -> int:
        try:
            cmd = ["ffmpeg", "-i", filepath]
            logger.info("获取音频时长命令: %s", " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', shell=True)
            info = result.stderr
            # 提取时长
            if duration_match := re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', info):
                hours, minutes, seconds = map(float, duration_match.groups())
                duration_seconds = hours * 3600 + minutes * 60 + seconds
                logger.info("音频时长: %d 秒", duration_seconds)
                return int(duration_seconds)
        except Exception as e:
            logger.exception("获取音频时长时出错: %s", str(e))
            return 600

    def stop(self):
        """停止 ASR 语音识别处理
        - 终止进程及其子进程
        """
        if self.process:
            logger.info("终止 Whisper ASR 进程")
            if os.name == 'nt':  # Windows系统
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)], 
                             capture_output=True)
            else:  # Linux/Mac系统
                import signal
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process = None


if __name__ == '__main__':
    # 简短示例
    asr = WhisperASR(
        audio_path="audio.mp3",
        model_path="models/ggml-tiny.bin",
        whisper_cpp_path="bin/whisper-cpp.exe",
        language="en",
        need_word_time_stamp=True
    )
    asr_data = asr._run(callback=print)
