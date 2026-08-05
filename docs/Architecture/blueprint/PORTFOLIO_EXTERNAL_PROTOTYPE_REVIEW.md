# PORTFOLIO EXTERNAL PROTOTYPE — REVIEW

**Date :** 2026-08-05
**Périmètre :** rendre Portfolio Home → Review Briefing testable par des professionnels externes, via une Vercel Preview Deployment isolée, sans exposer données réelles, Supabase de production, secrets, comptes réels, appels LLM payants ni fonctions d'écriture.
**Branche :** `prototype/portfolio-external-user-testing-2026-08-05`, depuis `main` (`5474452`), 2 commits (`e2791a5`, `2cba633`), 17 fichiers modifiés, 1406 insertions / 1 suppression.

---

## 1. Architecture d'isolation

Décision structurante : isoler par la **couche de données**, jamais par les composants d'interface. `PortfolioHome.tsx`, `ReviewBriefing.tsx`, `InputBar.tsx`, `MessageBubble.tsx`, `AnalysisResult.tsx` restent byte-identiques (aucune redéfinition du Portfolio ni du Review Briefing, conformément à l'interdiction du mandat), à une exception près documentée en section 2.

Le garde-fou central, `frontend/lib/demo-mode.ts::isDemoModeEnabled()`, exige **simultanément** :
- `NEXT_PUBLIC_DEMO_MODE === 'true'`
- `NEXT_PUBLIC_VERCEL_ENV !== 'production'` (variable Vercel native `VERCEL_ENV`, exposée côté client via `next.config.js::env`)

Ce double contrôle garantit que le mode démo ne peut **jamais** s'activer sur le domaine de production, même si le drapeau `NEXT_PUBLIC_DEMO_MODE` était positionné par erreur dans les réglages Production de Vercel — vérifié par 8 tests dédiés (`lib/__tests__/demo-mode.test.ts`), dont le cas critique flag=true + environnement=production → désactivé.

Toute fonction de `lib/arc-api.ts` et `lib/api.ts` qui doit rester strictement isolée consulte `isDemoModeEnabled()` **avant** toute construction de `fetch()` :
- `fetchPortfolio()`, `fetchReviewBriefing()` → lisent `lib/demo-data.ts` (aucun réseau).
- `abandonArc()` → réponse simulée en mémoire (aucune écriture, réelle ou distante).
- `downloadExcel/Pdf/Pptx()` → retournent un `Blob` texte local, honnêtement labellisé (« Aperçu de démonstration »), aucun appel réseau.

Les routes `/demo/portfolio` et `/demo/chat` vivent hors de `app/app/*` (donc hors de l'authentification Supabase requise par `app/app/layout.tsx`) et sont elles-mêmes protégées par un garde-fou de niveau layout (`app/demo/layout.tsx`) : si `isDemoModeEnabled()` est faux, un message neutre s'affiche à la place de l'interface.

---

## 2. Fichiers modifiés

| Fichier | Nature |
|---|---|
| `frontend/lib/demo-mode.ts` | Nouveau — garde-fou central. |
| `frontend/lib/demo-data.ts` | Nouveau — jeu de données fictif gelé (12 clients). |
| `frontend/next.config.js` | Modifié — ajout du seul bloc `env` exposant `NEXT_PUBLIC_VERCEL_ENV` ; `headers()` existant intact. |
| `frontend/lib/arc-api.ts`, `frontend/lib/api.ts` | Modifiés — court-circuit démo ajouté en tête de chaque fonction concernée, logique réelle inchangée en aval. |
| `frontend/app/demo/layout.tsx`, `frontend/app/demo/portfolio/page.tsx`, `frontend/app/demo/chat/page.tsx` | Nouveaux — pages de démonstration. |
| `frontend/components/demo/DemoBanner.tsx` | Nouveau — bandeau d'identification + lien de feedback. |
| `frontend/components/chat/PortfolioHome.tsx` | **Seul composant réutilisé modifié** — une ligne de wiring (voir ci-dessous), rien d'autre. |
| 6 fichiers `__tests__/*.test.ts(x)` | Nouveaux — 27 tests couvrant les 15 cas obligatoires de la Mission 9. |

**Détail de la modification à `PortfolioHome.tsx`** : `handlePrepareReview` naviguait en dur vers `/app/chat?entity=<id>` (route authentifiée). En mode démo, cette route redirigerait immédiatement vers `/login`, rendant le parcours testable impossible. La cible devient conditionnelle : `isDemoModeEnabled() ? '/demo/chat' : '/app/chat'`. Hiérarchie de carte, tri, densité, `why_it_matters` : strictement inchangés. Le test préexistant (`PortfolioHome.test.tsx`) reste vert sans modification ; un test dédié (`PortfolioHome.demo.test.tsx`) couvre la nouvelle branche.

---

## 3. Dataset fictif

`frontend/lib/demo-data.ts` réutilise exactement le jeu de données à 12 clients de `PORTFOLIO_HOME_PRODUCT_VALIDATION.md`, régénéré via un script jetable (`/tmp/portfolio-validation/build_demo_dataset.py`, non versionné) qui instancie le vrai `ArcService` (`backend/services/arc_service.py`) sur un faux client Supabase honorant réellement les filtres `.eq()`/`.neq()` — pas une liste triée à la main. Sortie gelée dans le fichier TypeScript.

Couverture : plusieurs priorités (urgent / to_check / done) ; deux clients à stricte égalité priorité + ancienneté (Nguyen, Girard — 60 jours) ; clients à un seul point actif et à plusieurs (Lefèvre ×4, Martin ×3, Lemoine ×2, Dupuis ×2) ; âges de 4 à 92 jours ; `why_it_matters` affiché (Martin, Roussel) et masqué (les 8 autres) ; titre court (Nguyen) et long (Fontaine) ; **Traiteur Second** (uniquement un point `closed`) — absent du Portfolio, consultable en historique via Review Briefing direct ; **Cabinet Rousseau** (aucun arc) — absent partout. Noms entièrement inventés, aucune réutilisation de donnée réelle ni des anciens dossiers Optilux/Démo (vérifié, section 6).

---

## 4. Comportements testables

Parcours complet couvert : arrivée sur `/demo/portfolio` → lecture des 10 cartes → clic « Préparer cette revue » → `/demo/chat?entity=<id>` → client correct présélectionné → Review Briefing immédiatement visible → clic « Préparer cette question » → texte prérempli dans le champ (brouillon existant préservé, jamais envoyé automatiquement) → exemple de rapport déjà visible → actions PDF / PowerPoint / Excel présentes et fonctionnelles (aperçus).

Aucune visite guidée ajoutée. Le seul texte d'orientation est celui déjà validé côté produit (« Vos clients avec un point à traiter, triés par priorité » — `PortfolioHome.tsx`, inchangé).

---

## 5. Fonctions délibérément simulées

| Fonction | Comportement réel | Comportement démo |
|---|---|---|
| Portfolio / Review Briefing | Lecture Supabase | Lecture `lib/demo-data.ts` |
| « Ne plus suivre » (`abandonArc`) | Écriture Supabase | Réponse simulée en mémoire, aucune écriture |
| Question de suivi (chat) | Appel LLM au backend | Réponse fixe expliquant la nature du prototype |
| Envoi de fichier | Upload + analyse réelle | Message expliquant que l'envoi est désactivé (chemin non atteignable dans l'UI démo, `InputBar` en mode non-`uploadOnly`) |
| Téléchargement PDF/PPTX/Excel | Génération réelle + fetch backend | `Blob` texte local, libellé « Aperçu de démonstration » |

