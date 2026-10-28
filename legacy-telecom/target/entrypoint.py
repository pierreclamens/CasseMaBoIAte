import json
import os
import pwd
import secrets
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, '/opt/legacy')
from database import initialize

STATE = Path('/var/lib/legacy-state')


def prepare():
    os.umask(0o077)
    STATE.mkdir(parents=True, exist_ok=True)
    STATE.chmod(0o700)
    state_file = STATE / 'state.json'
    if not state_file.exists():
        state = {
            'user': 'flag{' + secrets.token_hex(16) + '}',
            'root': 'flag{' + secrets.token_hex(16) + '}',
            'password': 'LT-' + secrets.token_hex(8),
        }
        temporary = STATE / 'state.new'
        temporary.write_text(json.dumps(state))
        temporary.chmod(0o600)
        temporary.replace(state_file)
    state = json.loads(state_file.read_text())
    account = pwd.getpwnam('support')
    subprocess.run(['chpasswd'], input=f"support:{state['password']}\n", text=True, check=True)
    for path, value, uid, gid in (
        (Path('/home/support/user.txt'), state['user'], account.pw_uid, account.pw_gid),
        (Path('/root/root.txt'), state['root'], 0, 0),
    ):
        path.write_text(value + '\n')
        os.chown(path, uid, gid)
        path.chmod(0o400)
    Path('/root').chmod(0o700)
    database = Path('/var/lib/legacy-app/portal.db')
    initialize(database, state['password'])
    web = pwd.getpwnam('www-data')
    os.chown(database.parent, web.pw_uid, web.pw_gid)
    database.parent.chmod(0o750)
    os.chown(database, web.pw_uid, web.pw_gid)
    database.chmod(0o400)
    Path('/run/sshd').mkdir(exist_ok=True)
    # Les clés SSH sont générées au lancement, jamais embarquées dans l'image.
    host_key = STATE / 'ssh_host_ed25519_key'
    if not host_key.exists():
        subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(host_key)], check=True)
    subprocess.run(['/usr/sbin/sshd', '-t'], check=True)
    subprocess.run(['/usr/sbin/nginx', '-t'], check=True)
    return web


def main():
    web = prepare()
    children = []
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    children.append(subprocess.Popen(['/usr/sbin/sshd', '-D', '-e'], start_new_session=True))
    children.append(subprocess.Popen(
        [sys.executable, '/opt/legacy/server.py'], user=web.pw_uid,
        group=web.pw_gid, extra_groups=[], start_new_session=True,
    ))
    children.append(subprocess.Popen(['/usr/sbin/nginx', '-g', 'daemon off;'], start_new_session=True))
    print('Legacy Telecom : legacy-telecom.hns — HTTP 80 / SSH 22.', flush=True)
    failed = False
    while not stopping:
        if any(child.poll() is not None for child in children):
            failed = True
            break
        time.sleep(0.25)
    for child in children:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
    for child in children:
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
