"""补液策略 — ACSM Hydration Position Stand

每日基础需水：30-40 ml/kg
训练补水：替代汗液 70-100%（出汗率 × 时长）
失水阈值：>2% 体重 → 表现下降；>4% → 健康风险
"""
from __future__ import annotations

from typing import Optional


def daily_baseline_ml(weight_kg: float) -> int:
    """每日基础需水量（不含训练）"""
    return int(weight_kg * 35)


def training_intake_ml_per_h(sweat_rate_ml_per_h: float, replacement_pct: float = 0.7) -> int:
    """训练中每小时建议补水（默认替代 70% 汗液）"""
    return int(sweat_rate_ml_per_h * replacement_pct)


def sweat_loss_pct_body_weight(sweat_rate_ml_per_h: float, duration_min: float, weight_kg: float, intake_ml: float = 0) -> float:
    """训练中失水占体重百分比

    失水量(g) = 出汗量 - 摄入量；1 ml ≈ 1 g
    """
    sweat_total = sweat_rate_ml_per_h * (duration_min / 60.0)
    net_loss = max(sweat_total - intake_ml, 0)
    if weight_kg <= 0:
        return 0.0
    return round(net_loss / (weight_kg * 1000) * 100, 2)


def hydration_alert(loss_pct: float) -> Optional[str]:
    if loss_pct >= 4.0:
        return "严重失水（>4% BW）— 立即降低强度并补水"
    if loss_pct >= 2.0:
        return "中度失水（>2% BW）— 表现下降，加强补给"
    return None
