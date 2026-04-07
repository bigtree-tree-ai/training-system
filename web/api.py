"""JSON API — Chart.js数据源"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import APIRouter
from storage.queries import get_daily_load, get_weekly_summaries
from storage.db import get_conn

router = APIRouter()


@router.get("/pmc")
async def pmc_data(days: int = 90):
    """PMC曲线数据 (ATL/CTL/TSB)"""
    from datetime import datetime, timedelta
    from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    data = get_daily_load(from_date=from_date)
    return {
        "dates": [d['date'] for d in data],
        "atl": [d['atl'] for d in data],
        "ctl": [d['ctl'] for d in data],
        "tsb": [d['tsb'] for d in data],
        "tss": [d['daily_tss'] for d in data],
    }


@router.get("/weekly-volume")
async def weekly_volume(weeks: int = 12):
    """周跑量柱状图"""
    data = get_weekly_summaries(limit=weeks)
    data.reverse()
    return {
        "labels": [f"W{d['week_number']}" for d in data],
        "run_km": [d['run_distance_km'] or 0 for d in data],
        "total_km": [d['total_distance_km'] or 0 for d in data],
        "hr_tss": [d['total_hr_tss'] or 0 for d in data],
    }


@router.get("/zone-distribution")
async def zone_distribution(days: int = 14):
    """心率分区分布"""
    from datetime import datetime, timedelta
    from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    conn = get_conn()
    row = conn.execute("""
        SELECT
            ROUND(SUM(h.zone1_sec), 0) as z1,
            ROUND(SUM(h.zone2_sec), 0) as z2,
            ROUND(SUM(h.zone3_sec), 0) as z3,
            ROUND(SUM(h.zone4_sec), 0) as z4,
            ROUND(SUM(h.zone5_sec), 0) as z5
        FROM sessions s
        JOIN hr_zone_splits h ON s.id = h.session_id
        WHERE s.sport='running' AND s.start_time >= ? AND h.zone1_pct IS NOT NULL
    """, (from_date,)).fetchone()
    conn.close()

    if not row or row['z1'] is None:
        return {"labels": [], "values": [], "colors": []}

    total = sum([row['z1'], row['z2'], row['z3'], row['z4'], row['z5']])
    if total == 0:
        return {"labels": [], "values": [], "colors": []}

    return {
        "labels": ["Z1 恢复", "Z2 有氧", "Z3 节奏", "Z4 阈值", "Z5 极量"],
        "values": [
            round(row['z1'] / total * 100, 1),
            round(row['z2'] / total * 100, 1),
            round(row['z3'] / total * 100, 1),
            round(row['z4'] / total * 100, 1),
            round(row['z5'] / total * 100, 1),
        ],
        "colors": ["#4CAF50", "#2196F3", "#FF9800", "#f44336", "#9C27B0"],
    }


@router.get("/pace-trend")
async def pace_trend(limit: int = 20):
    """轻松跑配速趋势"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT DATE(start_time) as date, avg_pace_sec, distance_km, avg_hr
        FROM sessions
        WHERE sport='running' AND avg_pace_sec IS NOT NULL AND avg_pace_sec > 330
        ORDER BY start_time DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    rows = list(reversed(rows))
    return {
        "dates": [r['date'] for r in rows],
        "pace": [r['avg_pace_sec'] for r in rows],
        "hr": [r['avg_hr'] for r in rows],
        "distance": [r['distance_km'] for r in rows],
    }


@router.post("/analyze/macro")
def trigger_macro_analysis(days: int = 30):
    """触发AI宏观分析（同步，FastAPI自动在线程池运行）"""
    from ai_coach.coach import macro_review
    result = macro_review(days=days)
    if result.startswith("[错误]"):
        return {"success": False, "error": result}
    return {"success": True, "preview": result[:200] + "..."}


@router.post("/analyze/session/{session_id}")
def trigger_session_analysis(session_id: int):
    """触发AI单次训练分析（同步，FastAPI自动在线程池运行）"""
    from ai_coach.coach import session_review
    result = session_review(session_id)
    if result.startswith("[错误]"):
        return {"success": False, "error": result}
    return {"success": True, "preview": result[:200] + "..."}


@router.post("/pipeline")
def run_pipeline():
    """一键全流程: 导入→分析→AI"""
    results = []
    try:
        from data_import.batch_import import scan_and_import
        scan_and_import()
        results.append("FIT导入完成")
    except Exception as e:
        results.append(f"FIT导入失败: {e}")

    try:
        from analysis.session_metrics import compute_all_session_metrics
        from analysis.macro_metrics import compute_daily_load
        from analysis.weekly_summary import compute_weekly_summaries
        compute_all_session_metrics()
        compute_daily_load()
        compute_weekly_summaries()
        results.append("分析计算完成")
    except Exception as e:
        results.append(f"分析计算失败: {e}")

    return {"success": True, "steps": results}


@router.get("/summary")
async def summary():
    """概览数据"""
    conn = get_conn()

    total = conn.execute("SELECT COUNT(*) as cnt FROM sessions").fetchone()['cnt']
    running = conn.execute("SELECT COUNT(*) as cnt FROM sessions WHERE sport='running'").fetchone()['cnt']
    total_km = conn.execute("SELECT ROUND(SUM(distance_km), 1) as km FROM sessions WHERE sport='running'").fetchone()['km']
    total_hrs = conn.execute("SELECT ROUND(SUM(duration_sec)/3600, 1) as hrs FROM sessions").fetchone()['hrs']

    conn.close()
    return {
        "total_sessions": total,
        "running_sessions": running,
        "total_running_km": total_km or 0,
        "total_hours": total_hrs or 0,
    }
