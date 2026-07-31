---
name: changelog
description: Utilise ce skill à chaque fois que tu crées, modifies ou supprimes un fichier dans ce projet (script, config, doc...). Consigne le changement dans CHANGELOG.md pour permettre un rollback manuel, car ce dossier n'est PAS un dépôt git. À invoquer systématiquement après CHAQUE modification, même mineure — pas seulement en fin de tâche, et même si le skill a déjà été utilisé plus tôt dans la conversation.
---

# Journaliser les changements (CHANGELOG.md)

Ce projet n'est pas versionné avec git : `CHANGELOG.md` est le seul filet de sécurité en cas de besoin de rollback. Chaque modification de fichier doit être consignée immédiatement après avoir été effectuée, pas en fin de session.

## Quand l'utiliser

- Après chaque `Edit`, `Write`, ou commande shell qui crée, modifie ou supprime un fichier du projet.
- Une entrée par changement logique (pas une entrée géante regroupant toute la session).
- Même pour des changements mineurs (renommage, typo, valeur par défaut modifiée).

## Comment procéder

1. Avant d'éditer un fichier existant, garde trace du contenu original des lignes concernées (via `Read`) — l'instruction de rollback doit être réutilisable telle quelle.
2. Effectue le changement.
3. Ajoute immédiatement une entrée en **haut** de la section `## Entrées` de `CHANGELOG.md` (ordre anté-chronologique, plus récent en premier) avec ce gabarit :

   ```
   ### AAAA-MM-JJ HH:MM — <titre court du changement>
   - **Fichier(s):** chemin/du/fichier.ext
   - **Type:** ajout | modification | suppression
   - **Changement:** description concise de ce qui a changé et pourquoi.
   - **Rollback:** instructions précises pour revenir en arrière manuellement.
     Pour une modification, inclure l'ancien contenu pertinent en bloc de
     code pour pouvoir le recoller tel quel. Pour un ajout, indiquer
     précisément quoi supprimer (ex: "supprimer la fonction sing_comments(),
     lignes 140-165"). Pour une suppression, inclure le contenu supprimé
     en entier.
   ```

4. N'attends pas la confirmation de l'utilisateur ni la fin de la tâche : journalise au fil de l'eau, dès qu'un changement est fait, avant de passer au suivant.
5. Ne journalise jamais de secrets (clés API, tokens) même s'ils apparaissent dans le diff — remplace-les par un placeholder du type `<clé retirée>`.

## Où

Le fichier vit à la racine du projet : `CHANGELOG.md`. S'il n'existe pas encore, le créer avec un en-tête minimal puis une section `## Entrées`.
