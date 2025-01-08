FROM python:3.10-slim

WORKDIR /streamlit

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt


# 设置环境变量
ENV OPENAI_BASE_URL=https://dg.bkfeng.top/v1
ENV OPENAI_API_KEY=sk-0000
# 创建临时目录
RUN mkdir -p temp

# 暴露端口
EXPOSE 8501

# 健康检查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 启动应用
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
