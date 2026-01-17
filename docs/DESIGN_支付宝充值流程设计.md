# 支付宝充值模块设计文档

创建日期：2026-01-17  
适用项目：AIOffer 会员管理系统  
状态：设计阶段（仅方案，不含实现）

---

## 1. 设计目标与范围

- 支持会员通过支付宝完成人民币充值，系统将充值金额按规则转换为积分（points）或包时长，写入现有积分体系。
    - 套餐的设定：
    - 注册赠送：会员注册成功后，系统自动赠送 3 点（不走支付宝，仅作为系统内置赠送策略）。
    - 积分充值套餐：
    - 5 元 → 10 点（小额体验包）。
    - 时长套餐：
    - 15 日套餐：15 元。
    - 月度套餐：25 元。
    - 季度套餐：50 元。
    - 半年套餐：80 元。
    - 年度套餐：120 元。

## 2. 功能设计
### 2.1 充值流程

1. **会员登录**：会员登录后，可在我的账户页面、入学评估页面看到“购买套餐”按钮。
2. **选择购买套餐**：会员在系统中选择自己心仪的充值套餐（积分套餐或时长套餐）。
3. **确认充值金额**：系统显示该套餐的充值金额，会员确认无误后点击“确认充值”。
4. **跳转至支付宝支付**：系统将跳转到支付宝支付页面（pc端扫码支付、移动端H5，优先调起支付宝app支付，若app未安装，则跳转至h5支付页面）。
5. **支付成功**：支付宝返回支付成功通知，系统更新会员的积分或时长余额。
6. **充值记录**：会员可以在系统中查看自己的充值记录，包括已使用的套餐和套餐余量。

## 3. 技术实现

### 3.1 架构概览

- 后端：基于 FastAPI 的 API 服务，在现有订单与会员体系之上新增 `recharge` 路由模块：
  - 路由文件：`backend/routers/recharge.py`。
  - 工具组件：`backend/utils/alipay_client.py`（Alipay 客户端封装）、`backend/utils/alipay_sign.py`（回调验签）。
  - 配置：通过 `backend/config/settings.py` 中的 `alipay_*` 配置项从 `.env` 读取支付宝参数。
  - 数据模型：复用现有 `Order`、`Member`、`PointTransaction` 等模型，保证充值记录与积分流水统一管理。
- 前端：基于 React + Ant Design 的管理后台，前端通过统一的 HTTP 工具与后端交互：
  - API 封装：`frontend/src/services/orders.ts` 新增支付宝充值相关接口。
  - 页面入口：`frontend/src/pages/Members.tsx` 在“我的账户”页面新增充值入口，调用后端创建支付订单并跳转支付宝。
- 支付宝 SDK：基于 `alipay-sdk-python`（3.7.x 系列）完成下单 URL 生成与签名验签。

整体调用链路：

1. 前端调用 `/api/orders/products/list` 获取可售充值套餐，将“积分类产品”呈现给会员。
2. 会员点击某个套餐后，前端调用 `/api/recharge/alipay/create` 创建充值订单。
3. 后端生成订单记录、构造支付宝支付 URL 返回给前端。
4. 前端使用返回的 `alipay_scheme` 或 `pay_url` 调起支付宝支付。
5. 支付宝在支付完成后，按配置回调 `/api/recharge/alipay/notify`（异步）与 `/api/recharge/alipay/return`（同步）。
6. 后端在异步回调中完成验签、金额校验、订单状态变更与积分发放。

### 3.2 后端实现

#### 3.2.1 主要组件与配置

- 配置项（`backend/config/settings.py`）：
  - `alipay_app_id`：支付宝应用 AppID。
  - `alipay_private_key_path`：商户应用私钥文件路径（PEM）。
  - `alipay_alipay_public_key_path`：支付宝公钥文件路径（PEM）。
  - `alipay_gateway`：网关地址，生产环境为 `https://openapi.alipay.com/gateway.do`。
  - `alipay_notify_url`：支付宝服务端异步通知回调地址，例如 `https://www.corsefnder.com.cn/api/recharge/alipay/notify`。
  - `alipay_return_url`：用户浏览器同步回跳地址，例如 `https://www.corsefnder.com.cn/api/recharge/alipay/return`。
