FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY webdav_monitor_mt.py .
COPY entrypoint.sh .

# 确保entrypoint.sh有执行权限
RUN chmod +x entrypoint.sh

# 创建下载目录
RUN mkdir -p /data

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 设置入口点
ENTRYPOINT ["/app/entrypoint.sh"] 