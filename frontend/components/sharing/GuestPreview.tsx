'use client';

/**
 * GuestPreview — "Voir ce que cette personne verra" (Organisation Sharing
 * Demo, prototype externe, 2026-08-05).
 *
 * Aperçu volontairement statique et non interactif, quel que soit le rôle :
 * ce n'est pas une simulation fonctionnelle d'authentification par rôle,
 * seulement une illustration de ce qui serait visible. Réutilise les mêmes
 * données de démonstration que le parcours principal (Review Briefing,
 * exemple d'analyse) — jamais de contenu inventé séparément.
 *
 * Masque par construction (en ne les rendant simplement jamais dans ce
 * composant autonome) : le reste du portefeuille, les réglages du compte,
 * les quotas, les autres organisations, les fonctions d'administration.
 */

import { SHARING_ROLES, type SharingRoleKey } from '@/lib/sharing-data';
import { buildExampleAnalysis, getDemoReviewBriefing } from '@/lib/demo-data';

interface GuestPreviewProps {
  entityId: string;
  entityName: string;
  role: SharingRoleKey;
  onClose: () => void;
}

/** Retire les marqueurs markdown légers (**gras**) pour un rendu texte simple. */
function stripBold(text: string): string {
  return text.replace(/\*\*(.+?)\*\*/g, '$1');
}

export function GuestPreview({ entityId, entityName, role, onClose }: GuestPreviewProps) {
  const briefingItems = getDemoReviewBriefing(entityId);
  const analysis = buildExampleAnalysis(entityName) as {
    resume_executif?: string;
    decision?: string;
    plan_action?: string[];
  };
  const roleDef = SHARING_ROLES[role];

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 px-4"
      data-testid="guest-preview-overlay"
      role="dialog"
      aria-modal="true"
      aria-label={`Aperçu — vue ${roleDef.label}`}
    >
      <div className="bg-white rounded-2xl shadow-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between px-5 pt-5">
          <div>
            <p className="text-xs font-semibold text-[#5F6368]">Aperçu — vue simulée</p>
            <p className="text-base font-bold text-[#1A1A2E]" data-testid="guest-preview-role-title">
              Ce que verra : {roleDef.label}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[#5F6368] hover:text-[#1A1A2E] text-sm"
            data-testid="guest-preview-close"
            aria-label="Fermer"
          >
            ✕
          </button>
        </div>

        <div className="p-5 flex flex-col gap-4">
          <p className="text-sm font-bold text-[#1A1A2E]" data-testid="guest-preview-org-name">
            {entityName}
          </p>

          {briefingItems.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-[#5F6368] mb-1.5">Briefing de revue</p>
              <div className="flex flex-col gap-1.5" data-testid="guest-preview-briefing">
                {briefingItems.map((item) => (
                  <div
                    key={item.arc_id}
                    className="text-xs text-[#1A1A2E] bg-gray-50 border border-gray-100 rounded-lg px-3 py-2"
                  >
                    <p className="font-medium">{item.title}</p>
                    <p className="text-[#5F6368]">{item.temporal_context}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis.resume_executif && (
            <div>
              <p className="text-xs font-semibold text-[#5F6368] mb-1">Exemple d&apos;analyse</p>
              <p className="text-xs text-[#1A1A2E] leading-relaxed" data-testid="guest-preview-analysis">
                {stripBold(analysis.resume_executif)}
              </p>
            </div>
          )}

          {analysis.decision && (
            <div>
              <p className="text-xs font-semibold text-[#5F6368] mb-1">Décision</p>
              <p className="text-xs text-[#1A1A2E]">{stripBold(analysis.decision)}</p>
            </div>
          )}

          {analysis.plan_action && analysis.plan_action.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-[#5F6368] mb-1">Plan d&apos;action</p>
              <ul className="space-y-0.5">
                {analysis.plan_action.map((action, i) => (
                  <li key={i} className="text-xs text-[#1A1A2E]">
                    · {stripBold(action)}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
            <p className="text-xs font-semibold text-[#1A1A2E] mb-1">Actions autorisées pour ce rôle</p>
            <ul className="space-y-0.5" data-testid="guest-preview-capabilities">
              {roleDef.capabilities.map((c) => (
                <li key={c} className="text-xs text-[#5F6368]">
                  · {c}
                </li>
              ))}
            </ul>
          </div>

          <p className="text-xs text-[#5F6368] italic">
            Aucun autre élément du portefeuille — ni les autres organisations, ni les réglages du
            compte, ni les quotas — n&apos;est visible dans cet aperçu.
          </p>
        </div>
      </div>
    </div>
  );
}
