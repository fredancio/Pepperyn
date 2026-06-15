"""
security_config.py — Pepperyn
Centralise la résolution des secrets sensibles avec une politique « fail-closed » :
le backend refuse d'utiliser un secret absent ou laissé à sa valeur par défaut
publique (qui figurait dans le code source). Cela empêche la forge de jetons
invités / d'appels webhook avec un secret connu de tous.
"""
import os

# Valeurs par défaut historiques (publiques) — interdites en exécution.
_INSECURE_JWT_DEFAULTS = {
    "",
    "pepperyn_guest_secret_key_change_in_prod",
}
_INSECURE_WEBHOOK_DEFAULTS = {
    "",
    "pepperyn_webhook_secret_change_me",
}


def get_jwt_guest_secret() -> str:
    """Retourne le secret de signature des JWT invités. Lève si non configuré."""
    secret = os.getenv("JWT_GUEST_SECRET", "")
    if secret in _INSECURE_JWT_DEFAULTS or len(secret) < 32:
        raise RuntimeError(
            "JWT_GUEST_SECRET non configuré ou trop faible. "
            "Définissez une valeur aléatoire d'au moins 32 caractères dans l'environnement "
            "(ex. `python -c \"import secrets; print(secrets.token_urlsafe(48))\"`)."
        )
    return secret


def get_webhook_secret() -> str:
    """Retourne le secret partagé du webhook Supabase. Lève si non configuré."""
    secret = os.getenv("WEBHOOK_SECRET", "")
    if secret in _INSECURE_WEBHOOK_DEFAULTS or len(secret) < 16:
        raise RuntimeError(
            "WEBHOOK_SECRET non configuré ou trop faible. "
            "Définissez une valeur aléatoire dans l'environnement et côté Supabase Database Webhook."
        )
    return secret
