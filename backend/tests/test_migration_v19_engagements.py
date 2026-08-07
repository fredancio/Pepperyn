"""
test_migration_v19_engagements.py — T2A : tests statiques sur les migrations SQL.

Ces tests lisent le TEXTE des fichiers de migration — aucune connexion
DB réelle (Supabase est en pause). Ils ne prouvent donc pas le comportement
d'exécution (voir T2A_Implementation_Plan.md §8, limitation documentée), mais
vérifient des propriétés structurelles fiables :
  - qu'aucune table existante n'est altérée (ADR-002, mandat de PR-T2A) ;
  - la présence des contraintes attendues sur la nouvelle table ;
  - l'absence de tout trigger générique AFTER INSERT sur `entities`, dans
    TOUTES les migrations du dépôt — pas seulement v19/v20 — pour protéger
    contre une régression future vers le mécanisme révoqué (amendement
    PR-T2A, comparaison d'architecture trigger générique vs EngagementService).
"""
import os
import re
import glob

import pytest

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")
V19_PATH = os.path.join(MIGRATIONS_DIR, "v19_engagements.sql")

EXISTING_TABLES_MUST_NOT_BE_ALTERED = [
    "entities", "analyses", "evidence_ledger_entries",
    "decision_arcs", "companies", "workspaces",
]


def _strip_sql_comments(text: str) -> str:
    """Retire les lignes de commentaire SQL ('-- ...') avant toute recherche
    de motif — évite les faux positifs quand un commentaire mentionne, en
    prose, un mot-clé SQL qu'il explique justement ne pas utiliser (ex. :
    'aucun ALTER TABLE, aucun UPDATE')."""
    return "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("--")
    )


@pytest.fixture(scope="module")
def v19_text():
    with open(V19_PATH, "r", encoding="utf-8") as f:
        return _strip_sql_comments(f.read())


@pytest.fixture(scope="module")
def v19_raw_text():
    """Texte non filtré — utilisé quand un test a besoin de lire aussi les
    commentaires (aucun cas dans ce fichier à ce jour, gardé pour parité
    avec test_migration_v20_handle_new_user.py)."""
    with open(V19_PATH, "r", encoding="utf-8") as f:
        return f.read()


class TestV19NoExistingTableAltered:

    def test_no_alter_table_statement_at_all(self, v19_text):
        assert not re.search(r"\bALTER\s+TABLE\b", v19_text, re.IGNORECASE)

    def test_no_update_statement_at_all(self, v19_text):
        # UPDATE apparaîtrait ici s'il existait un backfill/rewrite caché.
        assert not re.search(r"\bUPDATE\s+public\.", v19_text, re.IGNORECASE)

    @pytest.mark.parametrize("table", EXISTING_TABLES_MUST_NOT_BE_ALTERED)
    def test_existing_table_name_not_altered_or_dropped(self, v19_text, table):
        assert not re.search(rf"\bALTER\s+TABLE\s+public\.{table}\b", v19_text, re.IGNORECASE)
        assert not re.search(rf"\bDROP\s+TABLE\s+public\.{table}\b", v19_text, re.IGNORECASE)


class TestV19SchemaConstraints:

    def test_creates_engagements_table(self, v19_text):
        assert re.search(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+public\.engagements",
                          v19_text, re.IGNORECASE)

    def test_entity_id_is_not_null_and_unique(self, v19_text):
        assert re.search(r"entity_id\s+UUID\s+NOT\s+NULL\s+UNIQUE", v19_text)

    def test_status_check_constraint_present(self, v19_text):
        assert re.search(
            r"CHECK\s*\(\s*status\s+IN\s*\(\s*'prospect'\s*,\s*'active'\s*,\s*'paused'\s*,\s*'at_risk'\s*,\s*'churned'\s*\)\s*\)",
            v19_text,
        )

    def test_no_company_id_column_on_engagements(self, v19_text):
        """ADR-002 §3.2/§3.12 (amendé) : pas de dénormalisation de company_id."""
        # Isole le CREATE TABLE engagements (jusqu'à la parenthèse fermante du
        # bloc), pour ne pas se laisser tromper par 'company_id' ailleurs
        # dans le fichier (ex. paramètre de la RPC).
        table_block_match = re.search(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+public\.engagements\s*\((.*?)\);",
            v19_text, re.IGNORECASE | re.DOTALL,
        )
        assert table_block_match is not None
        assert "company_id" not in table_block_match.group(1)

    def test_no_scope_column_on_engagements(self, v19_text):
        """ADR-002 (note de revue n°4) : entity_id porte déjà le scope en T2."""
        table_block_match = re.search(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+public\.engagements\s*\((.*?)\);",
            v19_text, re.IGNORECASE | re.DOTALL,
        )
        assert table_block_match is not None
        assert not re.search(r"\bscope\b", table_block_match.group(1), re.IGNORECASE)


