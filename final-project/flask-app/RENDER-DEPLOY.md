# 部署到 Render + Supabase

## 1. Supabase：建库

1. Supabase 控制台新建 Project（区域选 Singapore / Tokyo，离国内近）。
2. **Project Settings → Database → Connection string → URI**，复制连接串，形如
   `postgresql://postgres.<ref>:<密码>@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres`
3. **SQL Editor → New query**，粘贴 `init_postgres.sql` 全文，Run。
   执行成功后应有 16 张表（users / news / services / feedback / announcements / blogs …）。
4. 端口选择建议：Render 是长驻进程，用 **5432（直连）** 或 **6543（Session pooler）** 均可；
   若遇到连接不稳定，优先改用 6543。

## 2. Render：创建 Web Service

推荐用仓库根目录的 `render.yaml`（Blueprint），免手工配置：

**Render Dashboard → New → Blueprint → 连接 GitHub 仓库 → Apply**

若选择手工创建，按下表填写：

| 配置项 | 值 |
|---|---|
| Repository | `Cate-Z/Covernment_system` |
| Region | Singapore |
| Branch | `main` |
| Root Directory | `final-project/flask-app` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 60` |
| Instance Type | Free |
| Health Check Path | `/api/health` |

环境变量（Environment）：

| 变量 | 值 | 说明 |
|---|---|---|
| `DATABASE_URL` | 第 1 步复制的连接串 | 必填，Supabase 连接信息 |
| `DB_CONNECT_TIMEOUT` | `8` | 可选，连接超时秒数 |
| `DB_CONNECT_RETRIES` | `1` | 可选，失败重试次数（给冷启动留一次机会） |
| `DB_RETRY_DELAY` | `2` | 可选，重试前等待秒数 |

## 3. 验证

部署日志出现 `Your service is live` 后访问 `https://<服务名>.onrender.com`：

- **数据库正常**：页面加载无黄色提示，登录 `admin / admin123` 或 `zhangsan / 123456`，各模块可用。
- **数据库休眠**（Supabase 免费套餐 7 天无访问后触发）：页面照常渲染，顶部出现黄色提示条，
  所有读写接口返回 `503 + code=DB_UNAVAILABLE`，**不会出现 500 崩溃页**。

## 已知限制

- Render Free 实例 15 分钟无访问会休眠，首次访问需要等待约 30~60 秒冷启动。
- Render Free 实例磁盘是临时的，备份生成的 JSON 文件重启后会丢失（属正常现象，功能本身可用）。
- Supabase 免费项目连续 7 天无访问会被暂停，需在 Supabase 控制台手动恢复。
