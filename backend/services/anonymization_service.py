"""
Anonymization service — Pepperyn.

Objectif : tenir la promesse de confidentialité décrite sur la page
"/legal/donnees-securisees" :

  "Avant qu'une analyse ne soit réalisée par l'intelligence artificielle, ces
  informations sont automatiquement remplacées par des identifiants anonymes.
  Par exemple : « Dupont SA » devient « CLIENT_001 », « ABC Logistics » devient
  « FOURNISSEUR_001 »."

Architecture (couche 1 — règles déterministes) :

  1. anonymize_parsed_data(parsed_data)
       → détecte les colonnes sensibles (par nom : Client, Fournisseur, Nom,
         Société, Email, Téléphone, IBAN, TVA, Adresse, ...) ainsi que les
         valeurs sensibles par format (email, IBAN, n° TVA), quelle que soit
         la colonne.
       → remplace chaque valeur réelle par un alias stable (CLIENT_001,
         FOURNISSEUR_001, PERSONNE_001, ENTREPRISE_001, EMAIL_001, IBAN_001,
         TVA_001, ADRESSE_001, ...).
       → applique aussi un remplacement par sous-chaîne dans les colonnes de
         texte libre (ex. "Facture Dupont SA février" → "Facture CLIENT_001
         février") pour les valeurs déjà identifiées dans des colonnes
         structurées.
       → renvoie les données anonymisées + une CorrespondenceTable (table de
         correspondance alias ↔ valeur réelle).

  2. La table de correspondance N'EST JAMAIS envoyée à un modèle d'IA. Elle
     est conservée côté serveur (en mémoire, par analyse) pour la
     ré-identification.

  3. deanonymize_recursive(obj, table)
       → parcourt récursivement le résultat produit par l'IA et remplace
         chaque alias (CLIENT_001, ...) par la valeur réelle correspondante,
         avant affichage à l'utilisateur.

Limites connues (couche 2 — non couverte ici, roadmap) :
  - Détection d'entités nommées (NER) dans du texte libre non lié à une
    colonne structurée déjà anonymisée (ex. nom de personne mentionné
    uniquement dans un commentaire).
  - Numéros de téléphone en texte libre (non détectés par regex pour éviter
    les faux positifs avec des montants financiers) — seuls les téléphones
    présents dans une colonne explicitement identifiée comme telle sont
    anonymisés.
"""
from __future__ import annotations

import copy
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any


# ─── Détection des colonnes sensibles par nom ────────────────────────────────

# Ordre = priorité (la première catégorie qui matche est retenue).
# Chaque mot-clé est comparé à la colonne normalisée (minuscule, sans accent,
# ponctuation → espace). Les mots-clés multi-mots sont comparés en
# sous-chaîne ; les mots-clés d'un seul mot doivent correspondre à un mot
# entier (pour éviter par ex. "nom" ⊂ "nombre").
COLUMN_CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("EMAIL", ["email", "e mail", "mail", "courriel"]),
    ("TELEPHONE", ["telephone", "tel", "phone", "gsm", "mobile", "fax"]),
    ("IBAN", ["iban", "rib", "compte bancaire", "numero de compte", "n de compte"]),
    ("TVA", ["tva", "vat", "siret", "siren", "numero d entreprise", "numero entreprise", "bce", "company number"]),
    ("ADRESSE", ["adresse", "address", "rue", "street", "code postal", "zip", "ville", "city"]),
    ("CLIENT", ["client", "customer", "acheteur", "donneur d ordre"]),
    ("FOURNISSEUR", ["fournisseur", "supplier", "vendor", "prestataire"]),
    ("PERSONNE", [
        "nom", "name", "prenom", "employe", "employee", "salarie", "collaborateur",
        "contact", "responsable", "representant", "gerant", "manager",
    ]),
    ("ENTREPRISE", [
        "societe", "company", "entreprise", "raison sociale", "organisation",
        "compagnie", "firme",
    ]),
]

# Longueur minimale pour qu'une valeur soit considérée comme "anonymisable"
# par sous-chaîne (évite de remplacer des caractères/chiffres isolés partout
# dans le document).
MIN_VALUE_LENGTH = 3

# Patterns regex appliqués à TOUTE valeur texte, indépendamment du nom de la
# colonne — formats suffisamment distinctifs pour ne pas générer de faux
# positifs sur des données financières.
VALUE_REGEX_CATEGORIES: list[tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"[\w.\-+]+@[\w\-]+\.[\w.\-]+")),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")),
    ("TVA", re.compile(r"\b[A-Z]{2}\d{8,12}\b")),
]

# Pattern de reconnaissance des alias générés (pour la ré-identification).
ALIAS_PATTERN = re.compile(
    r"\b(?:CLIENT|FOURNISSEUR|PERSONNE|ENTREPRISE|ADRESSE|EMAIL|TVA|IBAN|TELEPHONE)_\d{3}\b"
)


