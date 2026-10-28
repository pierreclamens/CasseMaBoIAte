"""Validation réservée à l'opérateur, sans afficher les flags attendus."""
import hmac
import json
import sys
from pathlib import Path

if len(sys.argv) != 2 or sys.argv[1] not in ('user', 'root'):
    sys.exit('Usage : admin.py user|root (flag sur entrée standard)')
expected = json.loads(Path('/var/lib/legacy-state/state.json').read_text())[sys.argv[1]]
candidate = sys.stdin.readline(256).strip()
valid = hmac.compare_digest(expected.encode(), candidate.encode())
print('Flag validé !' if valid else 'Flag incorrect.')
sys.exit(0 if valid else 1)
