"""Integração opt-in com PostgreSQL; tabelas temporárias e rollback integral."""
import os
from contextlib import contextmanager
from datetime import date

import pytest
from fastapi import HTTPException

from app import monitor
from etl.load_orders import conectar_banco

pytestmark = pytest.mark.skipif(
    os.getenv('RUN_DB_TESTS') != '1', reason='Defina RUN_DB_TESTS=1 para PostgreSQL local',
)


def test_failure_recovery_and_idempotence_in_temporary_table(monkeypatch):
    monkeypatch.setenv('MONITOR_TOKEN', 'isolated-test-token')
    monkeypatch.setenv('MONITOR_GEMINI_ENABLED', 'false')
    connection = conectar_banco()
    try:
        connection.execute('CREATE TEMP TABLE monitor_runs (LIKE public.monitor_runs INCLUDING ALL) ON COMMIT DROP')

        @contextmanager
        def isolated_connection(**kwargs):
            yield connection

        monkeypatch.setattr(monitor, 'conectar_banco', isolated_connection)

        def fail():
            raise TimeoutError('simulated processing failure')

        monkeypatch.setattr(monitor, 'read_snapshot', fail)
        with pytest.raises(HTTPException) as error:
            monitor.run_monitor('Bearer isolated-test-token')
        assert error.value.status_code == 503
        assert connection.execute("SELECT status, report FROM pg_temp.monitor_runs").fetchall() == [('failed', None)]

        monkeypatch.setattr(monitor, 'read_snapshot', lambda: {
            'period': {'start_date': date(2026, 1, 1), 'end_date': date(2026, 1, 14)},
            'summary': {'orders': 0, 'cancellation': None, 'late': None},
            'previous': None,
        })
        first = monitor.run_monitor('Bearer isolated-test-token')
        second = monitor.run_monitor('Bearer isolated-test-token')
        assert first['id'] == second['id']
        assert first['status'] == 'completed'
        assert connection.execute('SELECT count(*) FROM pg_temp.monitor_runs').fetchone()[0] == 2
    finally:
        connection.rollback()
        connection.close()
