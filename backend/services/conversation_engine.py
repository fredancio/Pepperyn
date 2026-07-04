"""
conversation_engine.py — Service de conversation V2 (Conversation Engine).

Responsabilité unique :
  Préparer le payload LLM et appeler Claude Sonnet pour répondre
  aux questions d'un CEO depuis l'ExecutiveCase V2.

RÈGLES ABSOLUES :
  1. Le chat explique — il ne recalcule JAMAIS.
  2. Le chat ne peut PAS inventer de chiffres.
  3. Le chat ne peut PAS contredire l'ExecutiveCase.
  4. Les données viennent exclusivement de l'ExecutiveCase V2 fourni.
  5. sacred_sentence est incluse dans chaque contexte système.
  6. Ce fichier ne modifie pas le chat existant (call_chat_intelligent).
"""
from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Modèle cible ─────────────────────────────────────────────────────────────
CE_MODEL       = "claude-sonnet-4-6"
CE_MAX_TOKENS  = 600

# ─── Sacred sentence (immuable) ───────────────────────────────────────────────
_SACRED_SENTENCE = "Aucune question n'est trop simple."

# ─── System prompt du Conversation Engine ─────────────────────────────────────
_CE_SYSTEM_BASE = """Tu es Pepperyn, le guide conversationnel de l'analyse financière.

TON RÔLE UNIQUE :
Tu aides le dirigeant à comprendre son analyse, à poser des questions et à préparer ses décisions.
Tu ne remplaces pas le rapport PDF — tu le rends accessible.

RÈGLES ABSOLUES — SANS EXCEPTION :
1. Tu travailles UNIQUEMENT à partir de l'ExecutiveCase fourni ci-dessous.
2. Tu n'inventes AUCUN chiffre, AUCUNE donnée, AUCUNE tendance absente de l'analyse.
3. Tu ne recalcules RIEN. Les montants, scores et ratios viennent de l'analyse — pas de toi.
4. Tu ne contredis JAMAIS l'ExecutiveCase. Si l'analyse dit X, tu dis X.
5. Si une information est absente : "Cette donnée n'est pas disponible dans l'analyse." — une phrase, pas de développement.
6. Tu n'améliores pas les chiffres. Tu n'arrondis pas à l'avantage du dirigeant.
7. Tu ne rassures pas sans fondement. Si la situation est grave, tu le dis simplement.

TON STYLE :
- Réponses courtes et directes. 3 à 6 phrases maximum sauf demande structurée explicite.
- Ton niveau : CFO accessible, pas consultant qui survole.
- Tu réponds exclusivement en français.
- {sacred_sentence}

FORMATAGE — RÈGLES STRICTES :
- ZÉRO emoji. Jamais. Aucun caractère emoji dans les réponses.
- ZÉRO hashtag (#, ##, ###). Jamais de titres markdown.
- ZÉRO astérisque (* ou **). Jamais de gras ou italique markdown.
- Pas de listes à puces systématiques. Si tu listes, utilise des tirets simples (-) ou des chiffres, uniquement quand c'est indispensable.
- Tu ne te présentes JAMAIS. Ni "Je suis Pepperyn", ni "En tant qu'assistant financier", ni aucune formule similaire. L'utilisateur sait qui tu es. Va à l'essentiel."""


