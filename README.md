# WebDAV监控工具

这是一个多线程WebDAV监控工具，用于从WebDAV服务器下载文件。支持自动扫描和增量同步。提供命令行和Web管理界面两种使用方式。

## 功能特点

- 多线程并行下载，提高效率
- 增量同步，只下载新文件
- 自动处理STRM文件内容，替换IP为域名
- 支持下载后执行自定义命令
- 自动重试和错误处理
- 支持中文路径处理
- **新增Web管理界面**，方便配置和监控

## Docker镜像使用方法

### 从Docker Hub拉取镜像

```bash
docker pull miemiefeng/webdav-monitor:latest
```

### 运行方式

#### 1. 命令行模式 (CLI Mode)

```bash
docker run -d \
  --name webdav-monitor \
  -v /path/to/local/downloads:/data \
  -e WEBDAV_URL="https://your-webdav-server.com" \
  -e WEBDAV_USERNAME="your_username" \
  -e WEBDAV_PASSWORD="your_password" \
  -e REMOTE_DIR="/your/remote/directory" \
  -e CHECK_INTERVAL="600" \
  -e THREADS="10" \
  -e REPLACE_IP="your.domain.com" \
  miemiefeng/webdav-monitor
```

#### 2. Web管理界面模式 (Web UI Mode)

```bash
docker run -d \
  --name webdav-monitor-web \
  -p 8080:8080 \
  -v /path/to/local/downloads:/data \
  -v /path/to/config:/config \
  -e WEB_MODE=true \
  -e WEB_PORT=8080 \
  miemiefeng/webdav-monitor
```

访问 `http://your-server-ip:8080` 进入Web管理界面

### 绿联NAS专用部署方式

绿联NAS上推荐使用主机网络模式（host network mode）部署，以避免可能的端口映射问题。项目中提供了专用的配置文件 `ugreen-nas-docker-compose.yml`：

1. 在绿联NAS上启用SSH，并登录到NAS
2. 创建一个目录用于存放项目文件
```bash
mkdir -p /volume1/docker/webdav-monitor
cd /volume1/docker/webdav-monitor
```
3. 上传或创建`ugreen-nas-docker-compose.yml`文件，内容如下：

```yaml
version: '3'

services:
  # Web界面模式
  webdav-monitor-web:
    image: miemiefeng/webdav-monitor:latest
    container_name: webdav-monitor-web
    restart: unless-stopped
    # 使用host网络模式，避免端口映射问题
    network_mode: "host"
    environment:
      # Web界面模式启用 - 必须使用小写true
      - WEB_MODE=true
      - WEB_PORT=8080
      # 替换为你的WebDAV配置
      - WEBDAV_URL=your_webdav_url
      - WEBDAV_USERNAME=your_username
      - WEBDAV_PASSWORD=your_password
      - REMOTE_DIR=/your/remote/dir
      - LOCAL_DIR=/data
      - CHECK_INTERVAL=600
      - THREADS=10
      - REPLACE_IP=your_domain.com
      # 日志设置 - 减少详细日志量
      - LOG_LEVEL=WARNING
      - VERBOSE=false
    volumes:
      # 替换为绿联NAS上实际的媒体目录路径
      - /volume1/your_media_folder:/data
      # 配置文件存储位置
      - /volume1/docker/webdav-monitor/config:/config
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

4. 启动容器
```bash
docker-compose -f ugreen-nas-docker-compose.yml up -d
```

5. 访问Web界面
   - 打开浏览器，输入 `http://绿联NAS的IP:8080`
   - 如果无法访问，请检查绿联NAS的防火墙设置

6. 故障排查
   - 如果8080端口无法访问，可以修改`WEB_PORT`为其他端口
   - 使用`docker logs webdav-monitor-web`查看容器日志以排查问题
   - **注意**: 确保`WEB_MODE`设置为小写的`true`，不要使用大写的`TRUE`，因为脚本区分大小写

