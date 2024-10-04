import logging
from bk_asr import BcutASR, JianYingASR, KuaiShouASR
from utils.video_utils import add_subtitles, video2audio
from bk_asr.ASRData import ASRData

if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # audio_file = r"test_audio.mp3"
    # asr = JianYingASR(audio_file, use_cache=True)
    # asr_data = asr.run()
    # print(asr_data.to_srt())
    # asr_data.to_srt(save_path="subtitles0.srt")

    asr_data = ASRData.from_srt(open("../src_subtitles.srt", encoding="utf-8").read())
    print(asr_data.to_srt())
