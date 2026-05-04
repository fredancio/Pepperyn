CANONICAL_TABLES = {
    "sales": {
        "required": ["date", "amount"],
        "recommended": ["customer", "product", "quantity", "unit_price", "discount"],
        "aliases": {
            "date": ["date", "invoice date", "posting date", "transaction date", "datum", "date facture", "facture date", "periode", "period"],
            "customer": ["customer", "client", "nom client", "customer name", "account", "buyer", "tiers", "debtor"],
            "product": ["product", "produit", "sku", "article", "item", "service", "description produit"],
            "quantity": ["quantity", "qty", "quantité", "qte", "volume", "units", "nombre"],
            "unit_price": ["unit price", "prix unitaire", "pu", "price", "prix", "selling price"],
            "discount": ["discount", "remise", "rabais", "ristourne"],
            "amount": ["amount", "net amount", "revenue", "sales", "ca", "chiffre d'affaires", "chiffre affaires", "montant", "montant ht", "total ht", "net revenue", "turnover"],
        },
    },
    "purchases": {
        "required": ["date", "amount"],
        "recommended": ["supplier", "product", "quantity", "unit_cost"],
        "aliases": {
            "date": ["date", "invoice date", "posting date", "date facture", "period", "periode"],
            "supplier": ["supplier", "fournisseur", "vendor", "provider", "creditor", "tiers"],
            "product": ["product", "produit", "sku", "article", "item", "service", "description"],
            "quantity": ["quantity", "qty", "quantité", "qte", "volume", "units"],
            "unit_cost": ["unit cost", "coût unitaire", "cout unitaire", "prix achat", "purchase price", "cost"],
            "amount": ["amount", "cost", "purchase", "achats", "montant", "montant ht", "total ht", "expense", "cogs", "coût", "cout"],
        },
    },
    "fixed_costs": {
        "required": ["date", "amount"],
        "recommended": ["category", "department", "supplier"],
        "aliases": {
            "date": ["date", "period", "periode", "month", "mois", "posting date"],
            "category": ["category", "catégorie", "categorie", "account", "compte", "nature", "type", "expense type"],
            "department": ["department", "département", "departement", "cost center", "centre de coût", "centre cout", "service"],
            "supplier": ["supplier", "fournisseur", "vendor", "provider"],
            "amount": ["amount", "montant", "cost", "expense", "fixed cost", "coût fixe", "cout fixe", "total"],
        },
    },
    "budget": {
        "required": ["period", "metric", "amount"],
        "recommended": ["dimension", "dimension_value"],
        "aliases": {
            "period": ["period", "periode", "month", "mois", "date", "fiscal period"],
            "metric": ["metric", "kpi", "account", "compte", "poste", "type"],
            "amount": ["amount", "budget", "budget amount", "montant", "prévision", "prevision", "forecast"],
            "dimension": ["dimension", "axe", "category", "segment"],
            "dimension_value": ["dimension value", "valeur", "segment", "client", "produit"],
        },
    },
    "cash": {
        "required": ["date", "amount"],
        "recommended": ["direction", "category"],
        "aliases": {
            "date": ["date", "payment date", "date paiement", "bank date", "posting date"],
            "amount": ["amount", "montant", "cash", "bank amount", "encaissement", "décaissement", "decaissement"],
            "direction": ["direction", "in/out", "cash in/out", "type", "sens"],
            "category": ["category", "catégorie", "categorie", "nature", "account", "compte"],
        },
    },
}
