# ANONYMIZATION_CAPABILITY_REVIEW.md

**Nature :** Mission 6 — cas pilote du protocole de conservation sélective. Vérifié par lecture directe du code réel de `main` (`backend/services/anonymization_service.py`, `backend/routers/analyze.py`, `backend/services/llm_service.py`, `backend/services/conversation_engine.py`, `backend/services/memory_service.py`, `backend/services/decision_memory_service.py`). Aucun code modifié.

---

## Ce qui existe (Layer 1, tel que le module lui-même le documente)

`anonymization_service.py` est un module pur, déterministe, sans I/O, bien conçu pour son périmètre déclaré : détection de colonnes sensibles par nom (Client, Fournisseur, Nom, Société, Email, Téléphone, IBAN, TVA, Adresse) et par format regex (email, IBAN, n° TVA), génération d'alias stables (`CLIENT_001`, `FOURNISSEUR_001`, ...), table de correspondance conservée côté serveur, jamais envoyée à l'IA, et fonction de ré-identification récursive. Le docstring du module reconnaît lui-même ses limites (pas de NER sur texte libre, pas de détection de téléphone en texte libre) — c'est une conception honnête sur son propre périmètre déclaré. Sur ce périmètre précis, le mécanisme est correct.

La question n'est pas la qualité du module. C'est sa couverture réelle sur l'ensemble des chemins qui atteignent un LLM — vérifiée ci-dessous point par point, comme demandé.

---

## Réponses aux 15 questions, fondées sur le code

**1. Quels types de données sont détectés et remplacés ?** Client, Fournisseur, Personne (nom/prénom/employé/contact), Entreprise, Adresse, Email, Téléphone (colonne uniquement, pas texte libre), IBAN, TVA/SIRET/SIREN — par nom de colonne ou par regex de format. Confirmé par lecture de `COLUMN_CATEGORY_KEYWORDS` et `VALUE_REGEX_CATEGORIES`.

**2. Quels chemins LLM passent obligatoirement par l'anonymisation ?** Un seul avec garantie complète : le pipeline principal d'analyse (`POST /api/analyze` → `anonymize_parsed_data()` → `run_full_pipeline()` → `deanonymize_recursive()`, lignes 475/550/572 de `analyze.py`). C'est le chemin le mieux protégé et le plus vérifié.

**3. Existe-t-il des chemins alternatifs qui la contournent ? Oui, quatre, vérifiés par le code, pas supposés :**

