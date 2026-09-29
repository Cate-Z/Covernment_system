# 政务数字门户平台 — 完整部署说明书

> **适用对象**：全新的 openEuler / CentOS 虚拟机  
> **部署方式**：Docker 一键部署  
> **预计时间**：10-15 分钟（视网络环境）

---

## 一、前置条件

### 1.1 虚拟机要求

| 项目 | 最低要求 |
|------|----------|
| 操作系统 | openEuler 22.03+ / CentOS 8+ / RHEL 8+ |
| CPU | 1 核以上 |
| 内存 | 2 GB 以上 |
| 磁盘 | 10 GB 以上 |
| 网络 | 能访问互联网（拉取 Docker 镜像用） |
| 用户 | 有 root 或 sudo 权限的用户 |

### 1.2 准备部署包

将 `项目部署包` 文件夹完整上传到虚拟机：

```bash
# 在宿主机 PowerShell 中执行（替换 IP 和路径）
scp -r "项目部署包" os@虚拟机IP:~/project/
```

**部署包目录结构：**
```
项目部署包/
├── setup.sh                ← 一键部署脚本
├── 部署说明书.md            ← 本文档
└── flask-app/              ← 项目完整代码
    ├── app.py              ← Flask 主程序
    ├── Dockerfile           ← 容器镜像构建文件
    ├── docker-compose.yml   ← 容器编排配置
    ├── init.sql             ← 数据库初始化脚本
    ├── migrate_blog.sql     ← 博客模块建表脚本
    ├── requirements.txt     ← Python 依赖
    ├── static/              ← 静态资源
    │   ├── css/style.css
    │   └── js/app.js
    └── templates/
        └── index.html       ← 前端模板
```

---

## 二、部署步骤

### 方式一：一键自动部署（推荐）

```bash
# 进入部署包目录
cd ~/project/项目部署包

# 给脚本执行权限
chmod +x setup.sh

# 以 root 或 sudo 运行
sudo ./setup.sh
```

脚本会自动完成：
1. 安装 Docker
2. 配置国内镜像加速
3. 修复防火墙与 Docker 兼容性
4. 拉取 MySQL 镜像
5. 构建 Flask 镜像
6. 启动所有容器
7. 设置开机自启

**脚本执行完成后，直接访问虚拟机 IP 的 5000 端口即可。**

---

### 方式二：手动分步部署

如果一键脚本遇到问题，可按以下步骤手动操作：

#### 2.1 安装 Docker

```bash
sudo dnf update -y
sudo dnf install docker -y
sudo systemctl start docker
sudo systemctl enable docker
docker --version
```

#### 2.2 配置 Docker 镜像加速

```bash
sudo mkdir -p /etc/docker
sudo bash -c 'cat > /etc/docker/daemon.json << EOF
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://mirror.aliyuncs.com",
    "https://hub-mirror.c.163.com"
  ]
}
EOF'
sudo systemctl daemon-reload
sudo systemctl restart docker
```

#### 2.3 修复防火墙兼容性

```bash
# 切换为 iptables 模式（兼容 Docker）
sudo sed -i 's/FirewallBackend=nftables/FirewallBackend=iptables/' /etc/firewalld/firewalld.conf
sudo systemctl restart firewalld

# 添加 Docker 信任规则
sudo firewall-cmd --permanent --zone=trusted --add-interface=docker0
sudo firewall-cmd --permanent --zone=trusted --add-source=172.18.0.0/16
sudo firewall-cmd --permanent --zone=public --add-masquerade
sudo firewall-cmd --permanent --zone=public --add-port=5000/tcp
sudo firewall-cmd --reload
```

#### 2.4 拉取镜像并构建

```bash
# 拉取 MySQL
sudo docker pull mysql:8.0.35

# 进入项目目录构建 Flask
cd ~/project/项目部署包/flask-app
sudo docker build -t gov-portal-flask .
```

#### 2.5 启动服务

