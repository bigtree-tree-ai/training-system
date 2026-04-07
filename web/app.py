"""FastAPI Web应用 — 页面路由"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

import config
from storage.db import init_db
from storage.queries import (
    get_all_sessions, get_session_by_id, get_laps_for_session,
    get_hr_zones_for_session, get_weekly_summaries, get_ai_reports,
)
from web.api import router as api_router

import os
ROOT_PATH = os.environ.get("ROOT_PATH", "")

app = FastAPI(title="训练分析系统")

templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"
templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.include_router(api_router, prefix="/api")


def format_pace(seconds):
    if not seconds:
        return "-"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


def format_duration(seconds):
    if not seconds:
        return "-"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_sport(sport):
    mapping = {'running': '跑步', 'cycling': '骑行', 'training': '力量训练',
               'hiking': '徒步', 'walking': '步行'}
    return mapping.get(sport, sport or '未知')


# 注册Jinja2过滤器
templates.env.filters['pace'] = format_pace
templates.env.filters['duration'] = format_duration
templates.env.filters['sport_cn'] = format_sport
templates.env.globals['base'] = ROOT_PATH


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    from storage.db import get_conn
    conn = get_conn()

    # 本周数据
    latest_week = conn.execute("""
        SELECT * FROM weekly_summaries ORDER BY year DESC, week_number DESC LIMIT 1
    """).fetchone()

    # 最新PMC
    latest_pmc = conn.execute("""
        SELECT date, atl, ctl, tsb FROM daily_load ORDER BY date DESC LIMIT 1
    """).fetchone()

    # 最近5次训练
    recent = conn.execute("""
        SELECT id, sport, start_time, distance_km, duration_sec, avg_hr, avg_pace_sec, hr_tss
        FROM sessions ORDER BY start_time DESC LIMIT 5
    """).fetchall()

    # 预警
    from analysis.trend_detector import detect_warnings
    warnings = detect_warnings()

    # 戈壁倒计时 (2026-10-01预估)
    race_date = datetime(2026, 10, 1)
    days_to_race = (race_date.date() - datetime.now().date()).days

    conn.close()

    return templates.TemplateResponse(request, "dashboard.html", {
        "week": dict(latest_week) if latest_week else {},
        "pmc": dict(latest_pmc) if latest_pmc else {},
        "recent_sessions": [dict(r) for r in recent],
        "warnings": warnings,
        "days_to_race": days_to_race,
    })


@app.get("/sessions", response_class=HTMLResponse)
async def session_list(request: Request, sport: str = None, page: int = 1):
    limit = 20
    offset = (page - 1) * limit
    sessions = get_all_sessions(sport=sport, limit=limit, offset=offset)

    from storage.db import get_conn
    conn = get_conn()
    total = conn.execute(
        "SELECT COUNT(*) as cnt FROM sessions" + (" WHERE sport=?" if sport else ""),
        (sport,) if sport else ()
    ).fetchone()['cnt']
    conn.close()

    total_pages = (total + limit - 1) // limit

    return templates.TemplateResponse(request, "session_list.html", {
        "sessions": sessions,
        "sport": sport,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    })


@app.get("/sessions/{session_id}", response_class=HTMLResponse)
async def session_detail(request: Request, session_id: int):
    session = get_session_by_id(session_id)
    if not session:
        return HTMLResponse("Session not found", status_code=404)

    laps = get_laps_for_session(session_id)
    hr_zones = get_hr_zones_for_session(session_id)

    return templates.TemplateResponse(request, "session_detail.html", {
        "session": session,
        "laps": laps,
        "hr_zones": hr_zones,
    })


@app.get("/weekly", response_class=HTMLResponse)
async def weekly_view(request: Request):
    weeks = get_weekly_summaries(limit=15)
    return templates.TemplateResponse(request, "weekly_view.html", {
        "weeks": weeks,
    })


@app.get("/ai-insights", response_class=HTMLResponse)
async def ai_insights(request: Request):
    reports = get_ai_reports(limit=20)
    return templates.TemplateResponse(request, "ai_insights.html", {
        "reports": reports,
    })