class TestV19CreateEntityWithEngagementRpc:

    def test_rpc_function_created(self, v19_text):
        assert re.search(
            r"CREATE\s+OR\s+REPLACE\s+FUNCTION\s+public\.create_entity_with_engagement",
            v19_text, re.IGNORECASE,
        )

    def test_rpc_inserts_entity_then_engagement_in_same_function_body(self, v19_text):
        func_match = re.search(
            r"CREATE\s+OR\s+REPLACE\s+FUNCTION\s+public\.create_entity_with_engagement.*?\$\$;",
            v19_text, re.IGNORECASE | re.DOTALL,
        )
        assert func_match is not None
        body = func_match.group(0)
        entity_insert_pos = body.upper().find("INSERT INTO PUBLIC.ENTITIES")
        engagement_insert_pos = body.upper().find("INSERT INTO PUBLIC.ENGAGEMENTS")
        assert entity_insert_pos != -1
        assert engagement_insert_pos != -1
        # Même transaction Postgres : les deux inserts sont dans le corps
        # d'une seule fonction, entity avant engagement.
        assert entity_insert_pos < engagement_insert_pos

    def test_rpc_always_inserts_prospect_status(self, v19_text):
        """Aucune Entity nouvellement créée ne peut avoir d'Analysis
        existante — la RPC ne doit jamais interroger `analyses`."""
        func_match = re.search(
            r"CREATE\s+OR\s+REPLACE\s+FUNCTION\s+public\.create_entity_with_engagement.*?\$\$;",
            v19_text, re.IGNORECASE | re.DOTALL,
        )
        body = func_match.group(0)
        assert "'prospect'" in body
        assert "analyses" not in body.lower()


class TestNoGenericTriggerOnEntitiesAcrossAllMigrations:
    """
    Amendement PR-T2A : le trigger générique `AFTER INSERT ON entities`
    envisagé en v1 du plan est révoqué. Ce test scanne TOUTES les
    migrations (pas seulement v19/v20) pour empêcher toute régression
    future vers ce mécanisme.
    """

    @staticmethod
    @pytest.fixture(scope="class")
    def all_migration_texts():
        texts = {}
        for path in glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")):
            with open(path, "r", encoding="utf-8") as f:
                texts[os.path.basename(path)] = f.read()
        return texts

    def test_no_after_insert_trigger_on_entities_anywhere(self, all_migration_texts):
        pattern = re.compile(
            r"CREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER\s+\S+\s+AFTER\s+INSERT\s+ON\s+public\.entities",
            re.IGNORECASE,
        )
        offending = {
            filename: text for filename, text in all_migration_texts.items()
            if pattern.search(text)
        }
        assert offending == {}, (
            f"Trigger générique AFTER INSERT ON entities détecté dans : "
            f"{list(offending.keys())} — mécanisme explicitement révoqué "
            f"(voir T2A_Implementation_Plan.md, historique des révisions)."
        )

    def test_existing_updated_at_trigger_on_entities_is_before_update_only(self, all_migration_texts):
        """Le seul trigger existant sur entities (update_entities_updated_at,
        v6) doit rester BEFORE UPDATE — sans rapport avec la création."""
        v6_text = all_migration_texts.get("v6_workspaces_entities.sql", "")
        assert re.search(
            r"CREATE\s+OR\s+REPLACE\s+TRIGGER\s+update_entities_updated_at\s+BEFORE\s+UPDATE\s+ON\s+public\.entities",
            v6_text, re.IGNORECASE,
        )


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
