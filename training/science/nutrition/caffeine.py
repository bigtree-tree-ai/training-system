"""咖啡因摄入策略 — Guest et al. ISSN 2021

剂量：3-6 mg/kg 体重
赛前：45-60 min 起效，60 min 达峰
半衰期：4-6 小时（个体差异大，sensitive 类型更长）
睡眠：与就寝时间间隔 ≥ 6 小时（敏感型 ≥ 8 小时）
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Optional


def recommended_dose_mg(weight_kg: float, response: str = "ok") -> tuple[int, int]:
    """返回 (低剂量, 高剂量)"""
    if response == "sensitive":
        return int(weight_kg * 2), int(weight_kg * 3)
    return int(weight_kg * 3), int(weight_kg * 6)


def half_life_hours(response: str = "ok") -> float:
    if response == "sensitive":
        return 6.0
    return 5.0


def sleep_safe(intake_time: datetime, dose_mg: float, bedtime: time = time(23, 0), response: str = "ok") -> bool:
    """检查咖啡因摄入是否会影响目标就寝时间

    安全规则：摄入后剩余血药浓度低于 50% 才算安全（半衰期 5h 后）。
    要求摄入与就寝间隔 ≥ 半衰期 + 1（高剂量再 +1）。
    """
    hl = half_life_hours(response)
    bed_dt = datetime.combine(intake_time.date(), bedtime)
    if bed_dt < intake_time:
        bed_dt += timedelta(days=1)
    gap_h = (bed_dt - intake_time).total_seconds() / 3600
    needed = hl + (1 if dose_mg > 200 else 0) + (1 if response == "sensitive" else 0)
    return gap_h >= needed


def plan(weight_kg: float, race_start: Optional[datetime] = None, bedtime: time = time(23, 0), response: str = "ok") -> dict:
    """主入口：剂量 + 时机 + 睡眠安全检查"""
    low, high = recommended_dose_mg(weight_kg, response)
    out: dict = {
        "dose_low_mg": low,
        "dose_high_mg": high,
        "half_life_h": half_life_hours(response),
        "response_type": response,
    }
    if race_start:
        intake = race_start - timedelta(minutes=50)
        out["intake_at"] = intake.isoformat()
        out["intake_min_pre_race"] = 50
        out["sleep_safe"] = sleep_safe(intake, high, bedtime, response)
    return out
