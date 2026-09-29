# 政务数字门户平台 - 项目重要代码文档

本文档整理了本项目中的核心代码，方便撰写项目报告时参考。

---

## 一、后端核心代码 (app.py)

### 1.1 Flask应用初始化与配置
**功能**：初始化Flask应用，配置数据库连接、密钥等基础设置

```python
# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, render_template, session
import mysql.connector
import os
from datetime import datetime
from decimal import Decimal
import sys

# 设置标准输出编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'kunpeng-cloud-training-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# MySQL配置
mysql_host = os.environ.get('MYSQL_HOST', 'mysql')
mysql_user = os.environ.get('MYSQL_USER', 'root')
mysql_password = os.environ.get('MYSQL_PASSWORD', 'trae123')
mysql_db = os.environ.get('MYSQL_DB', 'example_db')

# 管理员账号密码
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# 操作日志
operation_logs = []
server_start_time = datetime.now()
request_count = 0

# 政务分类数据
NEWS_CATEGORIES = ['政策法规', '政务动态', '通知公告', '办事指南', '政务公开']
SERVICE_TYPES = ['企业开办', '税务办理', '社保服务', '医疗服务', '教育服务', '住房服务']
FEEDBACK_TYPES = ['咨询', '投诉', '建议', '表扬']
```

### 1.2 数据库连接函数
**功能**：建立与MySQL数据库的连接

```python
def get_mysql_connection():
    return mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_db,
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )
```

### 1.3 操作日志记录函数
**功能**：记录用户操作日志，用于审计追踪

```python
def log_action(action, details):
    user = session.get('username', 'anonymous')
    operation_logs.append({
        'user': user,
        'action': action,
        'details': details,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
```

### 1.4 统一登录认证接口
**功能**：支持管理员和普通用户的统一登录认证

```python
@app.route('/api/login', methods=['POST'])
def unified_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # 1. 先检查管理员
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['username'] = username
        session['role'] = 'admin'
        log_action('LOGIN', 'Admin logged in')
        return jsonify({
            'success': True,
            'role': 'admin',
            'username': username,
            'name': '管理员',
            'message': '管理员登录成功'
        })

    # 2. 再查 portal_users 表
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM portal_users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['username'] = username
            session['role'] = 'user'
            session['display_name'] = user.get('name', username)
            return jsonify({
                'success': True,
                'role': 'user',
                'username': username,
                'name': user.get('name', username),
                'message': '登录成功'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
```

### 1.5 用户注册接口
**功能**：处理新用户注册请求

```python
@app.route('/api/register', methods=['POST'])
def user_register():
    data = request.json
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    name = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': '密码至少6位'}), 400
    if username == ADMIN_USERNAME:
        return jsonify({'success': False, 'message': '该用户名已被占用'}), 400

    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id FROM portal_users WHERE username = %s', (username,))
        if cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        cursor.execute('INSERT INTO portal_users (username, password, name, phone) VALUES (%s, %s, %s, %s)',
                       (username, password, name or username, phone))
        conn.commit()
        cursor.close(); conn.close()
        return jsonify({'success': True, 'message': '注册成功，请登录'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
```

### 1.6 用户管理CRUD接口
**功能**：实现用户的增删改查操作

