"""
engagement_service.py — T2A : persistance de l'agrégat Engagement (ADR-002).

Deux responsabilités distinctes, correspondant aux deux chemins réels de
création d'Entity identifiés dans T2A_Implementation_Plan.md §2 :

1. `create_for_new_entity()` — chemin applicatif (POST /api/entities,
   routers/entities.py::create_entity). Seul point d'entrée Python pour la
   création d'un Engagement en temps réel. Wrapper explicite autour de la
   RPC Postgres `create_entity_with_engagement()` (migration v19), qui
   garantit l'atomicité Entity+Engagement dans une seule transaction — le
   client Supabase applicatif (supabase-py) ne permet aucune transaction
   multi-appels (T2A_Implementation_Plan.md §5).

   Le chemin d'inscription (handle_new_user(), trigger AFTER INSERT ON
   auth.users) est amendé directement en SQL (migration v20) et ne passe
   PAS par ce module — c'est un bootstrap SQL transactionnel autonome,
   volontairement laissé tel quel (T2A_Implementation_Plan.md §3).

2. `backfill_engagements()` — backfill historique, ponctuel, pour les
   Entities déjà existantes avant T2A. Seul endroit qui applique la règle
   ADR-002 §3.5 ("active si Analysis existante, prospect sinon") : une
   Entity nouvellement créée (via 1. ou via v20) ne peut, par construction,
   avoir aucune Analysis existante — cette règle ne s'applique donc jamais
   à la création en temps réel.

Note de revue n°1 (adoption ADR-002) : le statut posé par ce module,
qu'il vienne du backfill ou d'une création en temps réel, est une
INITIALISATION DÉTERMINISTE fondée sur un signal disponible dans les
données — jamais une affirmation certifiée sur l'état commercial réel de
la relation aujourd'hui. Aucun code appelant ne doit le présenter comme
autre chose qu'un point de départ.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def create_for_new_entity(
    supabase: Any,
    workspace_id: str,
    company_id: str,
    name: str,
    industry: Optional[str] = None,
    business_model: Optional[str] = None,
    relation_type: Optional[str] = None,
) -> dict:
    """
    Crée une Entity et son Engagement associé, atomiquement, via la RPC
    create_entity_with_engagement() (migration v19, ADR-002).

    Remplace les deux appels séquentiels non atomiques qu'utilisait
    auparavant routers/entities.py::create_entity() — voir
    T2A_Implementation_Plan.md §5 pour la justification (supabase-py ne
    supporte aucune transaction applicative multi-opérations).

    Le statut de l'Engagement créé est toujours 'prospect' (posé côté SQL
    par la RPC elle-même, pas par ce wrapper) : une Entity qui vient d'être
    créée ne peut, par construction, avoir aucune Analysis existante.

    Args:
        supabase: client Supabase (service role — même client que le reste
                  de routers/entities.py).
        workspace_id, company_id, name, industry, business_model,
        relation_type: mêmes paramètres que l'ancien payload d'insert direct
                        sur `entities`.

    Returns:
        Le dict de l'Entity créée (même forme que l'ancien
        `result.data[0]`), ou {} si la RPC ne retourne aucune ligne.

    Raises:
        Toute exception levée par l'appel RPC est propagée telle quelle —
        c'est à l'appelant (le routeur) de la traduire en réponse HTTP.
        Aucune Entity orpheline n'est possible en cas d'échec : la RPC
        s'exécute dans une seule transaction Postgres (voir docstring du
        module et T2A_Implementation_Plan.md §5).
    """
    response = supabase.rpc(
        "create_entity_with_engagement",
        {
            "p_workspace_id": workspace_id,
            "p_company_id": company_id,
            "p_name": name,
            "p_industry": industry,
            "p_business_model": business_model,
            "p_relation_type": relation_type,
        },
    ).execute()

    data = response.data or []
    return data[0] if data else {}


def determine_initial_status(entity_id: str, supabase: Any) -> str:
    """
    ADR-002 §3.5 — règle de backfill historique UNIQUEMENT. Ne s'applique
    jamais à une création en temps réel (create_for_new_entity ci-dessus,
    ou handle_new_user() amendée en v20) : celles-ci posent toujours
    'prospect' directement, sans appeler cette fonction, car une Entity qui
    vient d'être créée ne peut avoir aucune Analysis existante.

    Args:
        entity_id: id de l'Entity à évaluer.
        supabase: client Supabase.

    Returns:
        'active' si au moins une Analysis existe pour cette entity
        (analyses.entity_id), 'prospect' sinon — 'prospect' est déjà le
        premier état du cycle de vie défini par le Modèle Idéal, cette
        fonction n'introduit donc aucune valeur nouvelle dans
        EngagementStatus.
    """
    result = (
        supabase.from_("analyses")
        .select("id")
        .eq("entity_id", entity_id)
        .limit(1)
        .execute()
    )
    return "active" if result.data else "prospect"


def backfill_engagements(supabase: Any) -> dict:
    """
    Backfill idempotent des Engagements pour toutes les Entities déjà
    existantes avant T2A (T2A_Implementation_Plan.md §4, répond à la note
    de revue n°2 : créer uniquement les Engagements absents, ne jamais
    dupliquer, ne jamais modifier ni recalculer un Engagement existant).

    Pour chaque Entity :
      1. vérifie l'absence d'un Engagement déjà existant pour cet entity_id
         (SELECT) ;
      2. si absent, calcule le statut via determine_initial_status() et
         insère (upsert avec ignore_duplicates=True sur entity_id — filet
         de sécurité côté DB en plus de la contrainte UNIQUE, équivalent à
         un INSERT ... ON CONFLICT (entity_id) DO NOTHING) ;
      3. si déjà présent, ne fait RIEN — aucune lecture de son statut
         actuel, aucun recalcul, aucun UPDATE nulle part dans cette
         fonction.

    Rejouer cette fonction un nombre quelconque de fois produit le même
    état final, sans effet de bord — c'est la propriété exigée par la note
    de revue n°2.

    Traitement entity par entity, sans transaction globale : une erreur
    isolée ne doit pas annuler le travail déjà fait sur les autres
    (T2A_Implementation_Plan.md §5 — approprié pour une opération
    ponctuelle, à la différence du chemin applicatif qui doit rester
    strictement atomique).

    Returns:
        dict avec les clés "created", "already_present", "errors"
        (compteurs), utilisé par le script one-off pour rapporter un
        résumé en fin d'exécution.
    """
    stats = {"created": 0, "already_present": 0, "errors": 0}

    entities_result = supabase.from_("entities").select("id").execute()
    entities = entities_result.data or []

    for entity in entities:
        entity_id = entity.get("id")
        if not entity_id:
            continue

        try:
            existing = (
                supabase.from_("engagements")
                .select("id")
                .eq("entity_id", entity_id)
                .limit(1)
                .execute()
            )
            if existing.data:
                stats["already_present"] += 1
                continue

            status = determine_initial_status(entity_id, supabase)

            (
                supabase.from_("engagements")
                .upsert(
                    {
                        "entity_id": entity_id,
                        "status": status,
                        "cadence": "mensuelle",
                    },
                    on_conflict="entity_id",
                    ignore_duplicates=True,
                )
                .execute()
            )
            stats["created"] += 1

        except Exception as e:
            logger.error(
                "[ENGAGEMENT BACKFILL ERROR] entity_id=%s | error=%s: %s",
                entity_id, type(e).__name__, e,
            )
            stats["errors"] += 1

    return stats
