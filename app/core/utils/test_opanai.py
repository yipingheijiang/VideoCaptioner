import openai

def test_openai(base_url, api_key, model):
    """
    这是一个测试OpenAI API的函数。
    它使用指定的API设置与OpenAI的GPT模型进行对话。

    参数:
    user_message (str): 用户输入的消息

    返回:
    str: AI助手的回复
    """
    # 创建OpenAI客户端
    client = openai.OpenAI(base_url=base_url, api_key=api_key)

    try:
        # 发送请求到OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
        )
        # 返回AI的回复
        return True, str(response.choices[0].message.content)
    except Exception as e:
        return False, str(e)

