# Indices progressifs

<details>
<summary>Indice 1 — Retrouver l’ancien système</summary>

Explorer les liens du site et le fichier `robots.txt`. Une directive `Disallow` donne une indication aux robots, mais ne protège pas une page.

</details>

<details>
<summary>Indice 2 — Interroger le catalogue</summary>

Observer le paramètre `id` d’une fiche offre. Que se passe-t-il si sa valeur n’est plus simplement un nombre ? Les messages d’erreur donnent la forme de la requête SQL et son nombre de colonnes. SQLite décrit ses tables dans `sqlite_master` ; une union peut faire apparaître d’autres données dans une fiche.

</details>

<details>
<summary>Indice 3 — Après l’accès utilisateur</summary>

Les identifiants du compte de maintenance servent aussi pour SSH. Une fois connecté, examiner `sudo -l`. Un outil autorisé à rechercher des fichiers peut aussi proposer une option pour exécuter une commande.

</details>
