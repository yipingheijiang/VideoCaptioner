
import os
# 添加上一级目录
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from bk_asr import BcutASR, JianYingASR, KuaiShouASR
from utils.video_utils import add_subtitles, video2audio
from bk_asr.ASRData import ASRData, from_srt, ASRDataSeg

import difflib
from typing import List


def merge_segments_based_on_sentences(asr_data: ASRData, sentences: List[str]):
    # 将 asr_data.segments 中的每个字符映射到其对应的段索引
    asr_text = ''.join(seg.text for seg in asr_data.segments)
    asr_char_to_seg_index = []
    for idx, seg in enumerate(asr_data.segments):
        asr_char_to_seg_index.extend([idx] * len(seg.text))
    
    new_segments = []
    asr_index = 0  # 记录在 asr_text 中的位置

    for sentence in sentences:
        sentence_len = len(sentence)
        found = False

        # 在 asr_text 中查找当前句子的位置
        pos = asr_text.find(sentence, asr_index)
        if pos != -1:
            start_char_pos = pos
            end_char_pos = pos + sentence_len - 1

            # 获取对应的段索引
            start_seg_index = asr_char_to_seg_index[start_char_pos]
            end_seg_index = asr_char_to_seg_index[end_char_pos]

            # 获取合并后的开始和结束时间
            merged_start_time = asr_data.segments[start_seg_index].start_time
            merged_end_time = asr_data.segments[end_seg_index].end_time

            # 创建合并后的段
            merged_seg = ASRDataSeg(sentence, merged_start_time, merged_end_time)
            new_segments.append(merged_seg)

            asr_index = pos + sentence_len  # 更新 asr_index 到当前句子的结束位置
            found = True
        else:
            # 如果未找到匹配的句子，可以选择跳过或采取其他处理方式
            pass

    # 更新 asr_data.segments
    asr_data.segments = new_segments


if __name__ == '__main__':
    audio_file = r"E:\GithubProject\VideoCaptioner\app\work_dir\audio\audio.mp3"
    asr = BcutASR(audio_file, use_cache=True, need_word_time_stamp=True)
    asr_data = asr.run()
    # print(asr_data.to_txt().replace("\n", ""))
    asr_data.to_srt(save_path=r"E:\GithubProject\SubtitleSpliter\audio.srt")

    # text = "大家好<br>今天我们带来的<br>3d创意设计作品是禁制演示器<br>我是来自中山大学附属中学的方若涵<br>我是陈欣然<br>我们这一次作品介绍分为三个部分<br>第一个部分提出问题<br>第二个部分解决方案<br>第三个部分作品介绍<br>当我们学习进制的时候难以掌握<br>老师教学也比较抽象<br>那有没有一种教具或演示器<br>可以将进制的原理形象生动地展现出来<br>又方便操作呢<br>于是我们就设计了进制演示器<br>来解决以上的问题<br>整个进制演示器是由条状进制数位提现器为基础<br>加上机械化半自动装置组成<br>这个就是我们利用3d打印打印出来的定制演示器<br>这个是条状静止数位体现器<br>这个是机械化半自动装置<br>接下来就让我们详细的介绍一下这个作品的制作原理吧<br>假设我们要演示的是五进制<br>那么就是逢五进一<br>右边的管子已经有了四颗珠子<br>第五颗珠子就会自动滚落到下一个管子里<br>也就是进了一位<br>如左图所示用五进制表示<br>就是14转换为十进制就是九<br>为了实现各种进制的演示<br>整个演示器是可拆卸的<br>我们的管子和滑道都有卡槽的设计<br>可以根据想演示的静止来调整数量<br>在最底部也设计了由固定的管道和收集弹珠的碗组成的收集器<br>来收集弹珠<br>我们整个进制演示器是由可拆卸设计<br>可以调整管子的数量来实现不同进制的演示<br>接下来由我为大家介绍机械化装置原理<br>当弹珠进位经过滑道时<br>它会触碰到图一的挡板<br>一向左侧移动<br>与之同时挡板一相连的板子二将引动下方的弹簧装置<br>由于板子三向上抬起<br>与其相连的弹簧会伸长<br>在右侧管道弹珠全部清零后<br>板子三会刚好卡到装置二的凹槽中<br>弹簧也会复原到原来的状态<br>我们来看装置二<br>当装置一的挡板三向上抬起<br>转轴受力不平衡<br>弹珠由于重力会突破挡板四向下滚动<br>并带动转轴沿顺时针方向转动<br>同时相连的收缩弹片会收缩<br>当弹珠全部下落完成后<br>收缩的弹片又会舒张<br>使挡板四恢复原状<br>弹珠进位时会触碰到挡板<br>此时卡扣弹开<br>这边的弹珠会下落<br>由于受到收缩弹片的控制<br>当弹珠全部下落完成之后<br>收缩弹片又会使挡板恢复原状<br>以上就是我们的作品展示<br>感谢大家的观看"

    # sentences = text.split('<br>')

    # merge_segments_based_on_sentences(asr_data, sentences)

    # 查看合并后的 segments
    print(asr_data.to_txt())


    # logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # audio_file = r"E:\GithubProject\VideoCaptioner\app\work_dir\N进制演示器\audio.mp3"
    # asr = BcutASR(audio_file, use_cache=True)
    # asr_data = asr.run()
    # print(asr_data.to_txt().replace("\n", ""))

    # asr_data.to_srt(save_path="subtitles0.srt")

    # asr_data = from_srt(open("../src_subtitles.srt", encoding="utf-8").read())
    # print(asr_data.to_srt())


