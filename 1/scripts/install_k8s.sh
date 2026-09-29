#!/bin/bash
# Kubernetes安装脚本

echo "=== 开始安装Kubernetes ==="

# 设置变量
K8S_VERSION="1.28.2"
CRI_DOCKER_VERSION="0.3.0"

# 安装kubelet、kubeadm、kubectl
echo "1. 安装Kubernetes组件..."
cat <<EOF | tee /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://pkgs.k8s.io/core:/stable:/v1.28/rpms/
enabled=1
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.28/rpms/repodata/repomd.xml.key
EOF

yum install -y kubelet-$K8S_VERSION kubeadm-$K8S_VERSION kubectl-$K8S_VERSION --disableexcludes=kubernetes

# 启动kubelet
echo "2. 启动kubelet..."
systemctl enable --now kubelet

# 安装CRI-Docker
echo "3. 安装CRI-Docker..."
wget https://github.com/Mirantis/cri-dockerd/releases/download/v${CRI_DOCKER_VERSION}/cri-dockerd-${CRI_DOCKER_VERSION}.amd64.tgz
tar xvf cri-dockerd-${CRI_DOCKER_VERSION}.amd64.tgz
cp cri-dockerd/cri-dockerd /usr/local/bin/

# 创建systemd服务
cat > /etc/systemd/system/cri-docker.service << EOF
[Unit]
Description=CRI Interface for Docker Application Container Engine
Documentation=https://docs.mirantis.com
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=notify
ExecStart=/usr/local/bin/cri-dockerd --container-runtime-endpoint fd://
ExecReload=/bin/kill -s HUP $MAINPID
TimeoutSec=0
RestartSec=2
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now cri-docker

echo "=== Kubernetes组件安装完成 ==="
echo "请在主节点执行: kubeadm init --cri-socket unix:///var/run/cri-dockerd.sock"