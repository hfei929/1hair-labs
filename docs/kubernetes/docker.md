# Docker与Docker Compose详细使用教程


## 一、Docker基础概念

### 1.1 什么是Docker

Docker是一种轻量级容器化技术，通过将应用及其依赖环境打包成标准化单元，实现“一次构建，到处运行”的目标。在传统开发模式中，环境配置不一致导致的“在我机器上能运行”问题，每年造成全球企业超300亿美元的损失。Docker通过容器化技术彻底终结了这场战争。

Docker通过共享主机内核实现资源高效利用，启动速度比虚拟机快5-10倍，镜像通常只有几十MB，可秒级部署。

### 1.2 核心三剑客：镜像、容器、仓库

Docker的核心概念可以用一个非常形象的比喻来理解：

**镜像（Image）—— 如同“食谱”或“类（Class）”**

镜像是一个只读的模板，包含软件运行所需的所有内容：操作系统、运行时环境、库文件、应用程序代码和配置参数。镜像采用分层存储结构，多个镜像可以共享基础层，显著减少存储占用。

**容器（Container）—— 如同“那道菜”或“对象（Object）”**

容器是镜像的运行实例，是独立运行的、隔离的进程。你可以在同一个镜像上启动多个容器，每个容器之间互不影响。容器是可读可写的，但应该保持轻量级，随时可以删除重建。

**仓库（Repository）—— 如同“超市货架”或“Maven仓库”**

仓库是集中存放镜像文件的地方。Docker Hub是最知名的公共仓库，还有阿里云ACR等国内服务。仓库让镜像的分享和分发变得像从Maven仓库拉取Jar包一样简单。

### 1.3 Docker架构

Docker采用客户端-服务器（C/S）架构。主要包含以下组件：
- **Docker客户端（Client）**：用户通过Docker命令行工具与Docker守护进程交互
- **Docker守护进程（Daemon）**：后台服务进程，负责容器的创建、运行和管理
- **镜像仓库（Registry）**：存储和分发Docker镜像
- **容器运行时（Container Runtime）**：实际运行容器的底层引擎


## 二、安装指南

### 2.1 系统要求

- **Linux**：支持systemd或Upstart的64位系统，推荐Ubuntu 20.04+或CentOS 7+，内核版本≥5.4
- **macOS**：macOS 12（Monterey）或更高版本，支持Hypervisor框架
- **Windows**：需Docker Desktop 4.20+，支持WSL2后端
- **硬件配置**：建议4核CPU、8GB内存、50GB磁盘空间

### 2.2 Ubuntu安装Docker

```bash
# 卸载旧版本
sudo apt-get remove docker docker-engine docker.io containerd runc

# 安装依赖
sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates curl gnupg lsb-release

# 添加官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 设置稳定版仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker引擎
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker version
docker run hello-world
```

### 2.3 CentOS安装Docker

```bash
# 卸载旧版本
sudo yum remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine

# 安装依赖
sudo yum install -y yum-utils

# 配置阿里云镜像源
sudo yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo

# 安装Docker引擎
sudo yum install docker-ce docker-ce-cli containerd.io

# 启动并开机自启
sudo systemctl start docker
sudo systemctl enable docker
```

### 2.4 配置镜像加速器

为加快镜像拉取速度，建议配置国内镜像加速器（阿里云、腾讯云等）。配置`/etc/docker/daemon.json`文件：

```json
{
  "registry-mirrors": ["https://your-mirror-address.mirror.aliyuncs.com"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "200m",
    "max-file": "3"
  }
}
```

配置完成后重启Docker：

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```


## 三、Docker基本命令使用

### 3.1 镜像管理命令

```bash
# 查看本地所有镜像
docker images

# 从仓库拉取镜像
docker pull ubuntu:22.04
docker pull nginx:alpine

# 搜索镜像
docker search nginx

# 删除镜像
docker rmi <image_id或镜像名>

# 给镜像打标签
docker tag <image_id> myusername/myapp:1.0

# 将镜像推送到仓库
docker push myusername/myapp:1.0

# 查看镜像详细信息
docker image inspect <image_name>

# 清理未使用的镜像
docker image prune
```

### 3.2 容器管理命令

```bash
# 查看正在运行的容器
docker ps

# 查看所有容器（包括已停止的）
docker ps -a

