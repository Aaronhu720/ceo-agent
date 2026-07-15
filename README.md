# CEO Agent - 企业 AI 合伙人

面向企业创始人的长期型 AI Agent 系统。具备长期记忆、企业知识库、自动任务提取、项目管理、决策记录、Heartbeat 自动巡检、每日早报/晚间复盘等功能。

## 技术栈

### 后端
- Python 3.12 + FastAPI
- PostgreSQL 16 + pgvector
- Redis 7
- Celery (异步任务 + 定时调度)
- SQLAlchemy 2 + Alembic
- JWT 认证 + RBAC

### 前端
- Next.js 15 + React 19
- TypeScript (strict)
- Tailwind CSS
- TanStack Query + Zustand
- PWA 支持

### AI 层
- 统一模型适配层 (OpenAI / Anthropic / Gemini)
- 记忆评估器 (Memory Evaluator)
- 上下文构建器 (Context Builder)
- 流式输出 (SSE)

## 快速开始

### 1. 克隆并配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少填入一个 AI 模型的 API Key
```

### 2. Docker 启动

```bash
docker-compose up -d
```

服务列表：
| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 3000 | Next.js 前端 |
| Backend | 8000 | FastAPI 后端 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 + 队列 |
| MinIO | 9000/9001 | 对象存储 |
| Nginx | 80 | 反向代理 |

### 3. 初始化数据库

```bash
# 进入后端容器
docker exec -it ceoagent-backend bash

# 创建表和初始数据
python -m app.utils.init_db

# 或使用 Alembic 迁移
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### 4. 访问系统

- 前端: http://localhost:3000
- API 文档: http://localhost:8000/api/docs
- MinIO 控制台: http://localhost:9001

### 5. 注册第一个用户

打开前端注册页面，创建账户时会自动创建组织。

## 本地开发

### 后端开发

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```
ceo-agent/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # API 端点
│   │   ├── core/                # 配置、安全、依赖
│   │   ├── models/              # SQLAlchemy 数据模型 (23张表)
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── model_gateway.py # 统一AI模型适配
│   │   │   ├── chat_service.py  # CEO Agent 对话服务
│   │   │   ├── context_builder.py # 上下文组装
│   │   │   └── memory_evaluator.py # 记忆评估
│   │   ├── workers/             # Celery 异步任务
│   │   └── utils/               # 工具函数
│   ├── migrations/              # Alembic 迁移
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js 页面
│   │   │   ├── auth/login/      # 登录/注册
│   │   │   └── (dashboard)/     # 仪表板
│   │   │       ├── chat/        # CEO Agent 对话
│   │   │       ├── daily/       # 今日经营
│   │   │       ├── tasks/       # 任务管理
│   │   │       ├── projects/    # 项目管理
│   │   │       ├── decisions/   # 决策中心
│   │   │       ├── memories/    # 记忆中心
│   │   │       ├── files/       # 文件中心
│   │   │       ├── agents/      # Agent 管理
│   │   │       ├── heartbeat/   # Heartbeat 规则
│   │   │       ├── notifications/ # 通知中心
│   │   │       ├── approvals/   # 审批中心
│   │   │       ├── audit/       # 操作日志
│   │   │       └── settings/    # 系统设置
│   │   ├── components/          # 组件
│   │   ├── lib/                 # API 客户端、工具
│   │   ├── stores/              # Zustand 状态
│   │   └── types/               # TypeScript 类型
│   └── public/
├── docker/
│   └── nginx.conf
├── docker-compose.yml
└── .env.example
```

## 数据模型 (23张表)

| 表名 | 说明 |
|------|------|
| organizations | 组织 |
| users | 用户 |
| roles | 角色 (RBAC) |
| conversations | 对话 |
| messages | 消息 |
| memories | 长期记忆 |
| memory_relations | 记忆关联 |
| entities | 企业实体 |
| entity_relations | 实体关联 |
| tasks | 任务 |
| projects | 项目 |
| project_updates | 项目更新 |
| decisions | 决策 |
| agents | Agent 配置 |
| agent_runs | Agent 运行记录 |
| agent_steps | Agent 执行步骤 |
| heartbeat_rules | Heartbeat 规则 |
| heartbeat_runs | Heartbeat 运行记录 |
| daily_logs | 日报 |
| notifications | 通知 |
| approvals | 审批 |
| files | 文件 |
| audit_logs | 审计日志 |

## API 端点

所有 API 以 `/api` 为前缀。完整文档见 `/api/docs`。

- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 登录
- `GET /api/auth/me` - 当前用户
- `GET/POST /api/conversations` - 对话列表/创建
- `POST /api/conversations/{id}/messages` - 发送消息 (SSE 流式响应)
- `GET/POST /api/memories` - 记忆管理
- `POST /api/memories/{id}/confirm` - 确认记忆
- `GET/POST /api/tasks` - 任务管理
- `GET/POST /api/projects` - 项目管理
- `GET/POST /api/decisions` - 决策管理
- `POST /api/decisions/{id}/approve` - 批准决策
- `GET /api/agents` - Agent 列表
- `GET /api/heartbeat-rules` - Heartbeat 规则
- `POST /api/files/presign` - 文件上传预签名
- `GET /api/notifications` - 通知列表
- `GET /api/approvals` - 审批列表
- `GET /api/audit-logs` - 审计日志

## 生产部署

建议部署在新加坡区域 (AWS AP-Southeast-1 / 阿里云新加坡)。

1. 配置生产 `.env`
2. 使用 `docker-compose -f docker-compose.prod.yml up -d`
3. 配置 HTTPS (Nginx + Let's Encrypt)
4. 配置数据库备份
5. 配置日志监控

## 备份与恢复

```bash
# 备份数据库
docker exec ceoagent-postgres pg_dump -U ceoagent ceoagent > backup.sql

# 恢复数据库
docker exec -i ceoagent-postgres psql -U ceoagent ceoagent < backup.sql
```

## 后续规划

- [ ] 产品资料库
- [ ] 图片 OCR
- [ ] 语音输入
- [ ] 知识图谱可视化
- [ ] 子 Agent (Amazon, eBay, Walmart, etc.)
- [ ] 电商平台 API 对接
- [ ] Google Drive / Gmail 集成
- [ ] React Native 移动端
- [ ] 数据看板
