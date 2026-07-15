"""
scripts/backfill_stripe_subscriptions.py — Pepperyn WP4B.5
Procédure contrôlée de backfill : stripe_subscription_id + subscription_status
pour les comptes PRO/SCALE créés avant l'application de la migration v12.

USAGE
-----
  cd backend/
  python scripts/backfill_stripe_subscriptions.py [--dry-run]

OPTIONS
-------
  --dry-run   Affiche les mises à jour prévues sans modifier la base.
              Toujours exécuter d'abord en --dry-run avant d'appliquer.

PRÉREQUIS
---------
  - Variables d'environnement chargées (.env ou Railway) :
      STRIPE_SECRET_KEY, STRIPE_PRICE_PRO, STRIPE_PRICE_SCALE
      SUPABASE_URL, SUPABASE_SERVICE_KEY
  - Migration v12_stripe_lifecycle_sync.sql déjà appliquée dans Supabase.

RÈGLES DE SÉCURITÉ
------------------
  1. Seules les companies avec stripe_customer_id non NULL et stripe_subscription_id NULL
     sont traitées (celles créées avant WP4B.5).
  2. Pour chaque customer, on récupère les subscriptions via l'API Stripe.
  3. Une seule subscription active autorisée — ambiguïté → SKIP + alerte.
  4. La price_id doit correspondre à PRO ou SCALE — price inconnue → SKIP + alerte.
  5. Aucune écriture si le résultat est ambigu.
  6. Le script est idempotent : relancer n'écrase pas des données déjà correctes.

SORTIES
-------
  ✅ BACKFILL   company_id  customer_id  sub_id  plan  status
  ⚠️  SKIP       company_id  raison
  ❌ ERROR      company_id  exception
"""
from __future__ import annotations

import os
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ── Import du contexte backend ────────────────────────────────────────────────
_BACKEND = os.path.join(os.path.dirname(__file__), "..")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_BACKEND, ".env"), override=False)
except ImportError:
    pass


def _load_config() -> dict:
    cfg = {
        "stripe_secret_key": os.environ.get("STRIPE_SECRET_KEY", ""),
        "price_pro":         os.environ.get("STRIPE_PRICE_PRO",   ""),
        "price_scale":       os.environ.get("STRIPE_PRICE_SCALE", ""),
        "supabase_url":      os.environ.get("SUPABASE_URL",        ""),
        "supabase_key":      os.environ.get("SUPABASE_SERVICE_KEY",""),
    }
    missing = [k for k, v in cfg.items() if not v]
    if missing:
        logger.error(f"Variables d'environnement manquantes : {missing}")
        sys.exit(1)

    # ── Garde-fou : clé Stripe Live refusée hors de ENVIRONMENT=production ───
    # Empêche toute modification accidentelle des données live depuis un poste local.
    # Pour exécuter contre les données de production, définir ENVIRONMENT=production.
    environment    = os.environ.get("ENVIRONMENT", "development")
    is_live_key    = cfg["stripe_secret_key"].startswith("sk_live_")
    if is_live_key and environment != "production":
        logger.error(
            "ARRÊT DE SÉCURITÉ : clé Stripe Live détectée avec ENVIRONMENT=%r. "
            "Une clé Live n'est autorisée que lorsque ENVIRONMENT=production. "
            "Configurez ENVIRONMENT=production explicitement avant d'utiliser "
            "ce script contre les données de production.",
            environment,
        )
        sys.exit(1)

    if is_live_key:
        logger.warning(
            "⚠️  Clé Stripe LIVE détectée + ENVIRONMENT=production. "
            "Ce script va écrire en BASE DE DONNÉES DE PRODUCTION. "
            "Assurez-vous d'avoir lancé --dry-run en premier."
        )
    else:
        logger.info(
            "Clé Stripe TEST détectée (ENVIRONMENT=%r). Mode sécurisé.", environment
        )

    return cfg


def _price_to_plan(price_id: str, cfg: dict) -> str | None:
    """Résout une price_id vers 'pro' ou 'scale'. Retourne None si inconnue."""
    if price_id == cfg["price_pro"]:
        return "pro"
    if price_id == cfg["price_scale"]:
        return "scale"
    return None


def _fetch_companies_to_backfill(sb) -> list[dict]:
    """
    Retourne les companies ayant :
      - stripe_customer_id IS NOT NULL
      - stripe_subscription_id IS NULL
    Ces companies ont été créées avant WP4B.5.
    """
    resp = (
        sb.from_("companies")
        .select("id, name, plan, stripe_customer_id, stripe_subscription_id, subscription_status")
        .not_.is_("stripe_customer_id", "null")
        .is_("stripe_subscription_id", "null")
        .in_("plan", ["pro", "scale"])
        .execute()
    )
    return resp.data or []


