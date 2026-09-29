# 鲲鹏云计算综合实训项目计划书

## 1. 项目背景

### 1.1 项目名称
鲲鹏云计算综合实训项目

### 1.2 项目目标
本项目通过两周实践，先在本地环境完成部署测试，然后在openEuler模拟服务器上进行生产环境部署，最终交付一个可访问的网址，实现所有核心功能。

### 1.3 项目意义
- 掌握云计算核心技术和容器化部署
- 提升云原生应用开发与运维能力
- 培养团队协作和项目管理能力
- 交付可实际访问的业务系统

### 1.4 最终交付物
- **本地部署环境**：本地开发测试环境
- **openEuler生产环境**：模拟云服务器生产环境
- **对外访问网址**：通过该网址可访问所有功能模块

---

## 2. 技术方案

### 2.1 部署架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        部署流程                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────┐         ┌─────────────────────────────┐   │
│   │   本地部署       │  ───>  │      openEuler双服务器部署    │   │
│   │  (开发测试)      │         │      (生产环境)             │   │
│   └────────┬────────┘         └───────────┬─────────────────┘   │
│            │                               │                     │
│            ▼                               ▼                     │
│   ┌─────────────────┐         ┌───────────┴─────────────────┐   │
│   │ Docker Compose  │         │                             │   │
│   │ - Flask App     │         │  ┌───────────┐ ┌───────────┐ │   │
│   │ - MySQL         │         │  │ 服务器A   │ │ 服务器B   │ │   │
│   └─────────────────┘         │  │ Web应用   │ │ 检测系统  │ │   │
│                               │  │ Nginx     │ │ 监控服务  │ │   │
│                               │  └─────┬─────┘ └─────┬─────┘ │   │
│                               │         │             │       │   │
│                               │         └─────┬───────┘       │   │
│                               │               │               │   │
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

#### 2.1.1 服务器职责划分

| 服务器 | 角色 | 部署内容 | 端口 |
|--------|------|----------|------|
| **服务器A** | Web服务器 | Flask应用、Nginx反向代理 | 80、5000 |
| **服务器B** | 检测服务器 | 监控服务、健康检查API、日志收集 | 8080 |
| **数据库** | 共享存储 | MySQL数据库 | 3306 |

### 2.2 技术栈详解

#### 2.2.1 基础设施层

| 技术 | 版本 | 用途 | 说明 |
|------|------|------|------|
| **openEuler** | 22.03 LTS SP3 | 操作系统 | 华为开源Linux发行版，兼容CentOS |
| **Docker** | 24.0.6 | 容器引擎 | 本地和服务器容器运行环境 |
| **Docker Compose** | 2.23.0 | 编排工具 | 本地多容器编排 |
| **Kubernetes** | 1.28.2 | 容器编排 | 生产环境集群管理 |
| **Helm** | 3.12.3 | 包管理 | K8s应用部署工具 |

#### 2.2.2 数据存储层

| 技术 | 版本 | 用途 | 说明 |
|------|------|------|------|
| **MySQL** | 8.0.35 | 关系型数据库 | 存储用户数据 |

#### 2.2.3 应用服务层

| 技术 | 版本 | 用途 | 说明 |
|------|------|------|------|
| **Python** | 3.11 | 编程语言 | 应用开发语言 |
| **Flask** | 3.0.0 | Web框架 | 轻量级Web应用框架 |
| **Gunicorn** | 21.2.0 | WSGI服务器 | 生产环境应用服务器 |
| **Nginx** | 1.25.3 | 反向代理 | 负载均衡、静态资源 |

#### 2.2.4 开发工具层

| 技术 | 版本 | 用途 | 说明 |
|------|------|------|------|
| **Git** | 2.42.0 | 版本控制 | 代码管理 |
| **VS Code** | 最新 | IDE | 代码编辑 |
| **Postman** | 最新 | API测试 | 接口测试工具 |
| **kubectl** | 1.28.2 | 命令行工具 | K8s集群管理 |

### 2.3 网络架构

#### 本地部署网络

| 服务 | 端口 | 访问地址 |
|------|------|----------|
| Flask应用 | 5000 | http://localhost:5000 |
| MySQL | 3306 | localhost:3306 |

#### openEuler部署网络

| 网络类型 | 网段 | 用途 |
|----------|------|------|
| 节点网络 | 192.168.56.0/24 | 虚拟机网络 |
| Pod网络 | 10.244.0.0/16 | Kubernetes Pod网络 |
| Service网络 | 10.96.0.0/12 | Kubernetes Service网络 |

