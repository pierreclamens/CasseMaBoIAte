#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

usage() {
  cat <<'HELP'
Legacy Telecom — labo local
  ./lab.sh start           Construire et démarrer la cible
  ./lab.sh stop            Arrêter (flags et clés SSH conservés)
  ./lab.sh status          État des services
  ./lab.sh logs            Journaux de la cible
  ./lab.sh tools           Ouvrir le conteneur d'attaque optionnel
  ./lab.sh hosts           Afficher la ligne à ajouter dans /etc/hosts
  ./lab.sh check user|root Valider un flag, sans afficher la solution
  ./lab.sh reset           Effacer la progression de CETTE box et redémarrer
  ./lab.sh test            Tests applicatifs locaux (Python 3, sans Docker)
  ./lab.sh verify          Test complet Docker (SPOILERS : exécute le parcours)
HELP
}

action="${1:-help}"
if [[ "$action" == help || "$action" == --help || "$action" == -h ]]; then
  usage
  exit 0
fi
if [[ "$action" == test ]]; then
  exec python3 -B -m unittest discover -s tests -p 'test_*.py' -v
fi
case "$action" in
  start|stop|status|logs|tools|hosts|check|reset|verify) ;;
  *) usage >&2; exit 2 ;;
esac
command -v docker >/dev/null || { echo 'Docker est nécessaire pour cette commande.' >&2; exit 1; }
docker compose version >/dev/null
compose=(docker compose --project-directory "$PWD" -f "$PWD/compose.yaml")

hosts_entry() {
  local address
  address="$("${compose[@]}" exec -T target hostname -i)"
  printf '%s legacy-telecom.hns\n' "$address"
}

case "$action" in
  start)
    "${compose[@]}" up -d --build --wait target
    echo 'Cible démarrée. Ajouter dans /etc/hosts :'
    hosts_entry
    echo 'Site : http://legacy-telecom.hns — SSH : port 22'
    ;;
  stop) "${compose[@]}" --profile tools down ;;
  status) "${compose[@]}" --profile tools ps -a ;;
  logs) "${compose[@]}" logs --tail 100 target ;;
  hosts) hosts_entry ;;
  tools)
    "${compose[@]}" --profile tools up -d --build --wait
    "${compose[@]}" exec attacker bash
    ;;
  check)
    kind="${2:-}"
    [[ "$kind" == user || "$kind" == root ]] || { echo 'Usage : ./lab.sh check user|root' >&2; exit 2; }
    # Le flag passe par stdin : aucune interpolation dans une commande shell.
    read -r -p "Flag ${kind} : " candidate
    printf '%s\n' "$candidate" | "${compose[@]}" exec -T target python3 /opt/legacy/admin.py "$kind"
    ;;
  reset)
    echo 'Réinitialisation de Legacy Telecom : flags, mot de passe et clés SSH remplacés.'
    "${compose[@]}" --profile tools down --volumes
    "${compose[@]}" up -d --build --wait target
    ;;
  verify)
    "${compose[@]}" --profile tools up -d --build --wait
    "${compose[@]}" exec -T attacker python3 /opt/tests/e2e.py
    "${compose[@]}" exec -T target python3 - < tests/runtime.py
    ;;
esac
