# 鲲鹏云计算综合实训项目

## 项目概述

本项目通过两周实践，先在**本地环境**完成部署测试，然后在**openEuler模拟服务器**上进行生产环境部署，最终交付一个可访问的网址。

**部署流程**：本地部署 → openEuler部署 → 对外访问网址

## 团队角色（4人）

| 角色 | 职责 |
|------|------|
| **项目经理** | 整体协调、进度把控、文档管理 |
| **基础设施工程师** | Docker安装、openEuler配置 |
| **应用开发工程师** | 应用开发、容器化、Helm Chart |
| **运维工程师** | K8s集群部署、数据库部署、Ingress配置 |

## 技术栈

### 基础设施层

| 技术 | 版本 | 用途 |
|------|------|------|
| openEuler | 22.03 LTS SP3 | 操作系统 |
| Docker | 24.0.6 | 容器引擎 |
| Docker Compose | 2.23.0 | 本地编排工具 |
| Kubernetes | 1.28.2 | 容器编排 |
| Helm | 3.12.3 | 包管理 |

### 数据存储层

| 技术 | 版本 | 用途 |
|------|------|------|
| MySQL | 8.0.35 | 关系型数据库 |

### 应用服务层

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11 | 编程语言 |
| Flask | 3.0.0 | Web框架 |
| Gunicorn | 21.2.0 | WSGI服务器 |
| Nginx | 1.25.3 | 反向代理 |

## 部署架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        部署流程                                  │
├─────────────────────────────────────────────────────────────────┤
│   ┌─────────────────┐         ┌─────────────────────────────┐   │
│   │   本地部署       │  ───>  │      openEuler双服务器部署    │   │
│   │  (开发测试)      │         │      (生产环境)             │   │
│   └────────┬────────┘         └───────────┬─────────────────┘   │
│            │                               │                     │
│            ▼                               ▼                     │
│   ┌─────────────────┐         ┌───────────┴─────────────────┐   │
│   │ Docker Compose  │         │  ┌───────────┐ ┌───────────┐ │   │
│   │ - Flask App     │         │  │ 服务器A   │ │ 服务器B   │ │   │
│   │ - MySQL         │         │  │ Web应用   │ │ 检测系统  │ │   │
│   └─────────────────┘         │  │ Nginx     │ │ 监控服务  │ │   │
│                               │  └─────┬─────┘ └─────┬─────┘ │   │
│                               │         │             │       │   │
│                               │         └─────┬───────┘       │   │
│                               │               ▼               │   │
│                               │       ┌───────────┐           │   │
│                               │       │  MySQL    │           │   │
│                               │       └───────────┘           │   │
│                               └───────────────────────────────┘   │
│                                        │                        │
│                                        ▼                        │
│                                 对外访问网址                     │
└─────────────────────────────────────────────────────────────────┘
```

### 服务器职责划分

| 服务器 | 角色 | 部署内容 | 端口 |
|--------|------|----------|------|
| **服务器A** | Web服务器 | Flask应用、Nginx反向代理 | 80、5000 |
| **服务器B** | 检测服务器 | 监控服务、健康检查API | 8080 |
| **数据库** | 共享存储 | MySQL数据库 | 3306 |

## 功能模块

| 功能模块 | 说明 | API路径 |
|----------|------|---------|
| 首页 | 欢迎页面 | `/` |
| 用户管理 | 查看/添加用户 | `/api/users` |
| 健康检查 | 系统状态 | `/api/health` |

## 项目结构

```
1/
├── README.md                    # 项目概述
├── 项目计划书.md               # 详细项目计划书
├── 项目结构说明.md             # 目录结构说明
├── 需求分析文档.md             # 需求分析文档
├── scripts/                     # 运维脚本
│   ├── init_server.sh          # 服务器初始化
│   ├── install_docker.sh       # Docker安装
│   ├── install_k8s.sh          # K8s安装
│   ├── setup_server_a.sh       # 服务器A配置（Web服务器）
│   └── setup_server_b.sh       # 服务器B配置（检测服务器）
├── k8s/                        # K8s配置文件
│   └── mysql-deployment.yaml   # MySQL部署
├── app/                        # 应用代码
│   ├── app.py                  # Flask应用
│   ├── Dockerfile              # Docker构建文件
│   ├── requirements.txt        # Python依赖
│   └── docker-compose.yml      # Docker Compose
└── helm/myapp/                 # Helm Chart
    ├── Chart.yaml
    ├── values.yaml
    └── templates/deployment.yaml
```

---

## 🚀 本地部署（第一阶段）

### 环境要求

| 软件 | 版本要求 |
|------|----------|
| Docker Desktop | 4.0+ (Windows/Mac) 或 Docker Engine 24.0+ (Linux) |
| Docker Compose | 2.23.0+ |
| 内存 | 8GB+ |
| 磁盘 | 20GB+ |

### 部署步骤

```bash
# 1. 进入应用目录
cd 1/app

# 2. 启动所有服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

### 访问本地应用

| 服务 | 地址 |
|------|------|
| 首页 | http://localhost:5000 |
| 用户列表 | http://localhost:5000/api/users |
| 健康检查 | http://localhost:5000/api/health |

### 停止服务

```bash
# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

---

## 🖥️ openEuler部署（第二阶段）

### 环境准备

| 项目 | 配置 |
|------|------|
| 虚拟机软件 | VirtualBox 7.0+ 或 VMware |
| 操作系统 | openEuler 22.03 LTS SP3 |
| CPU | 4核 |
| 内存 | 8GB |
| 磁盘 | 50GB |

### 部署步骤

#### 1. 系统初始化

```bash
# 更新系统
yum update -y

# 安装必要工具
yum install -y wget curl vim net-tools git

# 关闭防火墙
systemctl stop firewalld
systemctl disable firewalld

# 关闭SELinux
sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0
```

#### 2. 安装Docker

```bash
yum install -y docker docker-compose
systemctl enable docker
systemctl start docker
```

#### 3. 安装Kubernetes

```bash
# 添加K8s仓库
cat <<EOF | tee /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://pkgs.k8s.io/core:/stable:/v1.28/rpms/
enabled=1
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.28/rpms/repodata/repomd.xml.key
EOF

# 安装K8s组件
yum install -y kubelet kubeadm kubectl
systemctl enable --now kubelet

# 初始化集群
kubeadm init --pod-network-cidr=10.244.0.0/16

# 配置kubectl
mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config

# 安装网络插件
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml

# 允许master调度Pod
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```

#### 4. 部署应用

```bash
# 部署数据库
kubectl apply -f k8s/mysql-deployment.yaml

# 构建镜像
cd app
docker build -t myapp:latest .

# Helm部署
helm install myapp ../helm/myapp/

# 安装Ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml
```

---

## 最终交付

项目完成后，将交付：

1. **本地部署环境**：本地开发测试环境
2. **openEuler生产环境**：模拟云服务器生产环境
3. **对外访问网址**：通过该网址可访问所有功能
4. **项目文档**：包含需求文档、技术方案、部署手册等

## 参考资料

1. openEuler官方文档：https://docs.openeuler.org
2. Kubernetes官方文档：https://kubernetes.io/docs
3. Docker官方文档：https://docs.docker.com
4. Helm官方文档：https://helm.sh/docs