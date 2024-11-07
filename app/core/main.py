import os

from app.core.subtitle_processor.subtitle_config import OPENAI_API_KEY, OPENAI_BASE_URL, MODEL
from bk_asr.ASRData import ASRData
from utils.logger import setup_logger
from utils.optimize_subtitles import optimize_subtitles

# from subtitle_processor.translator import SubtitleTranslator

os.environ['OPENAI_BASE_URL'] = OPENAI_BASE_URL
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
# MODEL = "gpt-4o"
# MODEL = "claude-3-5-sonnet@20240620"

logger = setup_logger("main")

if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    original_language = "zh"
    target_language = "en"

    video_file = r"resources/Pointless Ai Products.mp4"
    output_file = os.path.abspath(video_file).split(".")[0] + "_subtitled.mp4"
    srt_file = f"subtitles_{MODEL}.srt"

    # 语音识别
    print("[+]正在进行语音识别...")
    # audio_file = video2audio(video_file, output="audio.mp3")
    # asr = JianYingASR(audio_file, use_cache=True)
    # asr_data = asr.run()
    # asr_data.segments = asr_data.segments[:200]
    # asr_data.to_srt(save_path="subtitles0.srt")
    # optimize_subtitles(asr_data)
    # asr_data.to_srt(save_path="subtitles_fix.srt")
    # # print(asr_data.to_txt())
    # # raise 4
    # subtitle_json = asr_data.to_json()

    asr_data = ASRData.from_srt(
        open(r"E:\GithubProject\VideoCaptioner\app\core\subtitles0.srt", encoding="utf-8").read())
    optimize_subtitles(asr_data)
    asr_data.segments = asr_data.segments[:20]
    subtitle_json = asr_data.to_json()
    print(subtitle_json)
    raise 0

    # 总结字幕
    print("[+]正在总结字幕...")
    summarizer = SubtitleSummarizer(model=MODEL)
    summarize_result = summarizer.summarize(asr_data.to_txt())
    print(summarize_result)
    # raise 0

    # 正在优化/翻译字幕...
    print("[+]正在优化/翻译字幕...")
    optimizer = SubtitleOptimizer(summary_content=summarize_result, model=MODEL)
    optimizer_result = optimizer.optimizer_multi_thread(subtitle_json, batch_num=10, thread_num=50, translate=True)
    print(optimizer_result)

    # print("[+]正在优化字幕...")
    # optimizer = SubtitleOptimizer(summary_content=summarize_result)
    # optimizer_result = optimizer.optimizer_multi_thread(subtitle_json, batch_num=50, thread_num=10)

    # 保存字幕
    for i, subtitle_text in optimizer_result.items():
        seg = asr_data.segments[int(i) - 1]
        seg.text = subtitle_text
    asr_data.to_srt(save_path=srt_file)

    print("[+]正在添加字幕...")
    subtitle_file = srt_file
    add_subtitles(video_file, subtitle_file, output_file, log='quiet', soft_subtitle=True)
