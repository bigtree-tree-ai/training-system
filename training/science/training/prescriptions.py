"""训练学处方文案 — 把 LoadProfile / PolarizationCheck 翻译成可读建议

设计原则：
- 不只输出"verdict 标签"，再附 1-2 句具体动作建议
- 个体化：考虑 athlete_profile 的目标周量、当前阶段、伤病
- 仍保留旧 interpretations.py 兼容（不删，避免破坏现有引用）
"""
from __future__ import annotations

from typing import Optional

from training.science.common.athlete_profile import AthleteProfile
from training.science.common.schemas import LoadProfile, PolarizationCheck


def explain_load(lp: LoadProfile, profile: Optional[AthleteProfile] = None) -> dict:
    """LoadProfile → {headline, action, why, severity}"""
    sev_map = {
        "no_data": "info",
        "detrain": "warn",
        "balanced": "ok",
        "build": "ok",
        "peak": "ok",
        "overreach": "warn",
        "monotonous_overreach": "warn",
        "high_injury_risk": "danger",
    }
    severity = sev_map.get(lp.verdict, "info")
    headline_map = {
        "no_data": "缺少负荷数据",
        "detrain": "体能基线偏低，需重启训练",
        "balanced": "训练与恢复平衡，状态稳定",
        "build": "正在积累训练刺激",
        "peak": "处于 peak 窗口，可安排关键训练或测试赛",
        "overreach": "急性疲劳明显，需要恢复",
        "monotonous_overreach": "负荷单调（缺乏变化），过劳风险",
        "high_injury_risk": "ACWR 飙升，伤病风险高",
    }
    actions: list[str] = []
    if lp.verdict == "detrain":
        target = profile.weekly_volume_target_km if profile and profile.weekly_volume_target_km else None
        if target:
            actions.append(f"按目标 {target}km/周 的 50-60% 起跑 2 周，渐进恢复")
        else:
            actions.append("先以低强度 Z2 跑 30-45 min × 3-4 次/周 重启 2 周")
        actions.append("配合 2 次力量+灵活性训练，避免高冲击")
    elif lp.verdict == "high_injury_risk":
        actions.append("立即将本周训练量下调 30-40%")
        actions.append("近 7 天暂停 Z4 / Z5 间歇")
    elif lp.verdict in ("overreach", "monotonous_overreach"):
        actions.append("安排 2-3 天 active recovery（散步/游泳/伸展）")
        actions.append("睡眠 ≥ 8h，蛋白 ≥ 1.8 g/kg")
    elif lp.verdict == "build":
        actions.append("继续当前刺激 1-2 周，然后插入减量周（量 -30%）")
    elif lp.verdict == "peak":
        actions.append("可安排测试赛或关键间歇课")
    elif lp.verdict == "balanced":
        actions.append("按计划继续；若想加量，每周 ≤ +10%")

    why = []
    why.append(f"CTL={lp.ctl}, ATL={lp.atl}, TSB={lp.tsb}")
    if lp.acwr_7_28 is not None:
        why.append(f"ACWR(7d:28d)={lp.acwr_7_28}")
    if lp.monotony is not None:
        why.append(f"Monotony={lp.monotony}, Strain={lp.strain}")

    return {
        "severity": severity,
        "headline": headline_map.get(lp.verdict, lp.verdict),
        "actions": actions,
        "why": why,
        "verdict": lp.verdict,
    }


def explain_polarization(pc: PolarizationCheck, profile: Optional[AthleteProfile] = None) -> dict:
    sev_map = {
        "no_data": "info",
        "polarized": "ok",
        "balanced": "ok",
        "easy_heavy": "warn",
        "threshold_heavy": "warn",
    }
    severity = sev_map.get(pc.verdict, "info")
    headline_map = {
        "no_data": "缺少分区数据",
        "polarized": "强度分布健康（符合 80/20 极化）",
        "balanced": "强度分布过于平均，建议向极化靠拢",
        "easy_heavy": "训练偏轻松，缺少高强度刺激",
        "threshold_heavy": "节奏区时间过多（'易跑窃取'）",
    }
    actions: list[str] = []
    if pc.verdict == "easy_heavy":
        actions.append("每周加 1 次 VO2max 间歇（4×4min Z4-Z5 慢跑恢复）")
    elif pc.verdict == "threshold_heavy":
        actions.append("把节奏跑改成 Z2 长跑或 Z4 短间歇，减少 Z3 时长")
    elif pc.verdict == "balanced":
        actions.append("增加 Z2 量到 ≥75%，保留 1-2 次 Z4+ 间歇")

    return {
        "severity": severity,
        "headline": headline_map.get(pc.verdict, pc.verdict),
        "actions": actions,
        "why": [f"Easy {pc.easy_pct}% / Mod {pc.moderate_pct}% / Hard {pc.hard_pct}%"],
        "verdict": pc.verdict,
        "polarization_index": pc.polarization_index,
    }