def _normalize(text: str) -> str:
    """minuscule, sans accents, ponctuation → espace, espaces compactés."""
    nfkd = unicodedata.normalize("NFKD", text)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    cleaned = re.sub(r"[^a-z0-9]+", " ", no_accents.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def classify_column(column_name: str) -> str | None:
    """Retourne la catégorie de sensibilité d'une colonne, ou None."""
    norm = _normalize(str(column_name))
    if not norm:
        return None
    words = set(norm.split())
    for category, keywords in COLUMN_CATEGORY_KEYWORDS:
        for kw in keywords:
            kw_norm = _normalize(kw)
            if " " in kw_norm:
                if kw_norm in norm:
                    return category
            elif kw_norm in words:
                return category
    return None


# ─── Table de correspondance ─────────────────────────────────────────────────

@dataclass
class CorrespondenceTable:
    """
    Table de correspondance alias ↔ valeur réelle pour une analyse donnée.

    - alias_to_real : utilisée pour la ré-identification (résultats IA → user)
    - real_to_alias : utilisée pour l'anonymisation (fichier → IA)

    Cette table N'EST JAMAIS transmise à un modèle d'IA. Elle est conservée
    côté serveur (en mémoire, par analyse) le temps de la session.
    """
    alias_to_real: dict[str, str] = field(default_factory=dict)
    real_to_alias: dict[str, str] = field(default_factory=dict)
    _counters: dict[str, int] = field(default_factory=dict)

    def alias_for(self, real_value: str, category: str) -> str:
        real_value = real_value.strip()
        if not real_value:
            return real_value
        existing = self.real_to_alias.get(real_value)
        if existing:
            return existing
        self._counters[category] = self._counters.get(category, 0) + 1
        alias = f"{category}_{self._counters[category]:03d}"
        self.real_to_alias[real_value] = alias
        self.alias_to_real[alias] = real_value
        return alias

    @property
    def is_empty(self) -> bool:
        return not self.alias_to_real

    def to_summary(self) -> dict[str, Any]:
        """Résumé non sensible (compte par catégorie) — utile pour les logs."""
        counts: dict[str, int] = {}
        for alias in self.alias_to_real:
            category = alias.rsplit("_", 1)[0]
            counts[category] = counts.get(category, 0) + 1
        return counts


# ─── Anonymisation ────────────────────────────────────────────────────────────

def _register_classified_columns(sheet: dict[str, Any], table: CorrespondenceTable) -> dict[str, str]:
    """
    Première passe : détecte les colonnes sensibles de la feuille et
    enregistre dans `table` un alias pour chaque valeur rencontrée dans
    `full_table` / `sample_rows`.

    Retourne le mapping {nom_colonne: catégorie} pour les colonnes classées.
    """
    columns = sheet.get("columns") or []
    column_categories: dict[str, str] = {}
    for col in columns:
        category = classify_column(str(col))
        if category:
            column_categories[col] = category

    if not column_categories:
        return column_categories

    for rows_key in ("full_table", "sample_rows"):
        rows = sheet.get(rows_key)
        if not rows:
            continue
        for row in rows:
            for col, category in column_categories.items():
                value = row.get(col)
                if isinstance(value, str) and len(value.strip()) >= MIN_VALUE_LENGTH:
                    table.alias_for(value, category)

    return column_categories


def _substitute_string(text: str, table: CorrespondenceTable, register_new: bool) -> str:
    """
    Remplace dans `text` :
      - les motifs reconnaissables par regex (email, IBAN, n° TVA), en créant
        de nouveaux alias à la volée si `register_new` est vrai ;
      - toute valeur réelle déjà connue de `table` (remplacement par
        sous-chaîne), des plus longues aux plus courtes pour éviter les
        chevauchements partiels.
    """
    if not text:
        return text

    result = text

    if register_new:
        for category, pattern in VALUE_REGEX_CATEGORIES:
            def _repl(m: re.Match, category=category) -> str:
                return table.alias_for(m.group(0), category)
            result = pattern.sub(_repl, result)

    if table.real_to_alias:
        # Remplacement par sous-chaîne, valeurs les plus longues d'abord.
        for real_value in sorted(table.real_to_alias, key=len, reverse=True):
            if len(real_value) < MIN_VALUE_LENGTH:
                continue
            if real_value in result:
                result = result.replace(real_value, table.real_to_alias[real_value])

    return result


def _substitute_recursive(obj: Any, table: CorrespondenceTable, register_new: bool) -> Any:
    if isinstance(obj, str):
        return _substitute_string(obj, table, register_new)
    if isinstance(obj, list):
        return [_substitute_recursive(item, table, register_new) for item in obj]
    if isinstance(obj, dict):
        return {k: _substitute_recursive(v, table, register_new) for k, v in obj.items()}
    return obj


def anonymize_parsed_data(parsed_data: dict[str, Any]) -> tuple[dict[str, Any], CorrespondenceTable]:
    """
    Anonymise les données extraites d'un fichier avant tout envoi à un modèle
    d'IA. Renvoie (données anonymisées, table de correspondance).

    La table de correspondance doit être conservée côté serveur (jamais
    transmise à l'IA) pour permettre la ré-identification des résultats.
    """
    table = CorrespondenceTable()
    data = copy.deepcopy(parsed_data)

    for sheet in data.get("sheets") or []:
        if isinstance(sheet, dict):
            _register_classified_columns(sheet, table)

    anonymized = _substitute_recursive(data, table, register_new=True)
    return anonymized, table


def anonymize_text(text: str, table: CorrespondenceTable, register_new: bool = True) -> str:
    """Anonymise un texte libre (ex. message de chat) avec une table existante."""
    return _substitute_string(text, table, register_new=register_new)


def deanonymize_recursive(obj: Any, table: CorrespondenceTable) -> Any:
    """
    Remplace, partout dans `obj`, les alias (CLIENT_001, ...) par les valeurs
    réelles correspondantes. Ne modifie pas les chaînes ne contenant aucun
    alias connu.
    """
    if table.is_empty:
        return obj

    if isinstance(obj, str):
        if "_" not in obj:
            return obj

        def _repl(m: re.Match) -> str:
            return table.alias_to_real.get(m.group(0), m.group(0))

        return ALIAS_PATTERN.sub(_repl, obj)
    if isinstance(obj, list):
        return [deanonymize_recursive(item, table) for item in obj]
    if isinstance(obj, dict):
        return {k: deanonymize_recursive(v, table) for k, v in obj.items()}
    return obj