- 客户端封装（`backend/utils/alipay_client.py`）：
  - `get_alipay_client()`：
    - 从配置加载网关地址、AppID、本地私钥和支付宝公钥。
    - 构造 `AlipayClientConfig`，设置 charset/format/sign_type（RSA2）。
    - 以单例形式初始化 `DefaultAlipayClient`，避免重复创建客户端。
  - `build_pay_url(...)`：
    - 根据 `client_type` 区分 PC 与 H5 支付：
      - PC：使用 `AlipayTradePagePayModel` + `AlipayTradePagePayRequest`，设置 `product_code=FAST_INSTANT_TRADE_PAY`。
      - H5：使用 `AlipayTradeWapPayModel` + `AlipayTradeWapPayRequest`，设置 `product_code=QUICK_WAP_WAY`。
    - 设置 `notify_url`、`return_url` 后调用 `client.page_execute()` 得到可直接访问的支付 URL。
    - H5 场景下，为方便在移动浏览器中直接拉起支付宝 App，对 URL 做 URL-encode，拼接成 `alipays://platformapi/startapp?...` 形式的 `alipay_scheme`。
- 签名验签（`backend/utils/alipay_sign.py`）：
  - `verify_alipay_sign(params: Dict[str, Any]) -> bool`：
    - 从参数字典中取出 `sign`，删除 `sign`、`sign_type` 字段。
    - 按 key 字典序构造 `key=value` 拼接的待验签字符串。
    - 读取配置中的支付宝公钥文件内容。
    - 使用 `verify_with_rsa(..., sign_type="RSA2")` 验证签名。
    - 对缺少签名、内容为空、公钥读取失败或验签异常等情况统一记录日志并返回 False。

#### 3.2.2 支付订单创建接口（/api/recharge/alipay/create）

- 路由定义：`backend/routers/recharge.py` 中的 `POST /alipay/create`，挂载在应用前缀 `/api/recharge` 下。
- 入参模型：`AlipayCreateRequest`：
  - `product_id`：待购买产品 ID（使用现有 `PRODUCTS` 配置）。
  - `amount`（可选）：前端确认金额，用于与产品配置做一致性校验。
  - `client_type`（可选）：`"pc"` 或 `"h5"`，默认为 `"h5"`。
- 处理逻辑：
  1. 校验支付宝配置是否完整（`alipay_app_id`、密钥路径、`notify_url`、`return_url` 等），缺失则直接返回错误提示。
  2. 从 `routers/orders.py` 中的 `PRODUCTS` 列表查找 `product_id` 对应的产品：
     - 产品不存在 → 返回“产品不存在”错误。
     - 当前仅允许 `type == "points"` 的产品通过支付宝充值，其他类型直接拒绝。
  3. 校验金额：
     - 以产品配置的 `price` 作为订单金额。
     - 若请求中携带 `amount`，则要求与产品价格完全一致，否则视为参数篡改。
  4. 生成订单号（`generate_order_no()`），创建一条 `Order`：
     - `user_id`：当前登录会员。
     - `product_id` / `product_type`：与选中的产品保持一致。
     - `amount`：使用 `Decimal` 存储精确金额。
     - `status`：初始为 `1`（待支付）。
     - `description`：标记为“支付宝充值：{产品名称}”。
  5. 提交订单到数据库并刷新，拿到订单 ID。
  6. 调用 `build_pay_url(...)` 构造支付宝支付 URL 与可选的 `alipay_scheme`。
  7. 返回数据：
     - `order_id`、`order_no`：供前端展示或后续查询。
     - `pay_url`：标准浏览器可访问的支付宝支付地址。
     - `alipay_scheme`：可用于在移动端直接唤起支付宝 App 的 URL Scheme。

#### 3.2.3 支付宝同步回调（/api/recharge/alipay/return）

- 用途：用户支付完成后，支付宝会在浏览器中重定向到此地址，用于给用户一个直观的支付结果页面（成功/失败）。
- 处理流程：
  1. 从 `Query` 中读取所有参数组成字典，记录日志。
  2. 调用 `verify_alipay_sign(params)` 做签名验证，失败时返回 400 状态码与错误信息。
  3. 校验 `app_id` 与配置中的 `alipay_app_id` 是否一致，防止错误应用或攻击。
  4. 提取 `out_trade_no`、`trade_status`，根据是否为 `TRADE_SUCCESS` / `TRADE_FINISHED` 组装简单的 HTML 文本返回给用户。
  5. 同步回调只负责展示，不做订单写操作，真正的记账逻辑在异步回调中完成。

#### 3.2.4 支付宝异步通知（/api/recharge/alipay/notify）

