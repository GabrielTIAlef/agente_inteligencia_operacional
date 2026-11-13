"""Real anonymous chat smoke test via public HTTPS, using synthetic data."""
import json
import urllib.error
import urllib.request

request = urllib.request.Request(
    'https://inteligencia-operacional.duckdns.org/agent/chat',
    data=json.dumps({'message': 'Consulte a ferramenta de indicadores gerais e informe quantos pedidos existem na base completa.'}).encode(),
    headers={'Content-Type':'application/json', 'Origin':'https://inteligencia-operacional.duckdns.org'},
)
try:
    with urllib.request.urlopen(request, timeout=100) as response:
        result = json.load(response)
except urllib.error.HTTPError as error:
    print('CHAT_HTTP_STATUS=', error.code)
    print(error.read().decode()[:1000])
    raise SystemExit(1)
assert result.get('status') == 'success', 'Unexpected chat status'
answer = result.get('response', '')
assert any(value in answer for value in ('1.000', '1000', '1,000')), 'Expected total not present'
print('CHAT_PUBLIC_HTTPS_OK')
print(answer)
