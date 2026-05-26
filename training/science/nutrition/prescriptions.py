"""营养学处方文案 — 把 EnergyBalanceReport / fueling 翻译成可读建议"""
from __future__ import annotations

from typing import Optional

from training.science.common.athlete_profile import AthleteProfile
from training.science.common.schemas import EnergyBalanceReport


def explain_energy_balance(eb: EnergyBalanceReport, profile: Optional[AthleteProfile] = None) -> dict:
    sev_map = {"green": "ok", "yellow": "warn", "red": "danger", "unknown": "info"}
    severity = sev_map.get(eb.reds_flag, "info")
    headline_map = {
        "green": "能量供给充分",
        "yellow": "能量供给偏低，需关注趋势",
        "red": "REDs 红灯：能量严重不足",
        "unknown": "缺少摄入数据",
    }
    actions: list[str] = []
    if eb.reds_flag == "red":
        actions.append(f"今日补足至 ≥ {int(eb.tdee_kcal)} kcal，优先碳水（{eb.macros_target.get('cho_g',0)}g）+ 蛋白（{eb.macros_target.get('pro_g',0)}g）")
        actions.append("连续 ≥7 天 EA<30 → 复查 HRV / RHR / 睡眠 / 月经（女性）")
    elif eb.reds_flag == "yellow":
        actions.append(f"今日加餐至 ≥ {int(eb.tdee_kcal * 0.95)} kcal，训练后 30 min 内补碳水")
        if profile and profile.has_active_injury:
            actions.append("有伤情，蛋白≥1.8 g/kg + 维生素 D + 钙以支持组织修复")
    elif eb.reds_flag == "green":
        actions.append("继续按目标 macros 执行")
    elif eb.reds_flag == "unknown":
        actions.append("记录今日摄入（可估算大类即可），系统才能给出准确建议")

    return {
        "severity": severity,
        "headline": headline_map.get(eb.reds_flag, ""),
        "actions": actions,
        "why": eb.notes,
        "macros_target": eb.macros_target,
        "ea": eb.ea_kcal_per_kg_ffm,
    }