def _get_active_subscriptions(stripe, customer_id: str) -> list:
    """
    Récupère les subscriptions actives (statuts : active, trialing, past_due)
    pour un customer Stripe donné.
    """
    resp = stripe.Subscription.list(
        customer=customer_id,
        status="all",
        limit=10,
        expand=["data.items.data.price"],
    )
    # Conserver uniquement les abonnements non annulés
    active_statuses = {"active", "trialing", "past_due", "unpaid", "incomplete"}
    return [s for s in resp.auto_paging_iter() if s["status"] in active_statuses]


def run_backfill(dry_run: bool = True) -> None:
    cfg = _load_config()

    import stripe as _stripe
    _stripe.api_key = cfg["stripe_secret_key"]

    from supabase import create_client
    sb = create_client(cfg["supabase_url"], cfg["supabase_key"])

    companies = _fetch_companies_to_backfill(sb)
    logger.info(f"Companies à traiter : {len(companies)}")

    if not companies:
        logger.info("Aucune company à backfiller. Fin du script.")
        return

    ok_count   = 0
    skip_count = 0
    err_count  = 0

    for company in companies:
        cid        = company["id"]
        name       = company.get("name", "?")
        plan       = company.get("plan", "?")
        customer   = company["stripe_customer_id"]

        try:
            subs = _get_active_subscriptions(_stripe, customer)
        except Exception as e:
            logger.error(f"❌ ERROR  {cid} ({name})  stripe.Subscription.list : {e}")
            err_count += 1
            continue

        # ── Règle 3 : unicité ────────────────────────────────────────────────
        if len(subs) == 0:
            logger.warning(
                f"⚠️  SKIP   {cid} ({name})  "
                f"customer={customer}  aucune subscription active dans Stripe."
            )
            skip_count += 1
            continue

        if len(subs) > 1:
            sub_ids = [s["id"] for s in subs]
            logger.warning(
                f"⚠️  SKIP   {cid} ({name})  "
                f"customer={customer}  {len(subs)} subscriptions actives — ambiguïté : {sub_ids}"
            )
            skip_count += 1
            continue

        sub = subs[0]

        # ── Règle 4 : price connue ───────────────────────────────────────────
        try:
            price_id = sub["items"]["data"][0]["price"]["id"]
        except (KeyError, IndexError):
            price_id = ""

        resolved_plan = _price_to_plan(price_id, cfg)
        if resolved_plan is None:
            logger.warning(
                f"⚠️  SKIP   {cid} ({name})  "
                f"price_id={price_id!r} ne correspond ni à PRO ni à SCALE."
            )
            skip_count += 1
            continue

        # ── Cohérence plan ───────────────────────────────────────────────────
        if resolved_plan != plan:
            logger.warning(
                f"⚠️  SKIP   {cid} ({name})  "
                f"plan en base={plan!r} ≠ plan Stripe={resolved_plan!r} — "
                f"vérification manuelle requise."
            )
            skip_count += 1
            continue

        sub_id     = sub["id"]
        sub_status = sub["status"]

        logger.info(
            f"{'[DRY-RUN] ' if dry_run else ''}✅ BACKFILL  "
            f"{cid} ({name})  customer={customer}  "
            f"sub={sub_id}  plan={resolved_plan}  status={sub_status}"
        )

        if not dry_run:
            try:
                sb.from_("companies").update({
                    "stripe_subscription_id": sub_id,
                    "subscription_status":    sub_status,
                }).eq("id", cid).execute()
                ok_count += 1
            except Exception as e:
                logger.error(f"❌ ERROR  {cid} ({name})  update Supabase : {e}")
                err_count += 1
        else:
            ok_count += 1

    print()
    print("=" * 62)
    print(f"RÉSUMÉ {'(DRY-RUN)' if dry_run else '(APPLIQUÉ)'}")
    print(f"  ✅ Traités  : {ok_count}")
    print(f"  ⚠️  Skippés : {skip_count}")
    print(f"  ❌ Erreurs  : {err_count}")
    if dry_run:
        print()
        print("  → Relancer sans --dry-run pour appliquer les mises à jour.")
    print("=" * 62)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Backfill stripe_subscription_id + subscription_status (WP4B.5)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Mode simulation (défaut). Ajouter --no-dry-run pour appliquer.",
    )
    parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Applique réellement les mises à jour en base.",
    )
    args = parser.parse_args()
    run_backfill(dry_run=args.dry_run)
