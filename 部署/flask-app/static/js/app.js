// 全局变量
let users = [];
let deleteUserId = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadUsers();
    setupEventListeners();
});

// 设置事件监听器
function setupEventListeners() {
    // 导航链接点击事件
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
            this.classList.add('active');
            
            const targetId = this.getAttribute('href').substring(1);
            document.querySelectorAll('section').forEach(section => {
                section.style.display = 'none';
            });
            document.getElementById(targetId).style.display = 'block';
        });
    });

    // 添加用户表单提交
    document.getElementById('addUserForm').addEventListener('submit', function(e) {
        e.preventDefault();
        addUser();
    });
}

// 加载用户列表
function loadUsers() {
    fetch('/api/users')
        .then(response => response.json())
        .then(data => {
            users = data;
            renderUserTable();
            updateUserCount();
        })
        .catch(error => {
            showToast('加载用户失败: ' + error.message, 'error');
        });
}

// 渲染用户表格
function renderUserTable() {
    const tbody = document.getElementById('userTableBody');
    const emptyState = document.getElementById('emptyState');
    
    if (users.length === 0) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${user.id}</td>
            <td>${user.name}</td>
            <td>${user.email}</td>
            <td>${user.created_at || '-'}</td>
            <td>
                <div class="actions">
                    <button class="btn btn-secondary" onclick="showDeleteModal(${user.id})">删除</button>
                </div>
            </td>
        </tr>
    `).join('');
}

// 更新用户数量
function updateUserCount() {
    const countElement = document.getElementById('userCount');
    countElement.textContent = users.length;
}

// 搜索用户
function searchUsers() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    
    if (!searchTerm) {
        renderUserTable();
        return;
    }
    
    const filteredUsers = users.filter(user => 
        user.name.toLowerCase().includes(searchTerm) ||
        user.email.toLowerCase().includes(searchTerm)
    );
    
    const tbody = document.getElementById('userTableBody');
    const emptyState = document.getElementById('emptyState');
    
    if (filteredUsers.length === 0) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        emptyState.innerHTML = '<p>未找到匹配的用户</p>';
        return;
    }
    
    emptyState.style.display = 'none';
    
    tbody.innerHTML = filteredUsers.map(user => `
        <tr>
            <td>${user.id}</td>
            <td>${user.name}</td>
            <td>${user.email}</td>
            <td>${user.created_at || '-'}</td>
            <td>
                <div class="actions">
                    <button class="btn btn-secondary" onclick="showDeleteModal(${user.id})">删除</button>
                </div>
            </td>
        </tr>
    `).join('');
}

// 显示添加用户弹窗
function showAddModal() {
    document.getElementById('addModal').style.display = 'block';
    document.getElementById('name').value = '';
    document.getElementById('email').value = '';
    document.getElementById('name').focus();
}

// 关闭添加弹窗
function closeModal() {
    document.getElementById('addModal').style.display = 'none';
}

// 添加用户
function addUser() {
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    
    if (!name || !email) {
        showToast('请填写完整信息', 'error');
        return;
    }
    
    fetch('/api/users', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email })
    })
    .then(response => {
        if (response.ok) {
            showToast('用户添加成功', 'success');
            closeModal();
            loadUsers();
        } else {
            response.json().then(data => {
                showToast('添加失败: ' + (data.error || '未知错误'), 'error');
            });
        }
    })
    .catch(error => {
        showToast('添加失败: ' + error.message, 'error');
    });
}

// 显示删除确认弹窗
function showDeleteModal(userId) {
    deleteUserId = userId;
    document.getElementById('deleteModal').style.display = 'block';
}

// 关闭删除弹窗
function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
    deleteUserId = null;
}

// 确认删除用户
function confirmDelete() {
    if (!deleteUserId) return;
    
    fetch(`/api/users/${deleteUserId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (response.ok) {
            showToast('用户删除成功', 'success');
            closeDeleteModal();
            loadUsers();
        } else {
            response.json().then(data => {
                showToast('删除失败: ' + (data.error || '未知错误'), 'error');
            });
        }
    })
    .catch(error => {
        showToast('删除失败: ' + error.message, 'error');
    });
}

// 显示Toast消息
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 点击弹窗外部关闭弹窗
window.addEventListener('click', function(e) {
    const addModal = document.getElementById('addModal');
    const deleteModal = document.getElementById('deleteModal');
    
    if (e.target === addModal) {
        closeModal();
    }
    if (e.target === deleteModal) {
        closeDeleteModal();
    }
});