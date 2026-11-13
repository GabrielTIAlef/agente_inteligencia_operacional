"""Finalize the existing VM only after the free IP certificate has been issued."""
from pathlib import Path
import subprocess

def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)

def write(path, text, mode=0o644):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')
    target.chmod(mode)

assert Path('/etc/letsencrypt/live/137.131.236.116/fullchain.pem').exists()
assert Path('/etc/letsencrypt/live/inteligencia-operacional.duckdns.org/fullchain.pem').exists()
run('cp', '/opt/aio/deploy/cloud-nginx.conf', '/etc/nginx/sites-available/aio-https')
link = Path('/etc/nginx/sites-enabled/aio')
link.unlink()
link.symlink_to('/etc/nginx/sites-available/aio-https')
run('nginx', '-t')
run('systemctl', 'reload', 'nginx')

for name, schedule, argument in (
    ('monitor', '*-*-* 09:00:00 America/Sao_Paulo', 'monitor'),
    ('health', '*-*-* *:0/5:00', 'health'),
):
    write(f'/etc/systemd/system/aio-{name}.service', f'''[Unit]
Description=AI Operations {name}
After=aio-api.service
[Service]
Type=oneshot
User=aio
Group=aio
WorkingDirectory=/opt/aio
EnvironmentFile=/etc/aio/app.env
ExecStart=/opt/aio/.venv/bin/python -m deploy.cloud-jobs {argument}
TimeoutStartSec=60
MemoryMax=160M
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
''')
    write(f'/etc/systemd/system/aio-{name}.timer', f'''[Unit]
Description=AI Operations {name} schedule
[Timer]
OnCalendar={schedule}
Persistent=true
[Install]
WantedBy=timers.target
''')
write('/usr/local/sbin/aio-backup', '''#!/usr/bin/python3
from datetime import datetime, timezone
from pathlib import Path
import subprocess
folder = Path('/var/backups/aio')
folder.mkdir(mode=0o700, parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
temporary = folder / (stamp + '.partial')
with temporary.open('wb') as output:
    subprocess.run(['runuser','-u','postgres','--','pg_dump','-Fc','aio'], stdout=output, check=True)
temporary.chmod(0o600)
temporary.rename(folder / (stamp + '.dump'))
for old in sorted(folder.glob('*.dump'))[:-7]:
    old.unlink()
print('Database backup completed')
''', 0o750)
write('/etc/systemd/system/aio-backup.service', '''[Unit]
Description=AI Operations local database backup
After=postgresql.service
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/aio-backup
UMask=0077
''')
write('/etc/systemd/system/aio-backup.timer', '''[Unit]
Description=Daily database backup
[Timer]
OnCalendar=*-*-* 03:00:00 America/Sao_Paulo
Persistent=true
[Install]
WantedBy=timers.target
''')
write('/etc/systemd/system/aio-cert-renew.service', '''[Unit]
Description=Renew free IP certificate
[Service]
Type=oneshot
ExecStart=/opt/certbot/bin/certbot renew --quiet --no-random-sleep-on-renew
''')
write('/etc/systemd/system/aio-cert-renew.timer', '''[Unit]
Description=Check short lived certificate twice daily
[Timer]
OnCalendar=*-*-* 00,12:00:00
RandomizedDelaySec=1800
Persistent=true
[Install]
WantedBy=timers.target
''')
run('systemctl', 'daemon-reload')
run('systemctl', 'enable', '--now', 'aio-monitor.timer', 'aio-health.timer', 'aio-backup.timer', 'aio-cert-renew.timer')
run('systemctl', 'start', 'aio-monitor.service', 'aio-health.service', 'aio-backup.service')
print('HTTPS, monitoring, health checks, backups and renewal configured')
