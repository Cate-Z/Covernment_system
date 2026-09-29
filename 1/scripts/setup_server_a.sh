#!/bin/bash
# 服务器A - Web服务器部署脚本

echo "=== 服务器A配置开始 ==="

# 1. 系统更新
echo "1. 系统更新..."
yum update -y

# 2. 安装依赖
echo "2. 安装依赖..."
yum install -y docker docker-compose nginx wget git

# 3. 启动Docker
echo "3. 启动Docker..."
systemctl start docker
systemctl enable docker

# 4. 配置Docker镜像加速
echo "4. 配置Docker镜像加速..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
    "registry-mirrors": ["https://hub-mirror.c.163.com"]
}
EOF
systemctl restart docker

# 5. 创建应用目录
echo "5. 创建应用目录..."
mkdir -p /opt/app
cd /opt/app

# 6. 下载应用代码（假设从Git仓库获取）
echo "6. 下载应用代码..."
git clone https://github.com/your-repo/cloud-training-app.git .

# 7. 启动应用
echo "7. 启动应用..."
docker-compose up -d

# 8. 配置Nginx
echo "8. 配置Nginx..."
cat > /etc/nginx/conf.d/myapp.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# 9. 启动Nginx
echo "9. 启动Nginx..."
systemctl start nginx
systemctl enable nginx

# 10. 配置防火墙
echo "10. 配置防火墙..."
firewall-cmd --add-port=80/tcp --permanent
firewall-cmd --add-port=5000/tcp --permanent
firewall-cmd --reload

echo "=== 服务器A配置完成 ==="
echo "Web应用地址: http://$(hostname -I | awk '{print $1}')"