#!/bin/bash
set -e

echo "=== 开始构建WebDAV监控工具Docker镜像 ==="

# 设置变量
IMAGE_NAME=${DOCKERHUB_USERNAME:-miemiefeng}/webdav-monitor
TAG=${TAG:-latest}

echo "构建镜像: $IMAGE_NAME:$TAG"

# 构建镜像
echo "使用多阶段构建方法..."
docker build -f Dockerfile.multistage -t $IMAGE_NAME:$TAG .

echo "构建成功！"
echo "您可以使用以下命令测试镜像:"
echo "docker run --rm $IMAGE_NAME:$TAG --help"

echo "如需推送到Docker Hub，请运行:"
echo "docker push $IMAGE_NAME:$TAG" 