# Agentic Coach v1 开发简报

## 一句话说明

本次开发把原来的训练分析系统升级为个人私有的 AI 运动康复与训练教练团：设备数据和主观反馈进入统一数据层，系统自动生成今日 readiness、风险评估、专家团建议、证据依据，并支持确认/拒绝训练调整。

## 本次新增

- Clean/Hexagonal 分层：
  - `training/domain/`：领域模型和端口。
  - `training/application/`：特征管线、教练团、心跳、今日聚合服务。
  - `training/adapters/`：SQLite 适配器。
  - `training/evidence/`：精选证据库和检索器。
- 三层数据管线：
  - raw：`raw_ingest_events`
  - canonical：`canonical_daily_metrics`
  - feature：`daily_features`
- Agentic Coach：
  - 数据质检
  - 恢复康复
  - 马拉松/戈21训练
  - 力量灵活性
  - 营养补给
  - 计划调整
  - 安全审核
  - 证据检索
- 心跳机制：
  - `heartbeat_runs`
  - `coach_recommendations`
  - CLI：`training.cli heartbeat`
- Web/PWA：
  - 首页改为“今天”工作台。
  - 支持晨检录入、建议刷新、训练确认、证据查看。
- API：
  - `GET /api/v1/today`
  - `POST /api/v1/checkins`
  - `POST /api/v1/sync/run`
  - `GET /api/v1/coach/recommendations`
  - `POST /api/v1/plan/confirm`
  - `GET /api/v1/evidence/search`

## 安全策略

- 康复保守优先。
- 高强度、降载、疼痛/伤病相关调整默认需要确认。
- AI 不做医疗诊断；红旗症状只触发降载和线下专业评估提醒。
- 生产环境启用 HTTP Basic auth。
- `.env`、`.coros_auth.json`、API key、服务器密码、私钥不得入库。

## 验收结果

最近一次完整验收：

- 全量测试：`96 passed`
- 新增 Agentic Coach 验收测试：`8 passed`
- 本地端到端临时 DB：
  - 今日建议 200
  - 提交高风险晨检 200
  - 查询晨检 200
  - 查询推荐 200
  - 证据搜索 200
  - 确认建议 200
  - 无效日期 400
  - 无效确认 400
  - 空数据库 `/dashboard` 200
- 阿里云：
  - `/training/` 200
  - `/training/dashboard` 200
  - `/training/api/v1/today` 200
  - `training-web.service` active

## Git 关键提交

- `4e7064b feat: add agentic training coach v1`
- `0e626f9 test: cover agentic coach user flows`
- `4f8198e fix: harden coach acceptance edge cases`

## 后续开发优先级

1. HealthKit/iOS companion adapter。
2. 饮食照片、饮水、咖啡因的结构化输入。
3. PubMed/NCBI 定期刷新精选证据库。
4. 课表调整从“建议确认”升级为“确认后自动写回未来计划”。
5. PWA 通知和每日心跳提醒。

