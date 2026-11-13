"""Interactive, hidden key entry over the user's SSH session. Run with sudo."""
import getpass
import os
from pathlib import Path
import subprocess

if os.geteuid() != 0 or not os.isatty(0):
    raise SystemExit('Execute com sudo no terminal SSH interativo.')
print('Use somente uma chave de projeto no plano Free, sem faturamento pago.')
key = getpass.getpass('Cole a chave Gemini (a digitacao fica oculta): ').strip()
if not key or any(character.isspace() for character in key) or len(key) < 20:
    raise SystemExit('Formato de chave invalido. Nenhuma alteracao feita.')
path = Path('/etc/aio/app.env')
values = dict(line.split('=', 1) for line in path.read_text().splitlines() if '=' in line)
values.update(GEMINI_API_KEY=key, GEMINI_MODEL='gemini-3.1-flash-lite', GEMINI_FREE_TIER_CONFIRMED='true')
temporary = path.with_suffix('.tmp')
temporary.touch(mode=0o600, exist_ok=False)
try:
    temporary.write_text(''.join(f'{name}={value}\n' for name, value in values.items()))
    temporary.replace(path)
finally:
    temporary.unlink(missing_ok=True)
subprocess.run(['systemctl', 'restart', 'aio-api'], check=True)
print('Chave salva com permissao restrita; API reiniciada. Avise no chat apenas: configurado.')
