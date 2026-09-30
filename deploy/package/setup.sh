#!/bin/bash
# ============================================================
# 政务数字门户平台 - 一键部署脚本
# 适用系统：openEuler / CentOS / RHEL
# 使用方法：chmod +x setup.sh && sudo ./setup.sh
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  政务数字门户平台 - 一键部署脚本${NC}"
echo -e "${GREEN}============================================${NC}"

# ---- 1. 安装 Docker ----
echo -e "${YELLOW}[1/7] 安装 Docker...${NC}"
if ! command -v docker &>/dev/null; then
    dnf update -y
    dnf install docker -y
    systemctl start docker
    systemctl enable docker
fi
echo -e "${GREEN}  Docker 安装完成${NC}"

# ---- 2. 配置 Docker 国内镜像加速 ----
echo -e "${YELLOW}[2/7] 配置 Docker 镜像加速...${NC}"
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'DAEMON_EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://mirror.aliyuncs.com",
    "https://hub-mirror.c.163.com"
  ]
}
DAEMON_EOF
systemctl daemon-reload
systemctl restart docker
echo -e "${GREEN}  镜像加速配置完成${NC}"

# ---- 3. 修复 firewalld 与 Docker 兼容性 ----
echo -e "${YELLOW}[3/7] 修复防火墙与 Docker 兼容性...${NC}"
FIREWALL_CONF="/etc/firewalld/firewalld.conf"
if [ -f "$FIREWALL_CONF" ]; then
    if grep -q "FirewallBackend=nftables" "$FIREWALL_CONF"; then
        sed -i 's/FirewallBackend=nftables/FirewallBackend=iptables/' "$FIREWALL_CONF"
        systemctl restart firewalld
    fi
    firewall-cmd --permanent --zone=trusted --add-interface=docker0 2>/dev/null || true
    firewall-cmd --permanent --zone=trusted --add-source=172.18.0.0/16 2>/dev/null || true
    firewall-cmd --permanent --zone=public --add-masquerade 2>/dev/null || true
    firewall-cmd --permanent --zone=public --add-port=5000/tcp 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
fi
echo -e "${GREEN}  防火墙配置完成${NC}"

# ---- 4. 拉取 MySQL 镜像 ----
echo -e "${YELLOW}[4/7] 拉取 MySQL 镜像...${NC}"
docker pull mysql:8.0.35
echo -e "${GREEN}  MySQL 镜像拉取完成${NC}"

# ---- 5. 构建 Flask 镜像 ----
echo -e "${YELLOW}[5/7] 构建 Flask 应用镜像...${NC}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 应用代码目录：优先使用与本脚本同级的 flask-app/（打包后的部署包结构），
# 若不存在则回退到仓库中的 final-project/flask-app/
if [ -d "$SCRIPT_DIR/flask-app" ]; then
    APP_DIR="$SCRIPT_DIR/flask-app"
else
    APP_DIR="$(cd "$SCRIPT_DIR/../../final-project/flask-app" && pwd)"
fi
echo -e "${GREEN}  应用代码目录: ${APP_DIR}${NC}"
cd "$APP_DIR"
docker build -t gov-portal-flask .
echo -e "${GREEN}  Flask 镜像构建完成${NC}"

# ---- 6. 创建 Docker 网络并启动容器 ----
echo -e "${YELLOW}[6/7] 启动服务...${NC}"
docker network create gov-portal-network 2>/dev/null || true

# 停止并删除旧容器（如果存在）
docker stop gov-portal-mysql gov-portal-flask 2>/dev/null || true
docker rm gov-portal-mysql gov-portal-flask 2>/dev/null || true

# 创建持久化数据卷
docker volume create mysql_data 2>/dev/null || true

# 启动 MySQL（带数据持久化）
docker run -d \
  --name gov-portal-mysql \
  --network gov-portal-network \
  -e MYSQL_ROOT_PASSWORD=trae123 \
  -e MYSQL_DATABASE=example_db \
  -v mysql_data:/var/lib/mysql \
  -v "$APP_DIR/init.sql:/docker-entrypoint-initdb.d/init.sql" \
  -p 3308:3306 \
  --restart unless-stopped \
  mysql:8.0.35

echo -e "${YELLOW}  等待 MySQL 启动（约40秒）...${NC}"
sleep 40

# 启动 Flask
docker run -d \
  --name gov-portal-flask \
  --network gov-portal-network \
  -e MYSQL_HOST=gov-portal-mysql \
  -e MYSQL_USER=root \
  -e MYSQL_PASSWORD=trae123 \
  -e MYSQL_DB=example_db \
  -p 5000:5000 \
  --restart unless-stopped \
  gov-portal-flask

echo -e "${GREEN}  容器启动完成${NC}"

# ---- 7. 设置开机自启 ----
echo -e "${YELLOW}[7/7] 设置开机自启...${NC}"
# Docker 自启
systemctl enable docker

# 项目自启服务
cat > /etc/systemd/system/gov-portal.service << 'SERVICE_EOF'
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
SERVICE_EOF

systemctl daemon-reload
systemctl enable gov-portal
echo -e "${GREEN}  开机自启设置完成${NC}"

# ---- 完成 ----
IP=$(ip addr show | grep 'inet ' | grep -v 127.0.0.1 | head -1 | awk '{print $2}' | cut -d/ -f1)

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  局域网访问: ${YELLOW}http://${IP}:5000${NC}"
echo ""
echo -e "  管理员账号: ${YELLOW}admin${NC}"
echo -e "  管理员密码: ${YELLOW}admin123${NC}"
echo ""
echo -e "  测试用户:   ${YELLOW}zhangsan / 123456${NC}"
echo ""
echo -e "  查看状态:   ${YELLOW}docker ps${NC}"
echo ""
echo -e "${GREEN}============================================${NC}"