# 运行容器
docker run -d --name mynginx -p 8080:80 nginx

# 常用参数说明
# -d：后台运行
# --name：指定容器名称
# -p 宿主机端口:容器端口：端口映射
# -v 宿主机目录:容器目录：挂载数据卷
# -e KEY=value：设置环境变量
# --restart=always：自动重启
# -it：交互式运行

# 停止/启动/重启容器
docker stop <容器名或ID>
docker start <容器名或ID>
docker restart <容器名或ID>

# 删除容器（需先停止）
docker rm <容器名或ID>

# 强制删除运行中的容器
docker rm -f <容器名或ID>

# 批量停止所有容器
docker stop $(docker ps -q)

# 批量删除所有容器
docker rm $(docker ps -aq)
```

### 3.3 进入容器和执行命令

```bash
# 进入容器终端
docker exec -it <容器名或ID> /bin/bash

# 在容器中执行命令
docker exec <容器名或ID> ls -la

# 查看容器日志
docker logs <容器名或ID>
docker logs -f <容器名或ID>   # 实时跟踪日志

# 查看容器资源使用情况
docker stats

# 在容器和宿主机之间复制文件
docker cp ./local/file.txt <容器名>:/container/path/
docker cp <容器名>:/container/path/file.txt ./local/

# 查看容器详细信息
docker inspect <容器名或ID>
```


## 四、Dockerfile详解与镜像定制

### 4.1 Dockerfile核心指令

Dockerfile是构建自定义镜像的蓝图，定义了镜像的生成过程。

```dockerfile
# FROM - 指定基础镜像（首选轻量级alpine镜像）
FROM node:18-alpine

# LABEL - 添加元数据
LABEL maintainer="team@example.com"
LABEL version="1.0"

# WORKDIR - 设置工作目录
WORKDIR /app

# COPY - 复制文件（推荐使用COPY而非ADD，更透明可控）
COPY package.json package-lock.json ./

# RUN - 执行命令（注意合并命令以减少层数）
RUN npm ci --only=production && \
    npm cache clean --force

# 复制源代码
COPY . .

# ARG - 构建参数
ARG APP_PORT=3000

# ENV - 环境变量
ENV NODE_ENV=production

# EXPOSE - 声明端口（仅为文档说明，不会自动暴露）
EXPOSE $APP_PORT

# HEALTHCHECK - 健康检查
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:$APP_PORT || exit 1

# USER - 切换非root用户（提升安全性）
USER node

# CMD - 启动命令（可被docker run覆盖）
CMD ["node", "app.js"]

# ENTRYPOINT - 入口点（不可被覆盖）
# ENTRYPOINT ["node", "app.js"]
```

### 4.2 .dockerignore文件

与.gitignore类似，在构建目录创建`.dockerignore`文件，排除不需要打包进镜像的文件：

```
node_modules
.git
*.log
.DS_Store
.gitignore
README.md
.env.local
Dockerfile
.dockerignore
```

### 4.3 构建镜像

```bash
# 基本构建
docker build -t myapp:1.0 .

# 指定Dockerfile文件
docker build -f Dockerfile.prod -t myapp:prod .

# 构建时不使用缓存
docker build --no-cache -t myapp:latest .

# 查看镜像构建历史
docker history myapp:latest
```


## 五、Docker Compose详解

### 5.1 Docker Compose是什么

Docker Compose是Docker官方推出的多容器应用编排与管理工具。它解决了手动管理多容器的痛点：
- 一个典型Web服务往往需要后端、数据库、缓存等多个组件协同工作
- 手动逐个启动容器、配置网络、挂载数据卷，不仅操作繁琐，还容易出错
- Compose通过YAML配置文件定义所有服务，用单条命令实现多容器的统一管理

可以把Compose理解为“乐高模型图纸”——只需提前画好图纸（docker-compose.yml），一键就能让所有积木自动拼成完整模型。

### 5.2 Compose V2说明

从Docker 20.10版本开始，Docker Compose V2被集成到Docker引擎中，可以直接使用`docker compose`命令（不带连字符）。

### 5.3 compose.yaml基础语法

```yaml
# Compose文件版本（推荐使用3.8或更高版本）
version: '3.8'

# 网络定义
networks:
  app-network:
    driver: bridge

# 数据卷定义（数据持久化）
volumes:
  mysql-data:
  redis-data:

