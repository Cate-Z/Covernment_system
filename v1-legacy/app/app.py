from flask import Flask, jsonify, request
import mysql.connector
import os

app = Flask(__name__)

# MySQL配置
mysql_host = os.environ.get('MYSQL_HOST', 'mysql')
mysql_user = os.environ.get('MYSQL_USER', 'root')
mysql_password = os.environ.get('MYSQL_PASSWORD', 'trae123')
mysql_db = os.environ.get('MYSQL_DB', 'example_db')

def get_mysql_connection():
    return mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_db
    )

@app.route('/')
def home():
    return jsonify({
        'message': '欢迎来到鲲鹏云计算实训项目',
        'status': 'success'
    })

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def add_user():
    try:
        data = request.json
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (name, email) VALUES (%s, %s)',
            (data['name'], data['email'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'User added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)