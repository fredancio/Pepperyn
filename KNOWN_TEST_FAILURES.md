# KNOWN TEST FAILURES — Pepperyn

> Échecs de tests **pré-existants**, non causés par Release 1.0.
> Ces tests échouaient déjà avant WP1A sur la branche `main`.
> Ils doivent être corrigés dans un work package dédié (hors scope Release 1.0).

---

## Baseline établie le 2026-07-13 (pré-WP1B)

Commande de référence :
```
python3 -m pytest tests/test_rule_001_zero_manual_intervention.py \
                  tests/test_rule_002_zero_truncation.py \
                  tests/test_rule_003_renderer_responsibility.py \
                  --tb=line -q
```

Résultat : **4 failed, 26 passed** — score 3.97s

---

## Échecs documentés

### 1. `TestEDMSourceValues::test_edm_source_values`
**Fichier** : `tests/test_rule_001_zero_manual_intervention.py`

**Symptôme** : Les valeurs source EDM (Énoncé de Mission Documentée) retournées par
le renderer ne correspondent pas aux valeurs attendues par le test.

**Catégorie** : Données de test / logique EDM — non liée au billing ou aux quotas.

**Impact** : 0 sur Release 1.0 (WP1A–WP10 ne touchent pas au renderer EDM).

---

### 2. `TestPPTXContent::test_pptx_has_20_slides`
**Fichier** : `tests/test_rule_001_zero_manual_intervention.py`

**Symptôme** : Le PPTX généré contient un nombre de slides différent de 20.

```
AssertionError: PPTX doit toujours produire 20 slides.
```

**Catégorie** : Renderer PPTX — nombre de slides incohérent entre le test et l'implémentation.

**Impact** : 0 sur Release 1.0.

---

### 3. `TestRendererIsolation::test_pptx_produces_valid_bytes_with_empty_lists`
**Fichier** : `tests/test_rule_003_renderer_responsibility.py`

**Symptôme** :
```
AssertionError: PPTX doit toujours produire 17 slides. Reçu : 20 slides.
assert 20 == 17
```

**Catégorie** : Renderer PPTX — nombre de slides attendu désynchronisé (test dit 17, renderer produit 20).

**Impact** : 0 sur Release 1.0.

---

### 4. `TestRendererSelfContainment::test_pptx_handles_extreme_text_length`
**Fichier** : `tests/test_rule_003_renderer_responsibility.py`

**Symptôme** :
```
AssertionError: PPTX doit toujours produire 17 slides même avec texte extrême. Reçu : 21.
assert 21 == 17
```

**Catégorie** : Renderer PPTX — le texte extrême génère des slides additionnels (overflow non géré).

**Impact** : 0 sur Release 1.0.

---

## Périmètre Release 1.0

Ces 4 échecs sont **hors scope** de Release 1.0 (WP1–WP10).
Tous les Work Packages Release 1.0 (billing, usage, frontend, Stripe) doivent
passer leurs propres tests **sans aggraver** ce baseline de 4 échecs.

Toute régression au-delà de 4 échecs sur les fichiers `test_rule_00*.py`
doit être investiguée et bloquante avant merge.

---

## Référence de triage

| ID | Fichier test | Classe | Méthode | Statut |
|----|-------------|--------|---------|--------|
| KF-01 | test_rule_001 | TestEDMSourceValues | test_edm_source_values | pré-existant |
| KF-02 | test_rule_001 | TestPPTXContent | test_pptx_has_20_slides | pré-existant |
| KF-03 | test_rule_003 | TestRendererIsolation | test_pptx_produces_valid_bytes_with_empty_lists | pré-existant |
| KF-04 | test_rule_003 | TestRendererSelfContainment | test_pptx_handles_extreme_text_length | pré-existant |
