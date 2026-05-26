"""电解质策略 — ACSM / IOC Sports Nutrition

钠：训练 >1h 或炎热环境 → 300-700 mg/h（取决于汗钠浓度）
钾：500-1000 mg/天（普通饮食足够，长课可补香蕉/电解质粉）
镁：300-400 mg/天，运动员需求略高
长课（>3h）/高温环境/抽筋史 → 钠 800-1200 mg/h
"""
from __future__ import annotations


def sodium_per_h(sweat_rate_ml_per_h: float, sweat_na_mg_per_l: float = 1000.0, replacement_pct: float = 0.7) -> int:
    """每小时建议钠摄入（mg）= 出汗中钠损失 × 替代比"""
    na_loss_per_h = sweat_rate_ml_per_h / 1000.0 * sweat_na_mg_per_l
    return int(na_loss_per_h * replacement_pct)


def plan(duration_min: float, sweat_rate_ml_per_h: float = 800.0, sweat_na_mg_per_l: float = 1000.0, hot_weather: bool = False, cramp_history: bool = False) -> dict:
    base_na = sodium_per_h(sweat_rate_ml_per_h, sweat_na_mg_per_l)
    if duration_min < 60 and not hot_weather:
        na_per_h = 0
    elif duration_min >= 180 or cramp_history or hot_weather:
        na_per_h = max(base_na, 800)
    else:
        na_per_h = base_na

    notes: list[str] = []
    if cramp_history:
        notes.append("有抽筋史，确保钠 ≥ 800 mg/h，并预补镁")
    if duration_min >= 180:
        notes.append("超长课需累计监控低钠血症风险，每小时严格按计划")
    if hot_weather:
        notes.append("高温环境出汗率上调 30-50%，预补水电解质")

    return {
        "sodium_mg_per_h": na_per_h,
        "potassium_mg_per_day": 1000,
        "magnesium_mg_per_day": 400,
        "notes": notes,
    }
