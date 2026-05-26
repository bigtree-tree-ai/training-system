# Changelog — 科学知识体系重构

## 2026-05-26 阶段 B：分析升级 + 个体化建议

### Added
- `training/science/training/thresholds.py` — LT_HR / Critical Speed 动态学习
- `training/science/training/prescriptions.py` — 训练学解读（个体化 actions）
- `training/science/rehab/prescriptions.py` — 康复学解读 + 部位 prehab 库
- `training/science/nutrition/prescriptions.py` — 营养学解读
- `training/science/nutrition/caffeine.py` — 咖啡因剂量+睡眠安全
- `training/science/nutrition/hydration.py` — 补液 + 失水警示
- `training/science/nutrition/electrolytes.py` — 电解质（钠钾镁）
- `training/science/llm_prompts.py` — Few-shot + 结构化 JSON schema（4 examples）
- `training/application/science_today.py` — SciencePrescription 聚合服务
- 23 个新单测，161 全套件 PASSED

### Changed
- `LoadProfile._verdict` 修复：低 CTL+低 ATL → detrain（替代误判 peak）
- electrolytes notes 触发条件简化（cramp_history 任何情况都加提示）

### Deploy
- main HEAD 已部署阿里云 `:8081/training/`
- 服务 active，API HTTP 200

---

## 2026-05-26 阶段 A：科学知识体系骨架 + 数据补齐

### Added
- `training/science/` 三学科目录（training/rehab/nutrition + common 9 模块）
- 8 张新表（GPS、步态、伤病、疼痛、康复、营养摄入、补给、阈值历史）
- athlete_config v2 + 幂等迁移脚本（自动反推结构化 injuries[]）
- FIT GPS+步态解析升级（每秒 lat/lon/altitude/hr/speed/cadence + 步态汇总）
- `scripts/reparse_fit_v2.py` 增量回填脚本
- 三学科首版算法（Daniels/Friel/Foster/Hulin/Seiler/IOC RED-S）
- 35 个 science 单测，138 全套件 PASSED

### Migration
- DB 自动 ALTER：`sessions.rpe / has_track_points / has_gait`
- DB 自动 ALTER：`athlete_checkins.session_rpe / session_id`

### Deploy
- main HEAD `e14f8d4` 已部署阿里云
- 8 张新表已在线，公网 200，内网 API 200
