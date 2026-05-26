"""运动营养学子包 — IOC 2018 / RED-S 2023 / Burke / Jeukendrup"""

from training.science.nutrition.energy_balance import (
    compute_tdee,
    compute_energy_availability,
    energy_balance_report,
)
from training.science.nutrition.macros import macros_target
from training.science.nutrition.fueling import fueling_plan
from training.science.nutrition.caffeine import plan as caffeine_plan, sleep_safe as caffeine_sleep_safe
from training.science.nutrition.hydration import (
    daily_baseline_ml,
    training_intake_ml_per_h,
    sweat_loss_pct_body_weight,
    hydration_alert,
)
from training.science.nutrition.electrolytes import plan as electrolytes_plan, sodium_per_h

__all__ = [
    "compute_tdee",
    "compute_energy_availability",
    "energy_balance_report",
    "macros_target",
    "fueling_plan",
    "caffeine_plan",
    "caffeine_sleep_safe",
    "daily_baseline_ml",
    "training_intake_ml_per_h",
    "sweat_loss_pct_body_weight",
    "hydration_alert",
    "electrolytes_plan",
    "sodium_per_h",
]