- 用途：支付宝服务端在支付结果确定后调用该接口，作为记账和积分发放的唯一依据。
- 处理流程：
  1. 从 `Request.form()` 读取表单数据，转换成字典，记录原始通知参数。
  2. 验签与基础校验：
     - 调用 `verify_alipay_sign(data)` 验证签名。
     - 校验 `app_id` 与配置，避免错误应用的通知。
     - 校验 `out_trade_no`、`total_amount` 等必需字段是否存在。
  3. 根据 `out_trade_no` 查询 `Order`，并预加载 `Order.user` 与 `User.member`：
     - 未找到订单 → 记录日志并返回 `"failure"`。
  4. 金额与状态校验：
     - 将 `total_amount` 转为 `Decimal`，与订单金额 `order.amount` 精确比对，一致性失败则拒绝通知。
     - 若 `order.status == 2`（已支付），直接返回 `"success"`，实现异步通知的幂等处理。
     - 若 `trade_status` 不在 `TRADE_SUCCESS` / `TRADE_FINISHED`，视为未支付成功，返回 `"failure"`。
  5. 积分发放逻辑：
     - 从 `PRODUCTS` 中找到与当前订单 `product_id` 且 `type == "points"` 的产品。
     - 读取产品配置中的 `points` 字段，作为本次充值发放的积分数。
     - 调用 `member.add_points(points)` 更新会员积分。
     - 创建 `PointTransaction` 记录积分变动：
       - `type=1`（充值）、`points`、`balance_after`、`amount`、`description`、`related_id`（订单 ID）、`related_type="alipay"`。
  6. 更新订单状态：
     - 将 `order.status` 更新为 `2`（已支付）。
     - `payment_method="alipay"`，`payment_time` 记录当前时间。
  7. 提交事务：
     - 成功提交则返回 `"success"`。
     - 若提交异常则回滚，并返回 `"failure"`，以便支付宝后续重试通知。

#### 3.2.5 幂等与安全设计

- 幂等控制：
  - 通过检查 `order.status == 2` 确保重复通知不会重复发放积分。
  - 订单创建与回调处理分离，任何环节失败时都会记录日志并保持订单在可恢复状态。
- 金额与产品校验：
  - 创建订单时校验前端金额与产品价格是否一致。
  - 回调时再次校验通知金额与订单金额是否一致，双向校验防止篡改。
- 应用校验：
  - 同步与异步回调均校验 `app_id`，防止错误应用或恶意请求。
- 密钥管理：
  - 私钥与支付宝公钥通过文件路径加载，不写死在代码中，应在生产环境放置于仅应用可读目录，并通过 `.env` 指定路径。

### 3.3 前端实现

#### 3.3.1 API 封装（orders 服务）

- 文件：`frontend/src/services/orders.ts`。
- 关键类型：
  - `Product`：包含 `id`、`name`、`type`、`price`、`description`、`duration?`、`points?` 等字段。
  - `AlipayRechargeResponse`：包含 `order_id`、`order_no`、`pay_url`、`alipay_scheme?`。
- 核心方法：
  - `getProducts()`：
    - GET `/orders/products/list`，获取后端定义的产品配置列表。
  - `createAlipayRecharge(params)`：
    - POST `/recharge/alipay/create`，入参包含 `product_id`、`amount?`、`client_type?`。
    - 返回后端生成的支付 URL 与 URL Scheme。

#### 3.3.2 会员自助充值入口（Members 页面）

- 文件：`frontend/src/pages/Members.tsx`。
- 会员视角（`isMemberMode`）下：
  - 页面顶部展示“我的账户”概要信息（用户基本信息 + 当前积分）。
  - 通过 `useEffect` 在组件加载时调用 `getProducts()` 获取产品列表，并过滤出 `type === 'points'` 的点数套餐。
  - 在“点数充值”卡片中以列表形式展示所有可选套餐：
    - 展示套餐名称、点数字段（`Tag`）、价格等信息。
    - 每个套餐提供“支付宝支付”按钮。
- 支付发起逻辑：
  - 点击“支付宝支付”时，调用：
    - `createAlipayRecharge({ product_id: product.id, amount: product.price, client_type: 'h5' })`。
  - 收到响应后：
    - 优先使用 `alipay_scheme`（移动端唤起支付宝 App）。
    - 若无 `alipay_scheme`，则回退到 `pay_url`（H5 页面）。
    - 设置 `window.location.href = targetUrl` 实现跳转。
  - 若请求失败或响应中未返回有效 URL，提示“发起支付宝充值失败”或“未获取到支付链接”。

### 3.4 配置与环境注意事项

- 配置分离：
  - 所有支付宝相关配置均通过 `.env` 注入，不在代码库中硬编码敏感信息。
  - 示例配置可参考 `backend/.env.example`，生产环境应使用独立 `.env` 文件。
- 密钥文件：
  - 私钥文件与支付宝公钥文件建议放在 `backend/keys/` 目录下，权限设置为仅应用用户可读。
  - `.gitignore` 中应忽略具体密钥文件，避免提交到仓库。
- 依赖版本：
  - 支付宝 SDK 使用 `alipay-sdk-python` 3.7.x 系列，版本需与可用的 PyPI 源兼容（如使用阿里云镜像时选择镜像中存在的版本号）。
- 回调地址：
  - 生产环境需在支付宝开放平台配置与 `.env` 中保持一致的 `notify_url`、`return_url`，并确保公网可访问。

