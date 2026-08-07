# TRUST_BOUNDARY_CLOSURE_PLAN.md

**Nature :** Phase 7. Plan uniquement — **correctif non écrit dans cette mission**, conforme à l'instruction explicite (« ne pas écrire le correctif tant que la fondation documentaire n'est pas validée »). Aucun code.

**Règle cible :** aucun composant Domain ou agent ne doit appeler directement un fournisseur LLM. Tout appel traverse un Trust Gateway canonique.

---

## 1. Inventaire complet des sites d'appel LLM (mis à jour et clos dans cette mission)

Complète `ANONYMIZATION_CAPABILITY_REVIEW.md`, qui laissait ouverte la couverture de 4 fichiers. **Vérifié cette session par lecture directe : `decision_rules.py`, `executive_decision_model.py`, `file_parser.py`, `financial_normalizer.py` ne contiennent aucun appel LLM** (grep confirmé : zéro occurrence de client/messages.create/llm_service dans leur propre code — leurs seules mentions de `llm_service` sont des commentaires de cohérence de règle, pas des appels). **L'inventaire des sites d'appel réels est donc désormais complet et fermé :**

| # | Site | Anonymisation | Isolation | Logging | Provenance |
|---|---|---|---|---|---|
| 1 | `classify_document` (Haiku, routage) | N/A — reçoit `parsed_data` déjà structuré, pas de texte libre sensible identifié | Par `analyse_id`, cohérent avec le reste du pipeline | Pas de contenu loggé (grep confirmé) | N/A |
| 2 | Evidence Graph agent (Sonnet) | **Oui, indirect** — reçoit `parsed_data` déjà anonymisé en amont (ligne 550 de `analyze.py`, `anonymized_data`) | Idem | Idem | Traçabilité déjà son objet (`sheets_verified`) |
| 3 | Financial Analyst pre-pass | **Oui, indirect** — même source anonymisée | Idem | Idem | — |
| 4 | Strategic CFO pre-pass | **Oui, indirect** — même source | Idem | Idem | — |
| 5 | Call 1 (analyse principale) | **Non complet** — `relation_section`, `memory_section`, `actions_section` en clair (voir `ANONYMIZATION_CAPABILITY_REVIEW.md`) | Par `analyse_id` | — | — |
| 6 | Call 2 (vérification) | Même statut que Call 1 (mêmes sections injectées) | Idem | — | — |
| 7 | `_score_analysis` | Oui, indirect (opère sur texte déjà produit par Call 2) | Idem | — | — |
| 8 | `/api/analyze/text` | **Non — aucune anonymisation, par conception (pas de fichier)** | Session/JWT invité, pas de correspondance à isoler | — | — |
| 9 | `call_chat_intelligent` (chat legacy) | Oui, conditionnelle à l'existence d'une table non vide | Par `analysis_id`, lue depuis `_anonymization_cache` (mémoire de processus, non partagée) | — | — |
| 10 | `conversation_engine.py::get_chat_response` (chat V2, **chemin préféré**) | **Non — contournement majeur déjà documenté**, le payload contient le dossier déjà ré-identifié | Idem | — | — |

## 2. Contournements confirmés, classés par gravité

1. **Critique — Conversation Engine V2 (#10)** : envoie le dossier complet en clair à chaque tour, sur le chemin de chat aujourd'hui préféré.
2. **Élevé — `relation_section`/`memory_section`/`actions_section` (#5, #6)** : noms réels injectés dans les deux appels du pipeline principal.
3. **Faible, assumé par conception — `/api/analyze/text` (#8)** : pas de fichier, pas de table à appliquer ; risque résiduel = l'utilisateur tape lui-même une donnée sensible en texte libre, hors du périmètre déclaré de la promesse actuelle.
4. **Fragilité structurelle, pas un contournement en soi — `_anonymization_cache` en mémoire de processus (#9, #10)** : disparaît silencieusement au redémarrage, désactivant l'anonymisation sans avertissement.

## 3. Trust Gateway minimal — proposition

```
TrustGateway
├── anonymize_before_llm(payload, correspondence_table) -> payload_safe
│     — point de passage OBLIGATOIRE pour tout contenu envoyé à un LLM
│     — refuse (lève une exception) si aucune correspondance_table n'est fournie
│       ET que le payload contient un motif reconnu (email, IBAN, TVA) — filet de
│       sécurité minimal même pour les chemins qui pensent ne pas en avoir besoin
├── deanonymize_after_llm(response, correspondence_table) -> response_safe
├── log_llm_call(site_id, payload_hash, anonymization_status) -> AuditRecord
│     — trace QUE l'appel a eu lieu et QUEL était son statut d'anonymisation,
│       jamais le contenu lui-même (cohérent avec la réserve déjà posée sur les logs)
└── require_provenance(payload) -> bool
      — vérifie que toute donnée externe porte source/date/juridiction
        (External Knowledge Gateway, déjà nommé dans la Cognitive Architecture)
```

**Principe de conception :** le Trust Gateway n'est pas un nouveau service métier — c'est un point de passage obligatoire, fin, sans logique de domaine. Les 10 sites d'appel actuels doivent tous être recâblés pour y passer, jamais dupliqués en une nouvelle couche parallèle (cohérent avec la leçon déjà posée : ne pas laisser deux mécanismes de garde-fou coexister indéfiniment).

## 4. Tests d'architecture empêchant tout appel direct futur

- **Test statique** : un test qui échoue si un import direct de `anthropic`/client LLM est détecté en dehors du module `TrustGateway` (grep automatisé en CI, pas un contrôle manuel).
- **Test de contrat** : chaque site d'appel doit démontrer, par test, qu'aucun appel LLM n'est possible sans passer par `anonymize_before_llm` en amont — testable par mock/spy sur le Gateway.
- **Test de non-régression Golden Case** : tout payload effectivement envoyé à un LLM, capturé dans un Golden Case (`GOLDEN_CASE_001_PHIDANI.md`), ne doit contenir aucun motif reconnu comme sensible — vérifiable automatiquement à chaque replay.

---

## Séquencement de correction, non exécuté ici

1. Conversation Engine V2 (le plus grave, le chemin le plus utilisé).
2. `relation_section`/`memory_section`/`actions_section`.
3. Décision explicite (Fred) sur `/api/analyze/text` : clarifier la promesse publique, ou border ce endpoint.
4. Remplacement de `_anonymization_cache` en mémoire par un stockage persistant (partagé avec la dette déjà nommée dans `LEGACY_CAPABILITY_REVIEW_MATRIX.md`, même famille de risque).

**Aucune de ces quatre étapes n'est exécutée dans cette mission** — ce document est un plan, pas un correctif, conforme à la Phase 7.

---

**TRUST_BOUNDARY_CLOSURE_PLAN ÉTABLI. AUCUN CODE ÉCRIT.**
