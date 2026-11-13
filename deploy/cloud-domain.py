"""Enable the approved DuckDNS hostname after issuing its free certificate."""
from pathlib import Path
import subprocess

domain = 'inteligencia-operacional.duckdns.org'
assert Path(f'/etc/letsencrypt/live/{domain}/fullchain.pem').exists()
path = Path('/etc/aio/app.env')
lines = path.read_text().splitlines()
origins = f'APP_CORS_ORIGINS=https://{domain},https://137.131.236.116'
updated = [origins if line.startswith('APP_CORS_ORIGINS=') else line for line in lines]
if not any(line.startswith('APP_CORS_ORIGINS=') for line in lines):
    updated.append(origins)
path.write_text('\n'.join(updated)+'\n')
path.chmod(0o600)
target = Path('/etc/nginx/sites-available/aio-https')
previous = target.read_text()
Path('/etc/aio/nginx-before-duckdns.conf').write_text(previous)
target.write_text(Path('/opt/aio/deploy/cloud-nginx.conf').read_text())
try:
    subprocess.run(['nginx','-t'], check=True)
except subprocess.CalledProcessError:
    target.write_text(previous)
    raise
subprocess.run(['systemctl','restart','aio-api'], check=True)
subprocess.run(['systemctl','reload','nginx'], check=True)
print('DuckDNS HTTPS and explicit CORS configured; secrets unchanged')
