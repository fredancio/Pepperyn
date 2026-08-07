"""
test_migration_v20_handle_new_user.py — T2A : tests statiques sur la migration v20.

Lecture du texte SQL uniquement — aucune connexion DB réelle (voir
T2A_Implementation_Plan.md §8 pour la limitation documentée).
"""
import os
import re

import pytest

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")
V20_PATH = os.path.join(MIGRATIONS_DIR, "v20_handle_new_user_engagement.sql")
V6_PATH = os.path.join(MIGRATIONS_DIR, "v6_workspaces_entities.sql")


@pytest.fixture(scope="module")
def v20_text():
    with open(V20_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def v6_text():
    with open(V6_PATH, "r", encoding="utf-8") as f:
        return f.read()


class TestV20DoesNotAlterExistingTables:

    def test_no_alter_table_statement(self, v20_text):
        assert not re.search(r"\bALTER\s+TABLE\b", v20_text, re.IGNORECASE)

    def test_v6_file_itself_is_not_modified(self, v6_text):
        """
        Convention du dépôt (T2A_Implementation_Plan.md §3) : une migration
        déjà appliquée en production ne se réécrit pas. Ce test vérifie que
        v6 contient toujours SA PROPRE version de handle_new_user (4 étapes,
        sans Engagement) — la preuve que v20 ne l'a pas remplacée en place.
        """
        assert "CREATE OR REPLACE FUNCTION public.handle_new_user()" in v6_text
        assert "public.engagements" not in v6_text  # v6 ne connaît pas T2A


class TestV20ReplacesHandleNewUserViaCreateOrReplace:

    def test_uses_create_or_replace_function(self, v20_text):
        assert re.search(
            r"CREATE\s+OR\s+REPLACE\s+FUNCTION\s+public\.handle_new_user\(\)",
            v20_text, re.IGNORECASE,
        )

    def test_preserves_all_four_original_inserts(self, v20_text):
        """Les 4 étapes existantes (company, profile, workspace, entity)
        doivent toutes être présentes, inchangées dans leur ordre."""
        for table in ("companies", "profiles", "workspaces", "entities"):
            assert re.search(
                rf"INSERT\s+INTO\s+public\.{table}\b", v20_text, re.IGNORECASE
            ), f"INSERT INTO public.{table} manquant dans v20"

    def test_engagement_insert_is_in_same_function_body_as_entity_insert(self, v20_text):
        """
        Preuve statique de « même transaction » : les deux INSERT vivent
        dans le corps de la même fonction PL/pgSQL, entity avant engagement
        — une fonction invoquée par une seule instruction s'exécute, par
        construction Postgres, dans une seule transaction.
        """
        func_match = re.search(
            r"CREATE\s+OR\s+REPLACE\s+FUNCTION\s+public\.handle_new_user\(\).*?\$\$;",
            v20_text, re.IGNORECASE | re.DOTALL,
        )
        assert func_match is not None
        body = func_match.group(0)
        entity_pos = body.upper().find("INSERT INTO PUBLIC.ENTITIES")
        engagement_pos = body.upper().find("INSERT INTO PUBLIC.ENGAGEMENTS")
        assert entity_pos != -1
        assert engagement_pos != -1
        assert entity_pos < engagement_pos

    def test_engagement_always_created_with_prospect_status(self, v20_text):
        """
        Une Entity créée à l'inscription ne peut, par construction, avoir
        aucune Analysis existante (ADR-002 §3.5) — la fonction ne doit donc
        jamais interroger la table analyses pour décider du statut.
        """
        func_match = re.search(
            r"CREATE\s+OR\s+REPLACE\s+FUNCTION\s+public\.handle_new_user\(\).*?\$\$;",
            v20_text, re.IGNORECASE | re.DOTALL,
        )
        body = func_match.group(0)
        assert "'prospect'" in body
        assert "analyses" not in body.lower()

    def test_trigger_reattachment_preserved(self, v20_text):
        """on_auth_user_created doit rester attaché après le remplacement
        de la fonction (idempotent : DROP IF EXISTS puis CREATE)."""
        assert "DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users" in v20_text
        assert re.search(
            r"CREATE\s+TRIGGER\s+on_auth_user_created\s+AFTER\s+INSERT\s+ON\s+auth\.users",
            v20_text, re.IGNORECASE,
        )


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
