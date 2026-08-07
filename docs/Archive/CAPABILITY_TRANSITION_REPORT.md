# CAPABILITY TRANSITION REPORT

**Date :** 2026-08-03
**Type :** document de référence (Niveau B), clôture du travail de gouvernance ouvert par « OPEN CAPABILITY ROADMAP v1 ».
**Objet :** comparer la roadmap au Pepperyn développé aujourd'hui, capacité par capacité, en distinguant toujours code existant et capacité métier réellement disponible ; conclure sur la prochaine capacité à développer.

---

## 1. Comparaison, capacité par capacité (Mission 9)

### Capability 1 — Financial Evidence
- **Ce qui existe déjà :** `evidence_ledger_entries` (v18), capture non-bloquante (`evidence_capture.py`, `evidence_ledger_service.py`), `amount`/`currency`/`fact_ids` atomiques et déterministes (T1C-B), immutabilité par trigger, validé en conditions Supabase réelles (Integration Gate 1).
- **Ce qui manque :** granularité « un par Engagement × période » (aujourd'hui : un par Analysis) ; `Materiality` comme Value Object dédié ; définition de la clôture de période (ADR-001, question ouverte n°2, toujours non tranchée).
- **Partiellement implémenté :** rien — le périmètre exact promis par ADR-001/ADR-001A est livré intégralement pour sa tranche.
- **À refactorer probablement :** aucun refactor de ce qui existe — la granularité manquante s'ajoutera par extension, pas par réécriture (le Blueprint C.3 le qualifie de « point de levier le plus favorable », déjà exploité).
- **Code existant vs capacité réellement disponible :** les deux coïncident ici — c'est la seule capacité où le code livré correspond très exactement à ce qui a été validé métier (Integration Gate 1), sans écart entre « ça tourne » et « c'est utilisable ».

### Capability 2 — Engagement Lifecycle
- **Ce qui existe déjà :** table `engagements`, relation 1:1 durable avec `Entity`, deux chemins de création atomiques (RPC + trigger signup), backfill idempotent — tout validé en conditions réelles.
- **Ce qui manque :** `StakeholderContact`, `ScopeDefinition`, `RetainerTerms` (entités/VO cible, Ideal Model E.1) ; aucune transition de statut câblée au-delà de l'initialisation (`active`/`prospect`) — pas de passage `paused`, `at_risk`, `churned` piloté par une règle ; `cadence` est un champ mort.
- **Partiellement implémenté :** le statut existe comme donnée mais pas comme cycle de vie gouverné par des règles métier.
- **À refactorer probablement :** aucun refactor du schéma existant — les transitions et entités manquantes s'ajoutent par extension de l'agrégat déjà posé.
- **Code existant vs capacité réellement disponible :** **écart net.** Le code garantit qu'un Engagement existe pour chaque Entity, mais aucun utilisateur ne peut aujourd'hui « gérer » un Engagement (pas de transition, pas de scope, pas de contact) — la capacité business (« suivre une relation client dans le temps ») n'est pas encore *utilisable*, seulement *fondée*.

### Capability 3 — Exception & Reconciliation
- **Ce qui existe déjà :** `DecisionKernel.Finding` (structure éphémère, recalculée à chaque analyse, jamais persistée).
- **Ce qui manque :** la quasi-totalité — agrégat `Exception`, persistance, cycle de vie, `InvestigationNote`, `ResolutionAction`.
- **Partiellement implémenté :** rien de véritablement partiel — le fragment existant n'est pas un embryon d'`Exception`, c'est un concept voisin construit pour un usage différent (alimenter le texte de l'analyse, pas suivre une investigation).
- **À refactorer probablement :** `DecisionKernel.Finding` devra vraisemblablement être repensé plutôt que simplement étendu — sa nature éphémère et non-identifiée contredit directement l'invariant cible (« aucune clôture silencieuse », Ideal Model H.4).
- **Code existant vs capacité réellement disponible :** aucune capacité réellement disponible aujourd'hui pour cet objet du domaine, malgré sa présence explicite dans la Constitution.