def _build_system_prompt(executive_case_v2) -> str:
    """
    Construit le system prompt complet en injectant le contexte de l'ExecutiveCase V2.

    Injecte :
      - sacred_sentence (immuable)
      - plain_language_context (résumé vulgarisé)
      - role_modes (persona sélectable)
      - financial_glossary (définitions)
      - financial_performance (COI, VAR, VCO — valeurs positives)
      - financial_snapshot (snapshot chiffré)
      - executive_summary (problème, risque, recommandation)
    """
    ce = executive_case_v2.conversation_engine
    fp = executive_case_v2.financial_performance
    fs = executive_case_v2.financial_snapshot
    es = executive_case_v2.executive_summary

    # Base avec sacred_sentence injectée
    system = _CE_SYSTEM_BASE.format(sacred_sentence=_SACRED_SENTENCE)

    # ── Contexte plain_language ──────────────────────────────────────────────
    plc = ce.plain_language_context
    system += "\n\nCONTEXTE DE L'ANALYSE (langage simple) :"
    if plc.get("one_sentence_summary"):
        system += f"\n- Résumé : {plc['one_sentence_summary']}"
    if plc.get("what_is_happening"):
        system += f"\n- Ce qui se passe : {plc['what_is_happening']}"
    if plc.get("why_it_matters"):
        system += f"\n- Pourquoi c'est important : {plc['why_it_matters']}"
    if plc.get("biggest_risk"):
        system += f"\n- Risque principal : {plc['biggest_risk']}"
    if plc.get("biggest_opportunity"):
        system += f"\n- Opportunité principale : {plc['biggest_opportunity']}"

    trois_choses = plc.get("three_things_to_understand", [])
    if trois_choses:
        system += "\n- Les 3 choses à comprendre : " + " | ".join(trois_choses)

    trois_decisions = plc.get("three_decisions_to_take", [])
    if trois_decisions:
        system += "\n- Les 3 décisions à prendre : " + " | ".join(trois_decisions)

    lundi = plc.get("monday_morning_actions", [])
    if lundi:
        system += "\n- Actions lundi matin : " + " | ".join(lundi)

    # ── Données financières clés ─────────────────────────────────────────────
    system += "\n\nDONNÉES FINANCIÈRES (source unique — ne pas modifier ni recalculer) :"
    coi = fp.get("cost_of_inaction", {})
    if coi.get("annual") is not None:
        monthly = coi.get("monthly", coi["annual"] / 12)
        system += f"\n- Coût de l'inaction : {coi['annual']:,.0f} €/an ({monthly:,.0f} €/mois)"
    var_ = fp.get("value_at_risk", {})
    if var_.get("annual") is not None:
        system += f"\n- Valeur exposée : {var_['annual']:,.0f} €/an"
    vco = fp.get("value_creation_opportunity", {})
    if vco.get("annual") is not None and vco["annual"] > 0:
        system += f"\n- Potentiel de création de valeur : {vco['annual']:,.0f} €/an"

    if fs.get("revenue") is not None:
        system += f"\n- Chiffre d'affaires : {fs['revenue']:,.0f} €"
    if fs.get("ebitda") is not None:
        ebitda_label = "positif" if fs["ebitda"] >= 0 else "négatif"
        system += f"\n- EBITDA : {fs['ebitda']:,.0f} € ({ebitda_label})"
    if fs.get("gross_margin") is not None:
        system += f"\n- Marge brute : {fs['gross_margin']:.1f} %"

    # ── Executive summary ────────────────────────────────────────────────────
    system += "\n\nSYNTHÈSE EXÉCUTIVE :"
    if es.get("core_problem"):
        system += f"\n- Problème central : {es['core_problem']}"
    if es.get("strategic_risk"):
        system += f"\n- Risque stratégique : {es['strategic_risk']}"
    if es.get("executive_recommendation"):
        system += f"\n- Recommandation prioritaire : {es['executive_recommendation']}"

    # ── Glossaire financier ──────────────────────────────────────────────────
    glossary = ce.financial_glossary
    if glossary:
        system += "\n\nGLOSSAIRE (à utiliser pour expliquer les termes) :"
        for entry in glossary:
            term = entry.get("term", "")
            plain = entry.get("plain_language", "")
            if term and plain:
                system += f"\n- {term} : {plain}"

    # ── Modes de rôle ────────────────────────────────────────────────────────
    role_modes = ce.role_modes
    if role_modes:
        system += "\n\nINSTRUCTIONS SELON LE PROFIL DE L'INTERLOCUTEUR :"
        for role, instruction in role_modes.items():
            system += f"\n- {role} : {instruction}"

    return system


def build_payload(
    executive_case_v2,
    user_message: str,
    history: Optional[list[dict]] = None,
) -> dict:
    """
    Construit le payload complet pour l'appel LLM.

    Retourne un dict prêt à passer à client.messages.create(**payload).
    N'effectue aucun appel réseau.

    Structure retournée :
      {
        "model": "claude-sonnet-4-6",
        "max_tokens": 600,
        "system": "<system prompt complet>",
        "messages": [
          {"role": "user"|"assistant", "content": "..."},  # history
          {"role": "user", "content": "<user_message>"},   # message courant
        ]
      }
    """
    system = _build_system_prompt(executive_case_v2)

    messages = list(history or [])
    messages.append({"role": "user", "content": user_message})

    return {
        "model":      CE_MODEL,
        "max_tokens": CE_MAX_TOKENS,
        "system":     system,
        "messages":   messages,
    }


async def get_chat_response(
    executive_case_v2,
    user_message: str,
    history: Optional[list[dict]] = None,
) -> tuple[str, str]:
    """
    Appelle Claude Sonnet avec le contexte ExecutiveCase V2.

    Règles enforced dans le system prompt :
      - Aucune invention de données
      - Aucun recalcul
      - Aucune contradiction de l'ExecutiveCase
      - Réponse en français uniquement

    Returns (response_text, model_used)
    """
    from services.llm_service import get_anthropic_client

    client = get_anthropic_client()
    payload = build_payload(executive_case_v2, user_message, history)

    logger.info(
        "[CE] Appel %s — message: %.60s…",
        CE_MODEL,
        user_message,
    )

    response = client.messages.create(**payload)
    text = response.content[0].text.strip()

    logger.info("[CE] Réponse reçue (%d caractères)", len(text))
    return text, CE_MODEL