```bash
# 创建网络和数据卷
sudo docker network create gov-portal-network 2>/dev/null || true
sudo docker volume create mysql_data 2>/dev/null || true

# 停止旧容器
sudo docker stop gov-portal-mysql gov-portal-flask 2>/dev/null || true
sudo docker rm gov-portal-mysql gov-portal-flask 2>/dev/null || true

# 启动 MySQL
sudo docker run -d \
  --name gov-portal-mysql \
  --network gov-portal-network \
  -e MYSQL_ROOT_PASSWORD=trae123 \
  -e MYSQL_DATABASE=example_db \
  -v mysql_data:/var/lib/mysql \
  -v ~/project/项目部署包/flask-app/init.sql:/docker-entrypoint-initdb.d/init.sql \
  -p 3308:3306 \
  --restart unless-stopped \
  mysql:8.0.35

# 等待 MySQL 就绪
sleep 40

# 启动 Flask
sudo docker run -d \
  --name gov-portal-flask \
  --network gov-portal-network \
  -e MYSQL_HOST=gov-portal-mysql \
  -e MYSQL_USER=root \
  -e MYSQL_PASSWORD=trae123 \
  -e MYSQL_DB=example_db \
  -p 5000:5000 \
  --restart unless-stopped \
  gov-portal-flask

# 验证运行状态
sudo docker ps
```

#### 2.6 设置开机自启

```bash
sudo bash -c 'cat > /etc/systemd/system/gov-portal.service << EOF
[Unit]
Description=Government Portal Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=/bin/bash -c "docker network create gov-portal-network 2>/dev/null || true"
ExecStart=/bin/bash -c "docker start gov-portal-mysql gov-portal-flask 2>/dev/null || true"
ExecStop=/bin/bash -c "docker stop gov-portal-mysql gov-portal-flask 2>/dev/null || true"

[Install]
WantedBy=multi-user.target
EOF'

sudo systemctl daemon-reload
sudo systemctl enable gov-portal
```

---

## 三、访问系统

### 3.1 局域网访问

在浏览器中输入：

```
http://虚拟机IP:5000
```

查看虚拟机 IP：
```bash
ip addr show | grep 'inet ' | grep -v 127.0.0.1
```

### 3.2 外网访问（可选 — cpolar 内网穿透）

```bash
# 安装 cpolar
curl -L https://www.cpolar.com/static/downloads/install-release-cpolar.sh | sudo bash

# 在 cpolar.com 注册获取 authtoken，然后：
cpolar authtoken 你的token

# 启动隧道
nohup cpolar http 5000 &
```

---

## 四、账号信息

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| **管理员** | admin | admin123 | 可访问管理后台全部功能 |
| 测试用户 | zhangsan | 123456 | 技术部 |
| 测试用户 | lisi | 123456 | 财务部 |
| 测试用户 | wangwu | 123456 | 人事部 |
| 测试用户 | zhaoliu | 123456 | 市场部 |
| 测试用户 | qianqi | 123456 | 技术部 |

---

## 五、日常运维

### 5.1 查看运行状态

```bash
docker ps
```

### 5.2 重启服务

```bash
docker restart gov-portal-mysql gov-portal-flask
```

### 5.3 查看日志

```bash
# Flask 日志
docker logs -f gov-portal-flask

# MySQL 日志
docker logs -f gov-portal-mysql
```

### 5.4 更新代码

在宿主机修改代码后，同步到虚拟机并重建容器：

```bash
# 在宿主机 PowerShell 中执行
scp -r "flask-app\." os@虚拟机IP:~/project/项目部署包/flask-app/

# 在虚拟机中重建并重启
cd ~/project/项目部署包/flask-app
sudo docker build -t gov-portal-flask .
sudo docker stop gov-portal-flask && sudo docker rm gov-portal-flask
sudo docker run -d \
  --name gov-portal-flask \
  --network gov-portal-network \
  -e MYSQL_HOST=gov-portal-mysql \
  -e MYSQL_USER=root \
  -e MYSQL_PASSWORD=trae123 \
  -e MYSQL_DB=example_db \
  -p 5000:5000 \
  --restart unless-stopped \
  gov-portal-flask
```

### 5.5 数据备份

