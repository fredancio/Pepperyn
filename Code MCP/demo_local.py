from pepperyn_mcp.data_loader import FinanceDataStore
from pepperyn_mcp.finance_engine import FinanceEngine
from pepperyn_mcp.codir_responder import CodirResponder
from pepperyn_mcp.config import settings

store = FinanceDataStore(settings.excel_path)
engine = FinanceEngine(store)
responder = CodirResponder(engine)

print("P&L:")
print(engine.monthly_pnl("2025-12"))
print("\nExplication marge:")
print(responder.explain_margin_drop("2025-12"))
