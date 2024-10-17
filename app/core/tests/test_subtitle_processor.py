import logging
import os

from configs.subtitle_config import OPENAI_API_KEY, OPENAI_BASE_URL, MODEL
from subtitle_processor import optimizer, summarizer, translator
from subtitle_processor.optimizer import SubtitleOptimizer
from subtitle_processor.summarizer import SubtitleSummarizer
from subtitle_processor.translator import SubtitleTranslator

from configs.subtitle_config import OPENAI_API_KEY, OPENAI_BASE_URL, MODEL

os.environ['OPENAI_BASE_URL'] = OPENAI_BASE_URL
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
MODEL = "gpt-4o-mini"

summarize_result = """{'summary': "The video features a humorous storytelling session where the speaker reminisces about a childhood game played with their mother, where they pretended to have died whenever she stopped the car. This segues into a discussion about the overload of marketing emails received, particularly from a fictional supermarket named 'safemart,' which becomes a source of comedic frustration. The speaker narrates a series of interactions with 'Dan,' a representative from safemart, regarding the opening of a new store, leading to a ridiculous exchange involving a bouncy castle. The story culminates in the speaker's creation of an email auto-responder that endlessly generates case numbers in response to safemart's emails, symbolizing a light-hearted rebellion against mundane bureaucratic annoyances. The message encourages viewers to embrace whimsy when faced with modern life's frustrations.", 'terms': {'entities': ['safemart', "King's Cross", 'Dan'], 'technical_terms': ['email auto replier', 'case number'], 'keywords': ['information overload', 'marketing emails', 'childhood game', 'bureaucracy', 'whimsy']}}
"""

print("[+]正在优化/翻译字幕...")
subtitle_json = {'0': 'Funny, the things you forget'}
optimizer = SubtitleTranslator(summarize_result=summarize_result)
optimizer_result = optimizer.optimizer(subtitle_json)
print(optimizer_result)

