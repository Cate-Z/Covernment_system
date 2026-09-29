# 鲲鹏云计算综合实训项目结构说明

## 项目概述

本项目通过两周实践，先在**本地环境**完成部署测试，然后在**openEuler模拟服务器**上进行生产环境部署，最终交付一个可访问的网址。

### 团队角色（4人）

| 角色 | 职责 |
|------|------|
| **项目经理** | 整体协调、进度把控、文档管理 |
| **基础设施工程师** | Docker安装、openEuler配置 |
| **应用开发工程师** | 应用开发、容器化、Helm Chart |
| **运维工程师** | K8s集群部署、数据库部署、Ingress配置 |

---

## 技术栈详解

### 基础设施层

| 技术 | 版本 | 用途 | 说明 |
|------|------|------|------|
| **openEuler** | 22.03 LTS SP3 | 操作系统 | 华为开源Linux发行版 |
| **Docker** | 24.0.6 | 容器引擎 | 本地和服务器容器运行环境 |
| **Docker Compose** | 2.23.0 | 编排工具 | 本地多容器编排 |
| **Kubernetes** | 1.28.2 | 容器编排 | 生产环境集群管理 |
| **Helm** | 3.12.3 | 包管理 | K8s应用部署工具 |

### 双服务器架构

| 服务器 | 角色 | 部署内容 | 端口 |
|--------|------|----------|------|
| **服务器A** | Web服务器 | Flask应用、Nginx反向代理 | 80、5000 |
| **服务器B** | 检测服务器 | 监控服务、健康检查API、日志收集 | 8080 |
| **数据库** | 共享存储 | MySQL数据库 | 3306 |

### 数据存储层

| 技术 | 版本 | 用途 | 说明 |
|------|------|------|------|
| **MySQL** | 8.0.35 | 关系型数据库 | 存储用户数据 |

### 应用服务层

| 技术 | 版本 | 用途 | 说明 |
|------|------|------|------|
| **Python** | 3.11 | 编程语言 | 应用开发语言 |
| **Flask** | 3.0.0 | Web框架 | 轻量级Web应用框架 |
| **Gunicorn** | 21.2.0 | WSGI服务器 | 生产环境应用服务器 |
| **Nginx** | 1.25.3 | 反向代理 | 负载均衡、静态资源 |

### 开发工具层

| 技术 | 版本 | 用途 | 说明 |
|------|------|------|------|
| **Git** | 2.42.0 | 版本控制 | 代码管理 |
| **VS Code** | 最新 | IDE | 代码编辑 |
| **Postman** | 最新 | API测试 | 接口测试工具 |
| **kubectl** | 1.28.2 | 命令行工具 | K8s集群管理 |

---

## 项目目录结构

```
1/
├── README.md                    # 项目概述文档
├── 项目计划书.md               # 详细项目计划书
├── 项目结构说明.md             # 目录结构说明
├── scripts/                     # 运维脚本目录
│   ├── init_server.sh          # 服务器初始化脚本
│   ├── install_docker.sh       # Docker安装脚本
│   └── install_k8s.sh          # Kubernetes安装脚本
├── k8s/                        # Kubernetes配置文件
│   └── mysql-deployment.yaml   # MySQL部署配置
├── app/                        # 应用代码目录
│   ├── app.py                  # Flask应用主文件
│   ├── Dockerfile              # Docker构建文件
│   ├── requirements.txt        # Python依赖
│   ├── docker-compose.yml      # Docker Compose配置
│   └── init.sql                # 数据库初始化脚本
└── helm/                       # Helm Chart目录
    └── myapp/                  # 应用Helm Chart
        ├── Chart.yaml          # Chart元数据
        ├── values.yaml         # 配置值
        └── templates/          # 模板文件
            └── deployment.yaml # 部署模板
```

---

## 部署流程

### 第一阶段：本地部署

#### 环境要求

| 软件 | 版本要求 |
|------|----------|
| Docker Desktop | 4.0+ (Windows/Mac) 或 Docker Engine 24.0+ (Linux) |
| Docker Compose | 2.23.0+ |
| 内存 | 8GB+ |
| 磁盘 | 20GB+ |

#### 部署步骤

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

#### 本地服务清单

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| Web应用 | myapp-web-1 | 5000 | Flask应用 |
| MySQL | myapp-mysql-1 | 3306 | 数据库 |

#### 访问地址

| 功能 | 地址 |
|------|------|
| 首页 | http://localhost:5000 |
| 用户列表 | http://localhost:5000/api/users |
| 健康检查 | http://localhost:5000/api/health |

---

### 第二阶段：openEuler部署

#### 环境准备

| 项目 | 配置 |
|------|------|
| 虚拟机软件 | VirtualBox 7.0+ 或 VMware |
| 操作系统 | openEuler 22.03 LTS SP3 |
| CPU | 4核 |
| 内存 | 8GB |
| 磁盘 | 50GB |

#### 部署步骤

##### 1. 系统初始化

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

# 配置内核参数
cat >> /etc/sysctl.conf << EOF
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
sysctl -p
```

##### 2. 安装Docker

```bash
# 安装Docker
yum install -y docker docker-compose

# 启动Docker
systemctl enable docker
systemctl start docker

# 配置镜像加速
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << EOF
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com"
  ]
}
EOF
systemctl restart docker
```

##### 3. 安装Kubernetes

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

# 启动kubelet
systemctl enable --now kubelet

# 初始化集群
kubeadm init --pod-network-cidr=10.244.0.0/16

# 配置kubectl
mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config

# 安装网络插件
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml

# 允许master调度Pod（单节点）
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```

##### 4. 部署应用

```bash
# 部署数据库
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml

# 构建应用镜像
cd app
docker build -t myapp:latest .

# 使用Helm部署应用
helm install myapp ../helm/myapp/

# 安装Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml

# 获取访问地址
kubectl get svc -n ingress-nginx
```

---

## API接口说明

### GET /
返回欢迎信息

**响应示例：**
```json
{
  "message": "欢迎来到鲲鹏云计算实训项目",
  "status": "success"
}
```

### GET /api/users
获取用户列表

**响应示例：**
```json
[
  {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
  {"id": 2, "name": "李四", "email": "lisi@example.com"}
]
```

### POST /api/users
创建新用户

**请求示例：**
```json
{
  "name": "王五",
  "email": "wangwu@example.com"
}
```

**响应示例：**
```json
{
  "message": "User added successfully"
}
```

### GET /api/health
健康检查

**响应示例：**
```json
{
  "status": "healthy"
}
```

---

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| MYSQL_HOST | mysql | MySQL服务地址 |
| MYSQL_USER | root | MySQL用户名 |
| MYSQL_PASSWORD | trae123 | MySQL密码 |
| MYSQL_DB | example_db | 数据库名 |

### Helm配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| replicaCount | 3 | Pod副本数 |
| image.repository | myapp | 镜像仓库 |
| image.tag | latest | 镜像标签 |
| service.type | ClusterIP | 服务类型 |
| service.port | 5000 | 服务端口 |
| ingress.enabled | true | 是否启用Ingress |

---

## 最终交付

项目完成后，将交付：

1. **本地部署环境**：本地开发测试环境
2. **openEuler生产环境**：模拟云服务器生产环境
3. **对外访问网址**：通过该网址可访问所有功能
4. **项目文档**：包含需求文档、技术方案、部署手册等

---

## 注意事项

1. 本地部署需要确保Docker Desktop正常运行
2. openEuler虚拟机建议配置4核8GB以上
3. Kubernetes集群部署前需关闭防火墙和SELinux
4. 配置Ingress后，需要确保端口映射正确