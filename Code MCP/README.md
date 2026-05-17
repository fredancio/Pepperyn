# Pepperyn MCP POC - Contrôle de gestion Codir

Base Python pour exposer des tools MCP orientés contrôle de gestion à partir d'un fichier Excel structuré.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
cp .env.example .env
```

Modifie `.env` pour pointer vers ton fichier Excel.

## Lancer le serveur MCP

```bash
python -m pepperyn_mcp.server
```

## Lancer un test local sans MCP

```bash
python demo_local.py
```

## Onglets Excel attendus

- companies
- periods
- customers
- products
- suppliers
- cost_centers
- sales_invoices
- purchase_invoices
- fixed_costs
- budget_lines
- cash_movements
- gl_entries

Un modèle Excel vide est générable avec :

```bash
python create_excel_template.py
```
