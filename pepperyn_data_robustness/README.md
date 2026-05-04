# Pepperyn Data Robustness Layer

Couche POC pour importer des fichiers Excel hétérogènes, suggérer un mapping, évaluer la qualité des données et produire un dataset canonique exploitable par le moteur financier / MCP Pepperyn.

## Installation
```bash
pip install -r requirements.txt
```

## Utilisation rapide
```python
from pepperyn_data_robustness import import_finance_excel

result = import_finance_excel("mon_fichier.xlsx")
print(result.quality.summary_text())
print(result.mapping)

# Datasets prêts pour tes calculs
sales = result.dataset.sales
purchases = result.dataset.purchases
fixed_costs = result.dataset.fixed_costs
```
