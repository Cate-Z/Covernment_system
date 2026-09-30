-- ============================================================
-- 政务数字门户平台 —— PostgreSQL(Supabase) 数据库初始化脚本
-- 用法：Supabase 控制台 → SQL Editor → 粘贴执行（只需执行一次）
-- 说明：本脚本由 MySQL 版 init.sql 转换而来，
--       AUTO_INCREMENT -> SERIAL，TINYINT -> SMALLINT，
--       ON UPDATE CURRENT_TIMESTAMP -> TIMESTAMPTZ + 触发器
--       保留字列 "user" 统一加双引号
-- ============================================================

-- ============ 统一用户表（合并前台用户和管理端用户）============
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NULL UNIQUE,
    phone VARCHAR(20),
    department VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    role VARCHAR(20) DEFAULT 'user',
    last_login_time TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 插入测试用户（账号/密码沿用旧版）
INSERT INTO users (username, password, name, email, phone, department, status) VALUES
('zhangsan', '123456', '张三', 'zhangsan@example.com', '13800138001', '技术部', 'active'),
('lisi', '123456', '李四', 'lisi@example.com', '13800138002', '财务部', 'active'),
('wangwu', '123456', '王五', 'wangwu@example.com', '13800138003', '人事部', 'active'),
('zhaoliu', '123456', '赵六', 'zhaoliu@example.com', '13800138004', '市场部', 'inactive'),
('qianqi', '123456', '钱七', 'qianqi@example.com', '13800138005', '技术部', 'active')
ON CONFLICT (username) DO NOTHING;

-- ============ 部门表 ============
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO departments (name) VALUES
('技术部'), ('财务部'), ('人事部'), ('市场部'), ('运营部'), ('行政部')
ON CONFLICT (name) DO NOTHING;

-- ============ 新闻表 ============
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) DEFAULT '政务动态',
    author VARCHAR(100),
    image_url TEXT,
    status VARCHAR(20) DEFAULT 'published',
    publish_time TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO news (title, content, category, author, publish_time) VALUES
('政务服务平台升级通知', '为提升服务质量，政务服务平台将于2024年1月15日进行系统升级维护，期间部分服务将暂停。请广大市民提前做好相关业务办理安排。', '通知公告', 'admin', '2024-01-10 09:00:00'),
('新政策解读：企业开办一网通办', '近日，市政务服务中心推出企业开办一网通办服务，申请人只需登录一个平台，即可完成企业注册全流程。', '政策法规', 'admin', '2024-01-09 14:30:00'),
('政务大厅办事指南', '政务服务大厅地址：XX市XX区XX路XX号，工作时间：周一至周五 9:00-17:00（法定节假日除外）。', '办事指南', 'admin', '2024-01-08 10:00:00'),
('我市社保服务实现全程网办', '从本月起，我市社保业务已实现全程网上办理，市民无需前往办事大厅，在家即可完成社保查询、缴费等业务。', '政务动态', 'admin', '2024-01-07 15:00:00'),
('政务公开信息发布', '根据政务公开要求，现将我市2023年度财政预算执行情况予以公开，欢迎市民监督。', '政务公开', 'admin', '2024-01-06 11:00:00');

-- ============ 政务服务表 ============
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type VARCHAR(50) DEFAULT '其他',
    icon VARCHAR(20) DEFAULT '📋',
    sort_order INT DEFAULT 999,
    created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO services (name, description, type, icon, sort_order) VALUES
('企业开办', '一站式企业注册服务，包含工商注册、税务登记、社保开户等', '企业开办', '🏢', 1),
('税务办理', '在线办理税务申报、发票管理、税收优惠申请等业务', '税务办理', '📊', 2),
('社保服务', '社保查询、缴费、转移、退休申请等服务', '社保服务', '💼', 3),
('医疗服务', '医保查询、定点医院管理、医疗费用报销等', '医疗服务', '🏥', 4),
('教育服务', '学籍查询、招生报名、教育资助申请等', '教育服务', '📚', 5),
('住房服务', '公积金查询、贷款申请、租房补贴等服务', '住房服务', '🏠', 6);

-- ============ 用户反馈表 ============
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    type VARCHAR(20) DEFAULT '咨询',
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    reply TEXT,
    create_time TIMESTAMPTZ DEFAULT now(),
    reply_time TIMESTAMPTZ NULL
);

