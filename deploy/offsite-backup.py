"""Download a verified database backup; no dependencies, passwords or cloud costs."""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re
import subprocess
import sys

def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()

def save_status(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)

def main():
    root = Path(__file__).resolve().parent
    logger = logging.getLogger('offsite')
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(root/'backup.log', maxBytes=1024*1024, backupCount=3, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(handler)
    status_path = root/'status.json'
    previous = json.loads(status_path.read_text(encoding='utf-8')) if status_path.exists() else {}
    temporary = None
    try:
        config = json.loads((root/'config.json').read_text(encoding='utf-8-sig'))
        folder = Path(config['backup_directory']).resolve()
        folder.mkdir(parents=True, exist_ok=True)
        ssh = [config['ssh_executable'], '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
               '-o', 'ConnectTimeout=15', '-o', 'ConnectionAttempts=3', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
               '-i', config['identity_file'], config['ssh_target']]
        remote = 'sudo -n python3 /opt/aio/deploy/cloud-export-backup.py '
        result = subprocess.run(ssh+[remote+'manifest'], capture_output=True, text=True, timeout=90, check=True)
        manifest = json.loads(result.stdout)
        name, size, expected = manifest['name'], manifest['size'], manifest['sha256']
        if not re.fullmatch(r'\d{8}T\d{6}Z\.dump', name) or not re.fullmatch(r'[0-9a-f]{64}', expected):
            raise ValueError('Invalid backup manifest')
        if not isinstance(size, int) or not 5 < size <= 256*1024*1024:
            raise ValueError('Unexpected backup size')
        stamp = datetime.strptime(name, '%Y%m%dT%H%M%SZ.dump').replace(tzinfo=timezone.utc)
        if not timedelta(minutes=-5) <= datetime.now(timezone.utc)-stamp <= timedelta(hours=30):
            raise ValueError('Remote backup is stale or has an invalid timestamp')
        target = folder/name
        if target.exists() and target.stat().st_size == size and digest(target) == expected:
            action = 'already_verified'
        else:
            temporary = folder/(name+'.partial')
            with temporary.open('wb') as output:
                subprocess.run(ssh+[remote+'stream '+name], stdout=output, stderr=subprocess.PIPE, timeout=180, check=True)
            if temporary.stat().st_size != size or digest(temporary) != expected:
                raise ValueError('Backup checksum/size mismatch; previous copies preserved')
            with temporary.open('rb') as handle:
                if handle.read(5) != b'PGDMP':
                    raise ValueError('Invalid PostgreSQL archive header')
            temporary.replace(target)
            action = 'downloaded'
        # Retention applies only to this application's verified dump filenames.
        copies = sorted(path for path in folder.glob('*.dump') if re.fullmatch(r'\d{8}T\d{6}Z\.dump', path.name) and not path.is_symlink())
        for old in copies[:-30]:
            if old.resolve().parent != folder:
                raise ValueError('Unexpected retention path')
            old.unlink()
        status = {'ok': True, 'last_attempt_utc': datetime.now(timezone.utc).isoformat(),
                  'last_success_utc': datetime.now(timezone.utc).isoformat(), 'backup': name,
                  'sha256': expected, 'size': size, 'action': action}
        save_status(status_path, status)
        logger.info('Verified %s (%s bytes): %s', name, size, action)
        print(json.dumps(status))
        return 0
    except Exception as error:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        # No command arguments, provider keys, or SSH stderr are written to logs.
        previous.update(ok=False, last_attempt_utc=datetime.now(timezone.utc).isoformat(), error_type=type(error).__name__)
        save_status(status_path, previous)
        logger.error('Backup failed: %s; previous verified copies preserved', type(error).__name__)
        print('Backup failed: '+type(error).__name__, file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
