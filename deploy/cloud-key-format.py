"""Report only non-secret formatting flags; never print credential characters."""
from pathlib import Path
values = dict(line.split('=', 1) for line in Path('/etc/aio/app.env').read_text().splitlines() if '=' in line)
key = values.get('GEMINI_API_KEY', '')
print('RECOGNIZED_KEY_FORMAT=', key.startswith(('AIza', 'AQ.')))
print('SURROUNDING_QUOTES=', len(key) >= 2 and key[0] == key[-1] and key[0] in ('"', "'"))
print('INCLUDES_VARIABLE_NAME=', key.startswith(('GEMINI_API_KEY=', 'GOOGLE_API_KEY=')))
