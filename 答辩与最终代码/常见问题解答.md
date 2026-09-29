# 政务数字门户平台 — 常见问题解答

---

## 一、部署相关问题

### Q1: 一键部署脚本执行失败怎么办？
**A**：请检查：
1. 虚拟机是否有 sudo 权限
2. 是否能访问互联网（ping baidu.com）
3. 执行 `chmod +x setup.sh` 确保脚本有执行权限
4. 手动执行脚本中的命令，定位具体错误

### Q2: 无法拉取 Docker 镜像？
**A**：
1. 检查网络连通性
2. 确认已配置国内镜像加速
3. 尝试使用手机热点

### Q3: 访问网站显示 500 错误？
**A**：
1. 检查 Flask 容器日志：`docker logs gov-portal-flask`
2. 确认 MySQL 容器已启动且健康
3. 检查防火墙设置，切换为 iptables 模式

### Q4: 容器启动后立即退出？
**A**：
1. 查看容器日志：`docker logs 容器名`
2. 检查端口是否被占用
3. 确认数据卷挂载正确

---

## 二、功能使用问题

### Q1: 登录失败，提示用户名或密码错误？
**A**：
- 管理员账号：admin / admin123
- 普通用户：zhangsan / 123456（或自行注册）
- 注意密码大小写

### Q2: 注册时提示用户名已存在？
**A**：请更换其他用户名，用户名需唯一

### Q3: 发布博客后看不到？
**A**：普通用户发布的博客需要管理员审核通过后才能显示

### Q4: 如何审核博客？
**A**：管理员登录后，进入"博客管理"→"待审核"，点击通过或拒绝

### Q5: 反馈提交后如何查看处理状态？
**A**：用户可在"个人主页"→"反馈"中查看自己提交的反馈及处理状态

---

## 三、技术相关问题

### Q1: 系统支持多少并发用户？
**A**：当前配置下支持约 1000 并发用户，可通过调整 Flask 线程数扩展

### Q2: 数据如何备份？
**A**：
- 自动：Docker Volume 持久化存储
- 手动：`docker exec gov-portal-mysql mysqldump -u root -ptrae123 example_db > backup.sql`

### Q3: 如何修改管理员密码？
**A**：管理员登录后，进入"系统设置"→"修改密码"

### Q4: 如何添加新部门？
**A**：管理员登录后，进入"部门管理"→"添加部门"

### Q5: 操作日志可以导出吗？
**A**：可以，管理员进入"操作日志"页面，点击导出按钮下载 CSV 文件

---

## 四、网络相关问题

### Q1: 虚拟机内可以访问，外部无法访问？
**A**：
1. 检查防火墙是否开放 5000 端口
2. 确认虚拟机网络模式（桥接模式需配置正确）
3. 检查路由配置

### Q2: 如何实现外网访问？
**A**：使用 cpolar 内网穿透：
```bash
curl -L https://www.cpolar.com/static/downloads/install-release-cpolar.sh | sudo bash
cpolar authtoken 你的token
nohup cpolar http 5000 &
```

### Q3: SSH 连接失败？
**A**：
1. 检查 SSH 服务是否启动：`systemctl status sshd`
2. 检查防火墙是否开放 22 端口
3. 确认虚拟机 IP 地址正确

---

## 五、运维维护问题

### Q1: 如何重启服务？
**A**：
```bash
docker restart gov-portal-mysql gov-portal-flask
```

### Q2: 如何更新代码？
**A**：
1. 在本地修改代码
2. 使用 scp 同步到虚拟机
3. 重建 Docker 镜像并重启容器

### Q3: 如何查看系统运行状态？
**A**：
```bash
docker ps                    # 查看容器状态
docker logs -f gov-portal-flask  # 实时查看日志
```

### Q4: 服务器重启后服务会自动启动吗？
**A**：是的，已配置 `--restart unless-stopped`，容器会随 Docker 自动启动

### Q5: 如何清理日志？
**A**：
```bash
docker logs --tail 0 -f gov-portal-flask  # 清空日志
```

---

## 六、项目结构说明

### 核心文件说明

| 文件 | 说明 |
|------|------|
| app.py | Flask 后端主程序，包含所有 API |
| templates/index.html | 前端主页面（单页应用） |
| static/css/style.css | 样式文件 |
| static/js/app.js | 前端逻辑 |
| docker-compose.yml | Docker 编排配置 |
| init.sql | 数据库初始化脚本 |

### 目录结构
```
flask-app/
├── app.py              # Flask主程序
├── Dockerfile          # Docker镜像构建
├── docker-compose.yml  # 容器编排
├── init.sql            # 数据库初始化
├── static/             # 静态资源
│   ├── css/style.css
│   └── js/app.js
└── templates/          # 模板文件
    └── index.html
```

---

## 七、常见错误码说明

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 401 | 未授权 | 请先登录 |
| 403 | 权限不足 | 检查用户角色 |
| 404 | 资源不存在 | 检查请求路径 |
| 500 | 服务器错误 | 查看 Flask 日志 |

---

*文档版本：v1.0 | 更新日期：2026-06-04*