# Legacy Telecom

Box Linux **très facile**, inspirée de TalkTalk (2015). Deux objectifs : trouver `user.txt`, puis `root.txt`. Prévoir environ 30 à 60 minutes pour une première découverte.

La [mission](docs/MISSION.md) ne dévoile pas le parcours. Le [corrigé](docs/SOLUTION.md), le code source et les tests d’intégration contiennent des spoilers.

## Démarrer et configurer le nom

Prérequis : **Docker Engine natif sur Linux**, Docker Compose v2 avec `--wait`, Bash et Internet pour construire les images. La box n’a pas besoin d’Internet pendant l’exécution. Python 3 sur l’hôte sert uniquement aux tests applicatifs.

```bash
cd legacy-telecom
./lab.sh start
```

La cible a sa propre IP fixe, **`172.30.10.10`**, avec **Nginx sur 80** et **SSH sur 22**. Aucun port n’est publié sur l’IP de l’hôte : son propre SSH et les futures box peuvent utiliser les mêmes numéros de ports.

Ajouter cette ligne dans `/etc/hosts` sur la machine qui exécute Docker, avec `sudoedit /etc/hosts` :

```text
172.30.10.10 legacy-telecom.hns
```

Si une entrée existe pour ce nom, la remplacer. `./lab.sh hosts` affiche la ligne correspondant à l’IP réelle de la cible démarrée ; le script ne modifie pas lui-même le fichier système.

Ouvrir **http://legacy-telecom.hns**. Aucun identifiant initial n’est fourni.

## Explorer comme une box HTB

Depuis la machine Linux qui exécute Docker, après configuration de `/etc/hosts` :

```bash
nmap -sT -Pn -sV -p- legacy-telecom.hns
curl http://legacy-telecom.hns/
ssh utilisateur@legacy-telecom.hns
```

Remplacer `utilisateur` par le compte découvert pendant l’exercice. Aucun `-p` spécifique n’est nécessaire pour SSH.

`/etc/hosts` associe un nom à une IP ; il ne redirige pas les ports. L’IP propre à chaque box permet de scanner ses services. Nginx transmet les requêtes au portail Python, qui écoute uniquement sur `127.0.0.1:8080` **dans la cible**. Ce backend n’est pas accessible sur l’IP de la box.

Un poste d’attaque optionnel fournit `curl`, `nmap`, `ssh`, `sshpass` et Python :

```bash
./lab.sh tools
# Dans ce conteneur, le nom est déjà résolu par le DNS Docker.
nmap -sT -Pn -sV -p- legacy-telecom.hns
curl http://legacy-telecom.hns/
ssh utilisateur@legacy-telecom.hns
```

Ce poste utilise `-sT -Pn` car il ne dispose pas des capacités nécessaires aux paquets bruts. Il reste sur le réseau interne du labo.

## Kali dans une autre VM et Docker Desktop