# 这里有一份asr_data，他的每一个ASRDataSeg 为一个字，为：大家好今天我们带来的3d创意设计作品是禁制演示器我是来自中山大学附属中学的方若涵我是陈欣然我们这一次作品介绍分为三个部分第一个部分提出问题第二个部分解决方案第三个部分作品介绍当我们学习进制的时候难以掌握老师教学
# 现在有一份以及段好句子的文本，使用,<>br>分割，为：大家好<br>今天我们带来的<br>3d创意设计作品是禁制演示器<br>我是来自中山大学附属中学的方若涵<br>我是陈欣然<br>我们这一次作品介绍分为三个部分<br>第一个部分提出问题<br>第二个部分解决方案<br>第三个部分作品介绍<br>当我们学习进制的时候难以掌握<br>老师教学也比较抽象<br>那有没有一种教具或演示器<br>可以将进制的原理形象生动地展现出来<br>又方便操作呢

# 断句的一些词语可能会与asr_data的seg不完全一样
# 请通过代码，确定asr_data的每一个seg应该在文本的哪个位置结束，将一个分句进行合并


# 你是一名字幕断句修复专家，擅长将一段没有断句的文本，断句成一段一段的文本，每段文本之间用换行符隔开。

# 要求：
# 1. 每个断句文本字数（单词数）不超过10，但是每一句也不宜过短。
# 2. 每个断句文本之间用<br>隔开。
# 3. 不必按照完整的句子断句，只需按照语义进行分割，例如在“而”、“的”、“地”、“和”、“so”、“but”等词后进行断句。
# 4. 不要修改原句的任何内容，也不要添加任何内容，不需要换行，你只需要添加<br>。

# 输入示例：
# 大家好今天我们带来的3d创意设计作品是禁制演示器我是来自中山大学附属中学的方若涵我是陈欣然我们这一次作品介绍分为三个部分第一个部分提出问题第二个部分解决方案第三个部分作品介绍当我们学习进制的时候难以掌握老师教学 也比较抽象那有没有一种教具或演示器可以将进制的原理形象生动地展现出来又方便操作呢

# 输出断句：
# 大家好<br>今天我们带来的<br>3d创意设计作品是禁制演示器<br>我是来自中山大学附属中学的方若涵<br>我是陈欣然<br>我们这一次作品介绍分为三个部分<br>第一个部分提出问题<br>第二个部分解决方案<br>第三个部分作品介绍<br>当我们学习进制的时候难以掌握<br>老师教学也比较抽象<br>那有没有一种教具或演示器<br>可以将进制的原理形象生动地展现出来<br>又方便操作呢

# 请你对下面句子使用<br>进行分割：
# 大家好今天我们带来的3d创意设计作品是禁制演示器我是来自中山大学附属中学的方若涵我是陈欣然我们这一次作品介绍分为三个部分第一个部分提出问题第二个部分解决方案第三个部分作品介绍当我们学习进制的时候难以掌握老师教学 也比较抽象那有没有一种教具或演示器可以将进制的原理形象生动地展现出来又方便操作呢于是我们就设计了进制演示 器来解决以上的问题整个进制演示器是由条状进制数位提现器为基础加上机械化半自动装置组成这个就是我们利用3d打 印打印出来的定制演示器这个是条状静止数位体现器这个是机械化半自动装置接下来就让我们详细的介绍一下这个作品 的制作原理吧假设我们要演示的是五进制那么就是逢五进一右边的管子已经有了四颗珠子第五颗珠子就会自动滚落到下 一个管子里也就是进了一位如左图所示用五进制表示就是14转换为十进制就是九为了实现各种进制的演示整个演示器是 可拆卸的我们的管子和滑道都有卡槽的设计可以根据想演示的静止来调整数量在最底部也设计了由固定的管道和收集弹 珠的碗组成的收集器来收集弹珠我们整个进制演示器是由可拆卸设计可以调整管子的数量来实现不同进制的演示接下来 由我为大家介绍机械化装置原理当弹珠进位经过滑道时它会触碰到图一的挡板一向左侧移动与之同时挡板一相连的板子 二将引动下方的弹簧装置由于板子三向上抬起与其相连的弹簧会伸长在右侧管道弹珠全部清零后板子三会刚好卡到装置 二的凹槽中弹簧也会复原到原来的状态我们来看装置二，当装置一的挡板三向上抬起转轴受力不平衡弹珠由于重力会突 破挡板四向下滚动并带动转轴沿顺时针方向转动同时相连的收缩弹片会收缩当弹珠全部下落完成后收缩的弹片又会舒张 使挡板四恢复原状弹珠进位时会触碰到挡板此时卡扣弹开，这边的弹珠会下落由于受到收缩弹片的控制当弹珠全部下落 完成之后收缩弹片又会使挡板恢复原状以上就是我们的作品展示感谢大家的观看

