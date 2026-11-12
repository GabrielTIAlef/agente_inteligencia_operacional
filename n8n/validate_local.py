"""Teste opt-in do retry do n8n em um workflow inativo separado, sem segredos no output."""
import json
import os
import sqlite3
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx

from etl.load_orders import BASE_DIR  # carrega o .env sem imprimi-lo


def main():
    root = Path(os.environ['LOCALAPPDATA']) / 'Author Software/nvm/installs'
    installs = sorted(root.glob('v*/node.exe'), key=lambda p: tuple(map(int, p.parent.name[1:].split('.'))))
    node = installs[-1]
    cli = node.parent / 'node_modules/n8n/bin/n8n'
    env = os.environ.copy()
    env.update(N8N_RUNNERS_BROKER_PORT='5681', N8N_DIAGNOSTICS_ENABLED='false')
    env['PATH'] = str(node.parent) + os.pathsep + env.get('PATH', '')

    def command(*args):
        result = subprocess.run([str(node), str(cli), *args], env=env, cwd=BASE_DIR,
                                capture_output=True, text=True, timeout=600)
        # Não publicar stdout/stderr: falhas do HTTP Request podem incluir headers.
        return result

    database = Path.home() / '.n8n/database.sqlite'
    with sqlite3.connect('file:' + database.as_posix() + '?mode=ro', uri=True) as connection:
        candidates = connection.execute('SELECT id, nodes FROM workflow_entity').fetchall()
    target = next((row for row in candidates if any(
        n.get('parameters', {}).get('url') == 'http://127.0.0.1:8000/operations/monitor/run'
        for n in json.loads(row[1]))), None)
    if not target:
        raise RuntimeError('Workflow operacional local não encontrado.')
    workflow = json.loads((BASE_DIR / 'n8n/operations-report.json').read_text(encoding='utf-8'))
    workflow.update(id='OpsMonitorRetryTest1', name='VALIDAÇÃO LOCAL — retry e falha (inativo)', active=False)
    original_http = next(n for n in json.loads(target[1]) if n['type'].endswith('httpRequest'))
    http_node = next(n for n in workflow['nodes'] if n['type'].endswith('httpRequest'))
    http_node['credentials'] = original_http['credentials']
    state = {'calls': 0, 'always_fail': False}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            state['calls'] += 1
            if state['always_fail'] or state['calls'] == 1:
                payload, status = {'detail': 'Falha temporária simulada para teste local.'}, 503
            else:
                response = httpx.post('http://127.0.0.1:8000/operations/monitor/run',
                    headers={'Authorization': self.headers.get('Authorization', '')}, timeout=30)
                payload, status = response.json(), response.status_code
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    http_node['parameters']['url'] = f'http://127.0.0.1:{server.server_port}/monitor-test'
    threading.Thread(target=server.serve_forever, daemon=True).start()
    fd, path = tempfile.mkstemp(suffix='.json')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            json.dump(workflow, output)
        result = command('import:workflow', '--input=' + path)
        assert result.returncode == 0 and 'Successfully imported' in result.stdout, 'Importação não confirmada'
        print('Workflow de validação importado e inativo.', flush=True)
        result = command('execute', '--id=OpsMonitorRetryTest1')
        assert result.returncode == 0 and state['calls'] == 2, 'Retry com recuperação não confirmado'
        print('503 temporário: duas tentativas, recuperação e sucesso confirmados.', flush=True)
        state.update(calls=0, always_fail=True)
        result = command('execute', '--id=OpsMonitorRetryTest1')
        assert result.returncode != 0 and state['calls'] == 2, 'Falha persistente não confirmada'
        print('503 persistente: duas tentativas e falha visível no n8n confirmadas.', flush=True)
    finally:
        Path(path).unlink(missing_ok=True)
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
