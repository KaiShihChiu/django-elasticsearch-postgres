# 使用官方的 Python 镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

RUN apt-get update && apt-get install -y make gcc

# 复制项目文件到工作目录
COPY . /app

# 安装依赖项
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 运行 Django 应用
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
