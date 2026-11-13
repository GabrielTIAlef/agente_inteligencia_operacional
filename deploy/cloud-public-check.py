"""Run from outside the VM. Uses normal HTTPS certificate verification."""
from concurrent.futures import ThreadPoolExecutor
import json
import re
import socket
import urllib.error
import urllib.request

BASE = 'https://inteligencia-operacional.duckdns.org'
checks = [('/', 200), ('/health', 200), ('/operations/dashboard', 200),
          ('/operations/monitor/runs', 200), ('/reports/operations', 200),
          ('/operations/monitor/run', 404), ('/docs', 404), ('/.env', 404),
          ('/agent/chat', 415)]
for path, expected in checks:
    request = urllib.request.Request(BASE + path, method='POST' if path in {'/agent/chat', '/operations/monitor/run'} else 'GET')
    try:
        response = urllib.request.urlopen(request, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        assert response.status == expected, (path, response.status, expected)
        if path == '/':
            html = response.read().decode()
            script = re.search(r'src="(/assets/[^\"]+\.js)"', html).group(1)
            with urllib.request.urlopen(BASE + script, timeout=15) as asset:
                javascript = asset.read().decode()
            assert 'Conversar com IA' in javascript, 'Chat button missing from published build'
            assert 'Chat de IA indisponível nesta demonstração' not in javascript
        if path == '/operations/monitor/runs':
            assert any(run['status'] == 'completed' for run in json.load(response)['runs'])
    print(path, expected)
request = urllib.request.Request(BASE+'/health', headers={'Origin':'https://untrusted.example'})
try:
    urllib.request.urlopen(request, timeout=15)
    raise AssertionError('Unexpected origin accepted')
except urllib.error.HTTPError as error:
    assert error.code == 403
print('Untrusted origin rejected')

def check_port(port):
    try:
        with socket.create_connection(('137.131.236.116', port), timeout=3):
            return port, True
    except (OSError, TimeoutError):
        return port, False

with ThreadPoolExecutor(max_workers=6) as pool:
    results = dict(pool.map(check_port, [22,80,443,5432,8000,5678]))
assert results == {22:True,80:True,443:True,5432:False,8000:False,5678:False}, results
print('Public port checks passed', results)