- **`relation_section`** (`analyze.py` lignes 490-513) : le nom réel de l'entité (`_ent.get("name")`) est lu directement depuis Supabase et injecté tel quel dans le prompt (`llm_service.py` ligne 867-868, `prompt += f"\n{relation_section}\n"`). Aucun passage par la table de correspondance. **Contournement total, systématique, sur chaque analyse où `entity_id` est fourni.**
- **`memory_section`** (mémoire entreprise — `memory_service.py`) : construite à partir de `financial_metrics` et `profile`, injectée telle quelle dans le prompt. Pas de vérification qu'elle contient des noms propres dans cette session (métriques probablement agrégées), mais la fonction ne passe par aucune anonymisation — l'absence de preuve de contenu sensible n'est pas une preuve d'absence de risque.
- **`actions_section`** (mémoire décisionnelle — `decision_memory_service.py`, `build_decision_memory_prompt_section`) : construite à partir de `get_latest_report_with_feedback()`, qui lit le texte des recommandations **déjà stockées après ré-identification** (le rapport stocké en base est le rapport final montré à l'utilisateur, donc avec les noms réels). Ce texte est réinjecté tel quel dans le prompt de la prochaine analyse. **Contournement confirmé : des noms réels, une fois ré-identifiés pour un rapport, reviennent en clair dans le prompt de l'analyse suivante.**
- **Le chat V2 (Conversation Engine)** : c'est le contournement le plus significatif. `POST /api/chat` anonymise bien `chat_message`/`chat_context`/`history` (lignes 966-969) — mais uniquement quand le Conversation Engine V2 n'est **pas** disponible. Quand il l'est (`_get_or_build_executive_case_v2`, chemin préféré), l'`ExecutiveCase V2` est construit depuis `_analysis_result_cache` — **le résultat déjà ré-identifié, en noms réels** — et c'est cet objet qui est transmis à `build_payload()` puis envoyé à Claude Sonnet (`conversation_engine.py`, `get_chat_response`). **L'anonymisation du message utilisateur devient sans objet : l'essentiel du contenu sensible (le dossier complet) part en clair à chaque tour de conversation, sur le chemin de chat aujourd'hui préféré.**

**4. Les différents agents reçoivent-ils tous les mêmes garanties ? Non.** Le pipeline principal (`run_full_pipeline`, les deux appels Claude de l'analyse) reçoit des données anonymisées pour `anonymized_data`, mais du texte en clair pour `relation_section`/`memory_section`/`actions_section` dans le même prompt. Le Conversation Engine V2 ne reçoit aucune garantie d'anonymisation sur l'objet central de son prompt.

**5. Les prompts, logs, traces, erreurs et fichiers temporaires sont-ils couverts ?** Aucune écriture de log contenant `parsed_data`, `prompt` complet, ou table de correspondance n'a été trouvée par grep sur `analyze.py`/`llm_service.py` — les logs observés sont des messages courts (ex. `[ANALYZE] Erreur pipeline IA`) sans contenu de données. Absence de preuve de fuite par les logs, mais absence de preuve n'est pas une garantie architecturale — aucun mécanisme n'empêche explicitement qu'un futur `logger.debug(prompt)` fuite des données non anonymisées. Aucun fichier temporaire sur disque détecté dans le chemin d'anonymisation (le traitement est en mémoire).

**6. Où et comment la correspondance de réidentification est-elle conservée ?** `_anonymization_cache: dict[str, CorrespondenceTable]`, dictionnaire Python **en mémoire, dans le processus du serveur API**, clé = `analyse_id`. Aucune persistance en base. Conséquence directe : un redémarrage du serveur, un déploiement multi-instances, ou un recyclage de processus fait disparaître silencieusement la table — le code de `/api/chat` gère ce cas par un simple `if correspondence_table and not correspondence_table.is_empty`, qui **désactive silencieusement l'anonymisation sans avertir l'utilisateur** plutôt que d'échouer bruyamment. C'est un choix de disponibilité au détriment de la garantie de confidentialité, non documenté comme tel dans le code.

**7. Comment évite-t-on une réidentification croisée entre organisations ?** La table est indexée par `analyse_id` (UUID), et l'accès aux exports est vérifié par `_verify_export_access(analyse_id, company_id)` contre `_analysis_owner`. Mais la table de correspondance elle-même, consultée par `/api/chat`, n'a pas été vérifiée dans cette session comme passant par le même contrôle d'accès explicite — `correspondence_table = _anonymization_cache.get(request.analysis_id)` ne revérifie pas `company_id` à cet endroit précis du code lu. **Point à vérifier plus profondément avant tout verdict définitif — signalé comme réserve, pas comme fait établi.**

**8. Les exports restaurent-ils correctement les valeurs ?** Oui, par construction : `export_pdf_service.py`, `export_pptx_service.py`, `excel_export.py` ne contiennent aucun appel LLM (confirmé par grep, zéro résultat) — ils rendent uniquement `analysis_result`, déjà ré-identifié en amont. Ce n'est pas une nouvelle surface d'anonymisation, c'est un rendu de données déjà réelles par conception : correct.

**9. Le chat conversationnel est-il couvert ?** Partiellement, et de façon contre-intuitive : le chemin *legacy* (`call_chat_intelligent`) anonymise correctement message/contexte/historique. Le chemin *V2, préféré*, ne le fait pas pour l'objet central du prompt (`ExecutiveCase V2`). Le point d'entrée sans fichier (`POST /api/analyze/text`) **n'anonymise rien du tout** — il envoie `request.query` tel quel à Claude Haiku, sans jamais consulter le module d'anonymisation. Ce n'est pas nécessairement une faute de conception (il n'y a pas de fichier, donc pas de table de correspondance à constituer), mais la promesse affichée sur `/legal/donnees-securisees` (« Avant qu'une analyse ne soit réalisée par l'IA, ces informations sont automatiquement remplacées ») ne précise pas cette limite à l'utilisateur.

**10. Les données structurées, non structurées et métadonnées sont-elles couvertes ?** Structurées (colonnes classées) : oui. Texte libre à l'intérieur d'un fichier structuré (ex. commentaire de facture) : oui, par substitution de sous-chaîne une fois une valeur déjà connue de la table. Texte libre totalement indépendant d'une colonne structurée (ex. un nom de personne mentionné uniquement dans une cellule de commentaire, jamais vu ailleurs) : **non couvert**, le docstring du module le reconnaît lui-même. Métadonnées de fichier (nom du fichier uploadé, par exemple) : non vérifiées dans cette session.

**11. L'anonymisation est-elle indépendante de la source (Excel/ERP/API/MCP) ?** Oui pour son mécanisme (elle opère sur `parsed_data`, une structure déjà normalisée après `FileConnector.fetch()`, indépendamment du format source). Mais aucun connecteur ERP/API/MCP n'existe aujourd'hui dans le code réel (confirmé absent lors des sessions précédentes de cartographie) — l'indépendance de la source est actuellement une propriété non testée en pratique, uniquement une propriété de conception.

**12. Fonctionne-t-elle avec un modèle cloud et un modèle local ?** Le mécanisme lui-même est agnostique du fournisseur (il transforme les données avant tout appel, quel que soit le client LLM utilisé). Mais aucun modèle local n'existe dans le code réel aujourd'hui — la question est actuellement théorique, pas vérifiable par le code.

**13. Quelle promesse de sécurité est réellement démontrable ?** *« Les données extraites d'un fichier uploadé et classées comme sensibles par nom de colonne ou par format reconnu, quand elles transitent par le pipeline d'analyse principal, ne sont pas envoyées en clair au modèle d'IA — à l'exception du contexte relationnel d'entité, de la mémoire entreprise, de la mémoire décisionnelle, et de l'essentiel du contenu du chat V2, qui le sont. »* C'est une promesse sensiblement plus étroite que celle affichée publiquement sur `/legal/donnees-securisees`.

**14. Quelles données restent sensibles même après anonymisation ?** Toute donnée numérique elle-même (montants, marges, ratios) n'est jamais anonymisée — ce n'est pas son objet, mais cela reste une donnée commercialement sensible transmise en clair à un tiers (l'API du fournisseur LLM), par design du produit, pas par défaut de l'anonymisation.

**15. Verdict.**

## STRENGTHEN

Le mécanisme de fond (Layer 1, `anonymization_service.py`) est correct, bien conçu, et ne doit pas être remplacé — REPLACE serait injustifié, il n'y a aucune preuve que le mécanisme lui-même est structurellement inadéquat. Mais le verdict ne peut pas être KEEP : quatre chemins de contournement réels et actuellement actifs ont été identifiés par lecture directe du code, dont un (le chat V2, chemin préféré) rend la protection largement illusoire pour la conversation continue avec un dossier. La priorité de renforcement, par ordre de risque décroissant : (1) faire passer le payload de l'`ExecutiveCase V2` par la table de correspondance avant tout appel LLM dans `conversation_engine.py` ; (2) anonymiser `relation_section` avant injection dans le prompt ; (3) anonymiser `actions_section` (mémoire décisionnelle) au moment de sa construction, pas seulement au moment du stockage ; (4) clarifier la promesse publique pour refléter honnêtement le périmètre réel, ou étendre la couverture à `/api/analyze/text`.

---

**ANONYMIZATION_CAPABILITY_REVIEW ÉTABLIE À PARTIR DU CODE RÉEL. AUCUN CODE MODIFIÉ.**
