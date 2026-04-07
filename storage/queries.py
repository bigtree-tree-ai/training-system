"""数据读取查询函数"""
from .db import get_conn


def get_all_sessions(sport=None, limit=None, offset=0):
    conn = get_conn()
    sql = "SELECT * FROM sessions"
    params = []
    if sport:
        sql += " WHERE sport=?"
        params.append(sport)
    sql += " ORDER BY start_time DESC"
    if limit:
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_by_id(session_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_session_by_filename(filename: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM sessions WHERE filename=?", (filename,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_laps_for_session(session_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM laps WHERE session_id=? ORDER BY lap_index", (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_hr_zones_for_session(session_id: int):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM hr_zone_splits WHERE session_id=?", (session_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_daily_load(from_date=None, to_date=None):
    conn = get_conn()
    sql = "SELECT * FROM daily_load"
    params = []
    conditions = []
    if from_date:
        conditions.append("date >= ?")
        params.append(from_date)
    if to_date:
        conditions.append("date <= ?")
        params.append(to_date)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY date"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_weekly_summaries(limit=None):
    conn = get_conn()
    sql = "SELECT * FROM weekly_summaries ORDER BY year DESC, week_number DESC"
    params = []
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_ai_reports(report_type=None, limit=20):
    conn = get_conn()
    sql = "SELECT * FROM ai_reports"
    params = []
    if report_type:
        sql += " WHERE report_type=?"
        params.append(report_type)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_count():
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) as cnt FROM sessions").fetchone()
    conn.close()
    return row['cnt']


def get_running_sessions(from_date=None, to_date=None):
    conn = get_conn()
    sql = "SELECT * FROM sessions WHERE sport='running'"
    params = []
    if from_date:
        sql += " AND start_time >= ?"
        params.append(from_date)
    if to_date:
        sql += " AND start_time <= ?"
        params.append(to_date)
    sql += " ORDER BY start_time"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_imported_filenames():
    """获取已导入的文件名集合"""
    conn = get_conn()
    rows = conn.execute("SELECT filename FROM sessions").fetchall()
    conn.close()
    return {r['filename'] for r in rows}
