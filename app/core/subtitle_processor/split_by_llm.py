import hashlib
import json
import os
import re
from typing import List, Optional
import openai
import retry

from .subtitle_config import SPLIT_SYSTEM_PROMPT
from app.config import CACHE_PATH


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
    cache_file = os.path.join(CACHE_PATH, f"{cache_key}.json")
    if os.path.exists(cache_file):
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
    cache_file = os.path.join(CACHE_PATH, f"{cache_key}.json")
    os.makedirs(CACHE_PATH, exist_ok=True)
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)
    except IOError:
        pass

# 设置次数
@retry.retry(tries=3)
def split_by_llm(text: str, model: str = "gpt-4o-mini", use_cache: bool = False) -> List[str]:
    """
    使用LLM进行文本断句
    """
    if use_cache:
        cached_result = get_cache(text, model)
        if cached_result:
            # print(f"[+] 从缓存中获取结果: {cached_result}")
            return cached_result

    prompt = f"请你对下面句子使用<br>进行分割：\n{text}"

    try:
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
        
        set_cache(text, model, split_result)
        return split_result
    except Exception as e:
        print(f"[!] 请求LLM失败: {e}")
        return []

if __name__ == "__main__":
    sample_text = (
        "大家好我叫杨玉溪来自有着良好音乐氛围的福建厦门自记事起我眼中的世界就是朦胧的童话书是各色杂乱的线条电视机是颜色各异的雪花小伙伴是只听其声不便骑行的马赛克后来我才知道这是一种眼底黄斑疾病虽不至于失明但终身无法治愈"
    )
    sentences = split_by_llm(sample_text, use_cache=True)
    print(sentences)