7. 日志级别设置
   - 默认日志级别为`INFO`，会显示详细的操作信息
   - 设置`LOG_LEVEL=WARNING`可以减少日志量，只显示警告、错误和关键信息(扫描耗时和新增文件数)
   - 可选值: `DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`(日志量依次减少)

### 环境变量

#### 命令行模式变量

- `WEBDAV_URL`: WebDAV服务器地址
- `WEBDAV_USERNAME`: WebDAV账号
- `WEBDAV_PASSWORD`: WebDAV密码
- `REMOTE_DIR`: 远程扫描目录，默认为`/links/影视`
- `LOCAL_DIR`: 本地保存目录，默认为`/data`
- `CHECK_INTERVAL`: 检查间隔(秒)，默认为600秒(10分钟)
- `THREADS`: 下载线程数，默认为10个
- `REPLACE_IP`: 替换STRM文件中的IP为指定域名
- `POST_COMMAND`: 下载完成后执行的命令，可使用`{local_path}`占位符
- `VERBOSE`: 是否显示详细日志，设置为`true`启用

#### Web界面模式变量

- `WEB_MODE`: 设置为`true`启用Web界面模式
- `WEB_PORT`: Web界面监听端口，默认为8080

## 直接使用Python脚本

### 命令行模式

```bash
python webdav_monitor_mt.py \
  --url https://your-webdav-server.com \
  --username your_username \
  --password your_password \
  --remote-dir /your/remote/directory \
  --local-dir ./downloads \
  --interval 600 \
  --threads 10 \
  --replace-ip your.domain.com
```

### Web界面模式

```bash
python webdav_monitor_web.py \
  --config-dir /path/to/config \
  --port 8080
```

## 参数说明

### 命令行模式参数

```
--url            WebDAV服务器地址 (必需)
--username       WebDAV账号 (必需)
--password       WebDAV密码 (必需)
--local-dir      本地保存目录，默认为./downloads
--remote-dir     远程扫描目录，默认为/links/影视
--interval       检查间隔(秒)，默认600秒(10分钟)
--threads        下载线程数，默认10个
--post-command   下载完成后执行的命令，可使用{local_path}占位符
--replace-ip     替换STRM文件中的IP为指定域名
--verbose        显示详细日志
```

### Web界面模式参数

```
--config-dir     配置文件目录，默认为当前目录
--port           Web服务端口，默认为8080
```

## 使用Docker Compose

使用Docker Compose可以更方便地管理容器。我们提供了两种模式的配置:

### 命令行模式

```yaml
version: '3'
services:
  webdav-monitor:
    image: miemiefeng/webdav-monitor:latest
    container_name: webdav-monitor
    restart: unless-stopped
    environment:
      - WEBDAV_URL=https://your-webdav-server.com
      - WEBDAV_USERNAME=your_username
      - WEBDAV_PASSWORD=your_password
      - REMOTE_DIR=/your/remote/dir
      - LOCAL_DIR=/data
      - CHECK_INTERVAL=600
      - THREADS=10
      - WEB_MODE=false
    volumes:
      - ./downloads:/data
```

### Web界面模式

```yaml
version: '3'
services:
  webdav-monitor-web:
    image: miemiefeng/webdav-monitor:latest
    container_name: webdav-monitor-web
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - WEB_MODE=true
      - WEB_PORT=8080
    volumes:
      - ./downloads:/data
      - ./config:/config
```

## Web界面功能

Web管理界面提供以下功能:

- 监控状态查看：运行状态、下载文件数、处理STRM数等
- 实时日志查看
- 配置管理：修改WebDAV连接信息和工作参数
- 操作控制：启动、停止、重启监控
- 最近下载文件列表

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

### 命令行模式

1. 克隆此仓库

```bash
git clone <repository-url>
cd <repository-dir>
```

