from __future__ import annotations
from .finance_engine import FinanceEngine


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x*100:.1f}%"


def eur(x: float | int | None) -> str:
    return "n/a" if x is None else f"{x:,.0f} €".replace(",", " ")

class CodirResponder:
    """Réponses synthétiques prêtes pour Codir. Ce n'est pas le LLM : c'est le garde-fou métier."""
    def __init__(self, engine: FinanceEngine):
        self.engine = engine

    def explain_margin_drop(self, period: str) -> dict:
        pnl = self.engine.monthly_pnl(period)
        breakdown = self.engine.margin_variance_breakdown(period)
        suppliers = self.engine.supplier_price_variation(period)[:5]
        customers = self.engine.customer_sales_variation(period)[:5]
        warnings = []
        if "warning" in breakdown:
            warnings.append(breakdown["warning"])

        causes = []
        if breakdown.get("cost_effect", 0) < 0:
            causes.append(f"Effet coût défavorable: {eur(breakdown['cost_effect'])} sur la marge.")
        if breakdown.get("volume_effect", 0) < 0:
            causes.append(f"Effet volume défavorable: {eur(breakdown['volume_effect'])}.")
        if breakdown.get("mix_effect", 0) < 0:
            causes.append(f"Effet mix défavorable estimé: {eur(breakdown['mix_effect'])}.")
        if breakdown.get("price_effect", 0) < 0:
            causes.append(f"Effet prix défavorable: {eur(breakdown['price_effect'])}.")

        supplier_lines = [
            f"{s.get('supplier_name', s.get('supplier_id'))}: impact coût estimé {eur(s.get('cost_impact'))}"
            for s in suppliers if s.get("cost_impact", 0) > 0
        ]
        customer_lines = [
            f"{c.get('customer_name', c.get('customer_id'))}: variation CA {eur(c.get('variation'))}"
            for c in customers if c.get("variation", 0) < 0
        ]

        answer = (
            f"Pour {period}, le CA est de {eur(pnl['revenue'])}, la marge brute de {eur(pnl['gross_margin'])} "
            f"et le taux de marge brute de {pct(pnl['gross_margin_rate'])}. "
            f"L'écart de marge vs période précédente est de {eur(breakdown.get('margin_variance'))}."
        )

        return {
            "question": "Pourquoi la marge baisse ?",
            "period": period,
            "answer": answer,
            "key_numbers": {**pnl, **breakdown},
            "causes": causes + supplier_lines + customer_lines,
            "recommended_actions": [
                "Valider les hausses fournisseurs qui pèsent le plus sur la marge.",
                "Identifier les clients à forte marge dont le CA baisse et préparer une action commerciale ciblée.",
                "Revoir les remises ou prix de vente sur les produits à marge dégradée.",
            ],
            "warnings": warnings,
        }