```python
@app.route('/api/users', methods=['GET'])
def get_users():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        search_query = request.args.get('search', '')
        status_filter = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 动态构建查询条件
        count_query = 'SELECT COUNT(*) as total FROM users WHERE 1=1'
        count_params = []
        
        if search_query:
            count_query += ' AND (name LIKE %s OR email LIKE %s OR phone LIKE %s OR department LIKE %s)'
            search_term = '%' + search_query + '%'
            count_params.extend([search_term, search_term, search_term, search_term])
        
        if status_filter:
            count_query += ' AND status = %s'
            count_params.append(status_filter)
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']
        
        # 分页查询
        query = 'SELECT * FROM users WHERE 1=1'
        params = []
        
        if search_query:
            query += ' AND (name LIKE %s OR email LIKE %s OR phone LIKE %s OR department LIKE %s)'
            search_term = '%' + search_query + '%'
            params.extend([search_term, search_term, search_term, search_term])
        
        if status_filter:
            query += ' AND status = %s'
            params.append(status_filter)
        
        query += ' ORDER BY created_at DESC LIMIT %s OFFSET %s'
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'users': users,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 1.7 健康检查接口
**功能**：提供服务健康状态检查，用于监控

```python
@app.route('/api/health', methods=['GET'])
def health_check():
    db_ok = False
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        db_ok = True
    except:
        pass
    uptime = int((datetime.now() - server_start_time).total_seconds())
    return jsonify({
        'status': 'healthy' if db_ok else 'degraded',
        'database': 'connected' if db_ok else 'disconnected',
        'uptime_seconds': uptime,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
```

---

## 二、数据库初始化脚本 (init.sql)

### 2.1 用户表结构
**功能**：存储系统用户信息

```sql
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    department VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 新闻表结构
**功能**：存储政务新闻和公告信息

```sql
CREATE TABLE IF NOT EXISTS news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) DEFAULT '政务动态',
    author VARCHAR(100),
    image_url TEXT,
    status VARCHAR(20) DEFAULT 'published',
    publish_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.3 政务服务表结构
**功能**：存储政务服务项目信息

```sql
CREATE TABLE IF NOT EXISTS services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type VARCHAR(50) DEFAULT '其他',
    icon VARCHAR(20) DEFAULT '📋',
    sort_order INT DEFAULT 999,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.4 用户反馈表结构
**功能**：存储用户反馈信息

```sql
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    type VARCHAR(20) DEFAULT '咨询',
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    reply TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reply_time TIMESTAMP NULL
);
```

### 2.5 前台用户表结构
**功能**：存储门户网站的普通用户登录信息

```sql
CREATE TABLE IF NOT EXISTS portal_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    name VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.6 通知公告表结构
**功能**：存储系统通知公告

```sql
CREATE TABLE IF NOT EXISTS announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    is_top TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 三、Docker部署配置

### 3.1 Docker Compose配置 (docker-compose.yml)
**功能**：定义多容器应用的编排配置

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0.35
    container_name: gov-portal-mysql
    environment:
      MYSQL_ROOT_PASSWORD: trae123
      MYSQL_DATABASE: example_db
      MYSQL_USER: admin
      MYSQL_PASSWORD: trae123
    ports:
      - "3308:3306"
    volumes:
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
      - mysql_data:/var/lib/mysql
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-ptrae123"]
      timeout: 20s
      retries: 10

  flask-app:
    build: .
    container_name: gov-portal-flask
    environment:
      MYSQL_HOST: mysql
      MYSQL_USER: root
      MYSQL_PASSWORD: trae123
      MYSQL_DB: example_db
    ports:
      - "5000:5000"
    depends_on:
      mysql:
        condition: service_healthy
    restart: unless-stopped

volumes:
  mysql_data:
```

### 3.2 Dockerfile配置
**功能**：定义Flask应用的容器镜像构建步骤

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 设置环境变量为UTF-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=utf-8

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

---

## 四、前端核心代码 (index.html)

### 4.1 CSS变量与主题切换
**功能**：定义CSS变量实现主题切换功能

```css
:root {
    --primary: #1a3c6d; --primary-light: #2b5ea7; --accent: #d43030;
    --bg: #f0f2f5; --card: #fff; --text: #2c3e50; --text-secondary: #7f8c8d;
    --border: #e8ecf1; --shadow: 0 2px 12px rgba(0,0,0,0.06);
    --shadow-hover: 0 8px 30px rgba(0,0,0,0.10); --radius: 12px;
    --transition: 0.25s cubic-bezier(0.4,0,0.2,1);
    --topbar-bg: #fff; --table-stripe: #f8fafc;
}
[data-theme="dark"] {
    --bg: #1a1d23; --card: #242730; --text: #e4e6eb; --text-secondary: #9ca3af;
    --primary: #60a5fa; --primary-light: #93bbfd;
    --border: #333840; --shadow: 0 2px 12px rgba(0,0,0,0.3);
    --shadow-hover: 0 8px 30px rgba(0,0,0,0.4);
    --topbar-bg: #242730; --table-stripe: #2a2d37;
    --input-bg: #2a2d37; --input-bg-focus: #303540; --input-border: #444a55;
    --modal-bg: #2a2d37; --hover-bg: #2a2d37;
    --badge-blue-bg: #1a2740; --badge-green-bg: #1a3020; --badge-red-bg: #302020; --badge-orange-bg: #302518; --badge-gray-bg: #2a2a2a;
    --stat-blue-bg: #1a2740; --stat-green-bg: #1a3020; --stat-orange-bg: #302518; --stat-purple-bg: #251a30; --stat-red-bg: #302020;
    --announce-bg: #2d2a18; --announce-border: #4a4520;
    --news-cat-bg: #1a2740; --news-cat-color: #60a5fa;
    --login-card-bg: rgba(36,39,48,0.97); --login-input-bg: #1e2130; --login-input-border: #3a3f4b;
    --detail-bg: #2a2d37; --reply-bg: #1a3020; --reply-border: #2a4a30;
}
```

### 4.2 登录页面样式
**功能**：实现渐变背景的登录页面

```css
.login-wrapper{
    display:flex;
    justify-content:center;
    align-items:center;
    min-height:100vh;
    background:linear-gradient(135deg,#0f1a30,#1a3c6d 40%,#1e4d8c 70%,#15325c);
    position:relative;
    overflow:hidden
}
.login-wrapper::before{
    content:'';
    position:absolute;
    top:-50%;
    left:-50%;
    width:200%;
    height:200%;
    background:radial-gradient(circle at 30% 50%,rgba(255,255,255,0.03),transparent 60%),
               radial-gradient(circle at 70% 20%,rgba(212,48,48,0.06),transparent 50%);
    animation:bgFloat 20s ease-in-out infinite
}
@keyframes bgFloat{
    0%,100%{transform:translate(0,0) rotate(0)}
    50%{transform:translate(2%,1%) rotate(1deg)}
}
```

### 4.3 动态徽章提示样式
**功能**：根据待处理数量动态改变颜色和动画

```css
.badge-count{
    display:inline-flex;
    align-items:center;
    justify-content:center;
    min-width:20px;
    height:20px;
    border-radius:10px;
    background:#dc2626;
    color:#fff;
    font-size:11px;
    font-weight:700;
    padding:0 6px;
    line-height:1;
    transition:all 0.3s ease
}
.badge-count.warning{
    background:#ea580c;
    animation:pulse 1.5s infinite
}
.badge-count.danger{
    background:#991b1b;
    animation:pulse 0.8s infinite
}
@keyframes pulse{
    0%,100%{
        transform:scale(1);
        box-shadow:0 0 0 0 rgba(220,38,38,0.4)
    }
    50%{
        transform:scale(1.1);
        box-shadow:0 0 0 6px rgba(220,38,38,0)
    }
}
```

### 4.4 饼图图表样式
**功能**：实现环形统计图表

```css
.pie-chart{
    width:180px;
    height:180px;
    border-radius:50%;
    margin:0 auto 16px;
    background:conic-gradient(
        #6366f1 0deg,
        #6366f1 calc(var(--active-deg,0)*1deg),
        #8b5cf6 calc(var(--active-deg,0)*1deg),
        #8b5cf6 180deg,
        #06b6d4 180deg,
        #06b6d4 360deg
    );
    position:relative
}
.pie-chart::after{
    content:'';
    position:absolute;
    top:25%;
    left:25%;
    width:50%;
    height:50%;
    border-radius:50%;
    background:#fff
}
```

### 4.5 JavaScript登录处理
**功能**：处理用户登录请求和状态管理

```javascript
async function handleLogin(){
    const u=document.getElementById('username').value.trim();
    const p=document.getElementById('password').value.trim();
    const r=document.getElementById('remember');
    const e=document.getElementById('loginError');
    if(!u||!p){e.textContent='请输入用户名和密码';e.classList.add('show');return}
    try{
        const res=await fetch('/api/login',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({username:u,password:p})
        });
        const d=await res.json();
        if(d.success){
            if(r&&r.checked){localStorage.setItem('remember_user',u)}
            else{localStorage.removeItem('remember_user')}
            if(d.role==='admin'){showAdminDashboard()}
            else{showUserDashboard(d.name||d.username)}
        }else{e.textContent=d.message||'登录失败';e.classList.add('show')}
    }catch(err){e.textContent='网络错误，请稍后重试';e.classList.add('show')}
}
```

### 4.6 动态徽章更新逻辑
**功能**：根据待处理反馈数量动态更新徽章样式

```javascript
const badge=document.getElementById('pendingBadge');
if(badge){
    badge.textContent=pending;
    badge.style.display=pending>0?'inline-flex':'none';
    badge.className='badge-count';
    if(pending>=10)badge.classList.add('danger');
    else if(pending>=5)badge.classList.add('warning')
}
```

### 4.7 主题切换功能
**功能**：实现明暗主题切换

```javascript
function initTheme(){
    const saved=localStorage.getItem('theme');
    const prefersDark=window.matchMedia('(prefers-color-scheme: dark)').matches;
    if(saved==='dark'||(!saved&&prefersDark)){
        document.documentElement.setAttribute('data-theme','dark')
    }
}
function toggleTheme(){
    const isDark=document.documentElement.getAttribute('data-theme')==='dark';
    if(isDark){
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme','light')
    }else{
        document.documentElement.setAttribute('data-theme','dark');
        localStorage.setItem('theme','dark')
    }
}
```

---

## 五、项目依赖 (requirements.txt)

```
Flask==2.3.3
mysql-connector-python==8.0.35
bcrypt==5.0.0
```

---

## 六、技术架构总结

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | HTML5 + CSS3 + JavaScript | 原生实现，无框架依赖 |
| 后端 | Flask (Python) | 轻量级Web框架 |
| 数据库 | MySQL 8.0 | 关系型数据库 |
| 容器化 | Docker + Docker Compose | 应用容器化部署 |
| 部署 | openEuler Linux | 国产操作系统 |

---

*文档生成时间：2026-05-28*