# 服务定义（核心部分）
services:
  # 服务1：数据库
  mysql:
    image: mysql:8.0
    container_name: mysql
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: mysecretpassword
      MYSQL_DATABASE: myapp
      MYSQL_USER: myuser
      MYSQL_PASSWORD: mypassword
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
      - ./mysql/init:/docker-entrypoint-initdb.d  # 初始化SQL脚本
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 服务2：缓存
  redis:
    image: redis:7-alpine
    container_name: redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 服务3：应用（从Dockerfile构建）
  app:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - APP_ENV=production
    container_name: myapp
    restart: always
    ports:
      - "8080:8080"
    environment:
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: myuser
      DB_PASSWORD: mypassword
      DB_NAME: myapp
      REDIS_HOST: redis
      REDIS_PORT: 6379
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
```

### 5.4 Compose常用命令

```bash
# 启动所有服务（-d后台运行）
docker compose up -d

# 指定配置文件
docker compose -f ./custom-compose.yml up -d

# 指定项目名称（影响容器名前缀）
docker compose -p myproject up -d

# 查看服务状态
docker compose ps

# 查看服务日志
docker compose logs
docker compose logs -f app   # 实时跟踪指定服务的日志

# 停止服务（不删除容器）
docker compose stop

# 启动已停止的服务
docker compose start

# 重启服务
docker compose restart

# 停止并删除所有容器、网络（保留数据卷）
docker compose down

# 停止并删除所有容器、网络、数据卷
docker compose down -v

# 重新构建镜像后启动
docker compose up -d --build

# 查看镜像列表
docker compose images

# 进入特定服务的容器
docker compose exec app /bin/bash

# 查看服务资源使用情况
docker compose stats

# 拉取所有服务的最新镜像
docker compose pull
```

### 5.5 高级配置示例

**多环境配置（使用profiles）** ：

```yaml
version: '3.8'
services:
  web:
    image: nginx:alpine
    ports:
      - "80:80"
    profiles: ["dev", "prod"]
  
  db-test:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: test123
    profiles: ["dev"]
  
  db-prod:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}  # 从环境变量读取
    volumes:
      - prod-db-data:/var/lib/postgresql/data
    profiles: ["prod"]

volumes:
  prod-db-data:
```

使用方式：
```bash
# 启动开发环境（包含db-test但不包含db-prod）
docker compose --profile dev up -d

# 启动生产环境
docker compose --profile prod up -d
```

**资源限制配置** ：

```yaml
services:
  app:
    image: myapp:latest
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### 5.6 使用.env文件管理环境变量

创建`.env`文件：

```
DB_PASSWORD=mysecretpassword
APP_PORT=8080
REDIS_PASSWORD=redispass
```

在compose.yaml中引用：

```yaml
services:
  app:
    environment:
      DB_PASSWORD: ${DB_PASSWORD}
      APP_PORT: ${APP_PORT}
    ports:
      - "${APP_PORT}:8080"
```


## 六、典型场景实战

### 场景一：Web应用 + MySQL + Redis

**项目结构**：
```
myproject/
├── docker-compose.yml
├── .env
├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── mysql/
│   └── init/
│       └── init.sql
└── nginx/
    └── nginx.conf
```

**docker-compose.yml完整示例**：

```yaml
version: '3.8'

networks:
  app-network:
    driver: bridge

volumes:
  mysql-data:
  redis-data:
  app-logs:

services:
  mysql:
    image: mysql:8.0
    container_name: mysql
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
      - ./mysql/init:/docker-entrypoint-initdb.d
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: ./app
      dockerfile: Dockerfile
    container_name: app
    restart: always
    ports:
      - "5000:5000"
    environment:
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: ${MYSQL_USER}
      DB_PASSWORD: ${MYSQL_PASSWORD}
      DB_NAME: ${MYSQL_DATABASE}
      REDIS_HOST: redis
      REDIS_PORT: 6379
    volumes:
      - app-logs:/app/logs
      - ./app:/app
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: always
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./app/static:/static:ro
    depends_on:
      - app
    networks:
      - app-network
```

**app/Dockerfile（Python Flask应用）** ：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 先复制依赖文件，利用缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 创建非root用户运行
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]
```

启动服务：
```bash
docker compose up -d
```

### 场景二：WordPress个人博客站点

这是一个最常见的Compose实战案例——通过Compose一键部署完整的WordPress博客站点：

```yaml
version: '3.8'

