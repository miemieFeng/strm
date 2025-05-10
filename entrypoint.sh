#!/bin/sh
set -e

# 处理日志级别设置
: ${LOG_LEVEL:="INFO"}
export LOG_LEVEL

# 强制使用Web界面模式，忽略配置
echo "强制启动WebDAV监控Web界面模式..."

# 确保配置目录存在
mkdir -p /config

# 如果配置文件不存在，则创建默认配置
if [ ! -f "/config/webdav_config.json" ]; then
    echo '{"webdav_url": "", "username": "", "password": "", "local_dir": "/data", "remote_dir": "/", "check_interval": 600, "max_workers": 10, "replace_ip": "", "post_command": "", "web_port": 8080}' > /config/webdav_config.json
    echo "已创建默认配置文件"
fi

# 如果环境变量中有WebDAV配置，则更新配置文件
if [ -n "$WEBDAV_URL" ] && [ -n "$WEBDAV_USERNAME" ] && [ -n "$WEBDAV_PASSWORD" ]; then
    echo "检测到环境变量配置，正在更新配置文件..."
    
    # 读取当前配置
    CONFIG_CONTENT=$(cat /config/webdav_config.json)
    
    # 使用临时文件更新配置
    TMP_FILE=$(mktemp)
    echo "$CONFIG_CONTENT" | \
        sed "s|\"webdav_url\": \".*\"|\"webdav_url\": \"$WEBDAV_URL\"|g" | \
        sed "s|\"username\": \".*\"|\"username\": \"$WEBDAV_USERNAME\"|g" | \
        sed "s|\"password\": \".*\"|\"password\": \"$WEBDAV_PASSWORD\"|g" | \
        sed "s|\"remote_dir\": \".*\"|\"remote_dir\": \"$REMOTE_DIR\"|g" | \
        sed "s|\"local_dir\": \".*\"|\"local_dir\": \"$LOCAL_DIR\"|g" | \
        sed "s|\"check_interval\": [0-9]*|\"check_interval\": $CHECK_INTERVAL|g" | \
        sed "s|\"max_workers\": [0-9]*|\"max_workers\": $THREADS|g" | \
        sed "s|\"replace_ip\": \".*\"|\"replace_ip\": \"$REPLACE_IP\"|g" > $TMP_FILE
    
    # 将更新后的配置写回文件
    cat $TMP_FILE > /config/webdav_config.json
    rm $TMP_FILE
fi

# 启动Web服务
: ${WEB_PORT:="8080"}
echo "启动Web服务在端口: ${WEB_PORT}"
cd /app && python webdav_monitor_web.py --config-dir /config --port ${WEB_PORT} 