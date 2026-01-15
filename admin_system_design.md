# 会员管理系统设计文档

## 项目概述

本文档描述了一个功能完整的会员管理系统设计，支持用户管理、权限控制、支付系统、外部页面系统集成等核心功能。

## 技术栈选择

### 后端技术栈
- **Python 3.11+**: 主要编程语言
- **FastAPI**: 现代异步Web框架，性能优秀，自动API文档
- **SQLAlchemy 2.0**: ORM框架，支持异步操作
- **MySQL 8.0**: 主数据库，支持复杂查询和事务
- **Redis**: 缓存层，会话存储，分布式锁
- **Celery**: 异步任务队列，处理耗时操作
- **Alembic**: 数据库迁移工具
- **Pydantic**: 数据验证和序列化
- **JWT**: 身份认证
- **bcrypt**: 密码加密

### 前端技术栈
- **React 18**: 前端框架
- **TypeScript**: 类型安全
- **Ant Design Pro**: 企业级UI组件库
- **Zustand**: 状态管理
- **React Query**: 数据获取和缓存
- **React Router v6**: 路由管理

### 部署和运维
- **Nginx**: 反向代理和静态文件服务
- **Gunicorn**: WSGI服务器
- **Supervisor**: 进程管理

## 系统架构设计

### 整体架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 (React)   │────│   API网关       │────│   业务服务       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 模块划分
1. **认证授权模块**: 用户注册、登录、权限管理
2. **用户管理模块**: 用户信息、会员等级、积分系统
3. **菜单管理模块**: 动态菜单配置、权限绑定
4. **支付模块**: 充值、消费、订单管理
5. **外部页面系统集成模块**: 页面嵌入、SSO集成
6. **系统管理模块**: 系统配置、日志管理

## 数据库设计

### 核心数据表

#### 用户表 (users)
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    full_name VARCHAR(100),
    avatar_url VARCHAR(255),
    phone VARCHAR(20),
    status TINYINT DEFAULT 1, -- 1:正常, 2:禁用, 3:删除
    user_type TINYINT DEFAULT 1, -- 1:普通用户, 2:会员, 3:管理员
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 用户认证表 (user_auths)
```sql
CREATE TABLE user_auths (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    auth_type VARCHAR(20) NOT NULL, -- 'email', 'wechat', 'wechat_qr', 'phone'
    auth_key VARCHAR(100), -- 邮箱、手机号、微信openid等
    auth_secret VARCHAR(255), -- 密码、微信unionid等
    wechat_nickname VARCHAR(100),
    wechat_avatar VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY unique_auth (auth_type, auth_key)
);
```

#### 会员信息表 (members)
```sql
CREATE TABLE members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    member_level INT DEFAULT 1,
    points INT DEFAULT 0,
    balance DECIMAL(10,2) DEFAULT 0.00,
    expired_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 角色表 (roles)
```sql
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 权限表 (permissions)
```sql
CREATE TABLE permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 菜单表 (menus)
```sql
CREATE TABLE menus (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    path VARCHAR(100),
    component VARCHAR(100),
    icon VARCHAR(50),
    parent_id INT,
    sort_order INT DEFAULT 0,
    is_visible BOOLEAN DEFAULT TRUE,
    permission_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES menus(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id)
);
```

#### 订单表 (orders)
```sql
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(32) UNIQUE NOT NULL,
    user_id INT,
    product_id INT,
    product_type VARCHAR(20), -- 'points', 'member', 'service'
    amount DECIMAL(10,2) NOT NULL,
    quantity INT DEFAULT 1,
    status TINYINT DEFAULT 1, -- 1:待支付, 2:已支付, 3:已取消, 4:已退款
    payment_method VARCHAR(20),
    payment_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 点数消费记录表 (point_transactions)
