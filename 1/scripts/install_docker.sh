#!/bin/bash
# Docker安装脚本

echo "=== 开始安装Docker ==="

# 卸载旧版本
echo "1. 卸载旧版本..."
yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine

# 设置仓库
echo "2. 设置Docker仓库..."
yum install -y yum-utils
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装Docker Engine
echo "3. 安装Docker Engine..."
yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 启动Docker
echo "4. 启动Docker..."
systemctl enable docker
systemctl start docker

# 配置镜像加速
echo "5. 配置镜像加速..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << EOF
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ],
  "exec-opts": ["native.cgroupdriver=systemd"]
}
EOF

# 重启Docker
systemctl daemon-reload
systemctl restart docker

# 验证安装
echo "6. 验证安装..."
docker --version
docker run hello-world

echo "=== Docker安装完成 ==="