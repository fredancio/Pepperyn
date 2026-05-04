from pepperyn_data_robustness import import_finance_excel

result = import_finance_excel("data/client_upload.xlsx")

print(result.quality.summary_text())

if result.quality.status == "blocked":
    raise SystemExit("Données insuffisantes: demander un mapping manuel ou un fichier plus complet.")

# Exemple: brancher ces DataFrames à ton moteur financier existant
sales_df = result.dataset.sales
purchases_df = result.dataset.purchases
fixed_costs_df = result.dataset.fixed_costs

print(sales_df.head())
