import pandas as pd
from pathlib import Path

out = Path("data/pepperyn_finance_template.xlsx")
out.parent.mkdir(exist_ok=True)

sheets = {
    "companies": pd.DataFrame([{"company_id":"C001","company_name":"Demo PME","sector":"Services","currency":"EUR","fiscal_year_start":"2025-01-01"}]),
    "periods": pd.DataFrame([{"period_id":"2025-11","year":2025,"month":11,"quarter":"Q4","start_date":"2025-11-01","end_date":"2025-11-30"},{"period_id":"2025-12","year":2025,"month":12,"quarter":"Q4","start_date":"2025-12-01","end_date":"2025-12-31"}]),
    "customers": pd.DataFrame([{"customer_id":"CU001","customer_name":"Client Alpha","segment":"Premium","region":"BE","industry":"Retail","account_manager":"Fred"},{"customer_id":"CU002","customer_name":"Client Beta","segment":"Standard","region":"FR","industry":"Services","account_manager":"Fred"}]),
    "products": pd.DataFrame([{"product_id":"P001","product_name":"Produit A","product_family":"Core","category":"Cat1"},{"product_id":"P002","product_name":"Produit B","product_family":"Addon","category":"Cat2"}]),
    "suppliers": pd.DataFrame([{"supplier_id":"S001","supplier_name":"Fournisseur X","category":"Matières","country":"BE","criticality_level":"high"},{"supplier_id":"S002","supplier_name":"Fournisseur Y","category":"Services","country":"FR","criticality_level":"medium"}]),
    "cost_centers": pd.DataFrame([{"cost_center_id":"CC001","department":"Sales","team":"Commercial","manager":"CEO"},{"cost_center_id":"CC002","department":"Admin","team":"Backoffice","manager":"CFO"}]),
    "sales_invoices": pd.DataFrame([
        {"invoice_id":"INV001","date":"2025-11-10","period_id":"2025-11","customer_id":"CU001","product_id":"P001","quantity":100,"unit_price":100,"discount":0,"net_revenue":10000,"sales_channel":"direct"},
        {"invoice_id":"INV002","date":"2025-11-12","period_id":"2025-11","customer_id":"CU002","product_id":"P002","quantity":80,"unit_price":70,"discount":0,"net_revenue":5600,"sales_channel":"direct"},
        {"invoice_id":"INV003","date":"2025-12-08","period_id":"2025-12","customer_id":"CU001","product_id":"P001","quantity":70,"unit_price":98,"discount":0,"net_revenue":6860,"sales_channel":"direct"},
        {"invoice_id":"INV004","date":"2025-12-09","period_id":"2025-12","customer_id":"CU002","product_id":"P002","quantity":110,"unit_price":68,"discount":0,"net_revenue":7480,"sales_channel":"direct"},
    ]),
    "purchase_invoices": pd.DataFrame([
        {"purchase_id":"PUR001","date":"2025-11-05","period_id":"2025-11","supplier_id":"S001","product_id":"P001","quantity":100,"unit_cost":55,"total_cost":5500,"cost_type":"raw_material"},
        {"purchase_id":"PUR002","date":"2025-11-05","period_id":"2025-11","supplier_id":"S002","product_id":"P002","quantity":80,"unit_cost":35,"total_cost":2800,"cost_type":"subcontracting"},
        {"purchase_id":"PUR003","date":"2025-12-05","period_id":"2025-12","supplier_id":"S001","product_id":"P001","quantity":70,"unit_cost":62,"total_cost":4340,"cost_type":"raw_material"},
        {"purchase_id":"PUR004","date":"2025-12-05","period_id":"2025-12","supplier_id":"S002","product_id":"P002","quantity":110,"unit_cost":38,"total_cost":4180,"cost_type":"subcontracting"},
    ]),
    "fixed_costs": pd.DataFrame([
        {"cost_id":"FC001","period_id":"2025-11","cost_center_id":"CC001","category":"salaries","amount":4500,"supplier_id":"","recurring_flag":True},
        {"cost_id":"FC002","period_id":"2025-11","cost_center_id":"CC002","category":"software","amount":900,"supplier_id":"","recurring_flag":True},
        {"cost_id":"FC003","period_id":"2025-12","cost_center_id":"CC001","category":"salaries","amount":4700,"supplier_id":"","recurring_flag":True},
        {"cost_id":"FC004","period_id":"2025-12","cost_center_id":"CC002","category":"software","amount":1300,"supplier_id":"","recurring_flag":True},
    ]),
    "budget_lines": pd.DataFrame(columns=["budget_id","period_id","account_type","dimension_type","dimension_id","budget_amount","budget_quantity","budget_margin"]),
    "cash_movements": pd.DataFrame([
        {"cash_id":"CA001","date":"2025-12-15","period_id":"2025-12","cash_in":9000,"cash_out":7500,"category":"operating","customer_id":"CU001","supplier_id":"","payment_status":"paid"}
    ]),
    "gl_entries": pd.DataFrame(columns=["entry_id","date","period_id","account_code","account_name","debit","credit","amount","cost_center_id","customer_id","supplier_id","product_id"]),
}

with pd.ExcelWriter(out, engine="openpyxl") as writer:
    for name, df in sheets.items():
        df.to_excel(writer, sheet_name=name, index=False)
print(f"Template créé: {out}")