```sql
CREATE TABLE point_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    type TINYINT NOT NULL, -- 1:充值, 2:消费, 3:退款
    points INT NOT NULL,
    balance_after INT NOT NULL,
    description TEXT,
    related_id INT, -- 关联订单ID或其他业务ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 外部系统配置表 (external_systems)
```sql
CREATE TABLE external_systems (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    system_type VARCHAR(20) NOT NULL, -- 'api', 'page', 'iframe'
    page_url VARCHAR(255), -- 页面系统集成时的URL
    api_key VARCHAR(255),
    api_secret VARCHAR(255),
    endpoint_url VARCHAR(255),
    config JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 系统配置表 (system_configs)
```sql
CREATE TABLE system_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 索引设计
```sql
-- 用户相关索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_user_auths_type_key ON user_auths(auth_type, auth_key);

-- 订单相关索引
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- 点数记录索引
CREATE INDEX idx_point_transactions_user_id ON point_transactions(user_id);
CREATE INDEX idx_point_transactions_created_at ON point_transactions(created_at);
```

## 多种登录方式设计

### 支持的登录方式
1. **邮箱登录**: 传统邮箱+密码登录
2. **微信一键登录**: 基于微信OAuth2.0授权
3. **微信扫码登录**: 生成二维码扫码登录
4. **手机号登录**: 手机号+验证码登录
5. **用户名登录**: 用户名+密码登录

### 微信登录流程
```
1. 用户点击微信登录
2. 跳转到微信授权页面
3. 用户确认授权
4. 获取微信openid和access_token
5. 查询是否已绑定用户
6. 已绑定: 直接登录
7. 未绑定: 创建新用户并绑定微信信息
8. 生成JWT token返回前端
```

### 扫码登录实现
```typescript
// 微信扫码登录组件
const WeChatQRLogin: React.FC = () => {
  const [qrCodeUrl, setQrCodeUrl] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  useEffect(() => {
    // 获取扫码登录二维码
    generateQRCode().then(codeUrl => {
      setQrCodeUrl(codeUrl);
      setIsLoading(false);
      // 开始轮询扫码状态
      startPollingScanStatus();
    });
  }, []);
  
  const startPollingScanStatus = () => {
    const interval = setInterval(async () => {
      const status = await checkScanStatus();
      if (status.scanned) {
        clearInterval(interval);
        // 处理登录成功
        handleLoginSuccess(status.token);
      }
    }, 2000);
  };
  
  return (
    <div className="wechat-qr-login">
      {isLoading ? (
        <Loading />
      ) : (
        <img src={qrCodeUrl} alt="微信扫码登录" />
      )}
      <p>请使用微信扫描二维码登录</p>
    </div>
  );
};
```

### 后端认证接口设计
```python
# 多种登录方式统一接口
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    if request.auth_type == "email":
        return await email_login(request.email, request.password)
    elif request.auth_type == "wechat":
        return await wechat_login(request.code)
    elif request.auth_type == "wechat_qr":
        return await wechat_qr_login(request.scene_id)
    elif request.auth_type == "phone":
        return await phone_login(request.phone, request.sms_code)
    else:
        raise HTTPException(status_code=400, detail="不支持的登录方式")

# 微信登录处理
async def wechat_login(code: str):
    # 1. 用code换取access_token和openid
    token_info = await get_wechat_access_token(code)
    
    # 2. 查询用户认证信息
    user_auth = await get_user_auth_by_wechat(token_info.openid)
    
    if not user_auth:
        # 3. 新用户注册
        user = await create_user_from_wechat(token_info)
        user_auth = await bind_wechat_auth(user.id, token_info)
    
    # 4. 生成JWT token
    access_token = create_access_token(user_auth.user_id)
    
    return {"access_token": access_token, "token_type": "bearer"}
```

## API接口设计

### 认证相关接口
```
POST   /api/auth/register          # 用户注册
POST   /api/auth/login             # 用户登录（支持多种方式）
POST   /api/auth/logout            # 用户登出
POST   /api/auth/refresh           # 刷新token
GET    /api/auth/profile           # 获取用户信息
PUT    /api/auth/profile           # 更新用户信息
POST   /api/auth/change-password   # 修改密码
POST   /api/auth/wechat/bind       # 绑定微信账号
POST   /api/auth/phone/send-sms    # 发送手机验证码
POST   /api/auth/phone/verify     # 验证手机验证码
```

### 用户管理接口
```
GET    /api/users                  # 获取用户列表
GET    /api/users/{id}             # 获取用户详情
POST   /api/users                  # 创建用户
PUT    /api/users/{id}             # 更新用户
DELETE /api/users/{id}             # 删除用户
GET    /api/users/{id}/points      # 获取用户点数记录
POST   /api/users/{id}/recharge    # 用户充值
```

### 权限管理接口
```
GET    /api/roles                  # 获取角色列表
POST   /api/roles                  # 创建角色
PUT    /api/roles/{id}             # 更新角色
DELETE /api/roles/{id}             # 删除角色
GET    /api/permissions            # 获取权限列表
POST   /api/roles/{id}/permissions # 分配权限
```

### 菜单管理接口
```
GET    /api/menus                  # 获取菜单树
POST   /api/menus                  # 创建菜单
PUT    /api/menus/{id}             # 更新菜单
DELETE /api/menus/{id}             # 删除菜单
GET    /api/menus/user             # 获取用户菜单
```

### 支付相关接口
```
GET    /api/orders                 # 获取订单列表
POST   /api/orders                 # 创建订单
GET    /api/orders/{id}            # 获取订单详情
POST   /api/orders/{id}/pay        # 订单支付
POST   /api/orders/{id}/cancel     # 取消订单
GET    /api/products               # 获取产品列表
```

### 外部系统接口
```
GET    /api/external-systems       # 获取外部系统列表
POST   /api/external-systems       # 创建外部系统
PUT    /api/external-systems/{id}  # 更新外部系统
DELETE /api/external-systems/{id}  # 删除外部系统
GET    /api/external-systems/{id}/preview  # 预览外部系统页面
```

## 权限系统设计

### RBAC权限模型
采用基于角色的访问控制（RBAC）模型：

```
用户 (User) ──┐
               ├── 用户角色关联 (user_roles) ──┐
用户组 (Group) ─┘                              │
                                               ├── 角色 (Role) ── 角色权限关联 (role_permissions) ── 权限 (Permission)
```

### 权限粒度
- **菜单权限**: 控制用户能看到哪些菜单
- **按钮权限**: 控制用户能操作哪些按钮
- **数据权限**: 控制用户能查看哪些数据
- **接口权限**: 控制用户能访问哪些API

### 权限验证流程
```
1. 用户登录获取JWT token
2. 每次请求携带token
3. 后端验证token有效性
4. 从token中获取用户权限
5. 验证用户是否有访问权限
6. 验证数据权限（如需要）
7. 返回请求数据或错误信息
```

## 支付系统设计

### 支付流程
```
1. 用户选择产品创建订单
2. 系统生成唯一订单号
3. 用户选择支付方式
4. 调用第三方支付接口
5. 支付成功后更新订单状态
6. 增加用户点数或会员时长
7. 记录交易日志
```

### 点数消费流程
```
1. 用户发起消费请求
2. 验证用户点数余额
3. 扣除相应点数
4. 记录消费日志
5. 执行具体业务逻辑
6. 返回操作结果
```

### 支付安全机制
- 订单号唯一性校验
- 支付状态防重复更新
- 金额校验和防篡改
- 异步回调验签
- 交易日志记录

## 外部页面系统集成设计

### 集成方式
1. **iframe嵌入**: 通过iframe嵌入外部页面系统
2. **页面跳转**: 新窗口或标签页打开外部系统
3. **API数据集成**: 通过API获取数据在内部展示
4. **单点登录**: 与外部系统实现SSO集成

### 页面系统集成配置
```json
{
  "system_name": "第三方页面系统",
  "system_type": "page",
  "page_url": "https://external-system.com/dashboard",
  "integration_type": "iframe", // iframe, redirect, api
  "width": "100%",
  "height": "800px",
  "allow_fullscreen": true,
  "sandbox_options": "allow-scripts allow-same-origin",
  "auth_type": "sso", // none, sso, token
  "sso_config": {
    "login_url": "https://external-system.com/sso/login",
    "logout_url": "https://external-system.com/sso/logout",
    "token_param": "access_token"
  },
  "custom_headers": {
    "X-Custom-Header": "value"
  }
}
```

### 前端集成实现
```typescript
// 外部页面组件
const ExternalPage: React.FC<{systemId: number}> = ({ systemId }) => {
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null);
  
  useEffect(() => {
    // 获取外部系统配置
    fetchSystemConfig(systemId).then(setSystemConfig);
  }, [systemId]);
  
  if (!systemConfig) return <Loading />;
  
  if (systemConfig.integration_type === 'iframe') {
    return (
      <iframe
        src={systemConfig.page_url}
        width={systemConfig.width}
        height={systemConfig.height}
        allowFullScreen={systemConfig.allow_fullscreen}
        sandbox={systemConfig.sandbox_options}
      />
    );
  }
  
  if (systemConfig.integration_type === 'redirect') {
    window.open(systemConfig.page_url, '_blank');
    return <div>正在打开外部系统...</div>;
  }
  
  return null;
};
```

### 安全考虑
- iframe沙箱配置
- CSP（内容安全策略）设置
- 跨域通信安全
- 用户权限验证
- 会话管理

## 前端设计

### 页面结构
```
src/
├── components/          # 通用组件
│   ├── Layout/         # 布局组件
│   ├── Auth/           # 认证相关组件
│   └── Common/         # 通用组件
├── pages/              # 页面组件
│   ├── Dashboard/      # 仪表板
│   ├── Users/          # 用户管理
│   ├── Permissions/    # 权限管理
│   ├── Orders/         # 订单管理
│   ├── ExternalSystems/ # 外部系统集成
│   └── Settings/       # 系统设置
├── hooks/              # 自定义Hooks
├── stores/             # 状态管理
├── services/           # API服务
├── utils/              # 工具函数
└── types/              # TypeScript类型定义
```

### 路由设计
```typescript
const routes = [
  {
    path: '/',
    component: Layout,
    routes: [
      { path: '/dashboard', component: Dashboard },
      { path: '/users', component: UserList },
      { path: '/users/:id', component: UserDetail },
      { path: '/roles', component: RoleList },
      { path: '/menus', component: MenuList },
      { path: '/orders', component: OrderList },
      { path: '/external-systems', component: ExternalSystemList },
      { path: '/external-systems/:id/preview', component: ExternalSystemPreview },
      { path: '/settings', component: Settings }
    ]
  },
  { path: '/login', component: Login },
  { path: '/login/wechat', component: WeChatLogin },
  { path: '/login/qr', component: WeChatQRLogin }
];
```

### 状态管理
```typescript
// 用户状态
interface UserState {
  user: User | null;
  token: string | null;
  permissions: string[];
  menus: Menu[];
}