---

## 6. Résultats des tests (Mission 9)

| Cas | Couverture | Résultat |
|---|---|---|
| 1 — Activation du mode démo | `demo-mode.test.ts` (8 tests) | ✅ |
| 2 — Impossibilité de contacter Supabase | `arc-api.demo.test.ts` — `fetch` jamais appelé | ✅ |
| 3 — Impossibilité d'appeler un LLM | `arc-api.demo.test.ts` — même preuve (LLM toujours servi via HTTP backend) | ✅ |
| 4 — 12 clients fictifs avant filtrage | `demo-data.test.ts` | ✅ |
| 5 — Exclusion du client closed-only | `demo-data.test.ts` | ✅ |
| 6 — Exclusion du client sans sujet actif | `demo-data.test.ts` | ✅ |
| 7 — Ordre des cartes | `demo-data.test.ts` | ✅ |
| 8 — Compteur multi-points | `demo-data.test.ts` | ✅ |
| 9 — Navigation Portfolio → Review Briefing | `PortfolioHome.demo.test.tsx` | ✅ |
| 10 — Client correct présélectionné | `app/demo/chat/__tests__/page.test.tsx` | ✅ |
| 11 — Préremplissage du chat | `app/demo/chat/__tests__/page.test.tsx` | ✅ |
| 12 — Préservation du brouillon | `app/demo/chat/__tests__/page.test.tsx` | ✅ |
| 13 — Bandeau "données fictives" | `DemoBanner.test.tsx` | ✅ |
| 14 — Absence de téléchargement réel | `api.demo.test.ts` | ✅ |
| 15 — Build de prévisualisation valide | `next build` (avec et sans `NEXT_PUBLIC_DEMO_MODE=true`) | ✅ |

**Suite complète frontend :** 65/65 tests verts (38 préexistants + 27 nouveaux), 10 suites.
**Tests ciblés Portfolio + Review Briefing (backend) :** 57/57 verts (backend non modifié).
**Build production Next.js :** réussi deux fois — configuration par défaut, et avec `NEXT_PUBLIC_DEMO_MODE=true` / `VERCEL_ENV=preview` (routes `/demo/chat`, `/demo/portfolio` générées).

---

## 7. Rapport de sécurité (Mission 10)

