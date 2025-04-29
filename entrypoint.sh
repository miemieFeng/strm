#!/bin/sh
set -e

# 检查必要环境变量
if [ -z "$WEBDAV_URL" ] || [ -z "$WEBDAV_USERNAME" ] || [ -z "$WEBDAV_PASSWORD" ]; then
    echo "错误: 缺少必要环境变量。请设置 WEBDAV_URL, WEBDAV_USERNAME, WEBDAV_PASSWORD。"
    exit 1
fi

# 构建命令行参数
COMMAND="python3 /app/webdav_monitor_mt.py \
    --url \"$WEBDAV_URL\" \
    --username \"$WEBDAV_USERNAME\" \
    --password \"$WEBDAV_PASSWORD\" \
    --remote-dir \"$WEBDAV_REMOTE_DIR\" \
    --local-dir \"$LOCAL_DIR\" \
    --threads \"$THREADS\" \
    --interval \"$CHECK_INTERVAL\" \
    --replace-ip \"$REPLACE_IP\""

# 可选参数
if [ "$VERBOSE" = "true" ]; then
    COMMAND="$COMMAND --verbose"
fi

if [ ! -z "$POST_COMMAND" ]; then
    COMMAND="$COMMAND --post-command \"$POST_COMMAND\""
fi

# 打印启动信息
echo "正在启动WebDAV监控服务..."
echo "WebDAV服务器: $WEBDAV_URL"
echo "扫描目录: $WEBDAV_REMOTE_DIR"
echo "本地保存目录: $LOCAL_DIR"
echo "替换IP为: $REPLACE_IP"
echo "检查间隔: $CHECK_INTERVAL 秒"
echo "使用线程数: $THREADS"

# 执行命令
echo "执行命令: $COMMAND"
eval $COMMAND 