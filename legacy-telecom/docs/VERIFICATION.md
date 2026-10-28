# Compte rendu des vérifications

Contrôles exécutés le **28 octobre 2026**, sur Linux avec Docker Engine 28.5.2 et Docker Compose 2.40.3. Les deux images (cible avec Nginx et poste d’attaque) ont été construites depuis les Dockerfiles livrés.

| Contrôle | Résultat |
|---|---|
| Validation du modèle Compose | Réussie |
| Syntaxe du script Bash | Réussie |
| Tests applicatifs sans socket | **9 tests réussis** |
| Santé Nginx sur 80 et SSH sur 22 | Réussie |
| Nom `legacy-telecom.hns` résolu dans le réseau Docker | Confirmé |
| Scan Nmap TCP complet de la box avec détection de services | Uniquement OpenSSH sur 22 et Nginx sur 80 |
| Accès depuis le réseau de l’hôte Linux à `172.30.10.10`, ports 80 et 22 | Réussi |
| Accès externe au backend 8080 et à l’ancien port 2222 | Refusé, comme attendu |
| Extraction des identifiants par SQLi à travers Nginx | Réussie |
| Connexion SSH comme `support`, UID différent de 0 | Réussie |
| Lecture du flag user | Réussie |
| Lecture directe du flag root et de l’état interne avant élévation | Refusée, comme attendu |
| Élévation par `sudo find`, UID 0 et flag root distinct | Réussie |
| Propriétaires et modes des flags, répertoire d’état et fichier d’état | Conformes |
| Validation des bons flags et rejet d’une mauvaise valeur | Réussis |
| Processus HTTP comme `www-data`, capacités effectives nulles | Confirmé |
| Absence de route réseau par défaut dans la cible | Confirmée |
| Migration vers IP fixe et ports standards sans suppression du volume | Flags et mot de passe conservés, empreinte de l’état identique |

Les tests applicatifs utilisent le vrai parseur HTTP du serveur avec des flux en mémoire : le bac à sable de l’agent ne permet pas de créer des sockets locales directement. Les tests d’intégration utilisent de véritables connexions HTTP et SSH entre conteneurs. L’accès depuis l’hôte a été vérifié séparément avec une sonde temporaire en réseau hôte, supprimée après exécution. La sonde utilisait sa propre entrée de résolution locale ; `/etc/hosts` sur l’hôte n’a pas été modifié et reste à configurer par l’utilisateur.

Le parcours complet ne lit aucun secret par un accès administrateur à la cible : il obtient les identifiants via HTTP, puis les flags par SSH. Les contrôles de permissions et du validateur sont, eux, exécutés en tant qu’opérateur. Aucune valeur de flag ou de mot de passe n’a été affichée dans les résultats de vérification.

## Reproduire

```bash
./lab.sh test
./lab.sh verify
```

`verify` lance le scan Nmap et le parcours réseau depuis le poste d’attaque, puis les contrôles opérateur. Il ne supprime pas la progression. La conservation de l’état après `stop`/`start` et son renouvellement après `reset` avaient également été validés dans la version initiale ; la migration vers Nginx a conservé le même volume et son contenu.

## Limites

Pas de validation sur Windows, macOS, Docker Desktop ou architecture ARM. Aucun navigateur n’étant disponible dans la session, le rendu visuel n’a pas été inspecté. Ces tests vérifient le parcours prévu et les contrôles indiqués ; ils ne constituent pas un audit exhaustif de l’isolation Docker.