INSERT INTO feedback (name, phone, email, type, content, status, reply, reply_time) VALUES
('市民A', '13900139001', 'shiminA@example.com', '咨询', '请问企业开办需要哪些材料？', 'processed', '您好，企业开办需要提供法人身份证、公司章程、注册地址证明等材料，具体可在办事指南中查看详细清单。', '2024-01-10 10:00:00'),
('市民B', '13900139002', 'shiminB@example.com', '建议', '希望能增加更多在线办理业务，方便市民办事。', 'pending', NULL, NULL),
('市民C', '13900139003', 'shiminC@example.com', '投诉', '上次去政务大厅办事，排队时间太长了。', 'pending', NULL, NULL),
('市民D', '13900139004', 'shiminD@example.com', '表扬', '政务服务态度很好，办事效率高，点赞！', 'processed', '感谢您的认可，我们会继续努力提升服务质量！', '2024-01-09 16:00:00');

-- ============ 通知公告表 ============
CREATE TABLE IF NOT EXISTS announcements (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    is_top SMALLINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO announcements (title, content, is_top) VALUES
('政务服务平台升级通知', '政务数字门户平台已完成全面升级，新增在线反馈、个人中心等功能模块，欢迎广大市民使用。', 1),
('温馨提示', '请广大市民注意防范电信诈骗，政务服务热线为12345。', 0);

-- ============ 博客表 ============
CREATE TABLE IF NOT EXISTS blogs (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    images TEXT,
    likes INT DEFAULT 0,
    views INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'published',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============ 博客评论表 ============
CREATE TABLE IF NOT EXISTS blog_comments (
    id SERIAL PRIMARY KEY,
    blog_id INT NOT NULL,
    user_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    FOREIGN KEY (blog_id) REFERENCES blogs(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============ 好友关系表 ============
CREATE TABLE IF NOT EXISTS friends (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    friend_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'accepted',
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT unique_friendship UNIQUE (user_id, friend_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (friend_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============ 博客点赞记录表 ============
CREATE TABLE IF NOT EXISTS blog_likes (
    id SERIAL PRIMARY KEY,
    blog_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT unique_like UNIQUE (blog_id, user_id),
    FOREIGN KEY (blog_id) REFERENCES blogs(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============ 操作日志表（安全审计）============
-- 注意：user 是 PostgreSQL 保留字，列名必须加双引号
CREATE TABLE IF NOT EXISTS operation_logs (
    id SERIAL PRIMARY KEY,
    "user" VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    details TEXT,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============ 系统配置表 ============
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL UNIQUE,
    key_value TEXT,
    description VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO system_config (key_name, key_value, description) VALUES
('site_name', '政务数字门户平台', '站点名称'),
('site_description', '政务服务一站式平台', '站点描述'),
('session_timeout', '3600', 'Session超时时间（秒）'),
('max_upload_size', '10485760', '最大上传文件大小（字节）')
ON CONFLICT (key_name) DO NOTHING;

-- ============ 数据备份记录表 ============
CREATE TABLE IF NOT EXISTS backup_records (
    id SERIAL PRIMARY KEY,
    backup_type VARCHAR(20) DEFAULT 'full',
    file_path VARCHAR(255),
    file_size INT,
    status VARCHAR(20) DEFAULT 'success',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============ 角色表 ============
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO roles (name, description) VALUES
('admin', '超级管理员 - 拥有所有权限'),
('dept_admin', '部门管理员 - 管理本部门用户'),
('user', '普通用户 - 基本操作权限')
ON CONFLICT (name) DO NOTHING;

-- ============ 权限表 ============
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    description VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO permissions (name, display_name, description) VALUES
('manage_users', '用户管理', '管理系统用户'),
('manage_dept', '部门管理', '管理部门信息'),
('manage_news', '新闻管理', '发布和管理新闻'),
('manage_service', '服务管理', '管理政务服务'),
('manage_feedback', '反馈管理', '处理用户反馈'),
('manage_blog', '博客管理', '审核和管理博客'),
('view_logs', '查看日志', '查看操作日志'),
('manage_config', '配置管理', '管理系统配置'),
('backup_data', '数据备份', '执行数据备份'),
('publish_blog', '发布博客', '发布博客文章')
ON CONFLICT (name) DO NOTHING;

-- ============ 角色权限关联表 ============
CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    CONSTRAINT unique_role_permission UNIQUE (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- admin：全部权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- dept_admin：部分权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'dept_admin' AND p.name IN ('manage_users', 'manage_dept', 'view_logs')
ON CONFLICT DO NOTHING;

-- user：基础权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'user' AND p.name IN ('publish_blog')
ON CONFLICT DO NOTHING;

-- ============ updated_at 自动更新触发器（替代 MySQL 的 ON UPDATE CURRENT_TIMESTAMP）============
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_blogs_updated_at ON blogs;
CREATE TRIGGER trg_blogs_updated_at BEFORE UPDATE ON blogs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_system_config_updated_at ON system_config;
CREATE TRIGGER trg_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
