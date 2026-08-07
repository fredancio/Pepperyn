"""
test_entities_router_engagement.py — T2A : intégration routers/entities.py
avec la création atomique Entity+Engagement (ADR-002).

Aucun fichier de test n'existait pour ce routeur avant T2A — ce fichier ne
couvre donc que le périmètre de ce PR (le point d'intégration avec
EngagementService), pas l'ensemble du routeur (résolution d'auth, gating
de plan, etc., inchangés et hors périmètre).

Les fonctions de routeur FastAPI sont de simples coroutines : elles sont
appelées directement ici (asyncio.run), sans TestClient/serveur HTTP —
cohérent avec le reste de la suite, qui teste toujours au niveau fonction
plutôt qu'au niveau HTTP.
"""
import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi import HTTPException

from routers.entities import create_entity, CreateEntityRequest


def make_supabase_mock(workspace_id="ws-1", rpc_response_data=None):
    """
    Mock chainable pour les deux appels que fait create_entity() :
      1. supabase.from_("workspaces").select(...).eq(...).eq(...).limit(...).execute()
      2. (via EngagementService) supabase.rpc("create_entity_with_engagement", ...).execute()
    """
    sb = MagicMock()
    for method in ("select", "eq", "limit"):
        getattr(sb.from_.return_value, method).return_value = sb.from_.return_value
    sb.from_.return_value.execute.return_value = MagicMock(data=[{"id": workspace_id}])

    sb.rpc.return_value.execute.return_value = MagicMock(
        data=rpc_response_data if rpc_response_data is not None else [{"id": "entity-1", "name": "Acme"}]
    )
    return sb


def _resolve_company_patch(company_id="company-1", plan="pro"):
    return patch(
        "routers.entities._resolve_company",
        new=AsyncMock(return_value=(company_id, plan)),
    )


class TestCreateEntityEngagementIntegration:

    def test_nominal_creates_entity_via_engagement_service_rpc(self):
        sb = make_supabase_mock(rpc_response_data=[{"id": "entity-1", "name": "Acme"}])
        body = CreateEntityRequest(name="Acme", relation_type="client")

        with _resolve_company_patch(), patch("main.get_supabase_service", return_value=sb):
            result = asyncio.run(create_entity(body, authorization="Bearer token"))

        assert result == {"success": True, "data": {"id": "entity-1", "name": "Acme"}}

        sb.rpc.assert_called_once()
        rpc_name, rpc_params = sb.rpc.call_args[0]
        assert rpc_name == "create_entity_with_engagement"
        assert rpc_params == {
            "p_workspace_id": "ws-1",
            "p_company_id": "company-1",
            "p_name": "Acme",
            "p_industry": None,
            "p_business_model": None,
            "p_relation_type": "client",
        }

    def test_no_direct_insert_on_entities_table_anymore(self):
        """
        Répond à l'amendement PR-T2A : le chemin applicatif ne fait plus
        JAMAIS d'insert direct sur `entities` — toute création passe par la
        RPC atomique create_entity_with_engagement() (v19).
        """
        sb = make_supabase_mock()
        body = CreateEntityRequest(name="Acme")

        with _resolve_company_patch(), patch("main.get_supabase_service", return_value=sb):
            asyncio.run(create_entity(body, authorization="Bearer token"))

        insert_calls_on_entities = [
            call for call in sb.from_.return_value.insert.call_args_list
        ]
        assert insert_calls_on_entities == []
        # Seule table lue via .from_() : workspaces (résolution du workspace
        # par défaut). L'écriture de l'Entity passe exclusivement par .rpc().
        from_calls = [call.args[0] for call in sb.from_.call_args_list]
        assert "entities" not in from_calls
        assert "workspaces" in from_calls

    def test_rpc_failure_raises_http_500_no_partial_entity_created(self):
        """
        Cas d'échec (T2A_Implementation_Plan.md §8) : l'endpoint renvoie une
        erreur explicite, pas un succès partiel. Aucun appel séparé à un
        insert entities n'est fait — la seule tentative d'écriture est la
        RPC elle-même, atomique par construction (v19).
        """
        sb = make_supabase_mock()
        sb.rpc.return_value.execute.side_effect = RuntimeError("DB indisponible")
        body = CreateEntityRequest(name="Acme")

        with _resolve_company_patch(), patch("main.get_supabase_service", return_value=sb):
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(create_entity(body, authorization="Bearer token"))

        assert exc_info.value.status_code == 500
        assert sb.from_.return_value.insert.call_args_list == []


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
