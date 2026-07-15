"""
PEPPERYN — Product Catalog
backend/config/product_catalog.py

Source canonique unique pour toutes les données commerciales de Pepperyn.

═══════════════════════════════════════════════════════════════════════════════
RÈGLE D'OR
═══════════════════════════════════════════════════════════════════════════════
Ce fichier est la SEULE source de vérité pour :
  - les Plans commerciaux (FREE, PRO, SCALE)
  - les Executive Capacity Packs (Starter, Growth, Scale)
  - les prix, quotas d'Analyses, caps d'Interactions, limites d'Entités
  - les Stripe Price IDs (résolus depuis les variables d'environnement Railway)

Ne jamais dupliquer ces valeurs ailleurs dans le code.
Toute évolution tarifaire ou de quota = modifier ce seul fichier.

Les consommateurs actuels (usage_service, billing_service, billing.py,
featureGate.ts) sont migrés dans WP1B et WP2.
Jusqu'à cette migration, le comportement observable de Pepperyn est inchangé.

═══════════════════════════════════════════════════════════════════════════════
RÈGLE CONTRACTUELLE CRITIQUE — INTERACTIONS
═══════════════════════════════════════════════════════════════════════════════
Il n'existe AUCUNE limite d'Interactions par Analyse dans Pepperyn.
Le quota d'Interactions est UNIQUEMENT mensuel (chat_monthly_cap).
  - Aucune clé chat_per_analysis ne doit exister ici ni dans ses consommateurs.
  - Aucune moyenne d'Interactions par Analyse ne doit être encodée.
  - L'utilisateur répartit ses Interactions librement entre ses Analyses.

═══════════════════════════════════════════════════════════════════════════════
ORDRE DE CONSOMMATION DES ANALYSES (logique implémentée dans usage_service)
═══════════════════════════════════════════════════════════════════════════════
  1. Les Analyses issues d'un Executive Capacity Pack (bonus_analyses en DB)
     sont consommées EN PREMIER.
  2. Le quota mensuel d'Analyses (analyses_count en DB) est utilisé ensuite.
  3. Au renouvellement mensuel : analyses_count → 0. bonus_analyses INCHANGÉ.
  4. Les Analyses bonus non consommées persistent indéfiniment.

═══════════════════════════════════════════════════════════════════════════════
RÉFÉRENCES
═══════════════════════════════════════════════════════════════════════════════
PEPPERYN_DECISIONS_V1.md (WP0.75) · PEPPERYN_BUSINESS_RULES_V1_FINAL.md
ADR_001_PRODUCT_CATALOG.md · TERMINOLOGY.md · RELEASE_1_CHECKLIST.md
Release 1.0 — WP1A — 13 juillet 2026
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# TYPES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PlanLimits:
    """
    Quotas mensuels d'un Plan Pepperyn.

    Attributs
    ---------
    analyses : Optional[int]
        Nombre maximum d'Analyses par mois.
        None = illimité (Enterprise uniquement).
    chat_monthly_cap : Optional[int]
        Nombre maximum d'Interactions par mois (quota GLOBAL mensuel).
        None = illimité (Enterprise uniquement).
        CRITIQUE : ce quota est mensuel et global. Aucune limite par Analyse.
    max_entities : Optional[int]
        Nombre maximum d'Entités gérées sur le compte.
        None = illimité (Plan SCALE, premium, power, enterprise).
    """
    analyses:         Optional[int]
    chat_monthly_cap: Optional[int]
    max_entities:     Optional[int]


@dataclass(frozen=True)
class ExecutiveCapacityPack:
    """
    Executive Capacity Pack — produit Stripe en paiement unique.

    Règles contractuelles NON NÉGOCIABLES :
    ─────────────────────────────────────────
    · Ajoute uniquement des Analyses supplémentaires (bonus_analyses en DB).
    · N'ajoute JAMAIS d'Interactions chat.
    · Ne modifie JAMAIS le Plan ni la date de renouvellement Stripe.
    · Les Analyses bonus sont consommées EN PREMIER (avant le quota mensuel).
    · Les Analyses bonus non consommées persistent au renouvellement mensuel.

    Attributs
    ---------
    pack_id : str
        Identifiant interne et Stripe metadata (ex : "addon_starter").
    display_name : str
        Nom officiel selon TERMINOLOGY.md (ex : "Starter Capacity Pack").
    analyses_added : int
        Nombre d'Analyses créditées sur bonus_analyses en DB.
    price_cents : int
        Prix en centimes d'euro (ex : 3_900 pour 39,00 €).
    stripe_price_id_env : str
        Nom de la variable d'environnement Railway contenant le Stripe Price ID.
    """
    pack_id:             str
    display_name:        str
    analyses_added:      int
    price_cents:         int
    stripe_price_id_env: str

    @property
    def stripe_price_id(self) -> Optional[str]:
        """
        Stripe Price ID résolu depuis l'environnement Railway.
        Retourne None si la variable est absente (environnement de test).
        Ne loggue jamais la valeur.
        """
        return os.environ.get(self.stripe_price_id_env) or None


@dataclass(frozen=True)
class PlanDisplay:
    """
    Métadonnées d'affichage d'un Plan (nom public, label, niveau hiérarchique).

    Attributs
    ---------
    plan_id : str
        Identifiant interne du Plan.
    name : str
        Nom court public (ex : "PRO").
    label : str
        Label complet public (ex : "Plan PRO").
    level : int
        Niveau hiérarchique (0 = FREE, 1 = PRO, 2 = SCALE, 3 = Enterprise).
    is_commercial : bool
        True uniquement pour FREE, PRO et SCALE.
        Les Plans legacy et internes ont is_commercial = False.
    """
    plan_id:       str
    name:          str
    label:         str
    level:         int
    is_commercial: bool


# ─────────────────────────────────────────────────────────────────────────────
# IDENTIFIANTS OFFICIELS
# ─────────────────────────────────────────────────────────────────────────────

COMMERCIAL_PLAN_IDS: List[str] = ["free", "pro", "scale"]
"""Plans commerciaux actifs. Seuls ces trois Plans sont retournés par
get_commercial_plans() et vendus via l'interface Pepperyn."""

