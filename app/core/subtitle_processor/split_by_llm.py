import hashlib
import json
import os
import re
from typing import List, Optional

import openai
import retry

from app.config import CACHE_PATH
from .subtitle_config import SPLIT_SYSTEM_PROMPT
from ..utils.logger import setup_logger

logger = setup_logger("split_by_llm")

MAX_WORD_COUNT = 20  # 英文单词或中文字符的最大数量


def count_words(text: str) -> int:
    """
    统计混合文本中英文单词数和中文字符数的总和
    """
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_text = re.sub(r'[\u4e00-\u9fff]', ' ', text)
    english_words = len(english_text.strip().split())
    return english_words + chinese_chars


def get_cache_key(text: str, model: str) -> str:
    """
    生成缓存键值
    """
    return hashlib.md5(f"{text}_{model}".encode()).hexdigest()


def get_cache(text: str, model: str) -> Optional[List[str]]:
    """
    从缓存中获取断句结果
    """
    cache_key = get_cache_key(text, model)
    cache_file = CACHE_PATH / f"{cache_key}.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return None
    return None


def set_cache(text: str, model: str, result: List[str]) -> None:
    """
    将断句结果设置到缓存中
    """
    cache_key = get_cache_key(text, model)
    cache_file = CACHE_PATH / f"{cache_key}.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)
    except IOError:
        pass


def split_by_llm(text: str, model: str = "gpt-4o-mini", use_cache: bool = False) -> List[str]:
    """
    包装 split_by_llm_retry 函数，确保在重试全部失败后返回空列表
    """
    try:
        return split_by_llm_retry(text, model, use_cache)
    except Exception as e:
        logger.error(f"断句失败: {e}")
        return [text]
        #TODO: 断句失败后。。。自己断句

@retry.retry(tries=3)
def split_by_llm_retry(text: str, model: str = "gpt-4o-mini", use_cache: bool = False) -> List[str]:
    """
    使用LLM进行文本断句
    """
    if use_cache:
        cached_result = get_cache(text, model)
        if cached_result:
            logger.info(f"从缓存中获取断句结果")
            return cached_result
    logger.info(f"未命中缓存，开始断句")
    prompt = f"Please use multiple <br> tags to separate the following sentence:\n{text}"
    # 初始化OpenAI客户端
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SPLIT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    result = response.choices[0].message.content
    # 清理结果中的多余换行符
    result = re.sub(r'\n+', '', result)
    split_result = [segment.strip() for segment in result.split("<br>") if segment.strip()]

    br_count = len(split_result)
    if br_count < count_words(text) / MAX_WORD_COUNT * 0.9:
        raise Exception("断句失败")
    set_cache(text, model, split_result)
    return split_result


if __name__ == "__main__":
    sample_text = (
        "大家好我叫杨玉溪来自有着良好音乐氛围的福建厦门自记事起我眼中的世界就是朦胧的童话书是各色杂乱的线条电视机是颜色各异的雪花小伙伴是只听其声不便骑行的马赛克后来我才知道这是一种眼底黄斑疾病虽不至于失明但终身无法治愈"
    )
    sentences = split_by_llm(sample_text, use_cache=True)
    print(sentences)
