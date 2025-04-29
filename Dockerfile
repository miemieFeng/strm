FROM python:3.9-alpine

WORKDIR /app

# 安装依赖和网络工具
COPY requirements.txt .
RUN apk add --no-cache curl iputils bind-tools ca-certificates && \
    pip install --no-cache-dir -r requirements.txt

# 复制脚本和配置文件
COPY webdav_monitor_mt.py .
COPY entrypoint.sh .

# 确保entrypoint.sh使用LF行尾而不是CRLF
RUN sed -i 's/\r$//' entrypoint.sh

# 设置非敏感环境变量
ENV WEBDAV_REMOTE_DIR="/links/影视"
ENV LOCAL_DIR="/data"
ENV THREADS="10"
ENV CHECK_INTERVAL="600"
ENV REPLACE_IP="hu.miemiejun.me"
ENV VERBOSE="true"
ENV POST_COMMAND=""

# 禁用代理设置，避免网络问题
ENV HTTP_PROXY=""
ENV HTTPS_PROXY=""
ENV http_proxy=""
ENV https_proxy=""
ENV no_proxy="hu.miemiejun.me,localhost,127.0.0.1"
ENV NO_PROXY="hu.miemiejun.me,localhost,127.0.0.1"

# 创建数据目录并确保entrypoint脚本有执行权限
RUN mkdir -p /data && chmod +x entrypoint.sh

# 使用sh来执行脚本
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"] 