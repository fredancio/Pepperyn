"""
verify_security.py — Pepperyn
Contrôle pré-déploiement des correctifs de sécurité. NE MODIFIE RIEN.
À lancer depuis le dossier backend :  python verify_security.py

Vérifie :
  1. Que tous les fichiers .py compilent (aucune erreur de syntaxe).
  2. Que les secrets requis sont définis, forts, et différents des défauts publics.
  3. Que les dépendances vulnérables ont bien été montées de version.
  4. Qu'aucun secret par défaut public ne subsiste dans le code.

Code de sortie 0 = tout est bon, 1 = au moins un problème à corriger.
"""
from __future__ import annotations

import os
import re
import sys
import py_compile
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
OK = "\033[92m✅\033[0m"
KO = "\033[91m❌\033[0m"
WARN = "\033[93m⚠️\033[0m"

problems: list[str] = []


def section(title: str) -> None:
    print(f"\n── {title} " + "─" * max(0, 50 - len(title)))


# 1. Compilation de tous les .py
section("1. Compilation des fichiers Python")
compiled, failed = 0, 0
for path in BACKEND.rglob("*.py"):
    if "__pycache__" in path.parts:
        continue
    try:
        py_compile.compile(str(path), doraise=True)
        compiled += 1
    except py_compile.PyCompileError as e:
        failed += 1
        problems.append(f"Erreur de compilation : {path.name}")
        print(f"  {KO} {path.relative_to(BACKEND)} : {e.msg.splitlines()[0]}")
print(f"  {OK if failed == 0 else KO} {compiled} fichiers compilés, {failed} en échec")


# 2. Secrets (charge backend/.env si présent)
section("2. Secrets requis")
try:
    from dotenv import load_dotenv
    load_dotenv(BACKEND / ".env")
except Exception:
    print(f"  {WARN} python-dotenv non installé — vérification des secrets via l'environnement courant")

INSECURE = {
    "JWT_GUEST_SECRET": {"", "pepperyn_guest_secret_key_change_in_prod"},
    "WEBHOOK_SECRET": {"", "pepperyn_webhook_secret_change_me"},
}
MIN_LEN = {"JWT_GUEST_SECRET": 32, "WEBHOOK_SECRET": 16}

for var, bad in INSECURE.items():
    val = os.getenv(var, "")
    if val in bad:
        problems.append(f"{var} absent ou égal au défaut public")
        print(f"  {KO} {var} : absent ou valeur par défaut publique")
    elif len(val) < MIN_LEN[var]:
        problems.append(f"{var} trop court (<{MIN_LEN[var]})")
        print(f"  {KO} {var} : trop court ({len(val)} car., minimum {MIN_LEN[var]})")
    else:
        print(f"  {OK} {var} : défini et fort ({len(val)} car.)")


# 3. Dépendances
section("3. Dépendances corrigées")
req = (BACKEND / "requirements.txt").read_text(encoding="utf-8")


def _ver(pkg: str) -> str | None:
    # [^\n=]* couvre un éventuel [extras] sans franchir la ligne ni le ==
    m = re.search(rf"^{re.escape(pkg)}[^\n=]*==([\d.]+)", req, re.MULTILINE)
    return m.group(1) if m else None


def _ge(v: str, target: str) -> bool:
    def t(s): return tuple(int(x) for x in s.split("."))
    return t(v) >= t(target)


for pkg, target in (("python-jose", "3.4.0"), ("python-multipart", "0.0.18")):
    v = _ver(pkg)
    if v and _ge(v, target):
        print(f"  {OK} {pkg} == {v} (>= {target})")
    else:
        problems.append(f"{pkg} non à jour (trouvé {v}, requis >= {target})")
        print(f"  {KO} {pkg} == {v} (requis >= {target})")


# 4. Aucun secret par défaut résiduel dans le code
section("4. Aucun secret par défaut public dans le code")
leaks = []
for path in BACKEND.rglob("*.py"):
    if "__pycache__" in path.parts or path.name == "verify_security.py" or path.name == "security_config.py":
        continue
    txt = path.read_text(encoding="utf-8", errors="ignore")
    if "pepperyn_guest_secret_key_change_in_prod" in txt or "pepperyn_webhook_secret_change_me" in txt:
        leaks.append(path.relative_to(BACKEND))
if leaks:
    for l in leaks:
        problems.append(f"Secret par défaut résiduel dans {l}")
        print(f"  {KO} {l} contient encore un secret par défaut")
else:
    print(f"  {OK} Aucun secret par défaut public résiduel")


# Bilan
section("BILAN")
if problems:
    print(f"  {KO} {len(problems)} problème(s) à corriger avant déploiement :")
    for p in problems:
        print(f"     - {p}")
    sys.exit(1)
else:
    print(f"  {OK} Tous les contrôles de sécurité sont au vert. Prêt pour le déploiement.")
    sys.exit(0)
