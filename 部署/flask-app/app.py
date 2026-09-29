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

def get_mysql_connection():
    return mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_db,
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )

def log_action(action, details):
    user = session.get('username', 'anonymous')
    ip_address = request.remote_addr if request else 'unknown'
    user_agent = request.headers.get('User-Agent', '') if request else ''
    
    operation_logs.append({
        'user': user,
        'action': action,
        'details': details,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip_address': ip_address,
        'user_agent': user_agent
    })
    
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO operation_logs (user, action, details, ip_address, user_agent) VALUES (%s, %s, %s, %s, %s)',
            (user, action, details, ip_address, user_agent)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Failed to write log to database: {e}")

@app.route('/')
def home():
    return render_template('index.html')

# ==================== 统一登录认证 ====================

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

    # 2. 再查 users 表
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = username
            session['role'] = 'user'
            session['display_name'] = user.get('name', username)
            session['user_id'] = user.get('id')
            # 更新最后登录时间
            cursor.execute('UPDATE users SET last_login_time = NOW() WHERE id = %s', (user['id'],))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({
                'success': True,
                'role': 'user',
                'username': username,
                'name': user.get('name', username),
                'message': '登录成功'
            })
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': '登录失败，请稍后重试'}), 500


@app.route('/api/logout', methods=['POST'])
def unified_logout():
    session.clear()
    return jsonify({'success': True, 'message': '已退出登录'})


@app.route('/api/check_auth', methods=['GET'])
def check_auth():
    if 'username' in session:
        return jsonify({
            'authenticated': True,
            'username': session['username'],
            'role': session.get('role', ''),
            'name': session.get('display_name', session['username'])
        })
    return jsonify({'authenticated': False})

