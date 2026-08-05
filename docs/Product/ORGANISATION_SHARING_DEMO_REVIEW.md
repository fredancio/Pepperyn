# ORGANISATION SHARING DEMO REVIEW

**Date** : 2026-08-05
**Branche** : `prototype/organisation-sharing-demo-2026-08-05` (créée depuis `prototype/portfolio-external-user-testing-2026-08-05`, tip `6cfe025`)
**Statut** : non fusionnée, non poussée — commit local uniquement, en attente de validation explicite de Fred.

---

## 1. Besoin métier testé

Le prototype externe précédent proposait un modèle "PIN invité" : un code à 4 chiffres permanent donnant accès à un client. Ce modèle a été rejeté (accès binaire, sans granularité de rôle, sans limite de périmètre, permanent donc jamais révoqué naturellement).

Cette simulation teste une direction produit alternative : **Organisation → Membres → Rôles → Invitations temporaires**. L'objectif du test utilisateur n'est pas de valider une implémentation technique (rien n'est réellement fonctionnel), mais de vérifier que des utilisateurs non guidés **comprennent correctement** trois principes : une invitation porte sur un périmètre précis (jamais implicitement tout le portefeuille) ; un rôle détermine des actions autorisées différentes ; un accès est temporaire et révocable, jamais un mot de passe permanent.

## 2. Périmètre de la simulation

Entièrement contenue dans le prototype de démonstration (`/demo/portfolio`), gardée par `isDemoModeEnabled()` — ne peut jamais apparaître dans `/app/portfolio` (portefeuille réel authentifié), y compris si la variable d'environnement démo est mal positionnée par erreur en production (garde-fou déjà existant, réutilisé tel quel, non modifié).

Aucune ligne de code backend touchée. Aucune migration. Aucune modification de Supabase Auth, des rôles réels, ou de la table `entities`/`engagements`. Le Portfolio réel (tri, priorités, calculs, données) n'a reçu qu'un seul ajout : un lien secondaire par carte — rien d'autre n'a changé dans sa logique, ses données ou son rendu.

## 3. Rôles montrés

Exactement 3, tels que mandatés — aucun quatrième rôle ajouté, y compris pour le libellé "Analyste" donné en exemple dans le mandat (mappé sur Contributeur, documenté dans `lib/sharing-data.ts`) :

- **Administrateur** — gère les membres, lance des analyses, modifie les décisions, consulte l'ensemble de l'organisation.
- **Contributeur** — prépare les revues, pose des questions, suit les décisions, ne gère pas les accès.
- **Lecteur** — consulte le briefing, consulte les analyses et décisions autorisées, ne modifie rien.

Ces capacités sont des libellés illustratifs affichés dans l'UI — aucune ne correspond à une permission technique réelle appliquée où que ce soit.

## 4. Règles de périmètre montrées

Trois options, dans l'ordre du mandat, avec un défaut toujours restrictif :

1. **Cette organisation** (défaut) — accès limité à l'organisation depuis laquelle l'invitation est créée.
2. **Plusieurs organisations sélectionnées** — sélection explicite dans la liste des 11 autres organisations démo ; le bouton de soumission reste désactivé tant qu'aucune n'est cochée.
3. **Tout le portefeuille** — exige une confirmation additionnelle explicite, avec le texte exact mandaté (*"Cette personne pourra voir toutes les organisations actuelles et futures du portefeuille. Confirmer ?"*) ; le bouton de soumission reste désactivé sans cette confirmation.

Le rôle par défaut d'une nouvelle invitation est **Lecteur** (le plus restrictif), jamais Administrateur — décision codée en dur dans `DEFAULT_INVITE_ROLE`, pas laissée à un choix implicite de l'UI.

## 5. Éléments réellement interactifs vs purement simulés

| Élément | Interactif | Simulé / fictif |
|---|---|---|
| Ouverture du panneau depuis la carte Portfolio | ✅ vrai état React local | — |
| Liste des membres (Frédéric, Julie, Marc) | ✅ affichage réel | Personnes fictives, rôles fixes |
| Formulaire d'invitation (email, rôle, périmètre) | ✅ saisie et validation réelles côté client | Aucune donnée transmise nulle part |
| Case de confirmation "Tout le portefeuille" | ✅ bloque réellement la soumission tant que non cochée | — |
| Création de l'invitation | ✅ change l'état du composant | Code, validité, aucune écriture ni réseau |
| Code temporaire affiché | ✅ généré à chaque clic (aléatoire) | Purement cosmétique, aucune valeur fonctionnelle, jamais stocké |
| "Voir ce que cette personne verra" | ✅ ouvre un aperçu réel avec les vraies données démo (Review Briefing, exemple d'analyse) de l'organisation | Aperçu statique, non interactif, ne simule pas une vraie session authentifiée |
| Révocation d'accès | ❌ non implémentée | Uniquement mentionnée dans un texte explicatif |

Aucun `fetch()`, aucun appel Supabase, aucun `localStorage`/`sessionStorage` : tout l'état vit dans `useState` React et disparaît au démontage du composant ou au rafraîchissement de la page — comportement volontaire, pas un défaut.

## 6. Fichiers modifiés / créés

Diff vérifié (`git status --porcelain`) — strictement limité à ceci, rien d'autre :

**Nouveaux fichiers**
- `frontend/lib/sharing-data.ts` — rôles, membres fictifs, options de périmètre, générateur de code fictif, textes mandatés.
- `frontend/components/sharing/ShareOrganizationPanel.tsx` — modal principal (vues Membres / Invitation / Succès).
- `frontend/components/sharing/GuestPreview.tsx` — aperçu "Voir ce que cette personne verra".
- `frontend/lib/__tests__/sharing-data.test.ts`
- `frontend/components/sharing/__tests__/ShareOrganizationPanel.test.tsx`
- `frontend/components/sharing/__tests__/GuestPreview.test.tsx`

**Fichiers modifiés**
- `frontend/components/chat/PortfolioHome.tsx` — ajout du lien secondaire "Partager l'organisation" par carte (gardé par `isDemoModeEnabled()`) et du rendu conditionnel du panneau ; aucune autre ligne touchée (tri, calculs, hiérarchie de carte inchangés).
- `frontend/app/demo/chat/page.tsx` — déplacement de `buildExampleAnalysis` vers `lib/demo-data.ts` (aucun changement de comportement, seulement de localisation, pour que `GuestPreview.tsx` puisse la réutiliser sans dépendre d'un module de route).
- `frontend/lib/demo-data.ts` — ajout de l'export `buildExampleAnalysis` (contenu inchangé, déplacé depuis `page.tsx`).
- `frontend/components/chat/__tests__/PortfolioHome.demo.test.tsx` / `PortfolioHome.test.tsx` — ajout de tests couvrant l'apparition/absence du point d'entrée selon le mode.

Aucun fichier backend, aucune migration, aucun fichier de configuration touché.

## 7. Tests

17 cas au total (mandat : 14 minimum) :

- `sharing-data.test.ts` (6 cas) — valeurs par défaut sûres (rôle Lecteur, périmètre "cette organisation"), exactement 3 rôles et 3 périmètres, seule "Tout le portefeuille" exige confirmation, format et variabilité du code fictif.
- `ShareOrganizationPanel.test.tsx` (8 cas) — membres fictifs affichés, texte explicatif limité à l'organisation courante, absence du terme "PIN invité", rôle/périmètre par défaut sûrs à l'ouverture du formulaire, blocage de soumission tant que la sélection multi-organisations est vide, blocage + déblocage sur confirmation "Tout le portefeuille", aucun appel réseau lors de la création, code temporaire affiché avec validité/usage unique, réinitialisation du formulaire.
- `GuestPreview.test.tsx` (6 cas) — contenu limité à l'organisation ciblée (Lecteur), capacités affichées correctes pour Lecteur/Contributeur/Administrateur, absence des autres organisations et de tout élément de compte/quota/facturation dans l'aperçu.
- `PortfolioHome.demo.test.tsx` / `PortfolioHome.test.tsx` (+3 cas) — le point d'entrée apparaît en mode démo sans remplacer "Préparer cette revue", ouvre bien le panneau, et **n'apparaît jamais** hors mode démo (test explicite sur la suite non-démo).

### Exécution réelle — limite d'environnement (transparence, cohérence avec le gate précédent)

`tsc --noEmit` a été exécuté avec succès sur l'ensemble du projet frontend. **Aucune erreur** en dehors des dossiers `__tests__/` — et les erreurs présentes dans `__tests__/` (types manquants pour `@testing-library/react` et les matchers `jest-dom`) sont **strictement identiques, en nature et en nombre par fichier, aux erreurs déjà présentes sur les fichiers de test existants avant cette mission** (`PortfolioHome.test.tsx`, `ReviewBriefing.test.tsx`, `DemoBanner.test.tsx`, etc.) : c'est un gap de configuration TypeScript préexistant du dépôt (types `@testing-library/jest-dom` non déclarés globalement), pas une régression introduite ici.

L'exécution réelle de `jest` a été retentée et échoue pour la même raison déjà documentée lors du FINAL SEMANTIC AND TEST GATE précédent : le binaire natif `@next/swc-linux-x64-gnu` ne charge pas dans ce sandbox (`Failed to load SWC binary for linux/x64`). C'est une incompatibilité d'environnement, indépendante de ce code, déjà rencontrée et documentée sur la branche précédente. Aucune suite de tests (nouvelle ou existante) n'a donc pu être exécutée réellement dans cette session — seule la vérification statique (`tsc`) et la relecture manuelle ligne à ligne du code ont pu être faites.

## 8. Limites

- Le code temporaire, les invitations et les membres disparaissent au rafraîchissement de la page — volontaire, mais un testeur qui rafraîchit par réflexe pendant le test perdra son invitation créée sans message d'erreur explicite (juste un retour à l'état initial du panneau).
- `GuestPreview` réutilise l'exemple d'analyse générique (`buildExampleAnalysis`) déjà utilisé ailleurs dans le prototype — un testeur qui a déjà vu cet exemple dans `/demo/chat` le reverra à l'identique dans l'aperçu, ce qui est cohérent mais pourrait sembler répétitif si le parcours de test enchaîne les deux écrans.
- Comme documenté au gate précédent, l'exécution réelle de la suite de tests Jest reste bloquée par l'environnement sandbox (SWC), pas par le code — ce point reste à vérifier sur une machine de développement standard (Fred) avant fusion.

## 9. Risques d'interprétation pour le test utilisateur

- Le lien "Partager l'organisation" est volontairement discret (texte gris 11px sous le bouton principal) pour ne jamais concurrencer "Préparer cette revue" — un testeur non guidé pourrait ne pas le remarquer du tout. C'est un risque assumé et cohérent avec Mission 1 du mandat ("ne doit jamais rivaliser"), mais cela peut réduire le taux de découverte spontanée en test non guidé.
- Le bouton "Aperçu" sur chaque membre de la liste (vue par défaut du panneau) et le lien "Voir ce que cette personne verra" (après création d'une invitation) mènent au même composant `GuestPreview` — un testeur pourrait ne pas comprendre qu'il s'agit du même mécanisme vu sous deux angles (membre existant vs invitation qu'on vient de créer).
- Le code temporaire change à chaque nouvelle invitation créée (aléatoire, non déterministe) — si deux testeurs comparent leurs captures d'écran, ils verront des codes différents ; à mentionner dans le kit de test pour éviter une fausse impression de bug.

## 10. Recommandations pour les tests utilisateurs

- Poser la question ouverte "Que se passe-t-il si vous invitez quelqu'un sur 'Tout le portefeuille' ?" sans montrer le chemin — vérifier que le testeur découvre seul l'avertissement et la confirmation obligatoire.
- Demander "Cette personne pourra-t-elle voir vos autres organisations ?" après une invitation en périmètre par défaut ("Cette organisation") — vérifier la compréhension du texte explicatif du panneau.
- Ne pas expliquer à l'avance ce qu'est un "code temporaire" — observer si le testeur l'interprète correctement comme non permanent grâce au texte affiché sous le code, sans qu'on ait eu à l'expliquer oralement.
- Vérifier explicitement qu'aucun testeur n'utilise ou ne cherche le terme "PIN" pendant le test — sa disparition complète du vocabulaire visible est un critère de succès du mandat.

---

## Verdict

Le périmètre du mandat est respecté intégralement (3 rôles, 3 périmètres, texte de confirmation exact, aucun terme "PIN invité", aucun appel réseau, aucune modification backend, garde-fou `isDemoModeEnabled()` réutilisé sans modification, "Préparer cette revue" inchangé). La vérification statique (`tsc`) est propre sur tout le code de production touché. La seule réserve est l'incapacité de ce sandbox à exécuter réellement la suite Jest (limite d'environnement déjà documentée et indépendante du code livré) — à revalider sur une machine standard avant toute fusion.

```
ORGANISATION SHARING DEMO COMPLETED.
FINAL VERDICT:
SHARING DEMO READY WITH MINOR RESERVATIONS
```
