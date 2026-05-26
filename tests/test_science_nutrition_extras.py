"""营养扩展模块单测：caffeine / hydration / electrolytes"""
from datetime import datetime, time

from training.science.nutrition.caffeine import (
    plan as caffeine_plan,
    recommended_dose_mg,
    sleep_safe,
)
from training.science.nutrition.hydration import (
    daily_baseline_ml,
    hydration_alert,
    sweat_loss_pct_body_weight,
    training_intake_ml_per_h,
)
from training.science.nutrition.electrolytes import plan as electrolytes_plan, sodium_per_h


def test_caffeine_dose_normal():
    low, high = recommended_dose_mg(65)
    assert low == 195 and high == 390


def test_caffeine_dose_sensitive_lower():
    low, _ = recommended_dose_mg(65, "sensitive")
    assert low == 130


def test_caffeine_sleep_safe_morning_intake():
    intake = datetime(2026, 5, 26, 8, 0)
    assert sleep_safe(intake, 200, time(23, 0)) is True


def test_caffeine_sleep_unsafe_late_intake():
    intake = datetime(2026, 5, 26, 19, 0)
    # 19:00 + 5h = 24:00，刚好与 23:00 间隔 4h，不安全
    assert sleep_safe(intake, 250, time(23, 0)) is False


def test_caffeine_plan_with_race():
    rs = datetime(2026, 6, 1, 7, 0)
    p = caffeine_plan(65, race_start=rs, bedtime=time(23, 0))
    assert p["intake_min_pre_race"] == 50
    assert p["sleep_safe"] is True


def test_hydration_baseline():
    assert daily_baseline_ml(65) == 65 * 35


def test_training_intake_ml_default_70pct():
    assert training_intake_ml_per_h(800) == 560


def test_sweat_loss_severe_alert():
    loss = sweat_loss_pct_body_weight(1500, 180, 65, intake_ml=500)
    # 出汗 4500 - 500 = 4000g / 65000 = 6.15%
    assert loss > 4
    assert hydration_alert(loss) is not None and "严重" in hydration_alert(loss)


def test_sweat_loss_safe():
    loss = sweat_loss_pct_body_weight(800, 60, 65, intake_ml=500)
    assert loss < 1
    assert hydration_alert(loss) is None


def test_electrolytes_long_session_high_na():
    p = electrolytes_plan(duration_min=240, sweat_rate_ml_per_h=1000, sweat_na_mg_per_l=1200)
    assert p["sodium_mg_per_h"] >= 800


def test_electrolytes_short_session_zero():
    p = electrolytes_plan(duration_min=45)
    assert p["sodium_mg_per_h"] == 0


def test_electrolytes_cramp_history_increases_na():
    p = electrolytes_plan(duration_min=120, cramp_history=True)
    assert p["sodium_mg_per_h"] >= 800
    assert any("抽筋" in n for n in p["notes"])


def test_sodium_per_h_basic():
    assert sodium_per_h(1000, 1000) == 700
