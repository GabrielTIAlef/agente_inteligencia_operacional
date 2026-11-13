"""A damaged transfer must never replace an earlier verified backup."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

def test_corrupt_download_preserves_previous_copy_and_success(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1]/'deploy'/'offsite-backup.py'
    spec = importlib.util.spec_from_file_location('offsite_client_test', source)
    client = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(client)
    monkeypatch.setattr(client, '__file__', str(tmp_path/'offsite-backup.py'))
    folder = tmp_path/'copies'
    folder.mkdir()
    previous = folder/'20260101T000000Z.dump'
    previous.write_bytes(b'PGDMP-previous-verified-copy')
    (tmp_path/'config.json').write_text(json.dumps({
        'backup_directory':str(folder), 'ssh_executable':'unused',
        'identity_file':'unused', 'ssh_target':'unused',
    }))
    (tmp_path/'status.json').write_text(json.dumps({'ok':True, 'last_success_utc':'previous-success'}))
    stamp = client.datetime.now(client.timezone.utc).strftime('%Y%m%dT%H%M%SZ.dump')
    def fake_run(arguments, **kwargs):
        if arguments[-1].endswith('manifest'):
            return SimpleNamespace(stdout=json.dumps({'name':stamp,'size':20,'sha256':'0'*64}))
        kwargs['stdout'].write(b'PGDMP-corrupted-data')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(client.subprocess, 'run', fake_run)
    try:
        assert client.main() == 1
        assert previous.read_bytes() == b'PGDMP-previous-verified-copy'
        assert not list(folder.glob('*.partial'))
        assert not (folder/stamp).exists()
        status = json.loads((tmp_path/'status.json').read_text())
        assert status['ok'] is False
        assert status['last_success_utc'] == 'previous-success'
    finally:
        for handler in list(client.logging.getLogger('offsite').handlers):
            handler.close()
            client.logging.getLogger('offsite').removeHandler(handler)