2. 设置环境变量或创建 `.env` 文件，包含WebDAV凭据

3. 启动容器

```bash
docker-compose up -d webdav-monitor
```

### Web界面模式

1. 克隆此仓库

```bash
git clone <repository-url>
cd <repository-dir>
```

2. 创建配置和下载目录

```bash
mkdir -p downloads config
```

3. 启动容器

```bash
docker-compose up -d webdav-monitor-web
```

4. 访问Web界面 `http://your-server-ip:8080` 进行配置

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

如果不使用Docker，直接使用Python脚本：

```bash
pip install -r requirements.txt
```

## Web界面模式的配置文件

Web界面模式下，配置文件默认存储在配置目录中的 `webdav_config.json`，格式如下：

```json
{
  "webdav_url": "https://your-webdav-server.com",
  "username": "your_username",
  "password": "your_password",
  "local_dir": "/data",
  "remote_dir": "/your/remote/dir",
  "check_interval": 600,
  "max_workers": 10,
  "replace_ip": "your.domain.com",
  "post_command": "",
  "web_port": 8080
}
```

在Docker中，通过挂载配置目录保持配置持久化：

```
-v /path/to/config:/config
```

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

## GitHub Actions 设置

本项目使用GitHub Actions自动构建并推送Docker镜像到Docker Hub。这个镜像包含了命令行模式和Web界面模式的所有功能。如需使用此功能，请按照以下步骤设置：

### 1. 设置GitHub密钥

在GitHub仓库中添加以下密钥（Secrets）:

1. 打开您的GitHub仓库
2. 点击 "Settings" -> "Secrets and variables" -> "Actions"
3. 点击 "New repository secret" 添加以下密钥：

   - `DOCKERHUB_USERNAME`: 您的Docker Hub用户名
   - `DOCKERHUB_TOKEN`: 您的Docker Hub访问令牌（不是密码）

### 2. 获取Docker Hub访问令牌

1. 登录您的Docker Hub账号
2. 点击右上角您的用户名 -> "Account Settings" -> "Security"
3. 在 "Access Tokens" 部分点击 "New Access Token"
4. 给令牌起个名称（如"GitHub Actions"）并选择权限（至少需要"Read & Write"权限）
5. 点击创建并复制生成的令牌

### 3. 自动构建触发条件

镜像自动构建在以下情况下触发：
- 推送代码到`main`分支
- 创建以`v`开头的版本标签（例如：v1.0.0）
- 创建Pull Request到`main`分支（此情况下只会构建不会推送）

构建的镜像支持以下平台：
- linux/amd64（x86_64架构）
- linux/arm64（ARM 64位架构，如树莓派4）

### 4. 使用自动构建的镜像

自动构建的镜像会被推送到Docker Hub，并根据不同情况标记不同的标签：
- `latest`: 最新的`main`分支构建
- `vX.Y.Z`: 特定版本的构建（如v1.0.0）
- `vX.Y`: 主要版本的构建（如v1.0）
- 分支名称和短SHA值的标签

您可以通过以下命令拉取最新镜像：
```bash
docker pull miemiefeng/webdav-monitor:latest
```

或者拉取特定版本：
```bash
docker pull miemiefeng/webdav-monitor:v1.0.0
```

### 5. 常见问题解决

#### 构建失败："Username and password required"

这表明GitHub Actions无法访问Docker Hub。请检查：

1. 是否已正确设置 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN` 密钥
2. 令牌是否具有足够的权限（需要"Read & Write"权限）
3. 令牌是否已过期（如已过期，请生成新令牌并更新密钥）

#### 手动构建并推送镜像

如需手动构建并推送镜像，可以使用以下命令：

```bash
# 登录Docker Hub
docker login

# 构建镜像
docker build -t miemiefeng/webdav-monitor:latest -f Dockerfile.multistage .

# 推送镜像
docker push miemiefeng/webdav-monitor:latest
``` 