"""Root-only database integration and restore verification, with no secret output."""
import os
from pathlib import Path
import subprocess

def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)

env = os.environ.copy()
env.update(line.split('=', 1) for line in Path('/etc/aio/app.env').read_text().splitlines() if '=' in line)
env.pop('APP_PUBLIC_DEPLOYMENT', None)
env.pop('APP_CORS_ORIGINS', None)
env.pop('GEMINI_API_KEY', None)
env.pop('GOOGLE_API_KEY', None)
env['RUN_DB_TESTS'] = '1'
run('/opt/aio/.venv/bin/python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', cwd='/opt/aio', env=env)
run('systemctl', 'start', 'aio-backup.service')
backup = sorted(Path('/var/backups/aio').glob('*.dump'))[-1]
scratch = 'aio_restore_validation'
# This database is created solely for the restore test, and is removed afterward.
run('runuser', '-u', 'postgres', '--', 'createdb', scratch)
try:
    with backup.open('rb') as source:
        subprocess.run(['runuser','-u','postgres','--','pg_restore','--exit-on-error','--no-owner','--no-privileges','-d',scratch], stdin=source, check=True)
    result = run('runuser', '-u', 'postgres', '--', 'psql', '-d', scratch, '-Atc', 'SELECT count(*) FROM pedidos', capture_output=True)
    assert result.stdout.strip() == '1000', result.stdout
    print('Backup restoration verified: 1000 orders')
finally:
    run('runuser', '-u', 'postgres', '--', 'dropdb', scratch)
print('Integration and restore checks complete')
