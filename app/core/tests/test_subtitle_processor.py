import logging
import os
from pathlib import Path

from core.subtitle_processor.optimizer import SubtitleOptimizer
from core.subtitle_processor.summarizer import SubtitleSummarizer
from core.bk_asr.ASRData import from_srt

os.environ['OPENAI_BASE_URL'] = "https://api.ephone.ai/v1"
os.environ['OPENAI_API_KEY'] = "sk-msuqsbr4Ano2cV1GDk0AIaUS1MXS3vukQF0eI7Cble8CgF7Q"
MODEL = "gpt-4o-mini"

summarize_result = """{'summary': "The video features a humorous storytelling session where the speaker reminisces about a childhood game played with their mother, where they pretended to have died whenever she stopped the car. This segues into a discussion about the overload of marketing emails received, particularly from a fictional supermarket named 'safemart,' which becomes a source of comedic frustration. The speaker narrates a series of interactions with 'Dan,' a representative from safemart, regarding the opening of a new store, leading to a ridiculous exchange involving a bouncy castle. The story culminates in the speaker's creation of an email auto-responder that endlessly generates case numbers in response to safemart's emails, symbolizing a light-hearted rebellion against mundane bureaucratic annoyances. The message encourages viewers to embrace whimsy when faced with modern life's frustrations.", 'terms': {'entities': ['safemart', "King's Cross", 'Dan'], 'technical_terms': ['email auto replier', 'case number'], 'keywords': ['information overload', 'marketing emails', 'childhood game', 'bureaucracy', 'whimsy']}}
"""

asr_data = from_srt(Path(r"C:\Users\weifeng\Music\output_000.srt").read_text(encoding="utf-8"))
subtitle_json = {str(k): v["original_subtitle"] for k, v in asr_data.to_json().items()}

print("[+]正在优化/翻译字幕...")
optimizer = SubtitleOptimizer(summary_content=summarize_result, target_language="English")
optimizer_result = optimizer.optimizer_multi_thread(subtitle_json, translate=True)
print(optimizer_result)

