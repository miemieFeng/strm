#!/bin/bash

# WebDAV监控服务一键部署脚本

echo "========================================"
echo "  WebDAV监控服务部署脚本"
echo "========================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 创建部署目录
DEPLOY_DIR="$HOME/webdav-monitor"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

echo "正在下载配置文件..."
cat > docker-compose.yml << 'EOF'
version: '3'

services:
  webdav-monitor:
    image: fengmiemie/webdav-monitor:latest
    container_name: webdav-monitor
    restart: unless-stopped
    dns:
      - 8.8.8.8
      - 1.1.1.1
    environment:
      - WEBDAV_URL=${WEBDAV_URL:-http://hu.miemiejun.me:5005}
      - WEBDAV_USERNAME=${WEBDAV_USERNAME:-19965027242}
      - WEBDAV_PASSWORD=${WEBDAV_PASSWORD:-zhao131496}
      - WEBDAV_REMOTE_DIR=${WEBDAV_REMOTE_DIR:-/links/影视}
      - LOCAL_DIR=/data
      - THREADS=10
      - CHECK_INTERVAL=600
      - REPLACE_IP=hu.miemiejun.me
      - VERBOSE=true
      - HTTP_PROXY=
      - HTTPS_PROXY=
      - http_proxy=
      - https_proxy=
      - no_proxy=hu.miemiejun.me,localhost,127.0.0.1
      - NO_PROXY=hu.miemiejun.me,localhost,127.0.0.1
    volumes:
      - ${DATA_DIR:-/volume1/media/影视}:/data
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    entrypoint: >
      sh -c "apk add --no-cache curl iputils bind-tools &&
             echo '=== 系统信息 ===' &&
             cat /etc/resolv.conf &&
             echo '=== 环境变量 ===' &&
             env | grep -E 'proxy|PROXY' &&
             echo '=== 网络诊断 ===' &&
             ping -c 3 -4 hu.miemiejun.me || echo '无法通过IPv4 ping通服务器' &&
             ping -c 3 -6 hu.miemiejun.me || echo '无法通过IPv6 ping通服务器' &&
             nslookup hu.miemiejun.me || echo '无法解析域名' &&
             curl -v --connect-timeout 10 http://hu.miemiejun.me:5005 || echo '无法连接WebDAV服务' &&
             echo '=== 禁用潜在代理 ===' &&
             export http_proxy='' https_proxy='' HTTP_PROXY='' HTTPS_PROXY='' &&
             echo '=== 启动主程序 ===' &&
             exec /bin/sh /app/entrypoint.sh"
EOF

# 创建环境变量配置文件
echo "正在配置环境变量..."
cat > .env << 'EOF'
# WebDAV服务器配置
WEBDAV_URL=http://hu.miemiejun.me:5005
WEBDAV_USERNAME=19965027242
WEBDAV_PASSWORD=zhao131496
WEBDAV_REMOTE_DIR=/links/影视

# 本地存储路径
DATA_DIR=/volume1/media/影视
EOF

echo "请根据需要修改.env文件中的配置"
echo "特别是DATA_DIR变量，指定本地存储目录"
echo ""

# 询问是否立即启动服务
read -p "是否立即启动服务？(y/n): " start_service

if [ "$start_service" = "y" ] || [ "$start_service" = "Y" ]; then
    echo "拉取最新镜像..."
    docker pull fengmiemie/webdav-monitor:latest
    
    echo "启动服务..."
    docker-compose up -d
    
    echo "服务已启动！"
    echo "可以通过以下命令查看日志："
    echo "docker logs -f webdav-monitor"
else
    echo "部署文件已准备就绪，但服务未启动"
    echo "可以稍后通过以下命令启动服务："
    echo "cd $DEPLOY_DIR && docker-compose up -d"
fi

echo ""
echo "部署完成！" 