EXECUTIVE_CAPACITY_PACK_IDS: List[str] = ["addon_starter", "addon_growth", "addon_scale"]
"""Identifiants internes des Executive Capacity Packs actifs."""

LEGACY_PLAN_ALIASES: Dict[str, str] = {
    "standard":      "pro",
    "standard_beta": "pro",
    "premium":       "scale",
}
"""
Plans legacy présents dans companies.plan en base de données.
Alignement officiel (WP0.75) :
  standard       → PRO  (30 Analyses, 75 Interactions, 10 Entités)
  standard_beta  → PRO  (idem)
  premium        → SCALE (100 Analyses, 500 Interactions, Entités illimitées)

Ces plans ne sont jamais retournés par get_commercial_plans().
L'interface affiche "Plan PRO" ou "Plan SCALE" pour ces comptes.
"""

LEGACY_INTERNAL_PLANS: List[str] = ["power", "enterprise"]
"""
Plans internes hérités — NON commerciaux, JAMAIS exposés dans l'interface.

IMPORTANT : power et enterprise ne figurent PAS dans la CHECK constraint
companies_plan_check de Supabase (confirmé en audit pre-WP1, 13/07/2026).
Ces valeurs ne peuvent pas être écrites dans companies.plan en production.
Présents dans PLAN_LIMITS uniquement pour la compatibilité du code hérité
(usage_service.py) jusqu'à sa migration en WP1B.
"""


# ─────────────────────────────────────────────────────────────────────────────
# PLAN_LIMITS — Quotas officiels par Plan (WP0.75 — NON NÉGOCIABLES)
# ─────────────────────────────────────────────────────────────────────────────

PLAN_LIMITS: Dict[str, PlanLimits] = {

    # ── Plans commerciaux actifs ──────────────────────────────────────────────
    "free":  PlanLimits(analyses=1,    chat_monthly_cap=3,    max_entities=1),
    "pro":   PlanLimits(analyses=30,   chat_monthly_cap=75,   max_entities=10),
    "scale": PlanLimits(analyses=100,  chat_monthly_cap=500,  max_entities=None),

    # ── Plans legacy — alignés sur PRO ───────────────────────────────────────
    "standard":      PlanLimits(analyses=30,  chat_monthly_cap=75,   max_entities=10),
    "standard_beta": PlanLimits(analyses=30,  chat_monthly_cap=75,   max_entities=10),

    # ── Plans legacy — alignés sur SCALE ─────────────────────────────────────
    "premium": PlanLimits(analyses=100, chat_monthly_cap=500, max_entities=None),

    # ── Plans internes hérités — JAMAIS assignés via Stripe ──────────────────
    # Alignés sur SCALE pour limiter l'impact en cas de résidu en DB.
    # Retirés de l'interface publique. Migration usage_service : WP1B.
    "power":      PlanLimits(analyses=100,  chat_monthly_cap=500,  max_entities=None),
    "enterprise": PlanLimits(analyses=None, chat_monthly_cap=None, max_entities=None),
}


# ─────────────────────────────────────────────────────────────────────────────
# PLAN_PRICES — Prix des abonnements en centimes d'euro
# ─────────────────────────────────────────────────────────────────────────────

PLAN_PRICES: Dict[str, int] = {
    "free":  0,        #   0,00 €
    "pro":   14_900,   # 149,00 €
    "scale": 34_900,   # 349,00 €
}
"""
Prix des Plans commerciaux actifs en centimes d'euro.
Les Plans legacy et internes n'ont pas de prix défini (pas de Stripe).
"""