# ==================== 用户个人信息 ====================

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    if 'username' not in session or session.get('role') != 'user':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, username, name, email, phone, department, created_at, last_login_time FROM users WHERE username = %s', (session['username'],))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            return jsonify({'success': True, 'profile': user})
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user/profile', methods=['PUT'])
def update_user_profile():
    if 'username' not in session or session.get('role') != 'user':
        return jsonify({'success': False, 'message': '未授权'}), 401
    data = request.json
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        email = (data.get('email') or '').strip() or None
        department = (data.get('department') or '').strip() or None
        cursor.execute(
            'UPDATE users SET name = %s, phone = %s, email = %s, department = %s WHERE username = %s',
            (data.get('name', ''), data.get('phone', ''), email, department, session['username'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        session['display_name'] = data.get('name', session['username'])
        return jsonify({'success': True, 'message': '个人信息更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user/change_password', methods=['POST'])
def user_change_password():
    if 'username' not in session or session.get('role') != 'user':
        return jsonify({'success': False, 'message': '未授权'}), 401
    data = request.json
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    if len(new_pw) < 6:
        return jsonify({'success': False, 'message': '新密码至少6位'})
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (session['username'], old_pw))
        if not cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '原密码错误'})
        cursor.execute('UPDATE users SET password = %s WHERE username = %s', (new_pw, session['username']))
        conn.commit()
        cursor.close(); conn.close()
        return jsonify({'success': True, 'message': '密码修改成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user/my_feedback', methods=['GET'])
def get_my_feedback():
    if 'username' not in session or session.get('role') != 'user':
        return jsonify({'error': '未授权'}), 401
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        name = session.get('display_name', session['username'])
        cursor.execute('SELECT COUNT(*) as total FROM feedback WHERE name = %s', (name,))
        total = cursor.fetchone()['total']
        cursor.execute('SELECT * FROM feedback WHERE name = %s ORDER BY create_time DESC LIMIT %s OFFSET %s', (name, per_page, (page - 1) * per_page))
        items = cursor.fetchall()
        cursor.close(); conn.close()
        return jsonify({'success': True, 'feedback': items, 'total': total, 'page': page, 'per_page': per_page, 'total_pages': max((total + per_page - 1) // per_page, 1)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 密码管理 ====================

@app.route('/api/change_password', methods=['POST'])
def change_password():
    global ADMIN_PASSWORD
    if 'username' not in session:
        return jsonify({'success': False, 'message': '未授权'}), 401
    
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if old_password != ADMIN_PASSWORD:
        return jsonify({'success': False, 'message': '原密码不正确'})
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': '新密码至少6位'})
    
    ADMIN_PASSWORD = new_password
    log_action('CHANGE_PASSWORD', 'Admin changed password')
    return jsonify({'success': True, 'message': '密码修改成功'})

# ==================== 用户注册 ====================

@app.route('/api/register', methods=['POST'])
def user_register():
    data = request.json
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    name = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()
    email = (data.get('email') or '').strip() or None
    department = (data.get('department') or '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': '密码至少6位'}), 400
    if username == ADMIN_USERNAME:
        return jsonify({'success': False, 'message': '该用户名已被占用'}), 400

    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        if email:
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            if cursor.fetchone():
                cursor.close(); conn.close()
                return jsonify({'success': False, 'message': '邮箱已被使用'}), 400
        cursor.execute('INSERT INTO users (username, password, name, phone, email, department) VALUES (%s, %s, %s, %s, %s, %s)',
                       (username, password, name or username, phone, email, department))
        conn.commit()
        cursor.close(); conn.close()
        return jsonify({'success': True, 'message': '注册成功，请登录'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 管理员-用户管理 ====================

# ==================== 通知公告 ====================

@app.route('/api/announcements', methods=['GET'])
def get_announcements():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM announcements ORDER BY is_top DESC, created_at DESC')
        items = cursor.fetchall()
        cursor.close(); conn.close()
        return jsonify({'announcements': items})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/announcements', methods=['POST'])
def add_announcement():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    data = request.json
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO announcements (title, content, is_top) VALUES (%s, %s, %s)',
                       (data.get('title'), data.get('content', ''), data.get('is_top', 0)))
        conn.commit()
        cursor.close(); conn.close()
        log_action('ADD_ANNOUNCEMENT', f'Added announcement: {data.get("title")}')
        return jsonify({'success': True, 'message': '公告已发布'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/announcements/<int:ann_id>', methods=['PUT'])
def update_announcement(ann_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    data = request.json
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE announcements SET title=%s, content=%s, is_top=%s WHERE id=%s',
                       (data.get('title'), data.get('content', ''), data.get('is_top', 0), ann_id))
        conn.commit()
        cursor.close(); conn.close()
        return jsonify({'success': True, 'message': '公告已更新'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/announcements/<int:ann_id>', methods=['DELETE'])
def delete_announcement(ann_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM announcements WHERE id=%s', (ann_id,))
        conn.commit()
        cursor.close(); conn.close()
        return jsonify({'success': True, 'message': '公告已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/public/announcements', methods=['GET'])
def get_public_announcements():
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT title, content, is_top, created_at FROM announcements ORDER BY is_top DESC, created_at DESC LIMIT 3')
        items = cursor.fetchall()
        cursor.close(); conn.close()
        return jsonify({'announcements': items})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        search_query = request.args.get('search', '')
        status_filter = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Count total records
        count_query = 'SELECT COUNT(*) as total FROM users WHERE 1=1'
        count_params = []
        
        if search_query:
            count_query += ' AND (username LIKE %s OR name LIKE %s OR email LIKE %s OR phone LIKE %s OR department LIKE %s)'
            search_term = '%' + search_query + '%'
            count_params.extend([search_term, search_term, search_term, search_term, search_term])
        
        if status_filter:
            count_query += ' AND status = %s'
            count_params.append(status_filter)
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']
        
        # Get paginated results
        query = 'SELECT * FROM users WHERE 1=1'
        params = []
        
        if search_query:
            query += ' AND (username LIKE %s OR name LIKE %s OR email LIKE %s OR phone LIKE %s OR department LIKE %s)'
            search_term = '%' + search_query + '%'
            params.extend([search_term, search_term, search_term, search_term, search_term])
        
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

@app.route('/api/users', methods=['POST'])
def add_user():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '123456').strip()
        
        if not username:
            return jsonify({'success': False, 'message': '用户名不能为空'}), 400
        
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 检查用户名是否存在
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        # 检查邮箱是否存在
        if data.get('email'):
            cursor.execute('SELECT id FROM users WHERE email = %s', (data.get('email'),))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '邮箱已被使用'}), 400
        
        email = (data.get('email') or '').strip() or None
        cursor.execute(
            'INSERT INTO users (username, password, name, email, phone, department, status) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (username, password, data.get('name', username), email, data.get('phone', ''), data.get('department', ''), data.get('status', 'active'))
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()
        log_action('ADD_USER', f'Added user: {username} (ID: {user_id})')
        return jsonify({'success': True, 'message': '用户添加成功', 'user_id': user_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            return jsonify(user)
        else:
            return jsonify({'error': '用户不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 检查用户是否存在
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 如果要修改用户名，检查新用户名是否已存在
        new_username = data.get('username', user['username'])
        if new_username != user['username']:
            cursor.execute('SELECT id FROM users WHERE username = %s AND id != %s', (new_username, user_id))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        # 如果要修改邮箱，检查新邮箱是否已存在
        new_email = data.get('email', user['email'])
        if new_email and new_email != user['email']:
            cursor.execute('SELECT id FROM users WHERE email = %s AND id != %s', (new_email, user_id))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': '邮箱已被使用'}), 400
        
        # 构建更新语句
        update_fields = []
        update_values = []
        
        if data.get('username'):
            update_fields.append('username = %s')
            update_values.append(data.get('username'))
        if data.get('password'):
            update_fields.append('password = %s')
            update_values.append(data.get('password'))
        if 'name' in data:
            update_fields.append('name = %s')
            update_values.append(data.get('name'))
        if 'email' in data:
            update_fields.append('email = %s')
            update_values.append((data.get('email') or '').strip() or None)
        if 'phone' in data:
            update_fields.append('phone = %s')
            update_values.append(data.get('phone'))
        if 'department' in data:
            update_fields.append('department = %s')
            update_values.append(data.get('department'))
        if 'status' in data:
            update_fields.append('status = %s')
            update_values.append(data.get('status'))
        
        if update_fields:
            update_values.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, update_values)
            conn.commit()
        
        cursor.close()
        conn.close()
        log_action('EDIT_USER', f'Updated user ID: {user_id}')
        return jsonify({'success': True, 'message': '用户更新成功'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM users')
        next_id = cursor.fetchone()[0]
        cursor.execute(f'ALTER TABLE users AUTO_INCREMENT = {next_id}')
        conn.commit()
        cursor.close()
        conn.close()
        log_action('DELETE_USER', f'Deleted user ID: {user_id}')
        return jsonify({'success': True, 'message': '用户删除成功'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/batch-delete', methods=['POST'])
def batch_delete_users():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        user_ids = data.get('ids', [])
        
        if not user_ids:
            return jsonify({'success': False, 'message': '未提供用户ID'}), 400
        
        conn = get_mysql_connection()
        cursor = conn.cursor()
        placeholders = ','.join(['%s'] * len(user_ids))
        cursor.execute(f'DELETE FROM users WHERE id IN ({placeholders})', tuple(user_ids))
        cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM users')
        next_id = cursor.fetchone()[0]
        cursor.execute(f'ALTER TABLE users AUTO_INCREMENT = {next_id}')
        conn.commit()
        cursor.close()
        conn.close()
        log_action('BATCH_DELETE', f'Deleted users: {", ".join(map(str, user_ids))}')
        return jsonify({'success': True, 'message': f'成功删除{len(user_ids)}个用户'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<int:user_id>/status', methods=['PUT'])
def toggle_user_status(user_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        new_status = data.get('status', '')
        
        if new_status not in ['active', 'inactive']:
            return jsonify({'success': False, 'message': '无效的状态值'}), 400
        
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET status = %s WHERE id = %s', (new_status, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        log_action('TOGGLE_STATUS', f'User {user_id} status changed to {new_status}')
        status_text = '活跃' if new_status == 'active' else '非活跃'
        return jsonify({'success': True, 'message': f'用户状态已更新为{status_text}'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 部门管理（CRUD） ====================

@app.route('/api/departments', methods=['GET'])
def get_departments():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM departments ORDER BY id')
        depts = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(depts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/departments', methods=['POST'])
def add_department():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    data = request.json
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': '部门名称不能为空'}), 400
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO departments (name) VALUES (%s)', (name,))
        conn.commit()
        dept_id = cursor.lastrowid
        cursor.close()
        conn.close()
        log_action('ADD_DEPT', f'Added department: {name}')
        return jsonify({'success': True, 'message': '部门添加成功', 'id': dept_id}), 201
    except mysql.connector.IntegrityError:
        return jsonify({'success': False, 'message': '部门名称已存在'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/departments/<int:dept_id>', methods=['PUT'])
def update_department(dept_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    data = request.json
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': '部门名称不能为空'}), 400
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE departments SET name = %s WHERE id = %s', (name, dept_id))
        conn.commit()
        cursor.close()
        conn.close()
        log_action('EDIT_DEPT', f'Updated department ID: {dept_id}')
        return jsonify({'success': True, 'message': '部门更新成功'})
    except mysql.connector.IntegrityError:
        return jsonify({'success': False, 'message': '部门名称已存在'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/departments/<int:dept_id>', methods=['DELETE'])
def delete_department(dept_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET department = NULL WHERE department = (SELECT name FROM departments WHERE id = %s)', (dept_id,))
        cursor.execute('DELETE FROM departments WHERE id = %s', (dept_id,))
        conn.commit()
        cursor.close()
        conn.close()
        log_action('DELETE_DEPT', f'Deleted department ID: {dept_id}')
        return jsonify({'success': True, 'message': '部门删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 快速部署支持（模板功能） ====================

@app.route('/api/admin/export-template', methods=['GET'])
def export_template():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        template = {
            'version': '1.0',
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'departments': [],
            'services': [],
            'news_categories': NEWS_CATEGORIES
        }
        
        cursor.execute('SELECT name FROM departments ORDER BY id')
        depts = cursor.fetchall()
        template['departments'] = [d['name'] for d in depts]
        
        cursor.execute('SELECT name, description, type, icon, sort_order FROM services ORDER BY sort_order')
        services = cursor.fetchall()
        template['services'] = services
        
        cursor.close()
        conn.close()
        
        log_action('EXPORT_TEMPLATE', 'Exported system template')
        return jsonify(template)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/import-template', methods=['POST'])
def import_template():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        if 'departments' in data:
            for dept_name in data['departments']:
                try:
                    cursor.execute('INSERT IGNORE INTO departments (name) VALUES (%s)', (dept_name,))
                except Exception:
                    pass
        
        if 'services' in data:
            for service in data['services']:
                try:
                    cursor.execute(
                        'INSERT IGNORE INTO services (name, description, type, icon, sort_order) VALUES (%s, %s, %s, %s, %s)',
                        (service.get('name'), service.get('description', ''), service.get('type', '其他'), 
                         service.get('icon', '📋'), service.get('sort_order', 999))
                    )
                except Exception:
                    pass
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_action('IMPORT_TEMPLATE', 'Imported system template')
        return jsonify({'success': True, 'message': '模板导入成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/reset-demo', methods=['POST'])
def reset_demo_data():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM news WHERE author = 'demo'")
        cursor.execute("DELETE FROM services WHERE name IN ('企业开办', '税务办理', '社保服务', '医疗服务', '教育服务', '住房服务')")
        cursor.execute("DELETE FROM departments WHERE name IN ('技术部', '财务部', '人事部', '市场部', '运营部', '行政部')")
        
        demo_depts = ['技术部', '财务部', '人事部', '市场部', '运营部', '行政部']
        for dept in demo_depts:
            cursor.execute('INSERT IGNORE INTO departments (name) VALUES (%s)', (dept,))
        
        demo_services = [
            ('企业开办', '一站式企业注册服务，包含工商注册、税务登记、社保开户等', '企业开办', '🏢', 1),
            ('税务办理', '在线办理税务申报、发票管理、税收优惠申请等业务', '税务办理', '📊', 2),
            ('社保服务', '社保查询、缴费、转移、退休申请等服务', '社保服务', '💼', 3),
            ('医疗服务', '医保查询、定点医院管理、医疗费用报销等', '医疗服务', '🏥', 4),
            ('教育服务', '学籍查询、招生报名、教育资助申请等', '教育服务', '📚', 5),
            ('住房服务', '公积金查询、贷款申请、租房补贴等服务', '住房服务', '🏠', 6)
        ]
        for service in demo_services:
            cursor.execute(
                'INSERT IGNORE INTO services (name, description, type, icon, sort_order) VALUES (%s, %s, %s, %s, %s)',
                service
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_action('RESET_DEMO', 'Reset demo data')
        return jsonify({'success': True, 'message': '演示数据重置成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 公开接口：注册页面获取部门列表（无需登录）
@app.route('/api/departments/public', methods=['GET'])
def get_departments_public():
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name FROM departments ORDER BY id')
        depts = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(depts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 角色权限管理API ====================

@app.route('/api/admin/roles', methods=['GET'])
def get_roles():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM roles')
        roles = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'roles': roles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/roles', methods=['POST'])
def create_role():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        name = (data.get('name') or '').strip()
        description = data.get('description', '')
        
        if not name:
            return jsonify({'success': False, 'message': '角色名称不能为空'}), 400
        
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO roles (name, description) VALUES (%s, %s)', (name, description))
        conn.commit()
        role_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        log_action('CREATE_ROLE', f'Created role: {name}')
        return jsonify({'success': True, 'message': '角色创建成功', 'id': role_id})
    except mysql.connector.IntegrityError:
        return jsonify({'success': False, 'message': '角色名称已存在'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/permissions', methods=['GET'])
def get_permissions():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM permissions')
        permissions = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'permissions': permissions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/roles/<int:role_id>/permissions', methods=['GET'])
def get_role_permissions(role_id):
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT p.id, p.name, p.display_name 
            FROM permissions p 
            JOIN role_permissions rp ON p.id = rp.permission_id 
            WHERE rp.role_id = %s
        ''', (role_id,))
        permissions = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'permissions': permissions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/roles/<int:role_id>/permissions', methods=['PUT'])
def update_role_permissions(role_id):
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        permission_ids = data.get('permissions', [])
        
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM role_permissions WHERE role_id = %s', (role_id,))
        
        for perm_id in permission_ids:
            cursor.execute('INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)', (role_id, perm_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_action('UPDATE_ROLE_PERMISSIONS', f'Updated permissions for role ID: {role_id}')
        return jsonify({'success': True, 'message': '角色权限更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
def update_user_role(user_id):
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        role = (data.get('role') or '').strip()
        
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET role = %s WHERE id = %s', (role, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        log_action('UPDATE_USER_ROLE', f'Updated user {user_id} role to: {role}')
        return jsonify({'success': True, 'message': '用户角色更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user/permissions', methods=['GET'])
def get_current_user_permissions():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        role = session.get('role', 'user')
        
        if role == 'admin':
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT name FROM permissions')
            permissions = [p['name'] for p in cursor.fetchall()]
            cursor.close()
            conn.close()
            return jsonify({'permissions': permissions})
        
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT p.name 
            FROM permissions p 
            JOIN role_permissions rp ON p.id = rp.permission_id 
            JOIN roles r ON rp.role_id = r.id 
            WHERE r.name = %s
        ''', (role,))
        permissions = [p['name'] for p in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return jsonify({'permissions': permissions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/department_stats', methods=['GET'])
def get_department_stats():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT department, COUNT(*) as count 
            FROM users 
            WHERE department IS NOT NULL AND department != "" 
            GROUP BY department 
            ORDER BY count DESC
        ''')
        stats = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monthly_stats', methods=['GET'])
def get_monthly_stats():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT DATE_FORMAT(created_at, '%Y-%m') as month, COUNT(*) as count 
            FROM users 
            WHERE created_at IS NOT NULL 
            GROUP BY DATE_FORMAT(created_at, '%Y-%m') 
            ORDER BY month DESC 
            LIMIT 12
        ''')
        stats = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status_stats', methods=['GET'])
def get_status_stats():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM users 
            GROUP BY status
        ''')
        stats = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/export', methods=['GET'])
def export_users():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name, email, phone, department, status, created_at FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        log_action('EXPORT_USERS', 'Exported all users')
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "active"')
        active = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "inactive"')
        inactive = cursor.fetchone()[0]
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at) = %s", (today,))
        today_new = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT department) FROM users WHERE department IS NOT NULL AND department != ''")
        department_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'total': total,
            'active': active,
            'inactive': inactive,
            'today': today_new,
            'departments': department_count,
            'api_calls': len(operation_logs)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    start = (page - 1) * per_page
    end = start + per_page
    paginated_logs = operation_logs[::-1][start:end]
    return jsonify({
        'logs': paginated_logs,
        'total': len(operation_logs),
        'page': page,
        'per_page': per_page,
        'total_pages': (len(operation_logs) + per_page - 1) // per_page
    })

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    global operation_logs
    operation_logs = []
    log_action('CLEAR_LOGS', 'Cleared all operation logs')
    return jsonify({'success': True, 'message': '日志清除成功'}), 200

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy'})

# ==================== 安全运维功能 ====================

@app.route('/api/admin/backup', methods=['POST'])
def create_backup():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        import subprocess
        import os
        
        backup_dir = '/tmp/backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'{backup_dir}/backup_{timestamp}.sql'
        
        cmd = f"mysqldump -h mysql -u root -ptrae123 example_db > {backup_file}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            file_size = os.path.getsize(backup_file)
            
            conn = get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO backup_records (backup_type, file_path, file_size) VALUES (%s, %s, %s)',
                ('full', backup_file, file_size)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            log_action('BACKUP', f'Created backup: {backup_file} ({file_size} bytes)')
            return jsonify({'success': True, 'message': '备份成功', 'file_path': backup_file, 'file_size': file_size})
        else:
            return jsonify({'success': False, 'message': f'备份失败: {result.stderr}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/backups', methods=['GET'])
def get_backup_records():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM backup_records ORDER BY created_at DESC')
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'backups': records})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/backup/<int:backup_id>/restore', methods=['POST'])
def restore_backup(backup_id):
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT file_path FROM backup_records WHERE id = %s', (backup_id,))
        backup = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not backup:
            return jsonify({'success': False, 'message': '备份文件不存在'}), 404
        
        import subprocess
        cmd = f"mysql -h mysql -u root -ptrae123 example_db < {backup['file_path']}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            log_action('RESTORE', f'Restored from backup: {backup["file_path"]}')
            return jsonify({'success': True, 'message': '恢复成功'})
        else:
            return jsonify({'success': False, 'message': f'恢复失败: {result.stderr}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 系统配置API ====================

@app.route('/api/admin/config', methods=['GET'])
def get_system_config():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT key_name, key_value, description FROM system_config')
        configs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        config_dict = {}
        for config in configs:
            config_dict[config['key_name']] = {
                'value': config['key_value'],
                'description': config['description']
            }
        
        return jsonify({'config': config_dict})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/config', methods=['PUT'])
def update_system_config():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        for key, value in data.items():
            cursor.execute(
                'UPDATE system_config SET key_value = %s WHERE key_name = %s',
                (value, key)
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_action('UPDATE_CONFIG', f'Updated config: {data}')
        return jsonify({'success': True, 'message': '配置更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 日志审计API ====================

@app.route('/api/admin/logs', methods=['GET'])
def get_audit_logs():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        offset = (page - 1) * per_page
        
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('SELECT COUNT(*) as total FROM operation_logs')
        total = cursor.fetchone()['total']
        
        cursor.execute('SELECT * FROM operation_logs ORDER BY created_at DESC LIMIT %s OFFSET %s', (per_page, offset))
        logs = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': max((total + per_page - 1) // per_page, 1)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/logs/search', methods=['GET'])
def search_audit_logs():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        keyword = request.args.get('keyword', '')
        action = request.args.get('action', '')
        user = request.args.get('user', '')
        
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = 'SELECT * FROM operation_logs WHERE 1=1'
        params = []
        
        if keyword:
            query += ' AND (details LIKE %s OR user LIKE %s)'
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        if action:
            query += ' AND action = %s'
            params.append(action)
        if user:
            query += ' AND user LIKE %s'
            params.append(f'%{user}%')
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'logs': logs, 'total': len(logs)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/logs/export', methods=['GET'])
def export_audit_logs():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM operation_logs ORDER BY created_at DESC')
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '用户', '操作', '详情', 'IP地址', '用户代理', '时间'])
        
        for log in logs:
            writer.writerow([
                log['id'],
                log['user'],
                log['action'],
                log['details'],
                log['ip_address'],
                log['user_agent'],
                log['created_at']
            ])
        
        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 政务新闻管理 ====================

@app.route('/api/news', methods=['GET'])
def get_news():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        count_query = 'SELECT COUNT(*) as total FROM news WHERE status = "published"'
        count_params = []
        
        if category:
            count_query += ' AND category = %s'
            count_params.append(category)
        
        if search:
            count_query += ' AND (title LIKE %s OR content LIKE %s)'
            search_term = '%' + search + '%'
            count_params.extend([search_term, search_term])
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']
        
        query = 'SELECT * FROM news WHERE status = "published"'
        params = []
        
        if category:
            query += ' AND category = %s'
            params.append(category)
        
        if search:
            query += ' AND (title LIKE %s OR content LIKE %s)'
            search_term = '%' + search + '%'
            params.extend([search_term, search_term])
        
        query += ' ORDER BY publish_time DESC LIMIT %s OFFSET %s'
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        news_list = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'news': news_list,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/news/<int:news_id>', methods=['GET'])
def get_news_detail(news_id):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM news WHERE id = %s', (news_id,))
        news = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if news:
            return jsonify(news)
        else:
            return jsonify({'error': '新闻不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/news', methods=['POST'])
def add_news():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO news (title, content, category, author, image_url, status, publish_time) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (data.get('title'), data.get('content'), data.get('category', '政务动态'), 
             session.get('username'), data.get('image_url', ''), 'published', datetime.now())
        )
        conn.commit()
        news_id = cursor.lastrowid
        cursor.close()
        conn.close()
        log_action('ADD_NEWS', f'Added news: {data.get("title")} (ID: {news_id})')
        return jsonify({'success': True, 'message': '新闻添加成功', 'news_id': news_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/news/<int:news_id>', methods=['PUT'])
def update_news(news_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        conn = get_mysql_connection()
        cursor = conn.cursor()
        if 'title' in data and 'content' in data:
            cursor.execute(
                'UPDATE news SET title=%s, content=%s, category=%s, image_url=%s, status=%s WHERE id=%s',
                (data.get('title'), data.get('content'), data.get('category'), data.get('image_url',''), data.get('status'), news_id)
            )
        else:
            fields=[];vals=[]
            for k in ['status','image_url','title','content','category']:
                if k in data: fields.append(f'{k}=%s');vals.append(data[k])
            if fields:
                vals.append(news_id)
                cursor.execute(f'UPDATE news SET {", ".join(fields)} WHERE id=%s', vals)
        conn.commit()
        cursor.close()
        conn.close()
        log_action('UPDATE_NEWS', f'Updated news ID: {news_id}')
        return jsonify({'success': True, 'message': '新闻更新成功'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/news/<int:news_id>', methods=['DELETE'])
def delete_news(news_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM news WHERE id = %s', (news_id,))
        conn.commit()
        cursor.close()
        conn.close()
        log_action('DELETE_NEWS', f'Deleted news ID: {news_id}')
        return jsonify({'success': True, 'message': '新闻删除成功'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 政务服务管理 ====================

@app.route('/api/services', methods=['GET'])
def get_services():
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM services ORDER BY sort_order ASC')
        services = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(services)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/services/<int:service_id>', methods=['GET'])
def get_service_detail(service_id):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM services WHERE id = %s', (service_id,))
        service = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if service:
            return jsonify(service)
        else:
            return jsonify({'error': '服务不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/services', methods=['POST'])
def add_service():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO services (name, description, type, icon, sort_order) VALUES (%s, %s, %s, %s, %s)',
            (data.get('name'), data.get('description'), data.get('type', '其他'), 
             data.get('icon', '📋'), data.get('sort_order', 999))
        )
        conn.commit()
        service_id = cursor.lastrowid
        cursor.close()
        conn.close()
        log_action('ADD_SERVICE', f'Added service: {data.get("name")} (ID: {service_id})')
        return jsonify({'success': True, 'message': '服务添加成功', 'service_id': service_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/services/<int:service_id>', methods=['PUT'])
def update_service(service_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE services SET name = %s, description = %s, type = %s, icon = %s, sort_order = %s WHERE id = %s',
            (data.get('name'), data.get('description'), data.get('type'), 
             data.get('icon'), data.get('sort_order'), service_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        log_action('UPDATE_SERVICE', f'Updated service ID: {service_id}')
        return jsonify({'success': True, 'message': '服务更新成功'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/services/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM services WHERE id = %s', (service_id,))
        conn.commit()
        cursor.close()
        conn.close()
        log_action('DELETE_SERVICE', f'Deleted service ID: {service_id}')
        return jsonify({'success': True, 'message': '服务删除成功'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 用户反馈管理 ====================

@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        feedback_type = request.args.get('type', '')
        status = request.args.get('status', '')
        
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        count_query = 'SELECT COUNT(*) as total FROM feedback WHERE 1=1'
        count_params = []
        
        if feedback_type:
            count_query += ' AND type = %s'
            count_params.append(feedback_type)
        
        if status:
            count_query += ' AND status = %s'
            count_params.append(status)
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']
        
        query = 'SELECT * FROM feedback WHERE 1=1'
        params = []
        
        if feedback_type:
            query += ' AND type = %s'
            params.append(feedback_type)
        
        if status:
            query += ' AND status = %s'
            params.append(status)
        
        query += ' ORDER BY create_time DESC LIMIT %s OFFSET %s'
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        feedback_list = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'feedback': feedback_list,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.json
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO feedback (name, phone, email, type, content, status, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (data.get('name'), data.get('phone', ''), data.get('email', ''), 
             data.get('type', '咨询'), data.get('content'), 'pending', datetime.now())
        )
        conn.commit()
        feedback_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': '反馈提交成功', 'feedback_id': feedback_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/feedback/<int:feedback_id>', methods=['PUT'])
def update_feedback(feedback_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE feedback SET status = %s, reply = %s, reply_time = %s WHERE id = %s',
            (data.get('status', 'pending'), data.get('reply', ''), 
             datetime.now() if data.get('status') == 'processed' else None, feedback_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        log_action('UPDATE_FEEDBACK', f'Updated feedback ID: {feedback_id}')
        return jsonify({'success': True, 'message': '反馈更新成功'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/feedback/<int:feedback_id>', methods=['DELETE'])
def delete_feedback(feedback_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM feedback WHERE id = %s', (feedback_id,))
        conn.commit()
        cursor.close()
        conn.close()
        log_action('DELETE_FEEDBACK', f'Deleted feedback ID: {feedback_id}')
        return jsonify({'success': True, 'message': '反馈删除成功'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 政务统计 ====================

@app.route('/api/gov_stats', methods=['GET'])
def get_gov_stats():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # 新闻统计
        cursor.execute('SELECT COUNT(*) FROM news WHERE status = "published"')
        news_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM news WHERE DATE(publish_time) = CURDATE()')
        news_today = cursor.fetchone()[0]
        
        # 服务统计
        cursor.execute('SELECT COUNT(*) FROM services')
        service_count = cursor.fetchone()[0]
        
        # 反馈统计
        cursor.execute('SELECT COUNT(*) FROM feedback')
        feedback_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM feedback WHERE status = "pending"')
        feedback_pending = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM feedback WHERE status = "processed"')
        feedback_processed = cursor.fetchone()[0]
        
        # 用户统计
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        # 分类统计
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM news 
            WHERE status = "published"
            GROUP BY category
        ''')
        news_category_stats = []
        for row in cursor.fetchall():
            news_category_stats.append({'category': row[0], 'count': row[1]})
        
        # 反馈类型统计
        cursor.execute('''
            SELECT type, COUNT(*) as count 
            FROM feedback 
            GROUP BY type
        ''')
        feedback_type_stats = []
        for row in cursor.fetchall():
            feedback_type_stats.append({'type': row[0], 'count': row[1]})
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'news': {
                'total': news_count,
                'today': news_today,
                'category_stats': news_category_stats
            },
            'services': {
                'total': service_count
            },
            'feedback': {
                'total': feedback_count,
                'pending': feedback_pending,
                'processed': feedback_processed,
                'type_stats': feedback_type_stats
            },
            'users': {
                'total': user_count
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 获取分类列表 ====================

@app.route('/api/categories/news', methods=['GET'])
def get_news_categories():
    return jsonify(NEWS_CATEGORIES)

@app.route('/api/categories/services', methods=['GET'])
def get_service_types():
    return jsonify(SERVICE_TYPES)

@app.route('/api/categories/feedback', methods=['GET'])
def get_feedback_types():
    return jsonify(FEEDBACK_TYPES)

# ==================== 请求计数器 ====================

@app.before_request
def count_request():
    global request_count
    request_count += 1

# ==================== 系统监控 ====================

@app.route('/api/system/info', methods=['GET'])
def get_system_info():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT TABLE_NAME as table_name, TABLE_ROWS as table_rows FROM information_schema.tables WHERE table_schema = %s", (mysql_db,))
        tables = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM news")
        news_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM feedback WHERE status = 'pending'")
        pending_count = cursor.fetchone()['count']
        cursor.close()
        conn.close()
        
        uptime_seconds = (datetime.now() - server_start_time).total_seconds()
        return jsonify({
            'success': True,
            'system': {
                'start_time': server_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'uptime_seconds': int(uptime_seconds),
                'uptime_display': f'{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m {int(uptime_seconds % 60)}s',
                'request_count': request_count,
                'user_count': user_count,
                'news_count': news_count,
                'pending_feedback': pending_count,
                'log_count': len(operation_logs),
                'db_tables': [{'name': t['table_name'], 'rows': t['table_rows']} for t in tables]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 新闻导出 ====================

@app.route('/api/news/export', methods=['GET'])
def export_news():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM news ORDER BY publish_time DESC')
        news_list = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(news_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 博客模块 ====================

@app.route('/api/blogs', methods=['GET'])
def get_blogs():
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        cursor.execute('SELECT COUNT(*) as total FROM blogs WHERE status = %s', ('published',))
        total = cursor.fetchone()['total']
        cursor.execute('SELECT b.*, (SELECT COUNT(*) FROM blog_comments WHERE blog_id=b.id) as comment_count FROM blogs b WHERE b.status = %s ORDER BY b.created_at DESC LIMIT %s OFFSET %s',
                       ('published', per_page, offset))
        blogs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'blogs': blogs, 'total': total, 'page': page, 'per_page': per_page, 'total_pages': max((total + per_page - 1) // per_page, 1)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/blogs', methods=['POST'])
def create_blog():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        title = (data.get('title') or '').strip()
        content = (data.get('content') or '').strip()
        if not title or not content:
            return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        
        # 检查用户角色，管理员直接发布，普通用户需审核
        role = session.get('role', 'user')
        status = 'published' if role == 'admin' else 'pending'
        
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO blogs (user_id, username, title, content, images, status) VALUES (%s, %s, %s, %s, %s, %s)',
                       (user_id, session['username'], title, content, data.get('images', ''), status))
        conn.commit()
        blog_id = cursor.lastrowid
        cursor.close()
        conn.close()
        log_action('CREATE_BLOG', f'Created blog: {title} (status: {status})')
        
        message = '博客发布成功' if status == 'published' else '博客已提交，等待审核'
        return jsonify({'success': True, 'message': message, 'blog_id': blog_id, 'status': status}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/blogs/<int:blog_id>', methods=['GET'])
def get_blog_detail(blog_id):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('UPDATE blogs SET views = views + 1 WHERE id = %s', (blog_id,))
        cursor.execute('SELECT b.*, (SELECT COUNT(*) FROM blog_comments WHERE blog_id=b.id) as comment_count FROM blogs b WHERE b.id = %s', (blog_id,))
        blog = cursor.fetchone()
        if not blog:
            cursor.close(); conn.close()
            return jsonify({'error': '博客不存在'}), 404
        cursor.execute('SELECT * FROM blog_comments WHERE blog_id = %s ORDER BY created_at ASC', (blog_id,))
        comments = cursor.fetchall()
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'blog': blog, 'comments': comments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/blogs/<int:blog_id>', methods=['PUT'])
def update_blog(blog_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        title = (data.get('title') or '').strip()
        content = (data.get('content') or '').strip()
        if not title or not content:
            return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM blogs WHERE id = %s', (blog_id,))
        blog = cursor.fetchone()
        if not blog:
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '博客不存在'}), 404
        if str(blog['user_id']) != str(session.get('user_id')):
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '无权编辑'}), 403
        cursor.execute('UPDATE blogs SET title=%s, content=%s, images=%s WHERE id=%s',
                       (title, content, data.get('images', ''), blog_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': '博客更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/blogs/<int:blog_id>', methods=['DELETE'])
def delete_blog(blog_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM blogs WHERE id = %s', (blog_id,))
        blog = cursor.fetchone()
        if not blog:
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '博客不存在'}), 404
        if session.get('role') != 'admin' and str(blog['user_id']) != str(session.get('user_id')):
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '无权删除'}), 403
        cursor.execute('DELETE FROM blogs WHERE id = %s', (blog_id,))
        conn.commit()
        cursor.close()
        conn.close()
        log_action('DELETE_BLOG', f'Deleted blog ID: {blog_id}')
        return jsonify({'success': True, 'message': '博客删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/blogs/<int:blog_id>/like', methods=['POST'])
def toggle_like_blog(blog_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM blog_likes WHERE blog_id = %s AND user_id = %s', (blog_id, user_id))
        if cursor.fetchone():
            cursor.execute('DELETE FROM blog_likes WHERE blog_id = %s AND user_id = %s', (blog_id, user_id))
            cursor.execute('UPDATE blogs SET likes = likes - 1 WHERE id = %s', (blog_id,))
            conn.commit()
            cursor.close(); conn.close()
            return jsonify({'success': True, 'liked': False, 'message': '已取消点赞'})
        else:
            cursor.execute('INSERT INTO blog_likes (blog_id, user_id) VALUES (%s, %s)', (blog_id, user_id))
            cursor.execute('UPDATE blogs SET likes = likes + 1 WHERE id = %s', (blog_id,))
            conn.commit()
            cursor.close(); conn.close()
            return jsonify({'success': True, 'liked': True, 'message': '点赞成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/blogs/<int:blog_id>/comments', methods=['POST'])
def add_blog_comment(blog_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        content = (data.get('content') or '').strip()
        if not content:
            return jsonify({'success': False, 'message': '评论内容不能为空'}), 400
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '请先登录'}), 401
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO blog_comments (blog_id, user_id, username, content) VALUES (%s, %s, %s, %s)',
                       (blog_id, user_id, session['username'], content))
        conn.commit()
        comment_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': '评论成功', 'comment_id': comment_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/blogs/<int:blog_id>/comments/<int:comment_id>', methods=['DELETE'])
def delete_blog_comment(blog_id, comment_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM blog_comments WHERE id = %s', (comment_id,))
        comment = cursor.fetchone()
        if not comment:
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '评论不存在'}), 404
        if session.get('role') != 'admin' and str(comment['user_id']) != str(session.get('user_id')):
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '无权删除'}), 403
        cursor.execute('DELETE FROM blog_comments WHERE id = %s', (comment_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': '评论删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/my_blogs', methods=['GET'])
def get_my_blogs():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        cursor.execute('SELECT COUNT(*) as total FROM blogs WHERE username = %s', (session['username'],))
        total = cursor.fetchone()['total']
        cursor.execute('SELECT * FROM blogs WHERE username = %s ORDER BY created_at DESC LIMIT %s OFFSET %s',
                       (session['username'], per_page, offset))
        blogs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'blogs': blogs, 'total': total})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 好友模块 ====================

@app.route('/api/friends', methods=['GET'])
def get_friends():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify([])
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT u.id, u.username, u.name, u.email, u.department, f.created_at as friend_since
            FROM friends f
            JOIN users u ON (f.friend_id = u.id AND f.user_id = %s) OR (f.user_id = u.id AND f.friend_id = %s)
            WHERE u.id != %s AND f.status = 'accepted'
            ORDER BY f.created_at DESC
        ''', (user_id, user_id, user_id))
        friends = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(friends)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/friends/add', methods=['POST'])
def add_friend():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        friend_username = (data.get('username') or '').strip()
        if not friend_username:
            return jsonify({'success': False, 'message': '请输入好友用户名'}), 400
        if friend_username == session['username']:
            return jsonify({'success': False, 'message': '不能添加自己为好友'}), 400
        user_id = session.get('user_id')
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id FROM users WHERE username = %s', (friend_username,))
        friend = cursor.fetchone()
        if not friend:
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        friend_id = friend['id']
        cursor.execute('SELECT * FROM friends WHERE (user_id=%s AND friend_id=%s) OR (user_id=%s AND friend_id=%s)',
                       (user_id, friend_id, friend_id, user_id))
        if cursor.fetchone():
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': '已经是好友了'}), 400
        cursor.execute('INSERT INTO friends (user_id, friend_id) VALUES (%s, %s)', (user_id, friend_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': '好友添加成功'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/friends/<int:friend_id>', methods=['DELETE'])
def remove_friend(friend_id):
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        user_id = session.get('user_id')
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM friends WHERE (user_id=%s AND friend_id=%s) OR (user_id=%s AND friend_id=%s)',
                       (user_id, friend_id, friend_id, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': '好友已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/search', methods=['GET'])
def search_users():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        q = request.args.get('q', '').strip()
        if not q:
            return jsonify([])
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, username, name, department FROM users WHERE username LIKE %s OR name LIKE %s LIMIT 10',
                       (f'%{q}%', f'%{q}%'))
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 管理员博客管理 ====================

@app.route('/api/admin/blogs', methods=['GET'])
def admin_get_blogs():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status', 'all')
        search_query = request.args.get('q', '').strip()
        offset = (page - 1) * per_page
        
        # 构建查询条件
        where_clause = []
        params = []
        
        if status != 'all':
            where_clause.append('status = %s')
            params.append(status)
        
        if search_query:
            where_clause.append('(title LIKE %s OR username LIKE %s)')
            params.append(f'%{search_query}%')
            params.append(f'%{search_query}%')
        
        where_sql = ' WHERE ' + ' AND '.join(where_clause) if where_clause else ''
        
        # 获取总数
        cursor.execute(f'SELECT COUNT(*) as total FROM blogs{where_sql}', params)
        total = cursor.fetchone()['total']
        
        # 获取博客列表
        cursor.execute(f'SELECT b.*, (SELECT COUNT(*) FROM blog_comments WHERE blog_id=b.id) as comment_count FROM blogs b{where_sql} ORDER BY b.created_at DESC LIMIT %s OFFSET %s',
                       params + [per_page, offset])
        blogs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'blogs': blogs, 'total': total, 'page': page, 'total_pages': max((total + per_page - 1) // per_page, 1)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 博客审核API ====================

@app.route('/api/admin/blogs/pending', methods=['GET'])
def admin_get_pending_blogs():
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT COUNT(*) as total FROM blogs WHERE status = %s', ('pending',))
        total = cursor.fetchone()['total']
        cursor.execute('SELECT b.*, (SELECT COUNT(*) FROM blog_comments WHERE blog_id=b.id) as comment_count FROM blogs b WHERE b.status = %s ORDER BY b.created_at DESC', ('pending',))
        blogs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'blogs': blogs, 'total': total})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/blogs/<int:blog_id>/approve', methods=['POST'])
def admin_approve_blog(blog_id):
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE blogs SET status = %s WHERE id = %s', ('published', blog_id))
        conn.commit()
        cursor.close()
        conn.close()
        log_action('APPROVE_BLOG', f'Approved blog ID: {blog_id}')
        return jsonify({'success': True, 'message': '博客审核通过'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/blogs/<int:blog_id>/reject', methods=['POST'])
def admin_reject_blog(blog_id):
    if 'username' not in session or session.get('role') != 'admin':
        return jsonify({'error': '未授权'}), 401
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE blogs SET status = %s WHERE id = %s', ('rejected', blog_id))
        conn.commit()
        cursor.close()
        conn.close()
        log_action('REJECT_BLOG', f'Rejected blog ID: {blog_id}')
        return jsonify({'success': True, 'message': '博客已拒绝'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 图片上传 ====================
import base64

@app.route('/api/upload', methods=['POST'])
def upload_image():
    if 'username' not in session:
        return jsonify({'error': '未授权'}), 401
    try:
        data = request.json
        image_data = data.get('image', '')
        if not image_data:
            return jsonify({'success': False, 'message': '未提供图片数据'}), 400
        if image_data.startswith('data:image/'):
            header, encoded = image_data.split(',', 1)
            img_data = base64.b64decode(encoded)
            ext = header.split('/')[1].split(';')[0]
            import uuid
            filename = f"upload_{uuid.uuid4().hex[:12]}.{ext}"
            upload_dir = os.path.join(app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(img_data)
            url = f'/static/uploads/{filename}'
            return jsonify({'success': True, 'url': url})
        return jsonify({'success': False, 'message': '无效的图片格式'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