| Vérification | Résultat |
|---|---|
| Aucun secret dans le bundle client (clé service Supabase, clé secrète Stripe, clé API Anthropic) | ✅ PASS — recherche exhaustive sur `.next/static` et `.next/server/app/demo`, aucune correspondance |
| Aucune URL de production non voulue | ✅ PASS avec observation — la chaîne `localhost:8000` (valeur de repli par défaut de `lib/api.ts`, préexistante, non spécifique à ce prototype) apparaît dans un chunk partagé ; inerte car jamais atteinte en mode démo |
| Aucun identifiant Supabase réel | ⚠️ **CONDITIONNEL — action requise avant déploiement** (détail ci-dessous) |
| Aucun fichier utilisateur | ✅ PASS — `public/` ne contient que des assets de marque |
| Aucun vrai prospect | ✅ PASS — dataset 100% fictif, noms inventés |
| Aucune donnée démo issue des anciens dossiers Optilux/Démo sans validation explicite | ✅ PASS — dataset généré depuis zéro via le vrai `ArcService`, aucune référence aux anciens dossiers |
| Aucune fonction d'écriture atteignable | ✅ PASS — prouvé par test : `fetch()` jamais appelé par `abandonArc`, `downloadExcel/Pdf/Pptx` en mode démo |
| Aucune dépendance à un backend local | ✅ PASS — même preuve : zéro appel réseau en mode démo |

### Détail de l'item conditionnel — identifiants Supabase

Le dossier `frontend/` contient un `.env.local` local (non suivi par Git, correctement ignoré) portant les vraies valeurs `NEXT_PUBLIC_SUPABASE_URL` et `NEXT_PUBLIC_SUPABASE_ANON_KEY` du projet. Next.js inline **toute** variable `NEXT_PUBLIC_*` présente dans l'environnement de build au moment du `next build` — indépendamment du mode démo, qui est un garde-fou d'exécution, pas de compilation. Un build de test réalisé avec ce `.env.local` a confirmé que l'URL Supabase réelle apparaît dans un chunk JavaScript statique.

Cette clé est une clé anonyme publique par conception Supabase (protégée par Row Level Security, jamais un secret au sens strict), mais le mandat demande explicitement qu'aucun identifiant Supabase réel n'apparaisse dans ce prototype. Aucun code du prototype n'importe ni n'utilise cette valeur (`isDemoModeEnabled()` court-circuite avant tout accès), mais elle resterait techniquement présente et publiquement récupérable dans les fichiers statiques déployés si la Vercel Preview Deployment hérite des mêmes variables d'environnement `NEXT_PUBLIC_SUPABASE_*` que la production.

**Action requise avant toute mise en ligne (Mission 11) :** dans les réglages Vercel du projet, vérifier la portée (scope) de `NEXT_PUBLIC_SUPABASE_URL` et `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Si elles sont configurées pour tous les environnements (Production + Preview + Development), soit les redéfinir avec des valeurs vides/factices spécifiquement pour l'environnement Preview de cette branche, soit confirmer explicitement que l'exposition de la clé anonyme est acceptée (elle est conçue pour être publique). Cette décision revient à Fred — non prise unilatéralement ici.

---

## 8. URL de prévisualisation

**Non encore créée.** Aucun accès de push (`git push`) ni de déploiement Vercel n'est disponible dans cet environnement (confirmé : `git push --dry-run` échoue par absence d'identifiants). Conformément à la clause de repli de la Mission 11, les étapes exactes pour que Fred pousse la branche et crée la Preview Deployment sont données ci-dessous.

### Étapes exactes pour Fred

1. Depuis un poste avec accès `git push` : `git push origin prototype/portfolio-external-user-testing-2026-08-05` (uniquement cette branche — jamais `main`).
2. Sur le projet Vercel existant : la Preview Deployment se crée automatiquement au push si le projet est déjà connecté au dépôt GitHub (comportement standard Vercel pour toute branche non-`main`). Sinon, ouvrir l'onglet **Deployments** → **Create Deployment** → sélectionner la branche.
3. Avant ou juste après la création, définir la variable d'environnement `NEXT_PUBLIC_DEMO_MODE=true`, scope **Preview uniquement** (jamais Production) — sans elle, le garde-fou de `app/demo/layout.tsx` affichera le message neutre au lieu du prototype.
4. Traiter l'item conditionnel de la section 7 (`NEXT_PUBLIC_SUPABASE_URL`/`ANON_KEY`) avant de partager l'URL à des testeurs externes.
5. Ne jamais promouvoir cette Preview Deployment en Production ; ne jamais modifier le domaine principal.
6. Une fois l'URL de prévisualisation connue, la reporter dans `EXTERNAL_TESTING_README.md` (section « URL du prototype »).

---

## 9. Risques restants

- Item conditionnel de sécurité (section 7) — nécessite une action de configuration Vercel avant tout partage externe.
- Réserves UX déjà connues et volontairement non corrigées (densité de carte, couleur de `why_it_matters_display`) — inchangées, hors périmètre de cette mission (« Aucune correction des deux réserves UX »).
- Le déploiement effectif (push + Preview Deployment) n'a pas pu être exécuté dans cet environnement — reste à la charge de Fred selon les étapes ci-dessus.

---

## 10. Verdict

**PORTFOLIO EXTERNAL TESTING PROTOTYPE COMPLETED.**
**FINAL VERDICT:**
**PROTOTYPE READY WITH MINOR RESERVATIONS**
