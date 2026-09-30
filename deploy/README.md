# 部署说明

当前版本的部署方式是 **Docker**：一键部署包在 `deploy/package/`，应用代码在 `final-project/flask-app/`。

> Kubernetes / Helm 相关清单属于 v1 版本，已归档在 `v1-legacy/`（`v1-legacy/helm/`、`v1-legacy/k8s/`）。

## 目录结构

```
deploy/
└── package/                   # 部署包
    ├── setup.sh               # 一键部署脚本（Docker）
    └── deployment-guide.md    # 完整部署说明书
```

> 应用代码（Flask）位于 `final-project/flask-app/`，包含：
> `app.py`、`Dockerfile`、`docker-compose.yml`、`init.sql`、`migrate_blog.sql`、
> `requirements.txt`、`static/`、`templates/`。

## 🚀 本地部署步骤

### 前置条件

- Docker Desktop 4.0+
- Docker Compose 2.0+

### 1. 进入应用目录

```bash
cd final-project/flask-app
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 查看服务状态

```bash
docker-compose ps
```

### 4. 访问应用

| 服务 | 地址 |
|------|------|
| 首页 | http://localhost:5000 |
| 用户列表 | http://localhost:5000/api/users |
| 健康检查 | http://localhost:5000/api/health |

### 5. 停止服务

```bash
docker-compose down
```

## 📁 文件说明

### deploy/package/setup.sh
一键部署脚本。在 openEuler / CentOS 虚拟机上自动完成：安装 Docker、配置镜像加速、
修复 firewalld 与 Docker 兼容性、拉取 MySQL 镜像、构建 Flask 镜像、启动容器、设置开机自启。

### deploy/package/deployment-guide.md
完整部署说明书，含手动分步部署、日常运维、常见问题排查。

### final-project/flask-app/Dockerfile
Flask应用的Docker镜像构建配置

### final-project/flask-app/docker-compose.yml
本地多容器编排配置，包含：
- Flask Web应用
- MySQL数据库

### final-project/flask-app/app.py
Flask应用主文件，提供REST API接口

### final-project/flask-app/requirements.txt
Python依赖包列表

### final-project/flask-app/init.sql
MySQL数据库初始化脚本（16 张业务表）

## ⚠️ 注意事项

1. 首次启动时，MySQL需要一些时间初始化
2. 确保端口5000和3306未被占用
3. 数据会持久化到Docker卷中