### Capability 4 — Recommendation Engine
- **Ce qui existe déjà :** `DecisionArc` (agrégat réel, cycle de vie `intention→decision→execution→consequences_linked→learning_proposed→closed|abandoned`, testé), `DecisionFeedback`, `recommendation_id` déjà déterministe.
- **Ce qui manque :** fusion en un agrégat unique (Blueprint T3) ; citation formelle de `Provenance` vers `EvidenceLedger` ; mécanisme `supersedes` pour l'évolution du texte.
- **Partiellement implémenté :** le cycle de vie cible existe déjà presque à l'identique dans `DecisionArc` — c'est la capacité la plus proche de la cible parmi celles non encore DONE.
- **À refactorer probablement :** migration de données (pas de reconstruction) des 3 tables historiques vers un agrégat unique, en s'appuyant sur `recommendation_id` comme clé de fusion (Blueprint C.5, déjà planifié).
- **Code existant vs capacité réellement disponible :** **écart plus faible qu'il n'y paraît.** Un utilisateur du produit *aujourd'hui* reçoit déjà des recommandations, peut donner un feedback, et voir un arc de suivi — la capacité business existe et fonctionne en production, seulement pas sur l'architecture cible. C'est la capacité où la distinction « FOUNDATION architecturalement » et « déjà vendable fonctionnellement » est la plus marquée de toute la roadmap.

### Capability 5 — Monthly Review Engine
- **Ce qui existe déjà :** 3 renderers matures et testés (PDF/PPTX/Excel), lisant `ExecutiveDecisionModel` ; `engagements.cadence` existe en base.
- **Ce qui manque :** tout déclenchement calendaire (rien ne consomme `cadence`) ; agrégat `Deliverable` cible ; lien formel vers des Recommendations closes.
- **Partiellement implémenté :** la restitution existe et fonctionne, mais seulement à l'initiative manuelle d'un upload — jamais comme un cycle récurrent porté par la relation.
- **À refactorer probablement :** le point le plus délicat de toute la roadmap — `ExecutiveDecisionModel` doit changer de source (lire `EvidenceLedger`/`Recommendation` plutôt que le blob `AnalysisResult`) sans jamais changer de forme de sortie (Blueprint C.4, strangler fig, validation byte-à-byte).
- **Code existant vs capacité réellement disponible :** un cabinet peut déjà recevoir un rapport aujourd'hui (valeur réelle, immédiate) — mais pas une *revue mensuelle* au sens du modèle cible (récurrente, déclenchée par la Cadence contractuelle, disciplinée par une seule vérité). Le code existant délivre une partie de la valeur sous une forme différente de celle visée.

### Capability 6 — Attention Score
- **Ce qui existe déjà :** rien de directement exploitable. Matière première latente : matérialité déjà calculée dans `financial_truth.py` (Capability 1), ancienneté déjà en base (`analyses.created_at`).
- **Ce qui manque :** tout — Blueprint C.6 le confirme explicitement, seule capacité de la roadmap qualifiée de « création pure ».
- **Partiellement implémenté :** rien.
- **À refactorer probablement :** sans objet — rien à refactorer, tout à construire.
- **Code existant vs capacité réellement disponible :** aucune capacité disponible, aucun écart à mesurer — le champ est vide des deux côtés.

### Capability 7 — Portfolio Intelligence
- **Ce qui existe déjà :** rien.
- **Ce qui manque :** tout — dépend intégralement d'Attention Score, elle-même absente.
- **Partiellement implémenté :** rien.
- **À refactorer probablement :** sans objet.
- **Code existant vs capacité réellement disponible :** aucun écart, les deux colonnes sont vides.