L’IP du bridge Docker est directement joignable depuis **l’hôte Linux Docker**. Voir la [documentation du bridge Docker](https://docs.docker.com/engine/network/drivers/bridge/).

Une entrée `/etc/hosts` ne rend pas cette IP routable depuis une autre VM ou un autre ordinateur. Pour jouer depuis Kali, exécuter Docker directement dans Kali, ou utiliser le poste d’attaque fourni. Un accès depuis une VM séparée demande un routage ou un VPN de labo adapté, qui n’est pas configuré ici. Ce mode d’accès n’est pas prévu pour Docker Desktop sur macOS ou Windows.

## Personnaliser l’IP

Si `172.30.10.0/24` entre en conflit avec un réseau existant, copier `.env.example` vers `.env` et modifier **les deux valeurs ensemble**, par exemple :

```dotenv
LEGACY_SUBNET=172.30.50.0/24
LEGACY_IP=172.30.50.10
```

Choisir une adresse libre du sous-réseau, hors de l’adresse réseau, de broadcast et de la passerelle Docker (habituellement `.1`). Faire `./lab.sh stop` avant de changer le sous-réseau, puis `./lab.sh start`, et actualiser `/etc/hosts`.

## Flags et gestion

```bash
./lab.sh check user
./lab.sh check root
./lab.sh status
./lab.sh logs
./lab.sh stop
./lab.sh start
./lab.sh reset
```

Le validateur demande la valeur découverte. Les deux flags sont aléatoires, distincts et propres à ton installation, au format `flag{32_caracteres_hexadecimaux}`.

`stop` conserve le volume des flags, le mot de passe et les clés SSH. `start` réutilise ces valeurs. Les autres modifications disparaissent lors de la recréation du conteneur. `reset` supprime uniquement le volume de ce projet et remplace les secrets avant de redémarrer. Aucun `docker system prune` n’est utilisé.

Après `reset`, SSH signale normalement une nouvelle clé d’hôte. Retirer l’ancienne entrée avec `ssh-keygen -R legacy-telecom.hns` et, si utilisée, `ssh-keygen -R 172.30.10.10`, puis vérifier la nouvelle clé dans le cadre du labo.

## Migration de la première version

Les anciennes adresses `127.0.0.1:8080` et `127.0.0.1:2222` sont remplacées par l’IP dédiée et les ports 80/22. Mettre à jour une installation existante sans perdre ses flags :

```bash
docker compose --profile tools down --remove-orphans
./lab.sh start
```

Ne pas ajouter `--volumes`. Les anciennes variables `LEGACY_HTTP_PORT` et `LEGACY_SSH_PORT` ne sont plus utilisées. L’ancien relais `gateway` a été retiré.

## Vérifications

```bash
./lab.sh test     # Neuf tests du parseur HTTP et de l’application en mémoire
./lab.sh verify   # SPOILERS : scan Nmap et parcours complet jusqu’aux flags
```

Le test complet vérifie que le scan TCP ne trouve que SSH sur 22 et Nginx sur 80, puis effectue l’injection SQL, la connexion SSH et l’élévation vers root. Il vérifie aussi le refus de lecture initiale des secrets, les permissions et le validateur de flags. Aucune valeur de secret n’est affichée. Le [compte rendu](docs/VERIFICATION.md) précise les contrôles exécutés.

## Isolation et dépannage

La cible et le poste d’attaque sont sur un réseau dédié `internal: true`, sans route par défaut vers Internet. Aucun socket Docker ni dossier personnel n’est monté dans la cible et aucun conteneur n’utilise `privileged`. Le portail Python et les workers Nginx utilisent `www-data`. La cible conserve le fonctionnement de `sudo`, nécessaire à l’exercice. Le poste d’attaque utilise `no-new-privileges` et ne possède aucune capacité Linux.

Le root à obtenir est celui du conteneur. Docker partage le noyau de l’hôte : une VM Linux dédiée avec snapshot reste recommandée. L’opérateur qui contrôle Docker peut lire les secrets ; pour jouer, passer par les services réseau de la cible.

Les images utilisent les paquets Debian disponibles au build et ne sont pas verrouillées par digest. Le scénario utilise une faille applicative volontaire plutôt qu’un ancien système non maintenu.

- **Nom introuvable** : vérifier `/etc/hosts` ou utiliser l’IP de la box.
- **Proxy HTTP local** : exclure le nom et l’IP du proxy, par exemple `curl --noproxy '*' http://legacy-telecom.hns/`.
- **IP inaccessible** : vérifier que Docker s’exécute sur cette machine Linux et que le sous-réseau ne chevauche pas un autre réseau ou VPN.
- **Réseau Docker existant incompatible** : faire `./lab.sh stop`, puis `./lab.sh start` après modification de `.env`.
- **Service unhealthy** : consulter `./lab.sh logs` et `docker compose ps -a`.
- **Accès au démon refusé** : vérifier que Docker est démarré et que ton compte y a accès.

La [fiche historique](docs/HISTOIRE.md) explique les faits documentés, les adaptations pédagogiques et les correctifs.
