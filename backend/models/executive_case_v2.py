"""
executive_case_v2.py — Contrat de données officiel Pepperyn V2
Conversation Engine Edition.

Source de vérité pour :
  - le Conversation Engine (chat)
  - les futurs renderers V2 (PDF, Board Deck, Excel — pas encore branchés)

RÈGLES ABSOLUES :
  1. Ce modèle coexiste avec executive_case.py (V1) — il ne le remplace pas encore.
  2. Le pipeline export (PDF/PPTX/Excel) continue d'utiliser ExecutiveCaseJSON (V1).
  3. Seul le Conversation Engine lit ce modèle.
  4. cost_of_inaction, value_at_risk et value_creation_opportunity sont en valeur POSITIVE.
  5. sacred_sentence est immuable.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator


class ConversationEngine(BaseModel):
    auto_opening_message: str
    suggested_quick_prompts: List[str] = Field(min_length=4, max_length=6)
    plain_language_context: dict
    role_modes: dict
    financial_glossary: list
    sacred_sentence: Literal["Aucune question n'est trop simple."]


class ExecutiveCase(BaseModel):
    metadata: dict
    data_quality: dict
    executive_summary: dict
    health_score: dict
    financial_performance: dict
    financial_snapshot: dict
    value_drivers: dict
    priority_decisions: list
    roadmap: dict
    conversation_engine: ConversationEngine
    methodology: dict

    @model_validator(mode="after")
    def enforce_product_safety(self):
        fp = self.financial_performance
        assert fp["cost_of_inaction"]["annual"] >= 0, "cost_of_inaction cannot be negative"
        assert fp["value_at_risk"]["annual"] >= 0, "value_at_risk cannot be negative"
        assert fp["value_creation_opportunity"]["annual"] >= 0, "value_creation_opportunity cannot be negative"
        return self