```bash
# 导出数据库数据
docker exec gov-portal-mysql mysqldump -u root -ptrae123 example_db > backup_$(date +%Y%m%d).sql
```

### 5.6 数据恢复

```bash
docker exec -i gov-portal-mysql mysql -u root -ptrae123 example_db < backup_20260101.sql
```

---

## 六、项目功能模块

| 模块 | 功能说明 |
|------|----------|
| 统一认证 | 管理员/普通用户登录、注册、Session 管理 |
| 用户管理 | 用户增删改查、个人信息编辑、密码修改 |
| 部门管理 | 管理员动态增删改部门，注册时可选 |
| 新闻管理 | 政务新闻增删改查、分类筛选、搜索、快速发布/草稿 |
| 政务服务 | 服务项目增删改查、排序管理 |
| 用户反馈 | 提交反馈、管理员处理回复、类型/状态筛选 |
| 博客模块 | 发布博客（含图片）、审核、评论、点赞 |
| 好友系统 | 搜索用户、添加好友、删除好友 |
| 系统监控 | 运行时间、请求计数、数据库统计 |
| 数据统计 | 新闻分类、反馈类型、用户分布统计 |
| 操作日志 | 全操作审计日志、导出 CSV |
| 角色权限 | RBAC 角色权限管理 |

---

## 七、数据库表结构

| 表名 | 说明 |
|------|------|
| users | 用户表（统一前后台用户） |
| departments | 部门表 |
| news | 新闻表 |
| services | 政务服务表 |
| feedback | 用户反馈表 |
| announcements | 通知公告表 |
| blogs | 博客表 |
| blog_comments | 博客评论表 |
| blog_likes | 博客点赞记录表 |
| friends | 好友关系表 |
| operation_logs | 操作日志表 |
| system_config | 系统配置表 |
| backup_records | 备份记录表 |
| roles | 角色表 |
| permissions | 权限表 |
| role_permissions | 角色权限关联表 |

---

## 八、常见问题排查

### Q1: 访问网站一直转圈或 500 错误

```bash
# 检查是否防火墙阻止了 Docker 内部通信
sudo sed -i 's/FirewallBackend=nftables/FirewallBackend=iptables/' /etc/firewalld/firewalld.conf
sudo systemctl restart firewalld
sudo systemctl restart docker
```

### Q2: 无法拉取 Docker 镜像（网络超时）

```bash
# 确认镜像加速已配置
cat /etc/docker/daemon.json

# 如果还不行，换用手机热点
```

### Q3: 容器启动后立即退出

```bash
# 查看退出原因
docker logs gov-portal-mysql
docker logs gov-portal-flask
```

### Q4: 重启后容器丢失

```bash
# 确认 Volume 已配置
docker volume ls

# 重新执行 setup.sh
sudo ./setup.sh
```

### Q5: 端口被占用

```bash
# 查看端口占用
sudo netstat -tlnp | grep 5000

# 停止占用进程或修改 docker-compose.yml 中的端口
```

---

## 九、系统架构

```
┌──────────────────────────────────────────────┐
│               客户端（浏览器）                  │
│    http://虚拟机IP:5000                       │
└──────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│  gov-portal-flask (Docker 容器)               │
│  Python Flask - Port 5000                    │
│  ┌────────────────────────────────────────┐  │
│  │  RESTful API (JSON)                     │  │
│  │  Jinja2 模板渲染                        │  │
│  │  Session 会话管理                        │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│  gov-portal-mysql (Docker 容器)               │
│  MySQL 8.0.35 - Port 3306                    │
│  ┌────────────────────────────────────────┐  │
│  │  16 张业务表                             │  │
│  │  mysql_data Volume (数据永久保存)        │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

---

## 十、技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python Flask 2.3.3 |
| 数据库 | MySQL 8.0.35 |
| 容器化 | Docker + Volume 持久化 |
| 前端 | HTML5 + CSS3 + Vanilla JavaScript |
| 内网穿透 | cpolar |
| 系统 | openEuler 22.03 LTS |

---

*文档版本：v1.0 | 更新日期：2026-06-03*
