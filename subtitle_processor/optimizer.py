import difflib
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

import retry
from openai import OpenAI

from configs.subtitle_config import (
    TRANSLATE_PROMPT,
    OPTIMIZER_PROMPT,
    DEFAULT_MODEL,
    SIMILARITY_THRESHOLD,
    REPAIR_THRESHOLD,
    BATCH_SIZE,
    MAX_THREADS
)
from subtitle_processor.aligner import SubtitleAligner
from utils import json_repair
from utils.logger import setup_logger

logger = setup_logger("subtitle_translate")


class SubtitleOptimizer:
    """A class for optimize and translating subtitles using OpenAI's API."""

    def __init__(self, model: str = DEFAULT_MODEL, summary_content="") -> None:
        base_url = os.getenv('OPENAI_BASE_URL')
        api_key = os.getenv('OPENAI_API_KEY')
        assert base_url and api_key, "环境变量 OPENAI_BASE_URL 和 OPENAI_API_KEY 必须设置"

        self.model = model
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.summary_content = summary_content

        self.prompt = TRANSLATE_PROMPT

    @retry.retry(tries=3)
    def optimize(self, original_subtitle: Dict[int, str]) -> Dict[int, str]:
        """ Optimize the given subtitle. """
        logger.info(f"[+]正在优化字幕：{next(iter(original_subtitle))} - {next(reversed(original_subtitle))}")

        message = self._create_optimizer_message(original_subtitle)

        response = self.client.chat.completions.create(
            model=self.model,
            stream=False,
            messages=message)

        optimized_text = json_repair.loads(response.choices[0].message.content)

        aligned_subtitle = repair_subtitle(original_subtitle, optimized_text)  # 修复字幕对齐问题

        return aligned_subtitle

    def optimizer_multi_thread(self, subtitle_json: Dict[int, str], batch_num=BATCH_SIZE, thread_num: int = MAX_THREADS, translate=False):
        items = list(subtitle_json.items())[:]
        chunks = [dict(items[i:i + batch_num]) for i in range(0, len(items), batch_num)]
        logger.debug(chunks)

        with ThreadPoolExecutor(max_workers=thread_num) as executor:
            if translate:
                results = list(executor.map(self.translate, chunks))
            else:
                results = list(executor.map(self.optimize, chunks))

        # 合并结果
        optimizer_result = {k: v for result in results for k, v in result.items()}
        return optimizer_result

    @retry.retry(tries=3)
    def translate(self, original_subtitle: Dict[int, str]) -> Dict[int, str]:
        """Optimize and translate the given subtitle."""
        logger.info(f"[+]正在优化字幕：{next(iter(original_subtitle))} - {next(reversed(original_subtitle))}")

        message = self._create_translate_message(original_subtitle)
        response = self.client.chat.completions.create(
            model=self.model,
            stream=False,
            messages=message)

        response_content = json_repair.loads(response.choices[0].message.content)

        optimized_text = {k: v[0] for k, v in response_content.items()}  # 字幕文本

        aligned_subtitle = repair_subtitle(original_subtitle, optimized_text)  # 修复字幕对齐问题

        # 在 translations 中查找对应的翻译
        translations = dict(response_content.values())  # 文本-翻译 映射
        translated_subtitle = {k: f"{v}\n{translations.get(v, ' ')}" for k, v in aligned_subtitle.items()}

        return translated_subtitle

    def _create_translate_message(self, original_subtitle: Dict[int, str]):
        input_content = f"please correct and translate input_subtitle based on the summary and keywords:\n<input_subtitle>{str(original_subtitle)}</input_subtitle>"
        if self.summary_content:
            input_content += f"\nBelow is a summary of the subtitle content and related keywords:\n<summary>{self.summary_content}</summary>\n"

        example_input = ('{"0": "hello everyone my name is Yang Yuxi","1": "i come from Xiamen Fujian which has a '
                         'great musical atmosphere","2": "i used to play with myself to entertain myself.",'
                         '"3": "the world in my eye is blurry","4": "fairy tale books are chaotic lines of various '
                         'colors","5": "my buddies are mosaics that can be heard but not seen"}')
        example_output = ('{"0": ["Hello everyone, my name is Yang Yuxi", "大家好，我叫杨玉熙"],"1": ["I come from Xiamen, '
                          'Fujian, which has a great musical atmosphere", "来自有着良好音乐氛围的福建厦门"],"2": ["I used to play '
                          'with myself to entertain myself.", "我以前常常自娱自乐"],"3": ["The world in my eyes is blurry", '
                          '"我眼中的世界就是朦胧的"],"4": ["Fairy tale books are chaotic lines of various colors", '
                          '"童话书是各色杂乱的线条"],"5": ["My buddies are mosaics that can be heard but not seen", '
                          '"小伙伴是只听其声不见其形的马赛克"]}')

        message = [{"role": "system", "content": TRANSLATE_PROMPT},
                   {"role": "user", "content": example_input},
                   {"role": "assistant", "content": example_output},
                   {"role": "user", "content": input_content}]
        return message

    def _create_optimizer_message(self, original_subtitle):
        input_content = f"please correct the input_subtitle:\n<input_subtitle>{str(original_subtitle)}</input_subtitle>"
        if self.summary_content:
            input_content += f"\nBelow is a summary of the subtitle content and related keywords:\n<summary>{self.summary_content}</summary>\n"
        example_input = '{"0": "调用现成的start方法","1": "才能成功开启现成啊","2": "而且stread这个类","3": "很多业务罗技和这个代码","4": "全部都给掺到一块去了"}'
        example_output = '{"0": "调用线程的start()方法","1": "才能成功开启线程","2": "而且Thread这个类","3": "很多业务逻辑和这个代码","4": "全部都给掺到一块去了"}'
        message = [{"role": "system", "content": OPTIMIZER_PROMPT},
                   {"role": "user", "content": example_input},
                   {"role": "assistant", "content": example_output},
                   {"role": "user", "content": input_content}]
        return message


