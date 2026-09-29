# 本地部署指南

## 目录结构

```
部署/
├── docker/                    # Docker配置
│   └── Dockerfile            # 应用镜像构建文件
├── docker-compose/            # Docker Compose配置
│   └── docker-compose.yml     # 本地编排配置
├── flask-app/                # Flask应用代码
│   ├── app.py                # 应用主文件
│   ├── requirements.txt      # Python依赖
│   └── init.sql              # 数据库初始化脚本
├── helm/                     # Helm配置
│   ├── Chart.yaml            # Chart元数据
│   ├── values.yaml           # 配置值
│   └── templates/
│       └── deployment.yaml   # 部署模板
├── kubernetes/               # Kubernetes配置
│   └── mysql-deployment.yaml # MySQL部署配置
└── mysql/                    # 数据库配置
    └── init.sql              # 初始化脚本
```

## 🚀 本地部署步骤

### 前置条件

- Docker Desktop 4.0+
- Docker Compose 2.0+

### 1. 进入部署目录

```bash
cd 部署/docker-compose
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

### docker/Dockerfile
Flask应用的Docker镜像构建配置

### docker-compose/docker-compose.yml
本地多容器编排配置，包含：
- Flask Web应用
- MySQL数据库

### flask-app/app.py
Flask应用主文件，提供REST API接口

### flask-app/requirements.txt
Python依赖包列表

### flask-app/init.sql
MySQL数据库初始化脚本

### helm/
Helm Chart配置，用于Kubernetes部署

### kubernetes/mysql-deployment.yaml
MySQL的Kubernetes StatefulSet部署配置

### mysql/init.sql
数据库初始化脚本（与flask-app共享）

## ⚠️ 注意事项

1. 首次启动时，MySQL需要一些时间初始化
2. 确保端口5000和3306未被占用
3. 数据会持久化到Docker卷中