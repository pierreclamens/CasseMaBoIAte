"""Contrôles opérateur dans la cible ; aucune valeur de secret n'est affichée."""
import json
import pwd
import stat
import subprocess
from pathlib import Path


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


state_dir = Path('/var/lib/legacy-state')
state = json.loads((state_dir / 'state.json').read_text())
require(stat.S_IMODE(state_dir.stat().st_mode) == 0o700, 'Volume des secrets trop ouvert.')
require(stat.S_IMODE((state_dir / 'state.json').stat().st_mode) == 0o600, 'État trop ouvert.')
support = pwd.getpwnam('support')
for path, kind, uid in (
    (Path('/home/support/user.txt'), 'user', support.pw_uid),
    (Path('/root/root.txt'), 'root', 0),
):
    require(path.read_text().strip() == state[kind], 'Flag non synchronisé avec le volume.')
    require(path.stat().st_uid == uid, 'Propriétaire de flag incorrect.')
    require(stat.S_IMODE(path.stat().st_mode) == 0o400, 'Permissions de flag incorrectes.')
    good = subprocess.run(['python3', '/opt/legacy/admin.py', kind], input=state[kind] + '\n', text=True, capture_output=True)
    bad = subprocess.run(['python3', '/opt/legacy/admin.py', kind], input='incorrect\n', text=True, capture_output=True)
    require(good.returncode == 0 and bad.returncode == 1, 'Validation des flags incorrecte.')
print('OK — propriétaires, permissions, synchronisation et validation des flags.')

web_processes = []
for path in Path('/proc').glob('[0-9]*/cmdline'):
    try:
        if b'/opt/legacy/server.py' in path.read_bytes().split(b'\0'):
            web_processes.append(path.parent)
    except FileNotFoundError:
        continue
require(len(web_processes) == 1, 'Un seul processus HTTP est attendu.')
status = (web_processes[0] / 'status').read_text()
uid_line = next(line for line in status.splitlines() if line.startswith('Uid:'))
require(all(int(uid) == pwd.getpwnam('www-data').pw_uid for uid in uid_line.split()[1:]), 'Le portail ne tourne pas comme www-data.')
require('CapEff:\t0000000000000000' in status, 'Le portail conserve des capacités privilégiées.')
print('OK — portail exécuté comme www-data, sans capacité effective.')
routes = Path('/proc/net/route').read_text().splitlines()[1:]
require(all(line.split()[1] != '00000000' for line in routes), 'La cible ne doit pas avoir de route par défaut.')
print('OK — cible sans route réseau par défaut.')
