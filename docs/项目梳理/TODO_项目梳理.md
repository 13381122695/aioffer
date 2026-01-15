# TODO_项目梳理

创建日期：2026-01-09  
用途说明：精简列出待办与缺失配置，方便快速定位与推进。

## 待办（按优先级）

1. 高：补齐自检基线（前端 `npm run lint` / `npm run check`，后端 Python compile）
2. 高：确认 External Systems 路由前缀与 main.py 注册方式一致性，避免双前缀风险
3. 中：补齐最小回归用例（pytest + 关键接口 smoke test）

## 可能缺失/风险配置

- 后端 `.env`：DATABASE_URL / SECRET_KEY 等需按环境设置（避免使用默认值进入生产）
- Redis/Celery：requirements 存在依赖，但是否启用需明确，避免“配置存在但代码未对齐”的漂移