services:
  db:
    image: mysql:5.7
    container_name: wordpress-db
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: somewordpress
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wordpress
      MYSQL_PASSWORD: wordpress
    volumes:
      - db_data:/var/lib/mysql
    networks:
      - wordpress-network

  wordpress:
    depends_on:
      - db
    image: wordpress:latest
    container_name: wordpress
    restart: always
    ports:
      - "8000:80"
    environment:
      WORDPRESS_DB_HOST: db:3306
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: wordpress
      WORDPRESS_DB_NAME: wordpress
    volumes:
      - wordpress_data:/var/www/html
    networks:
      - wordpress-network

volumes:
  db_data:
  wordpress_data:

networks:
  wordpress-network:
    driver: bridge
```

一键启动即可访问`http://localhost:8000`完成WordPress安装向导。

### 场景三：Spring Boot微服务应用

对于需要编译打包的Java/Go应用，多阶段构建是必不可少的技巧：

```dockerfile
# ================= 第一阶段：构建阶段 =================
FROM maven:3.8.6-openjdk-11 AS builder

WORKDIR /app
# 先拷贝pom.xml，下载依赖（利用缓存）
COPY pom.xml .
RUN mvn dependency:go-offline -B

# 拷贝源码并打包
COPY src ./src
RUN mvn package -DskipTests

# ================= 第二阶段：运行阶段 =================
FROM openjdk:11-jre-slim

WORKDIR /app
# 只从构建阶段拷贝jar包
COPY --from=builder /app/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

配合Compose：

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      SPRING_DATASOURCE_URL: jdbc:mysql://mysql:3306/mydb
      SPRING_DATASOURCE_USERNAME: root
      SPRING_DATASOURCE_PASSWORD: secret
    depends_on:
      - mysql

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: mydb
    volumes:
      - mysql-data:/var/lib/mysql

volumes:
  mysql-data:
```


## 七、最佳实践与优化建议

### 7.1 Dockerfile优化

1. **多阶段构建**：分离构建环境与运行环境，最终镜像体积可减少85%以上。以Go应用为例，镜像可从800MB压缩至10MB。
2. **利用构建缓存**：变动越少的东西越写在Dockerfile前面。先拷贝依赖文件，再拷贝源代码。
3. **选择轻量级基础镜像**：优先使用`alpine`、`slim`版本，比完整版镜像减少60%以上体积。
4. **合并RUN命令**：使用`&&`连接多个命令，减少镜像层数。同时记得清理apt缓存。
5. **使用`.dockerignore`**：排除不必要的文件，避免将本地开发文件打包进镜像。
6. **使用USER切换非root用户**：不要在容器中使用root运行应用，提升安全性。

### 7.2 Docker Compose优化

1. **使用健康检查**：`depends_on`只能保证容器启动顺序，使用`condition: service_healthy`确保服务真正就绪。
2. **合理配置重启策略**：`restart: always`确保服务异常后自动恢复。
3. **限制容器资源**：避免单个容器耗尽宿主机资源，设置CPU和内存限制。
4. **日志管理**：限制日志大小和数量，避免磁盘被写满。在daemon.json中配置`max-size`和`max-file`。
5. **敏感信息管理**：使用`.env`文件或Docker secrets管理密码等敏感配置，禁止硬编码在yml文件中。

### 7.3 生产环境注意事项

1. 定期更新基础镜像，建议每周扫描一次漏洞。
2. 启用镜像签名验证，确保镜像来源可信。
3. 配置监控和日志集中管理。
4. 使用Swarm或Kubernetes进行容器编排管理。


## 八、总结

Docker通过“Build once, run anywhere”的理念，解决了软件开发中长期存在的环境一致性问题。掌握Docker和Docker Compose的核心技能，可以帮助开发者：

- 快速搭建标准化的开发环境，彻底告别“在我电脑上能跑”的问题
- 简化应用的部署流程，从多条docker run命令简化到一条docker compose up
- 显著提升CI/CD流水线的构建效率，某电商平台案例显示构建时间从45分钟降至8分钟
- 确保开发、测试、生产环境配置的高度一致

Docker的官方文档和社区资源非常丰富，建议读者在实际项目中多加练习，从单容器应用起步，逐步过渡到多容器编排的完整应用栈。