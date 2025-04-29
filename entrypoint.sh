#!/bin/sh
set -e

# 设置默认值
: ${WEBDAV_URL:?"请设置WEBDAV_URL环境变量"}
: ${WEBDAV_USERNAME:?"请设置WEBDAV_USERNAME环境变量"}
: ${WEBDAV_PASSWORD:?"请设置WEBDAV_PASSWORD环境变量"}
: ${REMOTE_DIR:="/links/影视"}
: ${LOCAL_DIR:="/data"}
: ${CHECK_INTERVAL:="600"}
: ${THREADS:="10"}
: ${REPLACE_IP:=""}
: ${POST_COMMAND:=""}
: ${VERBOSE:="false"}

# 构建命令行参数
ARGS="--url \"$WEBDAV_URL\" --username \"$WEBDAV_USERNAME\" --password \"$WEBDAV_PASSWORD\""
ARGS="$ARGS --remote-dir \"$REMOTE_DIR\" --local-dir \"$LOCAL_DIR\""
ARGS="$ARGS --interval \"$CHECK_INTERVAL\" --threads \"$THREADS\""

# 添加可选参数
if [ -n "$REPLACE_IP" ]; then
  ARGS="$ARGS --replace-ip \"$REPLACE_IP\""
fi

if [ -n "$POST_COMMAND" ]; then
  ARGS="$ARGS --post-command \"$POST_COMMAND\""
fi

if [ "$VERBOSE" = "true" ]; then
  ARGS="$ARGS --verbose"
fi

# 打印启动信息
echo "启动WebDAV监控工具..."
echo "WebDAV服务器: $WEBDAV_URL"
echo "远程目录: $REMOTE_DIR"
echo "本地目录: $LOCAL_DIR"
echo "检查间隔: $CHECK_INTERVAL 秒"
echo "下载线程数: $THREADS"

# 启动程序
echo "执行命令: python webdav_monitor_mt.py $ARGS"
eval "python webdav_monitor_mt.py $ARGS" 