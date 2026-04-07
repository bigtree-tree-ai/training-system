"""统一配置管理 — 所有可配置项集中在此，支持环境变量覆盖"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_ROOT = PROJECT_ROOT.parent  # 06-运动数据AI化/

# ---------- 数据库 ----------
DB_PATH = Path(os.getenv("TRAIN_DB_PATH", str(PROJECT_ROOT / "training.db")))

# ---------- FIT 文件目录 ----------
COROS_FIT_DIR = Path(os.getenv("TRAIN_FIT_DIR", str(DATA_ROOT / "高驰的运动数据导出")))
EXTRA_FIT_DIR = DATA_ROOT  # 根目录下的单独FIT文件
CSV_PATH = DATA_ROOT / "all_sessions.csv"

# ---------- Web 服务 ----------
WEB_HOST = os.getenv("TRAIN_WEB_HOST", "127.0.0.1")
WEB_PORT = int(os.getenv("TRAIN_WEB_PORT", "8080"))

# ---------- AI ----------
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("TRAIN_CLAUDE_MODEL", "claude-sonnet-4-20250514")

# ---------- 运动员参数 ----------
MAX_HEART_RATE = 173
RESTING_HEART_RATE = 56
HEART_RATE_RESERVE = MAX_HEART_RATE - RESTING_HEART_RATE  # 117
LACTATE_THRESHOLD_HR = int(RESTING_HEART_RATE + 0.88 * HEART_RATE_RESERVE)  # ~159

# 心率分区（Karvonen法）
HR_ZONES = {
    "Z1": {"name": "恢复", "min": 0,   "max": int(RESTING_HEART_RATE + 0.60 * HEART_RATE_RESERVE)},  # <126
    "Z2": {"name": "有氧", "min": 126,  "max": int(RESTING_HEART_RATE + 0.70 * HEART_RATE_RESERVE)},  # 126-138
    "Z3": {"name": "节奏", "min": 138,  "max": int(RESTING_HEART_RATE + 0.80 * HEART_RATE_RESERVE)},  # 138-150
    "Z4": {"name": "阈值", "min": 150,  "max": int(RESTING_HEART_RATE + 0.90 * HEART_RATE_RESERVE)},  # 150-161
    "Z5": {"name": "极量", "min": 161,  "max": 185},
}

# ---------- 赛事 ----------
GOBI_RACE_DATE = "2026-10-15"  # 戈21正赛（预估）
