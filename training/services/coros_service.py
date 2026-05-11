"""Service layer for COROS structured dashboard data."""
from __future__ import annotations

from training.coros.storage import get_coros_overview


def get_coros_dashboard_data(overview: dict | None = None) -> dict:
    overview = overview or get_coros_overview()
    fitness = _defaults(
        overview.get("fitness", {}),
        (
            "vo2max",
            "running_level",
            "threshold_pace_sec",
            "five_k_prediction_sec",
            "ten_k_prediction_sec",
            "half_marathon_prediction_sec",
            "marathon_prediction_sec",
        ),
    )
    recovery = _defaults(
        overview.get("recovery", {}),
        ("recovery_pct", "level", "estimated_full_recovery_hours"),
    )
    profile = _defaults(overview.get("profile", {}), ("height_cm", "weight_kg", "nickname"))
    daily = overview.get("daily_health", [])
    sleep = overview.get("sleep", [])
    hrv = overview.get("hrv", [])
    heart = overview.get("heart_rate", [])
    stress = overview.get("stress", [])
    load = overview.get("training_load", [])
    schedule = overview.get("schedule", [])

    return {
        "training": {
            "fitness": fitness,
            "training_load": load,
            "avg_load_ratio": _avg(load, "load_ratio"),
            "optimized_days": sum(1 for row in load if row.get("comment") == "Optimized"),
            "upcoming_load_tl": sum(row.get("load_tl") or 0 for row in schedule),
        },
        "daily_life": {
            "daily_health": daily,
            "avg_steps": _avg(daily, "steps"),
            "avg_exercise_min": _avg(daily, "exercise_min"),
            "avg_calories_kcal": _avg(daily, "calories_kcal"),
        },
        "health_recovery": {
            "recovery": recovery,
            "sleep": sleep,
            "hrv": hrv,
            "heart_rate": heart,
            "stress": stress,
            "avg_sleep_score": _avg(sleep, "sleep_score"),
            "avg_sleep_hours": _avg_minutes_as_hours(sleep, "main_sleep_min"),
            "avg_awake_min": _avg(sleep, "awake_min"),
            "avg_hrv": _avg(hrv, "hrv_avg_ms"),
            "avg_resting_hr": _avg(heart, "resting_hr"),
            "avg_stress": _avg(stress, "stress_avg"),
        },
        "planning_devices": {
            "profile": profile,
            "devices": overview.get("devices", []),
            "schedule": schedule,
            "sync_runs": overview.get("sync_runs", []),
        },
    }


def _avg(rows: list[dict], key: str) -> float | None:
    values = [row[key] for row in rows if row.get(key) is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def _avg_minutes_as_hours(rows: list[dict], key: str) -> float | None:
    avg = _avg(rows, key)
    return round(avg / 60, 2) if avg is not None else None


def _defaults(data: dict, keys: tuple[str, ...]) -> dict:
    value = dict(data or {})
    for key in keys:
        value.setdefault(key, None)
    return value
