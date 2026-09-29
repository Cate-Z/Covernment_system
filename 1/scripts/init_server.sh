#!/bin/bash
# 云服务器初始化脚本

echo "=== 开始初始化服务器 ==="

# 更新系统
echo "1. 更新系统..."
yum update -y

# 安装必要工具
echo "2. 安装必要工具..."
yum install -y wget curl vim net-tools telnet git

# 配置时间同步
echo "3. 配置时间同步..."
yum install -y chrony
systemctl enable chronyd
systemctl start chronyd
timedatectl set-timezone Asia/Shanghai

# 关闭防火墙（生产环境不建议）
echo "4. 配置防火墙..."
systemctl stop firewalld
systemctl disable firewalld

# 关闭SELinux
echo "5. 关闭SELinux..."
sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0

# 配置内核参数
echo "6. 配置内核参数..."
cat >> /etc/sysctl.conf << EOF
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
sysctl -p

# 创建用户
echo "7. 创建实训用户..."
useradd -m -s /bin/bash trae
echo "trae:trae123" | chpasswd
echo "trae ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

echo "=== 服务器初始化完成 ==="