# Inspiration historique et remédiation

## Faits documentés

En 2015, TalkTalk a subi une attaque par injection SQL. L’enquête de l’ICO a notamment relevé des pages anciennes non supprimées ou sécurisées et un logiciel de base de données obsolète. L’attaque a exposé des données de clients.

Source primaire : [TalkTalk cyber attack — how the ICO’s investigation unfolded](https://ico.org.uk/about-the-ico/media-centre/talktalk-cyber-attack-how-the-ico-investigation-unfolded).

## Adaptations de cette box

Legacy Telecom est une entreprise fictive. Le portail Python, SQLite, le compte `support`, le stockage en clair de son mot de passe, sa réutilisation sur SSH et la règle `sudo find` sont des choix pédagogiques. Ils ne prétendent pas reproduire la chaîne exacte de l’incident TalkTalk. Aucune donnée personnelle réelle n’est utilisée.

L’injection est introduite explicitement dans le code plutôt que dépendre d’une ancienne CVE de base de données. Aucun exploit noyau, service cloud réel ou accès à une entreprise n’est requis.

## Correctifs attendus

| Faiblesse du labo | Correction |
|---|---|
| Ancien portail oublié | Inventorier les applications, retirer les services inutiles et surveiller les accès |
| Concaténation du paramètre SQL | Utiliser une requête paramétrée : `db.execute('SELECT id, name, price, description FROM offers WHERE id = ?', (offer_id,))` ; vérifier également le type attendu |
| Erreurs SQL publiques | Renvoyer une erreur générique et conserver les détails dans les journaux internes |
| Mot de passe en clair | Pour l’authentification applicative, stocker un hachage de mot de passe adapté, salé ; ne pas conserver un secret SSH dans le catalogue |
| Réutilisation des identifiants | Séparer les comptes et les secrets de service ; renforcer l’authentification SSH |
| `sudo find` sans restriction | Retirer la règle ; si nécessaire, créer un outil limité, détenu par root et non modifiable par l’utilisateur, qui n’exécute pas de commande arbitraire |

`robots.txt` sert à orienter les robots d’indexation : il ne constitue pas un contrôle d’accès.

Pour un compte rendu d’étudiant, décrire pour chaque faille : preuve observée, prérequis, impact dans cette box, correctif et manière de vérifier ce correctif.
