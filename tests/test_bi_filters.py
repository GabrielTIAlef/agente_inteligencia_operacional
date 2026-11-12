"""Cross-filter behavior and export contract, with isolated PostgreSQL coverage."""
import os
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import reports
from app.dashboard import snapshot
from etl.load_orders import conectar_banco


def test_filtered_report_preserves_metrics_and_scope(monkeypatch):
    def dashboard(start, end, region, category, status):
        assert (start, end, region, category, status) == (
            date(2026, 10, 1), date(2026, 10, 14), 'Sul', 'Mercado', 'entregue')
        metric = {'orders': 2, 'value': 125.5, 'cancellation': 0, 'late': 0}
        return {'period': {'start': start, 'end': end}, 'summary': metric,
                'regions': [{'label': region, **metric}],
                'categories': [{'label': category, **metric}],
                'daily': [{'date': start, 'orders': 2}], 'previous': None}
    monkeypatch.setattr(reports, 'dashboard', dashboard)
    response = TestClient(app).get('/reports/operations', params={
        'start': '2026-10-01', 'end': '2026-10-14', 'region': 'Sul',
        'category': 'Mercado', 'status': 'entregue'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['summary']['total_pedidos'] == 2
    assert payload['summary']['valor_total'] == 125.5
    assert payload['scope']['status'] == 'entregue'
    assert payload['regions'][0]['regiao'] == 'Sul'
    assert payload['categories'][0]['categoria'] == 'Mercado'


@pytest.mark.parametrize('path', ['/operations/dashboard', '/reports/operations'])
@pytest.mark.parametrize('params', [
    {'status': 'invalid'}, {'start': '2026-10-01'},
    {'start': '2026-10-15', 'end': '2026-10-01'},
])
def test_invalid_bi_filters_rejected(path, params):
    assert TestClient(app).get(path, params=params).status_code == 422


@pytest.mark.skipif(os.getenv('RUN_DB_TESTS') != '1', reason='Requires local PostgreSQL')
def test_all_visuals_and_previous_window_share_filters():
    connection = conectar_banco()
    try:
        connection.execute('''CREATE TEMP TABLE pedidos (
            data_pedido date, regiao text, categoria text, valor numeric, status text
        ) ON COMMIT DROP''')
        for day, region, category, value, status in [
            (1, 'Sul', 'Mercado', 10, 'entregue'),
            (15, 'Sul', 'Mercado', 20, 'entregue'),
            (16, 'Sul', 'Mercado', 30, 'cancelado'),
            (17, 'Norte', 'Mercado', 40, 'entregue'),
            (18, 'Sul', 'Casa', 50, 'entregue'),
            (28, 'Sul', 'Mercado', 60, 'entregue'),
        ]:
            connection.execute('INSERT INTO pg_temp.pedidos VALUES (%s,%s,%s,%s,%s)',
                               (date(2026, 10, day), region, category, Decimal(value), status))
        view = snapshot(connection, date(2026, 10, 15), date(2026, 10, 28),
                        'Sul', 'Mercado', status='entregue')
        assert view['summary']['orders'] == 2
        assert view['summary']['value'] == 80
        assert view['previous']['orders'] == 1
        assert view['previous']['value'] == 10
        assert sum(row['orders'] for row in view['daily']) == 2
        assert [row['label'] for row in view['regions']] == ['Sul']
        assert [row['label'] for row in view['categories']] == ['Mercado']
        assert view['status_context']['status']['cancelado'] == 1
        assert view['summary']['status']['cancelado'] == 0
        empty = snapshot(connection, date(2026, 10, 15), date(2026, 10, 28),
                         'Sul', 'Mercado', status='em_atraso')
        assert empty['summary']['orders'] == 0
        assert empty['summary']['value'] == 0
        assert empty['summary']['cancellation'] is None
        assert not empty['regions']
    finally:
        connection.rollback()
        connection.close()
