# AIOffer 会员管理系统

AIOffer 是一个基于现代技术栈构建的会员管理系统，集成了用户管理、订单处理、外部系统对接、支付与积分系统等功能。

## 🛠 技术栈

### 后端 (Backend)
- **语言**: Python 3.8+
- **框架**: FastAPI (高性能异步Web框架)
- **ORM**: SQLAlchemy (Async IO)
- **数据库**: SQLite (默认) / MySQL (支持)
- **认证**: JWT (JSON Web Tokens)
- **其他**: Pydantic, Uvicorn, Aiosqlite

### 前端 (Frontend)
- **框架**: React 18
- **语言**: TypeScript
- **UI库**: Ant Design 5.x
- **构建工具**: Vite
- **状态管理**: Zustand
- **路由**: React Router v6

## 🚀 快速开始

### 1. 基础软件安装

在开始之前，请确保您的系统已安装以下基础服务：

#### Ubuntu / Debian
```bash
# 一键安装所有依赖 (Python3, Node.js, MySQL, Redis)
# 注意：如果使用 NodeSource 源，nodejs 包通常已包含 npm，无需单独安装 npm
sudo apt update
sudo apt install -y python3 python3-pip nodejs mysql-server redis-server
```

#### macOS (需安装 Homebrew)
```bash
brew install python node mysql redis
```

#### Windows
推荐直接下载安装包：
- [Python官网下载](https://www.python.org/downloads/)
- [Node.js官网下载](https://nodejs.org/)
- [MySQL官网下载](https://dev.mysql.com/downloads/installer/)
- Redis: [Windows版下载](https://github.com/tporadowski/redis/releases)

### 2. 后端初始化

```bash
# 进入后端目录
cd backend

# 创建并激活 Conda 环境 (推荐)
conda create -n aioffer python=3.12
conda activate aioffer

# 安装依赖
pip install -r requirements.txt

# 4. 数据库配置 (MySQL)

# 步骤 1: 创建 .env 配置文件
# 在 backend 目录下创建 .env 文件，填入以下内容（请根据实际 MySQL 配置修改）：
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/admin_system
SECRET_KEY=your_secure_secret_key

# 步骤 2: 创建 MySQL 数据库
# 请登录 MySQL 并执行以下命令创建数据库：
# CREATE DATABASE admin_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 步骤 3: 初始化数据
# 运行初始化脚本创建表并插入管理员账号：
python test_db.py

# 启动后端服务
python main.py
# 或者使用 uvicorn (开发模式)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 `http://localhost:8000` 启动。
API 文档地址: `http://localhost:8000/docs`

### 3. 前端初始化

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将在 `http://localhost:5173` 启动。

## 🔑 默认账号

在运行 `test_db.py` 初始化数据库后，可以使用以下管理员账号登录：

- **邮箱**: `admin@example.com`
- **密码**: `123456`

## 📂 项目结构

```
aioffer/
├── backend/                # 后端代码
│   ├── config/             # 配置文件
│   ├── models/             # 数据库模型
│   ├── routers/            # API路由
│   ├── schemas/            # Pydantic数据模式
│   ├── services/           # 业务逻辑服务
│   ├── utils/              # 工具函数
│   ├── main.py             # 入口文件
│   ├── test_db.py          # 数据库初始化脚本
│   └── requirements.txt    # 依赖列表
│
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # 公共组件
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API服务调用
│   │   ├── stores/         # 状态管理
│   │   ├── utils/          # 工具函数 (如 request.ts)
│   │   └── App.tsx         # 主应用组件
│   └── package.json        # 依赖配置
│
└── README.md               # 项目说明文档
```

## ⚙️ 环境配置详解

项目支持通过 `.env` 文件进行灵活配置。请在 `backend` 目录下创建 `.env` 文件，支持的配置项如下：

### 基础与安全
| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `DEBUG` | `True` | 是否开启调试模式 (生产环境建议 False) |
| `SECRET_KEY` | `your-secret-key-here` | JWT签名密钥，**生产环境务必修改** |
| `ALGORITHM` | `HS256` | JWT签名算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access Token 过期时间(分钟) |

### 数据库与缓存
| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `DATABASE_URL` | (MySQL默认) | 完整数据库连接串，支持 MySQL/SQLite |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接字符串 |

### 微信集成 (可选)
| 变量名 | 说明 |
| :--- | :--- |
| `WECHAT_APP_ID` | 微信公众号 AppID |
| `WECHAT_APP_SECRET` | 微信公众号 AppSecret |
| `WECHAT_TOKEN` | 微信服务器配置 Token |
| `WECHAT_ENCODING_AES_KEY` | 消息加解密密钥 |

### 系统服务
| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `HOST` | `0.0.0.0` | 服务监听地址 |
| `PORT` | `8000` | 服务监听端口 |
| `UPLOAD_DIR` | `./uploads` | 文件上传存储目录 |
| `MAX_FILE_SIZE` | `10485760` | 最大文件限制 (10MB) |
| `LOG_LEVEL` | `INFO` | 日志级别 |

**生产环境 .env 示例:**
```ini
DEBUG=False
SECRET_KEY=v3ry-s3cur3-r4nd0m-k3y-h3r3
DATABASE_URL=mysql+pymysql://user:strong_password@db_host:3306/aioffer_prod
REDIS_URL=redis://redis_host:6379/1
LOG_LEVEL=WARNING
```

## ⚠️ 常见问题与排查

1.  **登录报错 "Authentication failed"**:
    *   检查后端服务是否正在运行。
    *   确认数据库 (`test.db`) 是否存在且已初始化。
    *   尝试重新运行 `python test_db.py` 重置管理员账号。

2.  **前端页面 404**:
    *   确保访问的是 `http://localhost:5173`。
    *   检查路由配置 (`App.tsx`)。

3.  **Ant Design 警告**:
    *   控制台可能出现关于 `bodyStyle` 或 `TabPane` 的警告，这是由于 Antd v5 升级导致的，不影响功能使用，已在代码中进行修复适配。

4.  **端口被占用**:
    *   后端默认使用 8000 端口，前端默认使用 5173 端口。如果被占用，请修改配置文件或启动参数。
