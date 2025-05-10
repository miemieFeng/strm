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
    
    # 使用临时文件创建有效的JSON
    TMP_FILE=$(mktemp)
    cat > $TMP_FILE << EOF
{
  "webdav_url": "$(echo "$WEBDAV_URL" | sed 's/\\/\\\\/g; s/"/\\"/g')",
  "username": "$(echo "$WEBDAV_USERNAME" | sed 's/\\/\\\\/g; s/"/\\"/g')",
  "password": "$(echo "$WEBDAV_PASSWORD" | sed 's/\\/\\\\/g; s/"/\\"/g')",
  "local_dir": "$(echo "${LOCAL_DIR:-/data}" | sed 's/\\/\\\\/g; s/"/\\"/g')",
  "remote_dir": "$(echo "${REMOTE_DIR:-/}" | sed 's/\\/\\\\/g; s/"/\\"/g')",
  "check_interval": ${CHECK_INTERVAL:-600},
  "max_workers": ${THREADS:-10},
  "replace_ip": "$(echo "${REPLACE_IP:-}" | sed 's/\\/\\\\/g; s/"/\\"/g')",
  "post_command": "",
  "web_port": ${WEB_PORT:-8080}
}
EOF
    
    # 检查生成的JSON是否有效
    JSON_VALID=false
    if command -v jq >/dev/null 2>&1; then
        # 如果有jq命令，用它验证JSON
        if jq empty $TMP_FILE >/dev/null 2>&1; then
            JSON_VALID=true
        fi
    else
        # 没有jq命令，用Python验证JSON
        if python -c "import json; json.load(open('$TMP_FILE'))" >/dev/null 2>&1; then
            JSON_VALID=true
        fi
    fi
    
    if [ "$JSON_VALID" = "true" ]; then
        # 将更新后的配置写回文件
        cat $TMP_FILE > /config/webdav_config.json
        echo "配置更新成功"
    else
        echo "警告：生成的JSON配置无效，将使用默认配置"
        echo '{"webdav_url": "", "username": "", "password": "", "local_dir": "/data", "remote_dir": "/", "check_interval": 600, "max_workers": 10, "replace_ip": "", "post_command": "", "web_port": 8080}' > /config/webdav_config.json
    fi
    rm -f $TMP_FILE
fi

# 启动Web服务
: ${WEB_PORT:="8080"}
echo "启动Web服务在端口: ${WEB_PORT}"
cd /app && python webdav_monitor_web.py --config-dir /config --port ${WEB_PORT} 