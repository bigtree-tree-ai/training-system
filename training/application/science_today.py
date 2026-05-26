"""SciencePrescription 聚合服务 — 把三学科 + 置信度合并成一个今日决策对象

不依赖现有的 application/today.py（它走 product 用户路径），独立给专业版 v2 用。
未来 LLM Coach Agent 会把这个对象作为输入。
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from training.science.common.athlete_profile import AthleteProfile, Injury, load_athlete_profile
from training.science.common.confidence import score_confidence
from training.science.common.schemas import SciencePrescription
from training.science.training.load_model import compute_load_profile
from training.science.training.pyramid import polarization_check
from training.science.training.prescriptions import explain_load, explain_polarization
from training.science.rehab.return_to_run import assess_return_to_run
from training.science.rehab.prescriptions import explain_return_to_run, red_flags
from training.science.nutrition.energy_balance import energy_balance_report
from training.science.nutrition.prescriptions import explain_energy_balance
from training.storage.db import get_conn


def _compute_athlete_age(profile: AthleteProfile) -> int:
    """从 athlete_config 推断年龄；缺省 35"""
    return 35


def _pick_primary_injury(profile: AthleteProfile) -> Optional[Injury]:
    """选择当前最需要关注的伤病：post-op > 高 VAS > 其他"""
    if not profile.injuries:
        return None
    posts = [i for i in profile.injuries if "post-op" in (i.grade or "").lower()]
    if posts:
        return max(posts, key=lambda i: i.last_pain_vas or 0)
    return max(profile.injuries, key=lambda i: i.last_pain_vas or 0)


def _hr_tss_today() -> float:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(hr_tss), 0) AS s FROM sessions WHERE substr(start_time, 1, 10) = ?",
            (date.today().isoformat(),),
        ).fetchone()
    finally:
        conn.close()
    return float(row["s"] or 0)


def _weekly_hard_min() -> float:
    """近 7 天 z4+z5 时间（分钟）"""
    cutoff = (date.today() - timedelta(days=7)).isoformat()
    conn = get_conn()
    try:
        row = conn.execute(
            """SELECT COALESCE(SUM(z.zone4_sec + z.zone5_sec), 0) / 60.0 AS m
               FROM hr_zone_splits z JOIN sessions s ON z.session_id = s.id
               WHERE s.start_time >= ?""",
            (cutoff,),
        ).fetchone()
    finally:
        conn.close()
    return float(row["m"] or 0)


def _recent_vas(site: str, days: int = 14) -> list[float]:
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT vas_0_10 FROM pain_log WHERE site=? AND when_ts >= ? ORDER BY when_ts",
            (site, cutoff),
        ).fetchall()
    finally:
        conn.close()
    return [r["vas_0_10"] for r in rows]


def _today_intake_kcal() -> Optional[float]:
    today = date.today().isoformat()
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT SUM(kcal) AS s FROM nutrition_intake WHERE substr(when_ts, 1, 10) = ?",
            (today,),
        ).fetchone()
    finally:
        conn.close()
    return float(row["s"]) if row and row["s"] is not None else None


def build_today(profile: Optional[AthleteProfile] = None) -> SciencePrescription:
    """主入口：聚合三学科 + 置信度，返回 SciencePrescription"""
    profile = profile or load_athlete_profile()
    today = date.today().isoformat()

    # === Training ===
    conn = get_conn()
    try:
        load_rows = conn.execute(
            "SELECT date, COALESCE(daily_tss, 0) AS load FROM daily_load ORDER BY date"
        ).fetchall()
        cutoff = (date.today() - timedelta(days=7)).isoformat()
        zsum = conn.execute(
            """SELECT
                COALESCE(SUM(z.zone1_sec),0) z1, COALESCE(SUM(z.zone2_sec),0) z2,
                COALESCE(SUM(z.zone3_sec),0) z3, COALESCE(SUM(z.zone4_sec),0) z4,
                COALESCE(SUM(z.zone5_sec),0) z5
               FROM hr_zone_splits z JOIN sessions s ON z.session_id=s.id
               WHERE s.start_time >= ?""",
            (cutoff,),
        ).fetchone()
        last_session = conn.execute("SELECT MAX(start_time) AS t FROM sessions").fetchone()["t"]
        last_load = conn.execute("SELECT MAX(date) AS d FROM daily_load").fetchone()["d"]
        last_hrv = conn.execute("SELECT MAX(date) AS d FROM coros_hrv").fetchone()["d"]
        last_rhr = conn.execute("SELECT MAX(date) AS d FROM coros_heart_rate_daily").fetchone()["d"]
        last_sleep = conn.execute("SELECT MAX(date) AS d FROM coros_sleep").fetchone()["d"]
        today_checkin = conn.execute(
            "SELECT 1 FROM athlete_checkins WHERE date=? LIMIT 1", (today,)
        ).fetchone()
    finally:
        conn.close()

    series = [(r["date"], r["load"]) for r in load_rows]
    lp = compute_load_profile(series)
    pc = polarization_check(zsum["z1"], zsum["z2"], zsum["z3"], zsum["z4"], zsum["z5"])

    training_block = {
        "load_profile": lp.to_dict(),
        "polarization": pc.to_dict(),
        "load_explained": explain_load(lp, profile),
        "polarization_explained": explain_polarization(pc, profile),
    }

    # === Rehab ===
    primary = _pick_primary_injury(profile)
    rtr = assess_return_to_run(
        primary,
        today_vas=primary.last_pain_vas if primary else 0.0,
        recent_vas=_recent_vas(primary.site) if primary else [],
        weekly_hard_min=_weekly_hard_min(),
    )
    rehab_block = {
        "return_to_run": rtr.to_dict(),
        "explained": explain_return_to_run(rtr, primary),
        "red_flags": red_flags(profile.injuries),
        "active_injuries": [
            {"site": i.site, "grade": i.grade, "current_stage": i.current_stage, "vas": i.last_pain_vas}
            for i in profile.injuries
        ],
    }

    # === Nutrition ===
    eb = energy_balance_report(
        profile,
        age=_compute_athlete_age(profile),
        hr_tss_today=_hr_tss_today(),
        intake_kcal=_today_intake_kcal(),
    )
    nutrition_block = {
        "energy_balance": eb.to_dict(),
        "explained": explain_energy_balance(eb, profile),
    }

    # === Confidence ===
    dc = score_confidence(
        has_today_load=bool(last_load and last_load >= today),
        has_today_checkin=bool(today_checkin),
        hrv_latest_date=last_hrv,
        rhr_latest_date=last_rhr,
        sleep_latest_date=last_sleep,
        last_session_date=last_session,
        profile_complete=profile.weight_kg > 0,
        injuries_structured=len(profile.injuries) > 0,
    )

    # === 聚合结论 ===
    severities = [training_block["load_explained"]["severity"],
                  training_block["polarization_explained"]["severity"],
                  rehab_block["explained"]["severity"],
                  nutrition_block["explained"]["severity"]]
    if "danger" in severities:
        verdict = "今天需要降级训练或停训"
    elif "warn" in severities:
        verdict = "今日有需要关注的风险，按建议执行"
    else:
        verdict = "今日状态良好，可正常按计划训练"

    why: list[str] = []
    why.extend(training_block["load_explained"]["why"])
    why.extend(training_block["polarization_explained"]["why"])
    if rehab_block["red_flags"]:
        why.extend(rehab_block["red_flags"])
    why.extend(nutrition_block["explained"].get("why", []))

    next_actions: list[str] = []
    next_actions.extend(training_block["load_explained"]["actions"])
    next_actions.extend(training_block["polarization_explained"]["actions"])
    next_actions.extend(rehab_block["explained"]["actions"])
    next_actions.extend(nutrition_block["explained"]["actions"])

    return SciencePrescription(
        date=today,
        training=training_block,
        rehab=rehab_block,
        nutrition=nutrition_block,
        confidence=dc.score,
        verdict=verdict,
        why=why[:8],
        next_actions=next_actions[:8],
    )