---

## 3. 实施计划

### 3.1 项目进度安排

| 阶段 | 任务 | 负责人 | 交付物 |
|------|------|--------|--------|
| **第一阶段** | 环境准备与本地部署 | 全体 | 本地运行环境 |
| | - 安装Docker/Docker Compose | 基础设施工程师 | Docker环境 |
| | - 本地部署测试 | 应用开发工程师 | 本地可访问应用 |
| **第二阶段** | openEuler环境搭建 | 基础设施工程师 | openEuler虚拟机 |
| | - 安装openEuler系统 | 基础设施工程师 | 系统就绪 |
| | - 配置系统环境 | 运维工程师 | 网络、安全配置 |
| **第三阶段** | Kubernetes集群部署 | 运维工程师 | K8s集群就绪 |
| | - 安装K8s组件 | 运维工程师 | kubeadm/kubelet |
| | - 初始化集群 | 运维工程师 | 集群运行正常 |
| **第四阶段** | 应用部署与配置 | 应用开发工程师 | 生产环境应用 |
| | - 部署数据库 | 运维工程师 | MySQL运行 |
| | - 部署应用 | 应用开发工程师 | 应用可访问 |
| **第五阶段** | 测试验收 | 全体 | 项目交付 |
| | - 功能测试 | 全体 | 测试报告 |
| | - 项目演示 | 项目经理 | 演示视频 |

### 3.2 任务分解（按角色）

#### 3.2.1 项目经理任务

| 任务ID | 任务名称 | 描述 |
|--------|----------|------|
| PM001 | 需求分析 | 明确项目目标和需求 |
| PM002 | 进度跟踪 | 每日站会，跟踪进度 |
| PM003 | 风险管控 | 识别和应对风险 |
| PM004 | 文档管理 | 整理项目文档 |
| PM005 | 项目验收 | 组织验收演示 |

#### 3.2.2 基础设施工程师任务

| 任务ID | 任务名称 | 描述 |
|--------|----------|------|
| INF001 | Docker安装 | 本地安装Docker和Docker Compose |
| INF002 | openEuler安装 | 安装openEuler虚拟机 |
| INF003 | 系统配置 | 配置网络、防火墙、SELinux |
| INF004 | Docker安装(服务器) | 在openEuler上安装Docker |

#### 3.2.3 应用开发工程师任务

| 任务ID | 任务名称 | 描述 |
|--------|----------|------|
| DEV001 | 应用开发 | 开发Flask Web应用 |
| DEV002 | 本地测试 | 本地部署测试验证 |
| DEV003 | Dockerfile编写 | 编写Docker构建文件 |
| DEV004 | Helm Chart开发 | 创建Helm部署包 |
| DEV005 | 应用部署 | 部署应用到K8s集群 |

#### 3.2.4 运维工程师任务

| 任务ID | 任务名称 | 描述 |
|--------|----------|------|
| OPS001 | K8s组件安装 | 安装kubeadm/kubelet/kubectl |
| OPS002 | 集群初始化 | kubeadm init配置集群 |
| OPS003 | 网络配置 | 安装Calico网络插件 |
| OPS004 | 数据库部署 | 部署MySQL |
| OPS005 | Ingress配置 | 配置Nginx Ingress |

---

## 4. 部署方案详解

### 4.1 本地部署方案

#### 4.1.1 环境要求

| 软件 | 版本要求 |
|------|----------|
| Docker Desktop | 4.0+ (Windows/Mac) 或 Docker Engine 24.0+ (Linux) |
| Docker Compose | 2.23.0+ |
| 内存 | 至少8GB |
| 磁盘 | 至少20GB可用空间 |

#### 4.1.2 部署步骤

```bash
# 1. 进入应用目录
cd 1/app

# 2. 启动所有服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 访问应用
# 浏览器打开 http://localhost:5000
```

#### 4.1.3 本地服务清单

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| Web应用 | myapp-web-1 | 5000 | Flask应用 |
| MySQL | myapp-mysql-1 | 3306 | 数据库 |

### 4.2 openEuler部署方案

#### 4.2.1 环境准备

| 项目 | 配置 |
|------|------|
| 操作系统 | openEuler 22.03 LTS SP3 |
| CPU | 4核 |
| 内存 | 8GB |
| 磁盘 | 50GB |
| 网络 | NAT/桥接网络 |

