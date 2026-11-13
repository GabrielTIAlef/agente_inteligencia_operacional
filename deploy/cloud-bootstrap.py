"""Run as root on the existing Ubuntu VM after copying this source to /opt/aio.

No OCI resources or external paid services are created. Secrets stay on the VM.
"""
import os
from pathlib import Path
import secrets
import subprocess

def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)

def write(path, content, mode=0o644):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    target.chmod(mode)

if os.geteuid() != 0:
    raise SystemExit("Run as root")
if not Path('/etc/aio/app.env').exists():
    password = secrets.token_hex(32)
    monitor = secrets.token_hex(32)
    run('useradd', '--system', '--home', '/var/lib/aio', '--create-home', '--shell', '/usr/sbin/nologin', 'aio')
    write('/etc/postgresql/16/main/conf.d/aio.conf', """listen_addresses = '127.0.0.1'
shared_buffers = '32MB'
max_connections = 15
work_mem = '2MB'
maintenance_work_mem = '16MB'
effective_cache_size = '128MB'
max_parallel_workers_per_gather = 0
""")
    run('systemctl', 'restart', 'postgresql')
    run('runuser', '-u', 'postgres', '--', 'psql', '-v', 'ON_ERROR_STOP=1', input=f"CREATE ROLE aio LOGIN PASSWORD '{password}';\nCREATE DATABASE aio OWNER aio;\n")
    write('/etc/aio/app.env', f"""DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=aio
DB_USER=aio
DB_PASSWORD={password}
MONITOR_TOKEN={monitor}
MONITOR_GEMINI_ENABLED=false
MONITOR_NOTIFICATION_MODE=off
APP_PUBLIC_DEPLOYMENT=true
APP_CORS_ORIGINS=https://137.131.236.116
GEMINI_FREE_TIER_CONFIRMED=false
""", 0o600)
    chat_password = secrets.token_urlsafe(24)
    write('/etc/aio/chat-login.txt', f'URL: https://137.131.236.116\nUser: mentor\nPassword: {chat_password}\n', 0o600)
    result = run('htpasswd', '-niB', 'mentor', input=chat_password+'\n', capture_output=True)
    write('/etc/aio/chat.htpasswd', result.stdout, 0o640)
    run('chown', 'root:www-data', '/etc/aio/chat.htpasswd')
    # Small swap file uses only the existing free boot disk.
    if not Path('/swapfile').exists():
        run('fallocate', '-l', '1G', '/swapfile')
        Path('/swapfile').chmod(0o600)
        run('mkswap', '/swapfile')
        run('swapon', '/swapfile')
        with open('/etc/fstab', 'a') as handle:
            handle.write('\n/swapfile none swap sw 0 0\n')

env = os.environ.copy()
env.update(line.split('=', 1) for line in Path('/etc/aio/app.env').read_text().splitlines() if line and not line.startswith('#'))
run('python3', '-m', 'venv', '/opt/aio/.venv')
run('/opt/aio/.venv/bin/pip', 'install', '--no-cache-dir', '-r', '/opt/aio/requirements-dev.txt')
migration_env = env.copy()
if Path('/etc/aio/migration.env').exists():
    migration_env.update(line.split('=', 1) for line in Path('/etc/aio/migration.env').read_text().splitlines() if '=' in line)
run('/opt/aio/.venv/bin/python', '-m', 'etl.migrate', cwd='/opt/aio', env=migration_env)
# Only seed an empty database, never overwrite existing orders during deployment.
count = run('runuser', '-u', 'postgres', '--', 'psql', '-d', 'aio', '-Atc', 'SELECT count(*) FROM pedidos', capture_output=True).stdout.strip()
if count == '0':
    run('/opt/aio/.venv/bin/python', '-m', 'etl.load_orders', cwd='/opt/aio', env=migration_env)
# Runtime identity cannot alter orders/schema; monitor can only append its history.
run('runuser', '-u', 'postgres', '--', 'psql', '-d', 'aio', '-v', 'ON_ERROR_STOP=1', input="""
CREATE ROLE aio_runtime LOGIN;
GRANT CONNECT ON DATABASE aio TO aio_runtime;
GRANT USAGE ON SCHEMA public TO aio_runtime;
GRANT SELECT ON pedidos, monitor_runs TO aio_runtime;
GRANT INSERT ON monitor_runs TO aio_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO aio_runtime;
""" if env['DB_USER'] == 'aio' else 'SELECT 1;')
if env['DB_USER'] == 'aio':
    runtime_password = secrets.token_hex(32)
    run('runuser', '-u', 'postgres', '--', 'psql', '-v', 'ON_ERROR_STOP=1', input=f"ALTER ROLE aio_runtime PASSWORD '{runtime_password}';")
    write('/etc/aio/migration.env', Path('/etc/aio/app.env').read_text(), 0o600)
    env.update(DB_USER='aio_runtime', DB_PASSWORD=runtime_password)
    write('/etc/aio/app.env', ''.join(f'{key}={value}\n' for key, value in env.items() if key in {'DB_HOST','DB_PORT','DB_NAME','DB_USER','DB_PASSWORD','MONITOR_TOKEN','MONITOR_GEMINI_ENABLED','MONITOR_NOTIFICATION_MODE','APP_PUBLIC_DEPLOYMENT','APP_CORS_ORIGINS','GEMINI_FREE_TIER_CONFIRMED'}), 0o600)
run('cp', '/opt/aio/deploy/cloud-api.service', '/etc/systemd/system/aio-api.service')
write('/etc/nginx/aio-proxy.conf', """proxy_set_header Host localhost;
proxy_set_header X-Forwarded-For "";
proxy_set_header X-Real-IP "";
proxy_set_header X-Forwarded-Proto https;
proxy_pass http://127.0.0.1:8000;
""")
run('install', '-d', '-m', '755', '/var/www/aio', '/var/www/acme/.well-known/acme-challenge')
run('cp', '-r', '/opt/aio/frontend/dist/.', '/var/www/aio/')
write('/etc/nginx/sites-available/aio-bootstrap', """server {
listen 80 default_server;
server_name 137.131.236.116;
server_tokens off;
location ^~ /.well-known/acme-challenge/ { root /var/www/acme; }
location / { return 503; }
}
""")
default = Path('/etc/nginx/sites-enabled/default')
if default.is_symlink():
    default.unlink()
link = Path('/etc/nginx/sites-enabled/aio')
if not link.exists():
    link.symlink_to('/etc/nginx/sites-available/aio-bootstrap')
run('nginx', '-t')
run('systemctl', 'reload', 'nginx')
run('systemctl', 'daemon-reload')
run('systemctl', 'enable', '--now', 'aio-api')
for port in ('80', '443'):
    result = subprocess.run(['iptables','-C','INPUT','-p','tcp','--dport',port,'-j','ACCEPT'], capture_output=True)
    if result.returncode:
        run('iptables', '-I', 'INPUT', '4', '-p', 'tcp', '--dport', port, '-j', 'ACCEPT')
run('netfilter-persistent', 'save')
write('/etc/systemd/journald.conf.d/aio.conf', '[Journal]\nSystemMaxUse=100M\nRuntimeMaxUse=30M\nMaxRetentionSec=14day\n')
run('systemctl', 'restart', 'systemd-journald')
print('Bootstrap ready. HTTPS and scheduled jobs still require finalization.')
