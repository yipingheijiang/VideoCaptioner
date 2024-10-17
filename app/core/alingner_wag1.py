import rapidfuzz
from rapidfuzz import fuzz

def align_texts_sequence_alignment(text1, text2, gap_penalty=100):
    """
    使用序列比对算法（如 Needleman-Wunsch）对两个文本列表进行对齐，
    不改变原始列表的内容，只是在对齐过程中可能插入空字符串。

    Args:
        text1 (list): 源文本列表，保持不变。
        text2 (list): 目标文本列表，保持不变。
        gap_penalty (int): 插入或删除操作的固定惩罚分数。

    Returns:
        tuple: (aligned_source, aligned_target)
            - aligned_source (list): 对齐后的源文本列表。
            - aligned_target (list): 对齐后的目标文本列表。
    """
    n = len(text1)
    m = len(text2)

    # 初始化得分矩阵和方向矩阵
    score = [[0] * (m + 1) for _ in range(n + 1)]
    direction = [[None] * (m + 1) for _ in range(n + 1)]

    # 初始化第一列和第一行
    for i in range(1, n + 1):
        score[i][0] = score[i - 1][0] - gap_penalty
        direction[i][0] = 'up'  # 从上方来，表示插入空的目标句子
    for j in range(1, m + 1):
        score[0][j] = score[0][j - 1] - gap_penalty
        direction[0][j] = 'left'  # 从左方来，表示插入空的源句子

    # 填充得分矩阵和方向矩阵
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # 计算匹配得分
            sim = fuzz.ratio(text1[i - 1], text2[j - 1])
            match_score = score[i - 1][j - 1] + sim  # 相似度越高，得分越高

            # 计算插入和删除得分
            delete_score = score[i - 1][j] - gap_penalty  # 删除 text1 中的句子
            insert_score = score[i][j - 1] - gap_penalty  # 插入 text2 中的句子

            # 选择得分最高的操作
            max_score = max(match_score, delete_score, insert_score)
            score[i][j] = max_score

            # 记录方向
            if max_score == match_score:
                direction[i][j] = 'diag'  # 来自左上方，表示匹配或替换
            elif max_score == delete_score:
                direction[i][j] = 'up'  # 来自上方，表示删除（text2 中插入空行）
            else:
                direction[i][j] = 'left'  # 来自左方，表示插入（text1 中插入空行）

    # 回溯得到对齐结果
    aligned_source = []
    aligned_target = []
    i, j = n, m
    while i > 0 or j > 0:
        dir = direction[i][j]
        if dir == 'diag':
            aligned_source.insert(0, text1[i - 1])
            aligned_target.insert(0, text2[j - 1])
            i -= 1
            j -= 1
        elif dir == 'up':
            aligned_source.insert(0, text1[i - 1])
            aligned_target.insert(0, '')  # 插入空的目标句子
            i -= 1
        elif dir == 'left':
            aligned_source.insert(0, '')  # 插入空的源句子
            aligned_target.insert(0, text2[j - 1])
            j -= 1
        else:
            break  # 回溯结束

    return aligned_source, aligned_target

if __name__ == '__main__':
    text1 = ['yep human hair be about that thick', "yep and that's a really really tiny LED",
             'uvleds could be used to sterilize surfaces', 'like in hospitals or kitchens', 'just flick on the UV',
             'lights and pathogens would be dead in seconds', 'copy 19 or you know',
             "UV LED companies stop pressing like it's kind of better because",
             "everything's very good in these UV LEDs", 'you can start at all the covid 19',
             'for anything there we use aluminium gardenizer them', 'for UB we use aluminium gardenizer',
             'okay the Bam Jap is much bigger', "do you think this is what's coming", "it's okay to work",
             'but the problem the cost costs are too high changes', 'this is not thin passing', 'the cost is very high',
             'okay if the infinishing program', 'on a shifty pass closely is almost comparable']
    text2 = ['Yep, human hair is about that thick',
             "Yep, and that's a really tiny LEDUV LEDs could be used to sterilize surface",
             'Like in hospitals or kitchens', 'Just flick on the UV lights and pathogens would be dead in seconds',
             'COVID-19 or you know', "UV LED companies are improving, it's kind of better because",
             "everything's very good in these UV LEDs", 'You can start with all the COVID-19 precautions',
             'For everything, we use aluminum ganizers', 'For UV, we use aluminum ganizers',
             'Okay, the bigger one is much better', "Do you think this is what's coming?", "It's okay to work",
             'But the problem is the costs are too high', 'This is not a thin pass', 'The costs are very high',
             'Okay, if the finishing program', 'on a shifty pass closely is almost comparable']

    aligned_source, aligned_target = align_texts_sequence_alignment(text1, text2)

    for idx, (s, t) in enumerate(zip(aligned_source, aligned_target)):
        print(f"行 {idx + 1}:")
        print(f"文本1: {s}")
        print(f"文本2: {t}")
        sim = fuzz.ratio(s, t) if s and t else 0
        print(f"相似度: {sim:.2f}")
        print('----')