#### 4.2.2 系统初始化

```bash
# 1. 更新系统
yum update -y

# 2. 安装必要工具
yum install -y wget curl vim net-tools git

# 3. 关闭防火墙
systemctl stop firewalld
systemctl disable firewalld

# 4. 关闭SELinux
sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0

# 5. 配置内核参数
cat >> /etc/sysctl.conf << EOF
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
sysctl -p
```

#### 4.2.3 Docker安装

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

#### 4.2.4 Kubernetes安装

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

#### 4.2.5 应用部署

```bash
# 1. 部署数据库
kubectl apply -f k8s/mysql-deployment.yaml

# 2. 构建应用镜像
cd app
docker build -t myapp:latest .

# 3. 使用Helm部署应用
helm install myapp ../helm/myapp/

# 4. 安装Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml

# 5. 获取访问地址
kubectl get svc -n ingress-nginx
```

---

## 5. 资源需求

### 5.1 本地环境资源

| 资源 | 要求 |
|------|------|
| 操作系统 | Windows 10/11、macOS 10.15+、Linux |
| 内存 | 8GB+ |
| CPU | 4核+ |
| 磁盘 | 20GB+ |

### 5.2 openEuler虚拟机资源

| 资源 | 配置 |
|------|------|
| 虚拟机软件 | VirtualBox 7.0+ 或 VMware |
| CPU | 4核 |
| 内存 | 8GB |
| 磁盘 | 50GB |

### 5.3 人员安排（4人）

| 角色 | 职责 |
|------|------|
| **项目经理** | 整体协调、进度把控、文档管理 |
| **基础设施工程师** | Docker安装、openEuler配置 |
| **应用开发工程师** | 应用开发、容器化、Helm Chart |
| **运维工程师** | K8s集群部署、数据库部署、Ingress配置 |

---

## 6. 验收标准

### 6.1 本地部署验收

| 验收项 | 验收标准 |
|--------|----------|
| Docker环境 | Docker和Docker Compose安装成功 |
| 服务启动 | 所有容器正常运行 |
| 应用访问 | http://localhost:5000 可访问 |
| 功能测试 | 所有API接口正常响应 |

### 6.2 openEuler部署验收

| 验收项 | 验收标准 |
|--------|----------|
| 系统环境 | openEuler系统正常运行 |
| Docker | Docker服务正常 |
| Kubernetes | 集群状态Ready |
| 数据库 | MySQL运行正常 |
| **对外访问** | **通过网址可访问所有功能** |

### 6.3 网址功能清单

| 功能模块 | 说明 | API路径 |
|----------|------|---------|
| 首页 | 欢迎页面 | `/` |
| 用户管理 | 查看/添加用户 | `/api/users` |
| 健康检查 | 系统状态 | `/api/health` |

---

## 7. 风险评估

| 风险编号 | 风险描述 | 风险等级 | 应对措施 |
|----------|----------|----------|----------|
| R001 | 本地环境配置失败 | 中 | 使用官方安装文档，逐步验证 |
| R002 | openEuler安装失败 | 中 | 使用官方镜像，参考安装指南 |
| R003 | K8s集群部署失败 | 高 | 使用kubeadm标准流程，预留回滚 |
| R004 | 应用部署失败 | 中 | 先本地验证，再部署生产 |
| R005 | 网络配置问题 | 高 | 检查防火墙和SELinux配置 |

---

## 8. 项目管理

### 8.1 沟通机制

- 每日站会：15分钟，同步进度和问题
- 技术评审会：关键环节前进行方案评审
- 即时沟通：使用钉钉/微信进行实时交流

### 8.2 文档管理

- 文档统一存放在Git仓库
- 版本控制使用Git
- 文档格式统一为Markdown

---

## 附录

### A. 参考资料

1. openEuler官方文档：https://docs.openeuler.org
2. Kubernetes官方文档：https://kubernetes.io/docs
3. Docker官方文档：https://docs.docker.com
4. Helm官方文档：https://helm.sh/docs

### B. 工具清单

| 工具 | 用途 |
|------|------|
| VirtualBox/VMware | 虚拟机软件 |
| Docker Desktop | 本地容器环境 |
| VS Code | 代码编辑 |
| Git | 版本控制 |
| kubectl | K8s命令行工具 |
| helm | Helm命令行工具 |
| Postman | API测试 |