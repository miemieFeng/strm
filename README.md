# WebDAV 监控器

这是一个用于监控 WebDAV 服务器上的 STRM 文件并下载它们的工具。支持多线程下载，并可以自动替换 STRM 文件中的 IP 地址为域名。

## 功能特点

- 自动扫描并监控 WebDAV 服务器上的 STRM 文件
- 多线程并行下载，提高效率
- 自动处理 STRM 文件内容，替换 IP 地址为域名
- Docker 容器化部署，方便维护
- 可配置扫描间隔、线程数等参数
- 安全处理敏感信息，支持环境变量传递

## 安全说明

为了保护敏感信息（如WebDAV密码），建议通过以下方式之一传递：

1. 创建 `.env` 文件（不要提交到版本控制系统）：

```bash
# 创建环境变量文件
cat > .env << EOL
WEBDAV_URL=http://your-webdav-server.com
WEBDAV_USERNAME=your_username
WEBDAV_PASSWORD=your_password
EOL
```

2. 通过环境变量传递：

```bash
export WEBDAV_URL=http://your-webdav-server.com
export WEBDAV_USERNAME=your_username
export WEBDAV_PASSWORD=your_password
docker-compose up -d
```

## 快速开始

### 使用 Docker Compose

1. 克隆此仓库

```bash
git clone <repository-url>
cd <repository-dir>
```

2. 设置环境变量或创建 `.env` 文件，包含WebDAV凭据

3. 启动容器

```bash
docker-compose up -d
```

4. 查看日志

```bash
docker-compose logs -f
```

### 手动构建并运行 Docker 镜像

1. 构建 Docker 镜像

```bash
docker build -t webdav-monitor .
```

2. 运行容器

```bash
docker run -d \
  --name webdav-monitor \
  -e WEBDAV_URL=http://your-webdav-server.com \
  -e WEBDAV_USERNAME=your_username \
  -e WEBDAV_PASSWORD=your_password \
  -e WEBDAV_REMOTE_DIR=/your/remote/dir \
  -e REPLACE_IP=your.domain.name \
  -v $(pwd)/downloads:/data \
  webdav-monitor
```

## 环境变量说明

| 环境变量 | 描述 | 默认值 |
|----------|------|--------|
| WEBDAV_URL | WebDAV 服务器地址 | - |
| WEBDAV_USERNAME | WebDAV 用户名 | - |
| WEBDAV_PASSWORD | WebDAV 密码 | - |
| WEBDAV_REMOTE_DIR | 远程扫描目录 | /links/影视 |
| LOCAL_DIR | 本地下载目录 | /data |
| THREADS | 下载线程数 | 10 |
| CHECK_INTERVAL | 检查间隔(秒) | 600 |
| REPLACE_IP | 替换 STRM 文件中的 IP 为此域名 | your.domain.name |
| VERBOSE | 是否显示详细日志 | true |
| POST_COMMAND | 下载完成后执行的命令，可使用 {local_path} 占位符 | - |

## 卷挂载

- `./downloads:/data`: 下载的文件将存储在此目录中

## 日志

日志文件位于容器内的 `/app/webdav_monitor.log`，可通过以下方式查看：

```bash
docker exec -it webdav-monitor cat /app/webdav_monitor.log
```

或使用 Docker Compose:

```bash
docker-compose exec webdav-monitor cat /app/webdav_monitor.log
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行运行

```bash
python webdav_monitor.py --url "https://your-webdav-server.com" --username "your_username" --password "your_password" --remote-dir "/links" --local-dir "./downloads" --interval 300
```

### 仅列出文件模式

```bash
python webdav_monitor.py --url "https://your-webdav-server.com" --username "your_username" --password "your_password" --remote-dir "/links" --list-only
```

### 参数说明

- `--url`: WebDAV服务器地址（必需）
- `--username`: WebDAV账号（必需）
- `--password`: WebDAV密码（必需）
- `--remote-dir`: 远程扫描目录，默认为根目录(`/`)
- `--local-dir`: 本地保存目录，默认为`./downloads`
- `--interval`: 检查间隔(秒)，默认300秒(5分钟)
- `--list-only`: 仅列出文件，不下载

## Docker支持

### 使用docker-compose启动

1. 修改`docker-compose.yml`文件中的环境变量
2. 运行以下命令启动容器：

```bash
docker-compose up -d
```

### 或者使用docker命令启动：

```bash
docker build -t webdav-monitor .

docker run -d \
  --name webdav-monitor \
  -e WEBDAV_URL="http://your-webdav-server.com" \
  -e WEBDAV_USERNAME="your_username" \
  -e WEBDAV_PASSWORD="your_password" \
  -e REMOTE_DIR="/links" \
  -e LOCAL_DIR="/app/downloads" \
  -e CHECK_INTERVAL=300 \
  -v ./downloads:/app/downloads \
  -v ./config:/app/config \
  webdav-monitor
```

## 日志

日志会同时输出到控制台和`webdav_monitor.log`文件中。

## 已知问题

1. **中文路径处理**：某些WebDAV服务器在处理中文路径时可能会遇到问题。脚本尝试通过URL编码来解决这个问题，但可能不适用于所有服务器。

2. **目录遍历限制**：某些WebDAV服务器可能限制目录递归遍历的深度或频率，这可能导致无法找到深层嵌套的文件。

3. **文件访问权限**：确保您有足够的权限访问WebDAV服务器上的文件和目录。

## 故障排除

1. 如果遇到找不到文件或目录的问题，可以尝试使用`--list-only`参数来检查可访问的文件。

2. 检查WebDAV服务器的配置，确保允许列出目录和下载文件。

3. 检查日志文件`webdav_monitor.log`中的错误信息，以帮助诊断问题。

## 远程部署说明

### 前提条件

- 安装Docker和Docker Compose
- 确保网络可以访问Docker Hub和WebDAV服务器

### 部署步骤

1. 下载`docker-compose.remote.yml`文件到服务器：
   ```bash
   wget https://raw.githubusercontent.com/your-repo/webdav-monitor/main/docker-compose.remote.yml -O docker-compose.yml
   ```

2. 根据需要修改配置文件中的卷挂载路径：
   ```yaml
   volumes:
     - /volume1/media/影视:/data  # 将左侧修改为服务器上的实际路径
   ```

3. 启动服务：
   ```bash
   docker-compose up -d
   ```

4. 查看日志：
   ```bash
   docker logs -f webdav-monitor
   ```

### 环境变量说明

可以通过环境变量自定义配置：

- `WEBDAV_URL`: WebDAV服务器地址 (默认: http://hu.miemiejun.me:5005)
- `WEBDAV_USERNAME`: WebDAV用户名 (默认: 19965027242)
- `WEBDAV_PASSWORD`: WebDAV密码 (默认: zhao131496)
- `WEBDAV_REMOTE_DIR`: 远程监控目录 (默认: /links/影视)
- `LOCAL_DIR`: 本地存储目录 (固定为容器内的/data)
- `THREADS`: 并发线程数 (默认: 10)
- `CHECK_INTERVAL`: 检查间隔(秒) (默认: 600)
- `VERBOSE`: 是否输出详细日志 (默认: true)

### 自定义环境变量

如果需要自定义环境变量，可以创建`.env`文件:

```
WEBDAV_URL=http://your-server:port
WEBDAV_USERNAME=your-username
WEBDAV_PASSWORD=your-password
WEBDAV_REMOTE_DIR=/your/remote/path
```

## 自动启动

服务配置了`restart: unless-stopped`，会在Docker启动时自动重启。 