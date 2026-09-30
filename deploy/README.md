# 本地部署指南

## 目录结构

```
deploy/
├── helm/                      # Helm Chart 配置
│   ├── Chart.yaml             # Chart 元数据
│   ├── values.yaml            # 配置值
│   └── templates/
│       └── deployment.yaml    # 部署模板
├── kubernetes/                # Kubernetes 配置
│   └── mysql-deployment.yaml  # MySQL 部署配置
├── mysql/                     # 数据库配置
│   └── init.sql               # 初始化脚本
└── package/                   # 部署脚本与说明书
    ├── setup.sh               # 一键部署脚本
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
MySQL数据库初始化脚本

### deploy/helm/
Helm Chart配置，用于Kubernetes部署

### deploy/kubernetes/mysql-deployment.yaml
MySQL的Kubernetes StatefulSet部署配置

### deploy/mysql/init.sql
数据库初始化脚本（与 flask-app 共享）

### deploy/package/
一键部署脚本（`setup.sh`）与完整部署说明书（`deployment-guide.md`），
用于在 openEuler / CentOS 虚拟机上通过 Docker 快速部署。

## ⚠️ 注意事项

1. 首次启动时，MySQL需要一些时间初始化
2. 确保端口5000和3306未被占用
3. 数据会持久化到Docker卷中
