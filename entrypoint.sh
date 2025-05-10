#!/bin/sh
set -e

# 处理日志级别设置
: ${LOG_LEVEL:="INFO"}
export LOG_LEVEL

# 检查是否使用Web界面模式
if [ "$WEB_MODE" = "true" ]; then
    echo "启动WebDAV监控Web界面模式..."
    
    # 确保配置目录存在
    mkdir -p /config
    
    # 如果配置文件不存在，则创建默认配置
    if [ ! -f "/config/webdav_config.json" ]; then
        echo '{"webdav_url": "", "username": "", "password": "", "local_dir": "/data", "remote_dir": "/", "check_interval": 600, "max_workers": 10, "replace_ip": "", "post_command": "", "web_port": 8080}' > /config/webdav_config.json
        echo "已创建默认配置文件"
    fi
    
    # 启动Web服务
    echo "启动Web服务在端口: ${WEB_PORT}"
    cd /app && python webdav_monitor_web.py --config-dir /config --port ${WEB_PORT}
    exit 0
fi

# 以下是原来的命令行模式

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
echo "日志级别: $LOG_LEVEL"

# 启动程序
echo "执行命令: python webdav_monitor_mt.py $ARGS"
eval "python webdav_monitor_mt.py $ARGS" 