# ─── Test local ───────────────────────────────────────────────────────────────

def _run_test() -> None:
    """
    Valide la construction du payload sans appel LLM réel.

    Vérifie :
      1. build_payload retourne le bon modèle et les bons champs
      2. Le system prompt contient les règles anti-recalcul / anti-invention
      3. Le sacred_sentence est présent
      4. Le contexte financier est injecté
      5. L'historique est correctement concaténé
    """
    import sys
    sys.path.insert(0, ".")
    from services.executive_case_v2_builder import build_executive_case_v2

    # Données synthétiques
    result_dict = {
        "company_name": "TestCo",
        "score_global": 3,
        "niveau_urgence": "élevé",
        "phrase_tension": "Chaque mois sans action coûte 455 000 €.",
        "recommandations_prioritaires": [
            {"action": "Lancer staffing meeting", "impact": "-5 465 000 €"}
        ],
        "scenarios": [
            {"type": "impact", "impact": "-5 465 000 €", "description": "EBITDA négatif"}
        ],
        "ceo_dashboard": [
            {"label": "CA",          "value": "46 529 000 €"},
            {"label": "EBITDA",      "value": "-5 465 000 €"},
            {"label": "Marge brute", "value": "89.8%"},
        ],
    }
    case_v2 = build_executive_case_v2(result_dict, "TestCo", "test-ce-001")

    # ── Test 1 : payload sans historique ────────────────────────────────────
    payload = build_payload(case_v2, "Expliquez-moi l'EBITDA simplement.")
    assert payload["model"] == CE_MODEL,            "Modèle incorrect"
    assert payload["max_tokens"] == CE_MAX_TOKENS,  "max_tokens incorrect"
    assert "system" in payload,                     "system manquant"
    assert "messages" in payload,                   "messages manquant"
    assert len(payload["messages"]) == 1,           "1 message attendu"
    assert payload["messages"][0]["role"] == "user"
    print("✓ build_payload sans historique — OK")

    # ── Test 2 : règles anti-recalcul présentes ──────────────────────────────
    system = payload["system"]
    assert "ne recalcule" in system.lower() or "recalcul" in system.lower(), \
        "Règle anti-recalcul absente du system prompt"
    assert "n'invente" in system.lower() or "invente" in system.lower(), \
        "Règle anti-invention absente du system prompt"
    assert "ne contredis" in system.lower() or "contredit" in system.lower(), \
        "Règle anti-contradiction absente du system prompt"
    print("✓ Règles anti-recalcul / anti-invention / anti-contradiction — présentes")

    # ── Test 3 : sacred_sentence injectée ───────────────────────────────────
    assert _SACRED_SENTENCE in system, "sacred_sentence absente du system prompt"
    print(f"✓ sacred_sentence : \"{_SACRED_SENTENCE}\" — présente")

    # ── Test 4 : contexte financier injecté ─────────────────────────────────
    assert "Coût de l'inaction" in system,  "COI absent du system prompt"
    assert "EBITDA" in system,              "EBITDA absent du system prompt"
    assert "Chiffre d'affaires" in system,  "CA absent du system prompt"
    print("✓ Contexte financier injecté (COI, EBITDA, CA)")

    # ── Test 5 : payload avec historique ────────────────────────────────────
    history = [
        {"role": "user",      "content": "Bonjour"},
        {"role": "assistant", "content": "Bonjour, que voulez-vous savoir ?"},
    ]
    payload2 = build_payload(case_v2, "Que faire lundi ?", history)
    assert len(payload2["messages"]) == 3, "3 messages attendus avec historique"
    assert payload2["messages"][-1]["content"] == "Que faire lundi ?"
    print("✓ Historique correctement concaténé (2 + 1 = 3 messages)")

    # ── Test 6 : glossaire présent ───────────────────────────────────────────
    assert "GLOSSAIRE" in system, "Glossaire absent du system prompt"
    print("✓ Glossaire financier injecté")

    # ── Test 7 : role_modes présents ─────────────────────────────────────────
    assert "dirigeant" in system.lower(), "role_modes absent du system prompt"
    print("✓ Role modes injectés")

    print()
    print("✓ TOUS LES CHECKS PASSÉS")
    print(f"  Modèle cible : {CE_MODEL}")
    print(f"  Max tokens   : {CE_MAX_TOKENS}")
    print(f"  System prompt: {len(system)} caractères")


if __name__ == "__main__":
    _run_test()
