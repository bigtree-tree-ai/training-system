"""对比分析测试"""
import pytest
from training.services.comparison_service import compare_periods
from training.services.session_service import get_session_detail
from training.storage.queries import get_session_count


class TestComparePeriods:
    def test_30day_comparison(self):
        data = compare_periods(days=30)
        assert 'current_period' in data
        assert 'previous_period' in data
        assert 'metrics' in data
        assert len(data['metrics']) > 0
        assert 'summary' in data

    def test_metrics_structure(self):
        data = compare_periods(days=30)
        for m in data['metrics']:
            assert 'name' in m
            assert 'current' in m
            assert 'previous' in m
            assert 'trend' in m
            assert m['trend'] in ('better', 'worse', 'same')


class TestSessionComparison:
    def _get_latest_session_id(self):
        """动态获取最新session_id，不硬编码"""
        from training.storage.db import get_conn, init_db
        init_db()
        conn = get_conn()
        try:
            row = conn.execute("SELECT id FROM sessions ORDER BY start_time DESC LIMIT 1").fetchone()
            return row['id'] if row else None
        finally:
            conn.close()

    def test_with_valid_session(self):
        sid = self._get_latest_session_id()
        if sid is None:
            pytest.skip("No sessions in database")
        data = get_session_detail(sid)
        assert data is not None
        assert 'session' in data
        assert 'laps' in data

    def test_with_invalid_session(self):
        data = get_session_detail(99999)
        assert data is None

    def test_comparison_data(self):
        sid = self._get_latest_session_id()
        if sid is None:
            pytest.skip("No sessions in database")
        data = get_session_detail(sid)
        if data and data.get('comparison'):
            comp = data['comparison']
            assert 'metrics' in comp
            assert 'overall' in comp
            assert comp['overall'] in ('improving', 'declining', 'stable')
