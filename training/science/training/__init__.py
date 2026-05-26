"""运动训练学子包 — Daniels/Friel/Magness/Bompa/Seiler"""

from training.science.training.load_model import (
    compute_load_profile,
    compute_acwr_7_28,
    compute_monotony_strain,
)
from training.science.training.pyramid import polarization_check
from training.science.training.thresholds import (
    estimate_lt_hr_from_recent,
    estimate_critical_speed,
    learn_and_record,
    latest,
)

__all__ = [
    "compute_load_profile",
    "compute_acwr_7_28",
    "compute_monotony_strain",
    "polarization_check",
    "estimate_lt_hr_from_recent",
    "estimate_critical_speed",
    "learn_and_record",
    "latest",
]
