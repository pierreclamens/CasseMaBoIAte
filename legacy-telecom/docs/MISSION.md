# Mission — Legacy Telecom

Legacy Telecom modernise son portail client. Une partie de son ancien système reste accessible pour permettre aux abonnés de consulter leurs offres historiques.

Tu es chargé de vérifier si ce patrimoine oublié permet de compromettre le serveur de maintenance.

**Difficulté : très facile.** Aucun brute force massif, aucune exploitation du noyau et aucune évasion de conteneur ne sont nécessaires.

## Point de départ

- IP par défaut : `172.30.10.10`.
- Nom : `legacy-telecom.hns`, à associer à cette IP dans `/etc/hosts` sur la machine d’attaque.
- Site : `http://legacy-telecom.hns`.
- Périmètre : tous les ports de cette seule IP ; commencer par les découvrir avec Nmap.
- Aucun identifiant initial.

Si l’opérateur a modifié `.env`, utiliser l’IP qu’il indique. Le nom fonctionne automatiquement depuis le poste d’attaque Docker fourni.

## Objectifs

1. Explorer le portail et son historique.
2. Obtenir un accès à un compte utilisateur du serveur.
3. Récupérer le flag `user.txt` dans son répertoire personnel.
4. Devenir root dans la cible et lire `/root/root.txt`.

Les deux récompenses utilisent le format `flag{…}`. Valider les valeurs avec `./lab.sh check user` et `./lab.sh check root` sur l’hôte.

Pour préserver l’exercice, ne pas utiliser `docker exec`, lire les fichiers sources ou consulter les volumes Docker. Ces accès sont réservés à l’administration du labo.

Si tu bloques, ouvrir progressivement les [trois indices](INDICES.md).
