from __future__ import annotations
from fastmcp import FastMCP
from .config import settings
from .data_loader import FinanceDataStore
from .finance_engine import FinanceEngine
from .codir_responder import CodirResponder

mcp = FastMCP("pepperyn-codir-finance")


def engine() -> FinanceEngine:
    return FinanceEngine(FinanceDataStore(settings.excel_path))

@mcp.tool
def get_pnl(period: str) -> dict:
    """Retourne le P&L mensuel: CA, coûts variables, marge brute, coûts fixes, EBITDA."""
    return engine().monthly_pnl(period)

@mcp.tool
def get_revenue(period: str) -> dict:
    """Retourne le chiffre d'affaires net d'une période."""
    e = engine()
    return {"period": period, "revenue": e.revenue(period)}

@mcp.tool
def get_revenue_breakdown(period: str, dimension: str = "customer") -> list[dict]:
    """Décompose le CA par customer, product, segment ou region."""
    return engine().revenue_breakdown(period, dimension)

@mcp.tool
def get_margin(period: str) -> dict:
    """Retourne marge brute, taux de marge brute, EBITDA et taux EBITDA."""
    e = engine()
    return {
        "period": period,
        "gross_margin": e.gross_margin(period),
        "gross_margin_rate": e.gross_margin_rate(period),
        "ebitda": e.ebitda(period),
        "ebitda_rate": e.ebitda_rate(period),
    }

@mcp.tool
def get_margin_by_dimension(period: str, dimension: str = "product") -> list[dict]:
    """Retourne la marge par produit ou par client."""
    return engine().margin_by_dimension(period, dimension)

@mcp.tool
def get_margin_variance_breakdown(period: str) -> dict:
    """Explique la variation de marge vs période précédente: prix, volume, coût, mix."""
    return engine().margin_variance_breakdown(period)

@mcp.tool
def get_costs(period: str) -> dict:
    """Retourne coûts fixes, coûts variables et total des coûts."""
    e = engine()
    fixed = e.fixed_costs(period); variable = e.variable_costs(period)
    return {"period": period, "fixed_costs": fixed, "variable_costs": variable, "total_costs": fixed + variable}

@mcp.tool
def get_cost_breakdown(period: str, dimension: str = "category") -> list[dict]:
    """Décompose les coûts par catégorie, département, fournisseur, etc."""
    return engine().cost_breakdown(period, dimension)

@mcp.tool
def get_fixed_costs_evolution(period: str) -> dict:
    """Compare les coûts fixes d'une période avec la période précédente."""
    e = engine(); prev = e.previous_period(period)
    cur = e.fixed_costs(period); old = e.fixed_costs(prev) if prev else 0
    return {"period": period, "previous_period": prev, "fixed_costs": cur, "previous_fixed_costs": old, "variation": cur - old}

@mcp.tool
def get_customer_sales_variation(period: str) -> list[dict]:
    """Liste les clients dont le CA augmente ou baisse vs période précédente."""
    return engine().customer_sales_variation(period)

@mcp.tool
def get_supplier_price_variation(period: str) -> list[dict]:
    """Liste les hausses/baisses de prix fournisseurs vs période précédente."""
    return engine().supplier_price_variation(period)

@mcp.tool
def get_cash_flow(period: str) -> dict:
    """Retourne cash-in, cash-out et cash-flow net sur une période."""
    return engine().cash_flow(period)

@mcp.tool
def get_breakeven_point(period: str) -> dict:
    """Calcule le seuil de rentabilité sur base des coûts fixes et du taux de marge."""
    return engine().breakeven_point(period)

@mcp.tool
def explain_margin_drop(period: str) -> dict:
    """Produit une réponse Codir structurée expliquant une baisse de marge."""
    e = engine()
    return CodirResponder(e).explain_margin_drop(period)

@mcp.tool
def drilldown(metric: str, period: str, dimension: str = "customer") -> dict:
    """Creuse un indicateur: revenue, margin ou costs selon une dimension."""
    e = engine()
    if metric == "revenue":
        return {"metric": metric, "period": period, "rows": e.revenue_breakdown(period, dimension)}
    if metric == "margin":
        return {"metric": metric, "period": period, "rows": e.margin_by_dimension(period, dimension)}
    if metric == "costs":
        return {"metric": metric, "period": period, "rows": e.cost_breakdown(period, dimension)}
    return {"error": "metric doit être revenue, margin ou costs"}

if __name__ == "__main__":
    mcp.run()
