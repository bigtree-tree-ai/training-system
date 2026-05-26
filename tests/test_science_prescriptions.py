"""阶段 B 处方与解读单测"""
from training.science.common.athlete_profile import AthleteProfile, Injury
from training.science.common.schemas import (
    EnergyBalanceReport,
    LoadProfile,
    PolarizationCheck,
    ReturnToRunStage,
)
from training.science.training.prescriptions import explain_load, explain_polarization
from training.science.rehab.prescriptions import explain_return_to_run, red_flags
from training.science.nutrition.prescriptions import explain_energy_balance


def test_explain_load_detrain_severity():
    lp = LoadProfile(15, 0.2, 14.8, None, None, None, "detrain")
    out = explain_load(lp)
    assert out["severity"] == "warn"
    assert any("重启" in a or "起跑" in a for a in out["actions"])


def test_explain_load_high_injury_risk():
    lp = LoadProfile(50, 80, -30, 1.7, None, None, "high_injury_risk")
    out = explain_load(lp)
    assert out["severity"] == "danger"
    assert any("下调" in a for a in out["actions"])


def test_explain_polarization_easy_heavy():
    pc = PolarizationCheck(95, 3, 2, None, "easy_heavy")
    out = explain_polarization(pc)
    assert out["severity"] == "warn"
    assert "VO2max" in " ".join(out["actions"])


def test_explain_rtr_back_off():
    rtr = ReturnToRunStage(stage=3, stage_name="走跑 1:1", capacity_pct=70, last_pain_vas=5,
                            today_action="back-off", do=["cross-training"], avoid=["跑步"])
    inj = Injury(site="L_knee", grade="II")
    out = explain_return_to_run(rtr, inj)
    assert out["severity"] == "warn"
    assert "降阶" in out["headline"]
    assert "Copenhagen" in " ".join(out["prehab"])


def test_red_flags_high_vas():
    inj = Injury(site="L_knee", grade="II", last_pain_vas=5)
    flags = red_flags([inj])
    assert flags and "禁止跑步" in flags[0]


def test_explain_energy_balance_red():
    eb = EnergyBalanceReport(
        tdee_kcal=3000, intake_kcal=2000, exercise_kcal=800,
        ea_kcal_per_kg_ffm=20, reds_flag="red",
        macros_target={"cho_g": 400, "pro_g": 117, "fat_g": 65},
        notes=["EA<30"],
    )
    out = explain_energy_balance(eb)
    assert out["severity"] == "danger"
    assert any("3000" in a or "kcal" in a for a in out["actions"])
