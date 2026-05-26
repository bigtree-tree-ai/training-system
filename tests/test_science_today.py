"""SciencePrescription 聚合服务单测"""
from training.application.science_today import build_today
from training.science.common.schemas import SciencePrescription


def test_build_today_returns_prescription():
    rx = build_today()
    assert isinstance(rx, SciencePrescription)
    assert rx.training is not None
    assert rx.rehab is not None
    assert rx.nutrition is not None
    assert 0.0 <= rx.confidence <= 1.0


def test_build_today_with_known_injury_includes_rehab():
    rx = build_today()
    rehab = rx.rehab
    assert "return_to_run" in rehab
    assert "active_injuries" in rehab
    # athlete_config v2 中应该有 L_knee + lower_back
    sites = [i["site"] for i in rehab["active_injuries"]]
    assert "L_knee" in sites


def test_llm_payload_well_formed():
    from training.science.llm_prompts import build_payload
    rx = build_today()
    payload = build_payload(rx)
    assert "model" in payload
    assert "messages" in payload
    assert payload["max_tokens"] > 0
    # few-shot: 期望至少 4 个 few-shot + 1 个 user input = 9 messages（4 user + 4 assistant + 1 final user）
    assert len(payload["messages"]) >= 9


def test_verdict_low_ctl_is_detrain():
    """新增的 verdict 修正：低 CTL+正 TSB → detrain"""
    from training.science.training.load_model import compute_load_profile
    # 全部 0 序列 → CTL=0 ATL=0 → detrain
    p = compute_load_profile([("2026-01-01", 0), ("2026-01-02", 0)])
    assert p.verdict == "detrain"
