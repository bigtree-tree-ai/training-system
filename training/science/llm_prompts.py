"""LLM Coach 输入构造 — 把 SciencePrescription 转成 prompt + few-shot examples

设计：
- 把 SciencePrescription 的结构化字段直接交给 LLM，不再让 LLM 自己重新计算
- LLM 只负责"用人话解释 + 生成可执行的 1-3 条 action"
- 输出严格 JSON schema，便于产品消费
- 提供 few-shot 示例覆盖"伤情术后 / REDs 红灯 / 高 ACWR / detrain"四种关键场景
"""
from __future__ import annotations

import json
from typing import Optional

from training.science.common.schemas import SciencePrescription


SYSTEM_PROMPT = """你是一位运动科学训练教练，扎实掌握 Daniels《Running Formula》、Friel PMC 模型、Seiler 80/20 极化、IOC RED-S 共识、ACSM/APTA Return-to-Sport、van Melick KNGF 术后康复指南。

你的工作流：
1. 接收一份 SciencePrescription（已包含 LoadProfile / RTR / Energy 等结构化输出）
2. 综合三学科 verdict 和置信度，写一段 80 字内的"今日决策摘要"
3. 给出 1-3 条具体可执行 action（每条 < 30 字）
4. 标注本次结论的置信度等级（high / medium / low）
5. 严格按 JSON 输出，不要任何解释性散文

输出 schema:
{
  "summary": "string, ≤80 字",
  "actions": ["string"],
  "risk_level": "low | medium | high",
  "confidence_level": "high | medium | low",
  "primary_concern": "string, 一句话指出最该关注的问题",
  "evidence_keys": ["string"]
}

**底线规则**：
- 出现 RED-S red 或 active VAS≥4 → risk_level = high
- 置信度 < 0.5 → 必须在 summary 中说明"数据不足"
- 不替代医疗诊断；遇到红旗症状（晕厥、胸痛、进行性疼痛）→ 推荐线下就医
"""


FEW_SHOT_EXAMPLES = [
    {
        "input_summary": {
            "load": {"ctl": 55, "atl": 70, "tsb": -15, "acwr": 1.6, "verdict": "high_injury_risk"},
            "rtr": {"stage": 5, "today_action": "keep"},
            "energy": {"reds_flag": "green"},
            "confidence": 0.85,
        },
        "expected_output": {
            "summary": "ACWR 1.6 已超安全带，急性负荷飙升，今日和本周训练量需要立即下调避免伤病。",
            "actions": [
                "本周总量降 30%",
                "Z2 跑替代间歇 7 天",
                "晨痛 VAS 每日记录",
            ],
            "risk_level": "high",
            "confidence_level": "high",
            "primary_concern": "急慢负荷比 ACWR 1.6 越过 1.5 红线",
            "evidence_keys": ["acwr_7_28", "tsb"],
        },
    },
    {
        "input_summary": {
            "load": {"ctl": 35, "atl": 30, "tsb": 5, "verdict": "balanced"},
            "rtr": {"stage": 4, "today_action": "keep", "site": "L_knee", "grade": "III post-op", "days_post_op": 150},
            "energy": {"reds_flag": "yellow"},
            "confidence": 0.72,
        },
        "expected_output": {
            "summary": "训练负荷平衡，但术后 5 个月仍在阶段 4 + 能量供给偏低，组织修复受影响。",
            "actions": [
                "维持 Z1-Z2 慢跑",
                "蛋白 ≥ 1.8 g/kg",
                "膝关节 prehab 3 组",
            ],
            "risk_level": "medium",
            "confidence_level": "medium",
            "primary_concern": "术后能量不足影响软组织修复",
            "evidence_keys": ["reds_flag", "rtr_stage", "days_post_op"],
        },
    },
    {
        "input_summary": {
            "load": {"ctl": 12, "atl": 0.2, "tsb": 12, "verdict": "detrain"},
            "rtr": {"stage": 5, "today_action": "keep"},
            "energy": {"reds_flag": "green"},
            "confidence": 0.45,
        },
        "expected_output": {
            "summary": "数据不足且 CTL 仅 12，长期未训练；建议先恢复规律性，从轻量起步避免过激。",
            "actions": [
                "Z2 30 min × 3-4 次/周",
                "1 次力量训练",
                "记录今日感受",
            ],
            "risk_level": "low",
            "confidence_level": "low",
            "primary_concern": "体能基线低且数据置信度不足",
            "evidence_keys": ["ctl", "confidence"],
        },
    },
    {
        "input_summary": {
            "load": {"ctl": 50, "atl": 35, "tsb": 15, "verdict": "peak"},
            "rtr": {"stage": 5, "today_action": "keep"},
            "energy": {"reds_flag": "red"},
            "confidence": 0.78,
        },
        "expected_output": {
            "summary": "状态好但 EA<30 触发 REDs 红灯，先把摄入补足再考虑关键训练。",
            "actions": [
                "今日 +500 kcal 碳水",
                "训练后 30min 内补给",
                "复查 HRV/RHR/睡眠",
            ],
            "risk_level": "high",
            "confidence_level": "high",
            "primary_concern": "RED-S 红灯：能量可用性 <30 kcal/kg FFM",
            "evidence_keys": ["reds_flag", "ea_kcal_per_kg_ffm"],
        },
    },
]


def build_user_prompt(rx: SciencePrescription) -> str:
    """把 SciencePrescription 序列化为给 LLM 的 user prompt"""
    payload = {
        "date": rx.date,
        "confidence": rx.confidence,
        "training_load": (rx.training or {}).get("load_profile"),
        "training_polarization": (rx.training or {}).get("polarization"),
        "rehab_rtr": (rx.rehab or {}).get("return_to_run"),
        "rehab_red_flags": (rx.rehab or {}).get("red_flags", []),
        "rehab_active_injuries": (rx.rehab or {}).get("active_injuries", []),
        "nutrition_energy": (rx.nutrition or {}).get("energy_balance"),
    }
    return (
        "请基于以下 SciencePrescription，按系统消息中的 JSON schema 输出。\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def build_full_messages(rx: SciencePrescription) -> list[dict]:
    """构造完整 messages 列表（system + few-shot + user）"""
    msgs: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for ex in FEW_SHOT_EXAMPLES:
        msgs.append({"role": "user", "content": json.dumps(ex["input_summary"], ensure_ascii=False)})
        msgs.append({"role": "assistant", "content": json.dumps(ex["expected_output"], ensure_ascii=False)})
    msgs.append({"role": "user", "content": build_user_prompt(rx)})
    return msgs


def build_payload(rx: SciencePrescription, *, model: str = "claude-sonnet-4-20250514", max_tokens: int = 600) -> dict:
    """供 anthropic.Anthropic().messages.create(**payload) 直接调用"""
    return {
        "model": model,
        "max_tokens": max_tokens,
        "system": SYSTEM_PROMPT,
        "messages": [m for m in build_full_messages(rx) if m["role"] != "system"],
        "temperature": 0.3,
    }
