"""康复学处方文案 — 把 ReturnToRunStage / 负荷-疼痛矩阵翻译成可读建议"""
from __future__ import annotations

from typing import Optional

from training.science.common.athlete_profile import AthleteProfile, Injury
from training.science.common.schemas import ReturnToRunStage


_PREHAB_BY_SITE = {
    "L_knee": [
        "Copenhagen 侧桥 3×30s（左右）",
        "单腿提踵 3×15",
        "靠墙静蹲 3×45s",
        "弹力带髋外展 3×15",
    ],
    "R_knee": [
        "Copenhagen 侧桥 3×30s（左右）",
        "单腿提踵 3×15",
        "靠墙静蹲 3×45s",
    ],
    "lower_back": [
        "死虫式 3×10",
        "鸟狗式 3×10/侧",
        "髋桥 3×15",
        "猫驼伸展 3×10",
    ],
    "achilles": [
        "离心提踵 3×15（直腿+屈膝）",
        "小腿筋膜放松 2 min",
    ],
    "ITB": [
        "蚌式开合 3×15",
        "侧卧抬腿 3×15",
        "髋外展拉伸 60s/侧",
    ],
    "plantar_fascia": [
        "高尔夫球足底滚 3 min",
        "跟腱+小腿拉伸 60s×3",
        "脚趾抓毛巾 3×30s",
    ],
}


def explain_return_to_run(rtr: ReturnToRunStage, injury: Optional[Injury] = None) -> dict:
    """RTR 阶段 → {headline, action, prehab, severity}"""
    sev_map = {
        "back-off": "warn",
        "advance": "ok",
        "keep": "info",
        "stop": "danger",
    }
    severity = sev_map.get(rtr.today_action, "info")
    headline_map = {
        "back-off": f"今日降阶到「{rtr.stage_name}」",
        "advance": f"今日可进阶到「{rtr.stage_name}」",
        "keep": f"维持「{rtr.stage_name}」",
        "stop": "今日停跑",
    }
    prehab: list[str] = []
    if injury and injury.site in _PREHAB_BY_SITE:
        prehab = _PREHAB_BY_SITE[injury.site]

    return {
        "severity": severity,
        "headline": headline_map.get(rtr.today_action, ""),
        "actions": rtr.do,
        "avoid": rtr.avoid,
        "prehab": prehab,
        "stage": rtr.stage,
        "today_vas": rtr.last_pain_vas,
    }


def red_flags(injuries: list[Injury]) -> list[str]:
    """检查活跃伤病的红线规则"""
    out: list[str] = []
    for i in injuries:
        if i.last_pain_vas and i.last_pain_vas >= 4:
            out.append(f"{i.site} 当前痛 VAS={i.last_pain_vas}，禁止跑步")
        if i.grade and "post-op" in i.grade.lower() and i.capacity_pct and i.capacity_pct < 70:
            out.append(f"{i.site} 术后承载力 {i.capacity_pct}%，建议保留 ≥6 个月力量积累")
    return out
