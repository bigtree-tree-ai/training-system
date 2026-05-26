# 阶段 B 验收报告：分析升级 + 个体化建议

**分支**：`feature/science-viz-stage-b`
**完成时间**：2026-05-26
**测试结果**：161 passed（138 阶段 A + 23 阶段 B 新增）零回归

---

## 交付物

### B.1 LoadProfile verdict 修正 + LT/CV 动态学习

- `training/science/training/load_model.py:_verdict` 新增"低 CTL+低 ATL → detrain"规则，修复阶段 A 用真实数据时把"长期未训练"误判为 peak
- 新增 `training/science/training/thresholds.py`：
  - `estimate_lt_hr_from_recent(weeks=8)` — 从最近 N 周 tempo/threshold 跑提取 LT_HR 中位数
  - `estimate_critical_speed(weeks=8)` — 5-15 km 持续努力的最快平均配速
  - `learn_and_record(weeks=8)` — 一键学习 + 写 thresholds_history
  - `latest(kind)` — 读最新阈值

### B.2 prescriptions 解读迁移到 science（按学科分文件）

- `training/science/training/prescriptions.py`：`explain_load` / `explain_polarization`
  - 输出 `{severity, headline, actions[], why[], verdict}` 结构化
  - 个体化：读 `athlete_profile.weekly_volume_target_km` 等动态参数
- `training/science/rehab/prescriptions.py`：`explain_return_to_run` / `red_flags`
  - 按伤病部位（L_knee/R_knee/lower_back/achilles/ITB/plantar_fascia）输出 prehab 处方
  - 红线检查：VAS≥4 / 术后承载力 <70% 等
- `training/science/nutrition/prescriptions.py`：`explain_energy_balance`
  - REDs 三档（red/yellow/green）对应不同 actions
  - 伤情×能量不足联合警告

旧 `interpretations.py` 保留，避免破坏现有 `today.py` 引用。

### B.3 营养扩展模块

- `nutrition/caffeine.py`：剂量（3-6 mg/kg，sensitive 减半）+ 半衰期（5-6h）+ 睡眠安全检查
- `nutrition/hydration.py`：每日基础 35 ml/kg + 训练补水（70% 替代）+ 失水百分比 + 警示
- `nutrition/electrolytes.py`：钠（出汗率 × 汗钠 × 70%）+ 钾镁基础 + 抽筋史/高温/超长课调整

### B.4 LLM few-shot + 结构化输出

- `training/science/llm_prompts.py`：
  - 系统 prompt 锚定 Daniels/Friel/Seiler/IOC RED-S/ACSM/APTA/KNGF
  - 严格 JSON schema（summary/actions/risk_level/confidence_level/primary_concern/evidence_keys）
  - 4 个 few-shot example：高 ACWR / 术后能量不足 / detrain 数据低置信 / peak+REDs
  - `build_payload(rx)` 返回 anthropic SDK 直接可用的 dict

### B.5 SciencePrescription 聚合服务

- `training/application/science_today.py:build_today()`
  - 从 DB 拉 daily_load / hr_zone_splits / coros_hrv / pain_log / nutrition_intake
  - 聚合三学科 + DataConfidence
  - 输出统一 `SciencePrescription` 对象（前端/LLM 共用）
- 严格只读，不写表（避免与产品端写入路径冲突）

---

## 测试覆盖

| 文件 | 用例 | 覆盖 |
|---|---|---|
| `test_science_prescriptions.py` | 6 | explain_load/polarization/rtr/eb + red_flags |
| `test_science_nutrition_extras.py` | 12 | caffeine/hydration/electrolytes |
| `test_science_today.py` | 4 | build_today + LLM payload + verdict 修正 |
| **本阶段新增** | **22** | 单测 |
| 旧 nutrition 调整 1 个（electrolytes notes） | +1 | bug fix 联动 |
| **全套件** | **161 passed** | 零回归 |

---

## 用户验收 case（基于真实数据）

执行 `python -m scripts.science_demo` 末尾输出：

```
verdict: 今日有需要关注的风险，按建议执行
confidence: 0.15

--- why ---
  · CTL=15.23, ATL=0.19, TSB=15.04
  · Easy 0% / Mod 0% / Hard 0%

--- next_actions ---
  → 先以低强度 Z2 跑 30-45 min × 3-4 次/周 重启 2 周
  → 配合 2 次力量+灵活性训练，避免高冲击
  → 今日按阶段 5 执行
  → 记录晨痛 VAS
  → 记录今日摄入（可估算大类即可），系统才能给出准确建议

LLM messages: 9 条（含 4 few-shot）
```

✓ verdict 不再是错误的 peak，正确识别为"低体能基线 + 数据不足"
✓ next_actions 给出具体可执行的"重启 2 周"建议，含周数、时长、频次
✓ 自动追加"记录今日摄入"提示因为缺营养数据
✓ LLM payload 9 条 messages（4 few-shot user/assistant 对 + 1 final user）

---

## 已知遗留（阶段 C 处理）

1. RPE 录入 UI 入口
2. coach_recommendations 表的实际 LLM 调用尚未替换为 science.llm_prompts.build_payload（需要等阶段 C 重新设计页面+API）
3. 课表生成器 `planning/generator.py` 还未引用 SciencePrescription
4. `interpretations.py` 旧解读被产品端调用，留兼容；阶段 C 全切换到 prescriptions

---

## 部署信息

- 当前分支：`feature/science-viz-stage-b`
- 待操作：rebase main → push → SSH 服务器 git pull → restart
