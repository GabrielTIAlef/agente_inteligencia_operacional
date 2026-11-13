"""Restrict SSH to the administrator's current IPv4, keeping Oracle service rules."""
import ipaddress
import os
from pathlib import Path
import subprocess

def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)

source = str(ipaddress.IPv4Address(os.environ['ADMIN_IPV4']))
for family in ('iptables', 'ip6tables'):
    target = Path('/etc/aio') / (family + '-before-ssh.rules')
    if not target.exists():
        result = run(family+'-save', capture_output=True)
        target.write_text(result.stdout)
        target.chmod(0o600)
result = subprocess.run(['iptables','-C','INPUT','-s',source+'/32','-p','tcp','--dport','22','-j','ACCEPT'], capture_output=True)
if result.returncode:
    run('iptables','-I','INPUT','4','-s',source+'/32','-p','tcp','--dport','22','-j','ACCEPT')
result = subprocess.run(['iptables','-C','INPUT','-p','tcp','-m','state','--state','NEW','--dport','22','-j','ACCEPT'], capture_output=True)
if result.returncode == 0:
    run('iptables','-D','INPUT','-p','tcp','-m','state','--state','NEW','--dport','22','-j','ACCEPT')
# There is no configured public IPv6 endpoint for this deployment.
result = subprocess.run(['ip6tables','-C','INPUT','-p','tcp','--dport','22','-j','REJECT'], capture_output=True)
if result.returncode:
    run('ip6tables','-I','INPUT','1','-p','tcp','--dport','22','-j','REJECT')
Path('/etc/ssh/sshd_config.d/00-aio-hardening.conf').write_text('PasswordAuthentication no\nPermitRootLogin no\nMaxAuthTries 3\nAllowUsers ubuntu\n')
run('sshd','-t')
run('systemctl','reload','ssh')
run('netfilter-persistent','save')
print('SSH restricted to the current administrator IPv4; password and root login disabled')