### Capability 8 — Learning Loop
- **Ce qui existe déjà :** les états `consequences_linked`/`learning_proposed` du cycle de vie de `DecisionArc`, et la détection réelle de conséquence (`arc_service.py`).
- **Ce qui manque :** tout rebouclage formel vers une priorisation (qui n'existe pas encore, Capability 6) ; pas de Value Object `Learning` nommé et distinct.
- **Partiellement implémenté :** la détection de conséquence existe et fonctionne ; sa transformation en apprentissage exploitable n'existe pas.
- **À refactorer probablement :** peu — le fragment existant (`arc_service.py`) semble réutilisable tel quel comme source d'événements pour un futur `Learning`, plutôt qu'à réécrire.
- **Code existant vs capacité réellement disponible :** un fragment technique existe et fonctionne, mais ne produit aujourd'hui aucune valeur métier observable par l'utilisateur (rien n'en dépend encore côté produit) — capacité techniquement amorcée, commercialement inexistante.

---

## 2. Synthèse — où le code existant surestime ou sous-estime la roadmap

- **Le code existant sous-estime son propre avancement sur Recommendation Engine et Learning Loop** : des fragments réels, fonctionnels, testés existent (`DecisionArc`) sous des noms qui ne correspondent pas au vocabulaire cible — le risque, signalé dans `CAPABILITY_MATURITY_MATRIX.md`, est de les reconstruire par méconnaissance plutôt que de les fusionner/étendre.
- **Le code existant surestimerait Monthly Review Engine si on le jugeait à la valeur perçue plutôt qu'à l'architecture cible** : un rapport de qualité sort déjà du système aujourd'hui, mais ce n'est pas encore une *revue* au sens du modèle (récurrente, disciplinée par une seule vérité, pilotée par la Cadence).
- **Exception & Reconciliation, Attention Score, Portfolio Intelligence n'ont aucun angle où le code existant compenserait leur absence** — ce sont les trois capacités les plus honnêtement vides de la roadmap.

---

## 3. Conclusion (Mission 10)

**Quelle est maintenant la prochaine capacité métier à développer ?**

## Capability 5 — Monthly Review Engine

**Justification, exclusivement à partir des Domain Models, du Blueprint, des ADR et de la Constitution :**

1. **Dépendances satisfaites, et seules à l'être.** `CAPABILITY_DEPENDENCY_MAP.md` établit que Monthly Review Engine est la seule capacité restante dont une version légitime (réduite à `EvidenceLedger`, voir §3 de cette carte) ne dépend que de capacités déjà **DONE** — Financial Evidence et Engagement Lifecycle. Exception & Reconciliation et Recommendation Engine partagent cette même propriété de dépendances satisfaites, mais Monthly Review Engine est la seule des trois qui produit un artefact directement remis à un tiers (Constitution Article VIII) — condition de toute vente réelle.
2. **C'est la capacité manquante du MVP Capability Set.** `MVP_CAPABILITY_SET.md` établit que Financial Evidence et Engagement Lifecycle, déjà DONE, sont insuffisantes seules pour vendre à un premier cabinet — il manque un livrable régulier. Monthly Review Engine est cette pièce manquante, et la seule.
3. **C'est le prochain maillon du Blueprint lui-même.** La table de correspondance (Blueprint B, ligne 7 et 11) et la stratégie de migration (Blueprint E, phase T5) placent le recâblage d'`ExecutiveDecisionModel` vers une projection disciplinée comme la suite naturelle une fois T1 (Evidence) et T2 (Engagement) posées — exactement l'état actuel.
4. **C'est une exigence directe de la Constitution, pas une préférence de séquencement.** Article VIII : « les livrables peuvent disparaître, le domaine demeure » — mais un domaine qui ne restitue jamais rien à l'extérieur ne sert à rien au professionnel qui doit le présenter à son client. Article XI (Tests de conformité), question 1 : « améliore-t-elle réellement l'endroit où se porte l'attention du professionnel ? » — un rapport qui arrive au bon rythme, sans que le professionnel doive s'en souvenir, répond directement à cette question.

**Ce que cette conclusion n'est pas :** ce n'est pas « T2B » ni « T3 » — c'est **Capability 5, Monthly Review Engine**, une unité de valeur métier justifiée par ce qu'elle apporte au conseiller financier (un cycle de restitution disciplé par sa relation contractuelle réelle), pas par sa position dans une séquence technique.

**Portée recommandée pour son ouverture (à documenter séparément, dans une future ADR, hors périmètre de ce document) :** la version réduite documentée en `CAPABILITY_DEPENDENCY_MAP.md` §3 — `Deliverable` lisant `EvidenceLedger` seul, sans attendre `Recommendation Engine` — cohérente avec la discipline déjà appliquée à T1/T2 (une tranche à la fois, strictement additive, jamais d'élargissement de périmètre non demandé).

---

**CAPABILITY TRANSITION REPORT COMPLETED.**
