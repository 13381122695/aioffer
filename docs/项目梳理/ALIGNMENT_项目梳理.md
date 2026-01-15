# ALIGNMENT_项目梳理

创建日期：2026-01-09  
用途说明：对齐“按新个人规则与项目规则重新梳理项目”的范围、边界、验收口径。

## 1. 原始需求

- 我修改了个人规则和项目规则，请帮我按要求重新梳理项目

## 2. 任务范围（本次梳理覆盖）

- 建立项目全生命周期文档：根目录 `说明文档.md`，包含项目规划/实施方案/进度记录
- 按 6A 工作流输出本次“项目梳理”文档集：ALIGNMENT/CONSENSUS/DESIGN/TASK/ACCEPTANCE/FINAL/TODO
- 梳理当前项目技术栈、模块边界、关键路由与前端页面映射，沉淀为可执行的后续计划

## 3. 非范围（本次不做）

- 不新增业务功能、不做大规模重构（除非为修复阻塞性 BUG）
- 不引入新依赖、不安装额外包、不启动容器或额外服务

## 4. 现状理解（基于仓库现状）

**技术栈**
- 后端：FastAPI + SQLAlchemy Async + Pydantic v2
- 前端：React + TypeScript + Ant Design + Vite + Zustand

**核心模块**
- 后端路由注册：`/api/auth`、`/api/users`、`/api/roles`、`/api/menus`、`/api/orders`、`/api/external-systems`
- 前端页面：Users/Members/Orders/Transactions/ExternalSystems/Settings（Roles/Menus/ExternalSystemsConfig）

## 5. 不确定性与决策（本次采用默认决策）

- “重新梳理项目”优先解释为：文档体系 + 模块现状梳理 + 可执行计划，不额外扩展开发范围
- 若后续需要治理架构一致性（如 external systems 路由前缀/依赖风格），单独作为新任务进入 6A 流程