# ─────────────────────────────────────────────────────────────────────────────
# EXECUTIVE_CAPACITY_PACKS — Définitions des packs d'Analyses bonus
# ─────────────────────────────────────────────────────────────────────────────

EXECUTIVE_CAPACITY_PACKS: Dict[str, ExecutiveCapacityPack] = {

    "addon_starter": ExecutiveCapacityPack(
        pack_id             = "addon_starter",
        display_name        = "Starter Capacity Pack",
        analyses_added      = 10,
        price_cents         = 3_900,    # 39,00 €
        stripe_price_id_env = "STRIPE_PRICE_ADDON_STARTER",
    ),

    "addon_growth": ExecutiveCapacityPack(
        pack_id             = "addon_growth",
        display_name        = "Growth Capacity Pack",
        analyses_added      = 20,
        price_cents         = 7_900,    # 79,00 €
        stripe_price_id_env = "STRIPE_PRICE_ADDON_GROWTH",
    ),

    "addon_scale": ExecutiveCapacityPack(
        pack_id             = "addon_scale",
        display_name        = "Scale Capacity Pack",
        analyses_added      = 80,
        price_cents         = 23_900,   # 239,00 €
        stripe_price_id_env = "STRIPE_PRICE_ADDON_SCALE",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# STRIPE_PRICE_IDS — Price IDs résolus depuis les variables d'environnement
# ─────────────────────────────────────────────────────────────────────────────

def _load_stripe_price_ids() -> Dict[str, Optional[str]]:
    """
    Charge les Stripe Price IDs depuis les variables d'environnement Railway.
    Appelé une seule fois à l'import du module.
    Ne loggue jamais les valeurs des Price IDs.
    Un Price ID absent retourne None (module importable sans variables Stripe).
    """
    return {
        "free":          None,   # FREE n'a pas de Stripe Price ID
        "pro":           os.environ.get("STRIPE_PRICE_PRO")           or None,
        "scale":         os.environ.get("STRIPE_PRICE_SCALE")         or None,
        "addon_starter": os.environ.get("STRIPE_PRICE_ADDON_STARTER") or None,
        "addon_growth":  os.environ.get("STRIPE_PRICE_ADDON_GROWTH")  or None,
        "addon_scale":   os.environ.get("STRIPE_PRICE_ADDON_SCALE")   or None,
    }


STRIPE_PRICE_IDS: Dict[str, Optional[str]] = _load_stripe_price_ids()
"""
Stripe Price IDs pour les produits payants, résolus à l'import.
None pour FREE (pas de Stripe) et pour tout Price ID absent (test / staging).
Appeler validate_stripe_price_ids() avant un checkout pour détecter
les Price IDs manquants.
"""


# ─────────────────────────────────────────────────────────────────────────────
# PLAN_DISPLAY_NAMES — Noms publics des Plans
# ─────────────────────────────────────────────────────────────────────────────

PLAN_DISPLAY_NAMES: Dict[str, PlanDisplay] = {

    # ── Plans commerciaux actifs ──────────────────────────────────────────────
    "free":  PlanDisplay(plan_id="free",  name="FREE",  label="Plan FREE",  level=0, is_commercial=True),
    "pro":   PlanDisplay(plan_id="pro",   name="PRO",   label="Plan PRO",   level=1, is_commercial=True),
    "scale": PlanDisplay(plan_id="scale", name="SCALE", label="Plan SCALE", level=2, is_commercial=True),

    # ── Plans legacy — affichés sous le nom du Plan actif équivalent ──────────
    "standard":      PlanDisplay(plan_id="standard",      name="PRO",   label="Plan PRO",   level=1, is_commercial=False),
    "standard_beta": PlanDisplay(plan_id="standard_beta", name="PRO",   label="Plan PRO",   level=1, is_commercial=False),
    "premium":       PlanDisplay(plan_id="premium",       name="SCALE", label="Plan SCALE", level=2, is_commercial=False),

    # power et enterprise sont absents : jamais affichés dans l'interface.
}
"""
Noms publics des Plans.
power et enterprise n'ont pas d'entrée : ils ne doivent jamais apparaître
dans l'interface utilisateur ni dans les communications Pepperyn.
"""


# ─────────────────────────────────────────────────────────────────────────────
# FONCTIONS PUBLIQUES
# ─────────────────────────────────────────────────────────────────────────────

def get_plan(plan_id: str) -> PlanLimits:
    """
    Retourne les PlanLimits pour un identifiant de Plan donné.

    Accepte les Plans commerciaux (free, pro, scale), les Plans legacy
    (standard, standard_beta, premium) et les Plans internes hérités
    (power, enterprise — compat uniquement).

    Lève KeyError pour tout identifiant inconnu.

    Paramètres
    ----------
    plan_id : str
        Identifiant interne du Plan (ex : "pro", "standard").

    Retourne
    --------
    PlanLimits avec analyses, chat_monthly_cap, max_entities.

    Lève
    ----
    KeyError si plan_id est inconnu.

    Exemple
    -------
    >>> get_plan("pro")
    PlanLimits(analyses=30, chat_monthly_cap=75, max_entities=10)
    >>> get_plan("standard")  # legacy → même quotas que PRO
    PlanLimits(analyses=30, chat_monthly_cap=75, max_entities=10)
    """
    if plan_id not in PLAN_LIMITS:
        raise KeyError(
            f"Plan inconnu : '{plan_id}'. "
            f"Plans valides : {list(PLAN_LIMITS.keys())}"
        )
    return PLAN_LIMITS[plan_id]


def get_commercial_plans() -> List[Dict]:
    """
    Retourne la liste des Plans commerciaux actifs pour l'API publique frontend.

    Seuls FREE, PRO et SCALE sont inclus.
    Les Plans legacy (standard, standard_beta, premium) et les Plans internes
    (power, enterprise) ne sont JAMAIS retournés par cette fonction.

    Retourne
    --------
    List[Dict] avec les clés :
        id                 — identifiant interne du Plan
        name               — nom court public ("FREE", "PRO", "SCALE")
        label              — label complet ("Plan FREE", "Plan PRO", "Plan SCALE")
        price_cents        — prix en centimes d'euro
        analyses_per_month — quota mensuel d'Analyses
        chat_per_month     — quota mensuel d'Interactions (global, pas par Analyse)
        max_entities       — limite d'Entités (None = illimité pour SCALE)
        stripe_price_id    — Stripe Price ID (None pour FREE ou si non configuré)
    """
    return [
        {
            "id":                 plan_id,
            "name":               PLAN_DISPLAY_NAMES[plan_id].name,
            "label":              PLAN_DISPLAY_NAMES[plan_id].label,
            "price_cents":        PLAN_PRICES[plan_id],
            "analyses_per_month": PLAN_LIMITS[plan_id].analyses,
            "chat_per_month":     PLAN_LIMITS[plan_id].chat_monthly_cap,
            "max_entities":       PLAN_LIMITS[plan_id].max_entities,
            "stripe_price_id":    STRIPE_PRICE_IDS.get(plan_id),
        }
        for plan_id in COMMERCIAL_PLAN_IDS
    ]


def get_executive_capacity_pack(pack_id: str) -> ExecutiveCapacityPack:
    """
    Retourne l'ExecutiveCapacityPack pour un identifiant donné.

    Lève KeyError pour tout identifiant inconnu.

    Paramètres
    ----------
    pack_id : str
        Identifiant interne du pack (ex : "addon_growth").

    Retourne
    --------
    ExecutiveCapacityPack avec pack_id, display_name, analyses_added,
    price_cents, stripe_price_id_env et la property stripe_price_id.

    Lève
    ----
    KeyError si pack_id est inconnu.

    Exemple
    -------
    >>> p = get_executive_capacity_pack("addon_growth")
    >>> p.display_name
    'Growth Capacity Pack'
    >>> p.analyses_added
    20
    """
    if pack_id not in EXECUTIVE_CAPACITY_PACKS:
        raise KeyError(
            f"Executive Capacity Pack inconnu : '{pack_id}'. "
            f"Packs valides : {EXECUTIVE_CAPACITY_PACK_IDS}"
        )
    return EXECUTIVE_CAPACITY_PACKS[pack_id]


def validate_stripe_price_ids() -> Dict[str, bool]:
    """
    Vérifie que tous les Stripe Price IDs requis sont configurés.

    À appeler avant un checkout ou au démarrage du service billing.
    Ne loggue jamais les valeurs des Price IDs.

    Retourne
    --------
    Dict[str, bool]
        {product_id: is_configured} pour chaque produit payant.
        True si le Price ID est présent dans l'environnement, False sinon.

    Exemple
    -------
    >>> result = validate_stripe_price_ids()
    >>> all(result.values())   # True si tous les Price IDs sont configurés
    >>> result["pro"]          # True si STRIPE_PRICE_PRO est défini
    """
    payable = {
        "pro":           "STRIPE_PRICE_PRO",
        "scale":         "STRIPE_PRICE_SCALE",
        "addon_starter": "STRIPE_PRICE_ADDON_STARTER",
        "addon_growth":  "STRIPE_PRICE_ADDON_GROWTH",
        "addon_scale":   "STRIPE_PRICE_ADDON_SCALE",
    }
    return {
        product_id: bool(os.environ.get(env_var))
        for product_id, env_var in payable.items()
    }
