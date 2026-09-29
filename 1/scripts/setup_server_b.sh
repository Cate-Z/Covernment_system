#!/bin/bash
# 服务器B - 检测服务器部署脚本

echo "=== 服务器B配置开始 ==="

# 1. 系统更新
echo "1. 系统更新..."
yum update -y

# 2. 安装依赖
echo "2. 安装依赖..."
yum install -y docker python3 python3-pip wget git

# 3. 安装Python依赖
echo "3. 安装Python依赖..."
pip3 install flask requests

# 4. 创建监控目录
echo "4. 创建监控目录..."
mkdir -p /opt/monitor
cd /opt/monitor

# 5. 创建监控服务配置
echo "5. 创建监控服务..."
cat > /opt/monitor/monitor.py << 'EOF'
from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

# 配置Web服务器地址
WEB_SERVER_URL = "http://SERVER_A_IP:5000"

@app.route('/')
def index():
    return jsonify({
        "service": "monitor",
        "version": "1.0",
        "status": "running"
    })

@app.route('/health')
def check_health():
    """检查Web服务器健康状态"""
    try:
        response = requests.get(f"{WEB_SERVER_URL}/api/health", timeout=5)
        if response.status_code == 200:
            web_status = response.json()
            return jsonify({
                "status": "healthy",
                "web_server": "up",
                "web_status": web_status,
                "timestamp": time.time()
            })
        else:
            return jsonify({
                "status": "degraded",
                "web_server": "unhealthy",
                "timestamp": time.time()
            }), 503
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "critical",
            "web_server": "down",
            "error": str(e),
            "timestamp": time.time()
        }), 503

@app.route('/metrics')
def get_metrics():
    """获取监控指标"""
    return jsonify({
        "uptime": time.time(),
        "check_interval": 60,
        "web_server_url": WEB_SERVER_URL
    })

@app.route('/logs')
def get_logs():
    """获取Web服务器日志（简化版）"""
    try:
        response = requests.get(f"{WEB_SERVER_URL}/", timeout=5)
        return jsonify({
            "web_server_response": response.status_code,
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF

# 6. 创建systemd服务
echo "6. 创建systemd服务..."
cat > /etc/systemd/system/monitor.service << 'EOF'
[Unit]
Description=Monitor Service
After=network.target

[Service]
User=root
WorkingDirectory=/opt/monitor
ExecStart=/usr/bin/python3 monitor.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 7. 启动监控服务
echo "7. 启动监控服务..."
systemctl daemon-reload
systemctl start monitor
systemctl enable monitor

# 8. 配置防火墙
echo "8. 配置防火墙..."
firewall-cmd --add-port=8080/tcp --permanent
firewall-cmd --reload

echo "=== 服务器B配置完成 ==="
echo "监控服务地址: http://$(hostname -I | awk '{print $1}'):8080"