// 系统状态
interface SystemState {
  loading: boolean;
  theme: 'light' | 'dark';
  collapsed: boolean;
}
```

## 安全设计

### 认证安全
- JWT token有效期控制
- 刷新token机制
- 密码强度要求
- 登录失败锁定
- 单点登录控制

### 接口安全
- API频率限制
- SQL注入防护
- XSS攻击防护
- CSRF防护
- 敏感数据加密

### 数据安全
- 数据库连接加密
- 敏感字段加密存储
- 数据脱敏展示
- 操作日志记录
- 数据备份策略

## 性能优化

### 数据库优化
- 合理索引设计
- 查询优化
- 分页查询
- 连接池配置

### 缓存策略
- Redis缓存热点数据
- 数据库查询缓存
- 页面静态资源缓存

### 前端优化
- 代码分割和懒加载
- 图片压缩和WebP格式
- 资源压缩和合并
- 浏览器缓存利用

## 部署方案

### 传统部署方式
```bash
# 安装Python依赖
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 启动应用
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Nginx配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/your/static/files/;
    }
}
```

## 开发计划

### 第一阶段 (基础功能)
1. 项目架构搭建
2. 多种方式用户认证系统
3. 基础权限管理
4. 用户管理功能
5. 菜单管理功能

### 第二阶段 (业务功能)
1. 支付系统集成
2. 点数充值和消费
3. 订单管理功能
4. 会员管理功能
5. 外部页面系统集成

### 第三阶段 (高级功能)
1. 数据分析和报表
2. 系统配置管理
3. 性能优化
4. 安全加固

## 总结

本设计文档详细描述了一个现代化的会员管理系统，采用Python + React技术栈，支持多种登录方式、用户管理、权限控制、支付系统、外部页面系统集成等核心功能。系统设计注重安全性、可扩展性和可维护性，适合企业级应用开发。

后续可以根据具体业务需求进行调整和优化。
