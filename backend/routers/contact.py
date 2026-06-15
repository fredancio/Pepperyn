"""
routers/contact.py — Pepperyn
Endpoint pour recevoir les demandes de contact (plan SCALE).
Stocke dans Supabase + envoie une notification email via Resend.
"""
from __future__ import annotations

import html
import logging
import os
from typing import Optional, List

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/contact", tags=["contact"])


class ContactRequest(BaseModel):
    prenom_nom: str
    email: str
    entreprise: Optional[str] = None
    taille_equipe: Optional[str] = None
    defis: Optional[List[str]] = None
    utilise_ia: Optional[str] = None
    message: Optional[str] = None
    souhaite_contact: bool = True


def _send_notification(body: ContactRequest) -> None:
    """Envoie un email de notification via Resend. Silencieux si non configuré."""
    api_key = os.environ.get("RESEND_API_KEY")
    notify_to = os.environ.get("NOTIFY_EMAIL", "fredanciaux@hotmail.com")
    notify_from = os.environ.get("NOTIFY_FROM", "Pepperyn <noreply@pepperyn.fr>")

    if not api_key:
        logger.info("[CONTACT] RESEND_API_KEY non configuré — email ignoré")
        return

    try:
        import resend
        resend.api_key = api_key

        # Échappement HTML de toutes les entrées utilisateur (anti-injection HTML/email)
        e_prenom_nom = html.escape(body.prenom_nom or "")
        e_email = html.escape(body.email or "")
        e_entreprise = html.escape(body.entreprise or "")
        e_taille = html.escape(body.taille_equipe or "")
        e_utilise_ia = html.escape(body.utilise_ia or "")
        e_message = html.escape(body.message or "")

        defis_list = "".join(f"<li>{html.escape(str(d))}</li>" for d in (body.defis or []))
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: #0A2540; padding: 24px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 20px;">🚀 Nouvelle demande SCALE</h1>
            <p style="color: #94a3b8; margin: 4px 0 0; font-size: 14px;">Pepperyn — Plan SCALE sur-mesure</p>
          </div>
          <div style="background: white; padding: 24px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px;">

            <table style="width: 100%; border-collapse: collapse;">
              <tr>
                <td style="padding: 8px 0; color: #64748b; font-size: 13px; width: 40%;">Contact</td>
                <td style="padding: 8px 0; font-weight: bold; font-size: 14px;">{e_prenom_nom}</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #64748b; font-size: 13px;">Email</td>
                <td style="padding: 8px 0; font-size: 14px;"><a href="mailto:{e_email}" style="color: #1B73E8;">{e_email}</a></td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #64748b; font-size: 13px;">Entreprise</td>
                <td style="padding: 8px 0; font-size: 14px;">{e_entreprise or '—'}</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #64748b; font-size: 13px;">Taille équipe</td>
                <td style="padding: 8px 0; font-size: 14px;">{e_taille or '—'}</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #64748b; font-size: 13px;">Utilise IA</td>
                <td style="padding: 8px 0; font-size: 14px;">{e_utilise_ia or '—'}</td>
              </tr>
            </table>

            {"<div style='margin-top:16px;'><p style='color:#64748b;font-size:13px;margin:0 0 6px;'>Défis identifiés</p><ul style='margin:0;padding-left:20px;font-size:14px;'>" + defis_list + "</ul></div>" if body.defis else ""}

            {"<div style='margin-top:16px; padding:16px; background:#f8fafc; border-radius:8px;'><p style='color:#64748b;font-size:13px;margin:0 0 6px;'>Message</p><p style='font-size:14px;margin:0;'>" + e_message + "</p></div>" if body.message else ""}

            <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0;">
              <a href="mailto:{e_email}" style="display:inline-block; background:#1B73E8; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-size:14px; font-weight:bold;">
                Répondre à {e_prenom_nom} →
              </a>
            </div>
          </div>
        </div>
        """

        resend.Emails.send({
            "from": notify_from,
            "to": [notify_to],
            "subject": f"🚀 Nouvelle demande SCALE — {body.prenom_nom} ({body.entreprise or body.email})",
            "html": html_body,
        })
        logger.info(f"[CONTACT] Notification email envoyé à {notify_to}")

    except Exception as e:
        logger.error(f"[CONTACT] Erreur envoi email: {e}")


@router.post("")
async def submit_contact(body: ContactRequest):
    from main import get_supabase_service
    supabase = get_supabase_service()

    try:
        supabase.from_("contact_requests").insert({
            "prenom_nom": body.prenom_nom,
            "email": body.email,
            "entreprise": body.entreprise,
            "taille_equipe": body.taille_equipe,
            "defis": body.defis or [],
            "utilise_ia": body.utilise_ia,
            "message": body.message,
            "souhaite_contact": body.souhaite_contact,
        }).execute()

        logger.info(f"[CONTACT] New request from {body.email}")

        # Notification email (non-bloquant)
        _send_notification(body)

        return {"success": True}

    except Exception as e:
        logger.error(f"[CONTACT] Error: {e}")
        return {"success": False, "error": "Une erreur est survenue. Merci de réessayer."}


@router.get("/requests")
async def list_contact_requests(
    authorization: Optional[str] = Header(default=None),
):
    """Pour le CRM admin — liste toutes les demandes. Réservé au super-admin."""
    # ⚠️ Contient des données personnelles (noms, emails, messages) — accès super-admin uniquement.
    from routers.superadmin import _require_superadmin
    await _require_superadmin(authorization)

    from main import get_supabase_service
    supabase = get_supabase_service()

    try:
        result = (
            supabase.from_("contact_requests")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return {"success": True, "data": result.data or []}
    except Exception as e:
        logger.error(f"[CONTACT] list error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des demandes")
