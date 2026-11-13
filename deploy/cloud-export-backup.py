"""Root-only read/export of completed database backups over existing SSH access."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

FOLDER = Path('/var/backups/aio')
NAME = re.compile(r'\d{8}T\d{6}Z\.dump')

def main():
    if os.geteuid() != 0:
        raise SystemExit('Run through sudo over SSH')
    if sys.argv[1:] == ['manifest']:
        files = sorted(path for path in FOLDER.glob('*.dump') if NAME.fullmatch(path.name) and not path.is_symlink())
        if not files:
            raise SystemExit('No completed backup found')
        path = files[-1]
        with path.open('rb') as handle:
            digest = hashlib.file_digest(handle, 'sha256').hexdigest()
        print(json.dumps({'name': path.name, 'size': path.stat().st_size, 'sha256': digest}))
    elif len(sys.argv) == 3 and sys.argv[1] == 'stream' and NAME.fullmatch(sys.argv[2]):
        path = FOLDER / sys.argv[2]
        if path.is_symlink() or path.resolve().parent != FOLDER.resolve():
            raise SystemExit('Invalid backup path')
        with path.open('rb') as handle:
            shutil.copyfileobj(handle, sys.stdout.buffer)
    else:
        raise SystemExit('Use manifest or stream <backup-name>')

if __name__ == '__main__':
    main()
