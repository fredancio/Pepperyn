from __future__ import annotations
import pandas as pd
from .data_loader import FinanceDataStore

class FinanceEngine:
    """Moteur de calcul finance. L'agent IA doit utiliser ces calculs, pas improviser."""
    def __init__(self, store: FinanceDataStore):
        self.store = store

    def _period_filter(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        return df[df["period_id"].astype(str) == str(period)].copy() if "period_id" in df.columns else df.copy()

    def previous_period(self, period: str) -> str | None:
        periods = sorted(self.store.table("periods")["period_id"].astype(str).unique().tolist())
        if period not in periods:
            return None
        idx = periods.index(period)
        return periods[idx - 1] if idx > 0 else None

    def revenue(self, period: str) -> float:
        sales = self._period_filter(self.store.table("sales_invoices"), period)
        return float(sales.get("net_revenue", pd.Series(dtype=float)).sum())

    def variable_costs(self, period: str) -> float:
        purchases = self._period_filter(self.store.table("purchase_invoices"), period)
        return float(purchases.get("total_cost", pd.Series(dtype=float)).sum())

    def fixed_costs(self, period: str) -> float:
        costs = self._period_filter(self.store.table("fixed_costs"), period)
        return float(costs.get("amount", pd.Series(dtype=float)).sum())

    def gross_margin(self, period: str) -> float:
        return self.revenue(period) - self.variable_costs(period)

    def gross_margin_rate(self, period: str) -> float:
        rev = self.revenue(period)
        return self.gross_margin(period) / rev if rev else 0.0

    def ebitda(self, period: str) -> float:
        return self.gross_margin(period) - self.fixed_costs(period)

    def ebitda_rate(self, period: str) -> float:
        rev = self.revenue(period)
        return self.ebitda(period) / rev if rev else 0.0

    def breakeven_point(self, period: str) -> dict:
        rate = self.gross_margin_rate(period)
        fixed = self.fixed_costs(period)
        breakeven = fixed / rate if rate else None
        return {"fixed_costs": fixed, "contribution_margin_rate": rate, "breakeven_revenue": breakeven}

    def monthly_pnl(self, period: str) -> dict:
        rev = self.revenue(period)
        var = self.variable_costs(period)
        fixed = self.fixed_costs(period)
        gm = rev - var
        ebitda = gm - fixed
        return {
            "period": period,
            "revenue": rev,
            "variable_costs": var,
            "gross_margin": gm,
            "gross_margin_rate": gm / rev if rev else 0.0,
            "fixed_costs": fixed,
            "ebitda": ebitda,
            "ebitda_margin_rate": ebitda / rev if rev else 0.0,
        }

    def revenue_breakdown(self, period: str, dimension: str) -> list[dict]:
        sales = self._period_filter(self.store.table("sales_invoices"), period)
        if sales.empty:
            return []
        df = sales.copy()
        if dimension == "customer":
            customers = self.store.table("customers")
            df = df.merge(customers, on="customer_id", how="left")
            group_col = "customer_name"
        elif dimension == "product":
            products = self.store.table("products")
            df = df.merge(products, on="product_id", how="left")
            group_col = "product_name"
        elif dimension in ["segment", "region"]:
            customers = self.store.table("customers")
            df = df.merge(customers, on="customer_id", how="left")
            group_col = dimension
        else:
            group_col = dimension if dimension in df.columns else "customer_id"
        out = df.groupby(group_col, dropna=False)["net_revenue"].sum().reset_index()
        out = out.sort_values("net_revenue", ascending=False)
        return out.rename(columns={group_col: dimension, "net_revenue": "revenue"}).to_dict("records")

    def cost_breakdown(self, period: str, dimension: str = "category") -> list[dict]:
        fixed = self._period_filter(self.store.table("fixed_costs"), period)
        purchases = self._period_filter(self.store.table("purchase_invoices"), period)
        rows = []
        if not fixed.empty:
            group_col = dimension if dimension in fixed.columns else "category"
            f = fixed.groupby(group_col, dropna=False)["amount"].sum().reset_index()
            f["cost_type"] = "fixed"
            f = f.rename(columns={group_col: dimension, "amount": "amount"})
            rows.extend(f.to_dict("records"))
        if not purchases.empty:
            group_col = dimension if dimension in purchases.columns else "cost_type"
            p = purchases.groupby(group_col, dropna=False)["total_cost"].sum().reset_index()
            p["cost_type"] = "variable"
            p = p.rename(columns={group_col: dimension, "total_cost": "amount"})
            rows.extend(p.to_dict("records"))
        return sorted(rows, key=lambda r: r["amount"], reverse=True)

    def margin_by_dimension(self, period: str, dimension: str) -> list[dict]:
        sales = self._period_filter(self.store.table("sales_invoices"), period)
        purchases = self._period_filter(self.store.table("purchase_invoices"), period)
        if sales.empty:
            return []
        sales_group_col = "product_id" if dimension in ["product", "category"] else "customer_id"
        revenue = sales.groupby(sales_group_col)["net_revenue"].sum().reset_index()
        if sales_group_col in purchases.columns:
            costs = purchases.groupby(sales_group_col)["total_cost"].sum().reset_index()
            df = revenue.merge(costs, on=sales_group_col, how="left").fillna(0)
        else:
            df = revenue.copy(); df["total_cost"] = 0.0
        df["gross_margin"] = df["net_revenue"] - df["total_cost"]
        df["margin_rate"] = df.apply(lambda r: r["gross_margin"] / r["net_revenue"] if r["net_revenue"] else 0, axis=1)
        if dimension == "product":
            df = df.merge(self.store.table("products"), on="product_id", how="left")
            name_col = "product_name"
        else:
            df = df.merge(self.store.table("customers"), on="customer_id", how="left")
            name_col = "customer_name"
        df = df.sort_values("gross_margin", ascending=False)
        return df.rename(columns={name_col: dimension, "net_revenue": "revenue", "total_cost": "variable_costs"}).to_dict("records")

    def supplier_price_variation(self, period: str) -> list[dict]:
        prev = self.previous_period(period)
        purchases = self.store.table("purchase_invoices")
        if prev is None or purchases.empty:
            return []
        cur = self._period_filter(purchases, period)
        old = self._period_filter(purchases, prev)
        keys = ["supplier_id", "product_id"]
        cur_avg = cur.groupby(keys).agg(quantity_purchased=("quantity", "sum"), current_unit_cost=("unit_cost", "mean")).reset_index()
        old_avg = old.groupby(keys).agg(previous_unit_cost=("unit_cost", "mean")).reset_index()
        df = cur_avg.merge(old_avg, on=keys, how="left").fillna(0)
        df["unit_cost_variation"] = df["current_unit_cost"] - df["previous_unit_cost"]
        df["unit_cost_variation_pct"] = df.apply(lambda r: r["unit_cost_variation"] / r["previous_unit_cost"] if r["previous_unit_cost"] else None, axis=1)
        df["cost_impact"] = df["unit_cost_variation"] * df["quantity_purchased"]
        df = df.merge(self.store.table("suppliers"), on="supplier_id", how="left")
        df = df.merge(self.store.table("products"), on="product_id", how="left")
        return df.sort_values("cost_impact", ascending=False).to_dict("records")

    def customer_sales_variation(self, period: str) -> list[dict]:
        prev = self.previous_period(period)
        if prev is None:
            return []
        sales = self.store.table("sales_invoices")
        cur = self._period_filter(sales, period).groupby("customer_id")["net_revenue"].sum().reset_index(name="current_revenue")
        old = self._period_filter(sales, prev).groupby("customer_id")["net_revenue"].sum().reset_index(name="previous_revenue")
        df = cur.merge(old, on="customer_id", how="outer").fillna(0)
        df["variation"] = df["current_revenue"] - df["previous_revenue"]
        df["variation_pct"] = df.apply(lambda r: r["variation"] / r["previous_revenue"] if r["previous_revenue"] else None, axis=1)
        df = df.merge(self.store.table("customers"), on="customer_id", how="left")
        return df.sort_values("variation").to_dict("records")

    def margin_variance_breakdown(self, period: str) -> dict:
        prev = self.previous_period(period)
        if prev is None:
            return {"warning": "Aucune période précédente disponible."}
        sales = self.store.table("sales_invoices")
        purchases = self.store.table("purchase_invoices")
        cur_sales = self._period_filter(sales, period)
        old_sales = self._period_filter(sales, prev)
        cur = cur_sales.groupby("product_id").agg(cur_qty=("quantity", "sum"), cur_rev=("net_revenue", "sum")).reset_index()
        old = old_sales.groupby("product_id").agg(old_qty=("quantity", "sum"), old_rev=("net_revenue", "sum")).reset_index()
        df = cur.merge(old, on="product_id", how="outer").fillna(0)
        df["cur_price"] = df.apply(lambda r: r.cur_rev / r.cur_qty if r.cur_qty else 0, axis=1)
        df["old_price"] = df.apply(lambda r: r.old_rev / r.old_qty if r.old_qty else 0, axis=1)
        cur_cost = self._period_filter(purchases, period).groupby("product_id").agg(cur_cost=("unit_cost", "mean")).reset_index()
        old_cost = self._period_filter(purchases, prev).groupby("product_id").agg(old_cost=("unit_cost", "mean")).reset_index()
        df = df.merge(cur_cost, on="product_id", how="left").merge(old_cost, on="product_id", how="left").fillna(0)
        df["price_effect"] = (df["cur_price"] - df["old_price"]) * df["cur_qty"]
        df["volume_effect"] = (df["cur_qty"] - df["old_qty"]) * (df["old_price"] - df["old_cost"])
        df["cost_effect"] = (df["cur_cost"] - df["old_cost"]) * df["cur_qty"] * -1
        # mix approximatif POC : différence résiduelle entre variance réelle et effets simples
        actual_variance = self.gross_margin(period) - self.gross_margin(prev)
        price = float(df["price_effect"].sum())
        volume = float(df["volume_effect"].sum())
        cost = float(df["cost_effect"].sum())
        mix = actual_variance - price - volume - cost
        return {
            "period": period,
            "previous_period": prev,
            "gross_margin_current": self.gross_margin(period),
            "gross_margin_previous": self.gross_margin(prev),
            "margin_variance": actual_variance,
            "price_effect": price,
            "volume_effect": volume,
            "cost_effect": cost,
            "mix_effect": mix,
        }

    def cash_flow(self, period: str) -> dict:
        cash = self._period_filter(self.store.table("cash_movements"), period)
        cash_in = float(cash.get("cash_in", pd.Series(dtype=float)).sum())
        cash_out = float(cash.get("cash_out", pd.Series(dtype=float)).sum())
        return {"period": period, "cash_in": cash_in, "cash_out": cash_out, "net_cash_flow": cash_in - cash_out}
