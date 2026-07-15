# TICKET-SEC-001 — RLS sur stripe_webhook_events

**Type** : Sécurité  
**Priorité** : Haute (bloquer avant mise en production multi-clients)  
**Sprint** : Post WP4B.5  
**Branche cible** : release-1/security-rls-stripe-events  
**Statut** : Migration + tests prêts — à appliquer sur Supabase

---

## Problème

La table `public.stripe_webhook_events` n'a pas de Row Level Security activée.

**Protection actuelle (v10)** : REVOKE ALL sur TABLE et FUNCTION pour anon et authenticated.
C'est correct, mais la protection repose sur les seules permissions PostgreSQL. Si elles
étaient accidentellement révoquées ou modifiées, la table serait exposée.

**Conséquence sans RLS** : un utilisateur authentifié (rôle `authenticated`) pourrait lire
l'intégralité du registre d'idempotence Stripe si une faille dans un autre endpoint
lui donnait accès direct à la table — `stripe_event_id`, `action`, `company_id` de
toutes les entreprises seraient lisibles.

## Pourquoi `FOR ALL + WITH CHECK` (et pas juste `USING`)

PostgreSQL permet d'écrire `USING` seul et infère automatiquement la même expression
comme `WITH CHECK` pour INSERT et UPDATE. Cette version fonctionne, mais :

- La protection des écritures (INSERT) repose sur un comportement **implicite**.
- Un auditeur sécurité qui lit la migration ne voit pas immédiatement que les INSERTs
  non autorisés sont bloqués.
- La doc PostgreSQL précise que ce comportement implicite "may change in future versions".

La version `FOR ALL + USING + WITH CHECK` (même expression sur les deux clauses)
est **fonctionnellement équivalente** mais rend l'intention explicite et résistante
aux évolutions de PostgreSQL.

## Impact sur l'architecture existante

| Composant | Affecté ? | Pourquoi |
|---|---|---|
| `apply_stripe_webhook()` SECURITY DEFINER | ❌ Non | S'exécute comme `postgres` (superuser) → bypass RLS automatique |
| Backend Railway (service_role) | ❌ Non | Supabase accorde `BYPASSRLS` à service_role au niveau rôle PG |
| Webhooks Stripe | ❌ Non | Transitent via Railway → service_role → non affectés |
| Rôles `anon` / `authenticated` | ✅ Bloqués | Par REVOKE (v10) + RLS (v13) — double protection |

## Migration SQL (v13_rls_stripe_webhook_events.sql)

Fichier créé : `backend/migrations/v13_rls_stripe_webhook_events.sql`

```sql
ALTER TABLE public.stripe_webhook_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_only"
    ON public.stripe_webhook_events
    FOR ALL
    USING      (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');
```

**Rollback documenté dans le fichier :**
```sql
DROP POLICY IF EXISTS "service_role_only" ON public.stripe_webhook_events;
ALTER TABLE public.stripe_webhook_events DISABLE ROW LEVEL SECURITY;
```

## Tests structurels (déjà écrits et passants)

10 tests ajoutés dans `TestV13RLSStripeWebhookEvents` (`test_billing_migration.py`) :

- V13-01 : fichier v13 existe dans migrations/
- V13-02 : `ENABLE ROW LEVEL SECURITY` présent et cible `stripe_webhook_events`
- V13-03 : policy nommée `service_role_only`
- V13-04 : **`FOR ALL` explicitement déclaré**
- V13-05 : clause `USING` présente
- V13-06 : **clause `WITH CHECK` présente et explicite** ← objectif principal
- V13-07 : `USING` cible `auth.role() = 'service_role'`
- V13-08 : `WITH CHECK` cible la même condition (2 occurrences min.)
- V13-09 : instructions de rollback présentes
- V13-10 : v10 ne contient pas déjà ENABLE RLS (pas de doublon)

**Résultat :** 161 passed, 0 failed (suite billing complète).

## Procédure d'application

```sql
-- Dans Supabase SQL Editor (projet ljcqbwbjeoeiugcoxfcf)
-- Copier-coller le contenu de backend/migrations/v13_rls_stripe_webhook_events.sql
```

## Exigences

- [ ] Appliquer `v13_rls_stripe_webhook_events.sql` dans Supabase SQL Editor
- [ ] Vérifier dans Supabase Dashboard → Authentication → Policies
      que la policy `service_role_only` apparaît sur `stripe_webhook_events`
- [ ] Vérifier que les webhooks Stripe passent toujours après l'application
      (Railway logs — aucune erreur 500 attendue)

## Références

- `backend/migrations/v10_stripe_webhook_events.sql` — REVOKE TABLE et FUNCTION
- `backend/migrations/v13_rls_stripe_webhook_events.sql` — migration RLS (prête)
- `backend/tests/test_billing_migration.py` — Groupe 9 `TestV13RLSStripeWebhookEvents`
- Audit WP4B.5 — finding sécurité #1