def repair_subtitle(dict1, dict2) -> Dict[int, str]:
    list1 = list(dict1.values())
    list2 = list(dict2.values())
    text_aligner = SubtitleAligner()
    aligned_source, aligned_target = text_aligner.align_texts(list1, list2)

    similar_list = calculate_similarity_list(aligned_source, aligned_target)
    if similar_list.count(True) / len(similar_list) >= 0.8:
        # logger.info(f"修复成功！{similar_list.count(True) / len(similar_list)}:.2f")
        start_id = next(iter(dict1.keys()))
        modify_dict = {str(int(start_id) + i): value for i, value in enumerate(aligned_target)}
        return modify_dict
    else:
        logger.info(f"修复失败！{similar_list.count(True) / len(similar_list):.2f}")
        return dict1


def is_similar(text1, text2, threshold=0.4):
    similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
    return similarity >= threshold


def calculate_similarity_list(list1, list2, threshold=0.5):
    max_len = min(len(list1), len(list2))
    similar_list = [False] * max_len  # 初始化相似性列表

    for i in range(max_len):
        similar_list[i] = is_similar(list1[i], list2[i], threshold)

    return similar_list


if __name__ == "__main__":
    # os.environ['OPENAI_BASE_URL'] = 'https://api.gptgod.online/v1'
    # os.environ['OPENAI_API_KEY'] = 'sk-4StuHHm6Z1q0VcPHdPTUBdmKMsHW9JNZKe4jV7pJikBsGRuj'
    # MODEL = "gpt-4o-mini"
    os.environ['OPENAI_BASE_URL'] = 'https://api.turboai.one/v1'
    os.environ['OPENAI_API_KEY'] = 'sk-ZOCYCz5kexAS3X8JD3A33a5eB20f486eA26896798055F2C5'
    MODEL = "gpt-4o-mini"
