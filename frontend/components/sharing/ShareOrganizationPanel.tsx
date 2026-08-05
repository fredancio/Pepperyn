'use client';

/**
 * ShareOrganizationPanel — Organisation Sharing Demo (prototype externe,
 * 2026-08-05).
 *
 * Simule la direction produit retenue (Organisation → Membres → Rôles →
 * Invitations temporaires) en remplacement du modèle PIN invité permanent
 * rejeté. Sert à tester la COMPRÉHENSION du modèle collaboratif, pas sa
 * sécurité réelle.
 *
 * MODE DÉMO STRICT : aucun appel Supabase, aucune écriture, aucun email,
 * aucun vrai compte, aucune API, aucun stockage persistant. Tout l'état
 * (invitation créée, sélections) vit dans ce composant et disparaît au
 * démontage / rafraîchissement de la page — comportement volontaire.
 *
 * Principe métier montré : on ne partage jamais un code d'accès permanent
 * global. On invite une personne sur un périmètre précis (par défaut :
 * uniquement cette organisation), avec un rôle précis (par défaut : le
 * plus restrictif). Le portefeuille entier n'est jamais partagé par
 * défaut — seule une confirmation explicite supplémentaire le permet.
 */

import { useState } from 'react';
import {
  DEFAULT_INVITE_ROLE,
  DEFAULT_INVITE_SCOPE,
  SHARING_ROLE_ORDER,
  SHARING_ROLES,
  SHARING_SCOPE_OPTIONS,
  SIMULATED_MEMBERS,
  WHOLE_PORTFOLIO_CONFIRMATION_TEXT,
  TEMPORARY_CODE_VALIDITY_LABEL,
  TEMPORARY_CODE_USAGE_LABEL,
  generateFakeTemporaryCode,
  type SharingRoleKey,
  type SharingScope,
} from '@/lib/sharing-data';
import { DEMO_ENTITIES } from '@/lib/demo-data';
import { GuestPreview } from './GuestPreview';

interface ShareOrganizationPanelProps {
  entityId: string;
  entityName: string;
  onClose: () => void;
}

type PanelView = 'members' | 'invite' | 'success';

interface CreatedInvitation {
  code: string;
  role: SharingRoleKey;
  scope: SharingScope;
  selectedOtherOrgNames: string[];
}

function scopeSummaryLabel(invitation: CreatedInvitation, entityName: string): string {
  if (invitation.scope === 'this_organization') return entityName;
  if (invitation.scope === 'whole_portfolio') return 'Tout le portefeuille';
  return [entityName, ...invitation.selectedOtherOrgNames].join(', ');
}

export function ShareOrganizationPanel({ entityId, entityName, onClose }: ShareOrganizationPanelProps) {
  const [view, setView] = useState<PanelView>('members');

  // Formulaire d'invitation — jamais envoyé nulle part, jamais stocké.
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<SharingRoleKey>(DEFAULT_INVITE_ROLE);
  const [scope, setScope] = useState<SharingScope>(DEFAULT_INVITE_SCOPE);
  const [selectedOtherOrgIds, setSelectedOtherOrgIds] = useState<string[]>([]);
  const [portfolioConfirmed, setPortfolioConfirmed] = useState(false);

  const [createdInvitation, setCreatedInvitation] = useState<CreatedInvitation | null>(null);
  const [previewRole, setPreviewRole] = useState<SharingRoleKey | null>(null);

  const otherOrganizations = DEMO_ENTITIES.filter((e) => e.id !== entityId);

  const canSubmit =
    email.trim().length > 0 &&
    (scope !== 'selected_organizations' || selectedOtherOrgIds.length > 0) &&
    (scope !== 'whole_portfolio' || portfolioConfirmed);

  const toggleOtherOrg = (id: string) => {
    setSelectedOtherOrgIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleScopeChange = (next: SharingScope) => {
    setScope(next);
    if (next !== 'whole_portfolio') setPortfolioConfirmed(false);
    if (next !== 'selected_organizations') setSelectedOtherOrgIds([]);
  };

  const handleCreateInvitation = () => {
    if (!canSubmit) return;
    // Invitation simulée — aucun fetch(), aucune écriture, aucun email réel.
    const selectedOtherOrgNames = otherOrganizations
      .filter((o) => selectedOtherOrgIds.includes(o.id))
      .map((o) => o.name);
    setCreatedInvitation({
      code: generateFakeTemporaryCode(),
      role,
      scope,
      selectedOtherOrgNames,
    });
    setView('success');
  };

  const resetInviteForm = () => {
    setEmail('');
    setRole(DEFAULT_INVITE_ROLE);
    setScope(DEFAULT_INVITE_SCOPE);
    setSelectedOtherOrgIds([]);
    setPortfolioConfirmed(false);
    setCreatedInvitation(null);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4"
      data-testid="share-organization-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Partager cette organisation"
    >
      <div className="bg-white rounded-2xl shadow-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between px-5 pt-5">
          <p className="text-base font-bold text-[#1A1A2E]">Partager cette organisation</p>
          <button
            type="button"
            onClick={onClose}
            className="text-[#5F6368] hover:text-[#1A1A2E] text-sm"
            data-testid="share-panel-close"
            aria-label="Fermer"
          >
            ✕
          </button>
        </div>

        {view === 'members' && (
          <div className="p-5 flex flex-col gap-4">
            <p className="text-xs text-[#5F6368]" data-testid="share-panel-explainer">
              Cette invitation donne accès uniquement à {entityName}. Les autres organisations de
              votre portefeuille restent invisibles.
            </p>

            <div className="flex flex-col gap-2" data-testid="share-panel-members">
              {SIMULATED_MEMBERS.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-50 border border-gray-100"
                  data-testid={`share-member-${member.id}`}
                >
                  <div>
                    <p className="text-sm font-medium text-[#1A1A2E]">{member.name}</p>
                    <p className="text-xs text-[#5F6368]">{SHARING_ROLES[member.role].label}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setPreviewRole(member.role)}
                    className="text-xs text-[#1B73E8] hover:text-[#0D47A1] underline"
                  >
                    Aperçu
                  </button>
                </div>
              ))}
            </div>

            <button
              type="button"
              onClick={() => setView('invite')}
              className="text-sm font-semibold text-white bg-[#1B73E8] hover:bg-[#0D47A1] rounded-lg px-3 py-2.5 transition-colors"
              data-testid="share-panel-open-invite"
            >
              + Inviter quelqu&apos;un
            </button>
          </div>
        )}

        {view === 'invite' && (
          <div className="p-5 flex flex-col gap-4">
            <button
              type="button"
              onClick={() => setView('members')}
              className="text-xs text-[#1B73E8] hover:text-[#0D47A1] self-start"
            >
              ← Retour
            </button>

            <div>
              <label className="text-xs font-semibold text-[#1A1A2E] mb-1 block">Adresse email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="prenom@exemple.fr"
                className="w-full text-sm bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-[#1A1A2E] focus:outline-none focus:ring-1 focus:ring-[#1B73E8]"
                data-testid="share-invite-email"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-[#1A1A2E] mb-1 block">Rôle</label>
              <div className="flex gap-1.5 flex-wrap" data-testid="share-invite-role">
                {SHARING_ROLE_ORDER.map((key) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setRole(key)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
                      role === key
                        ? 'bg-[#1B73E8] border-[#1B73E8] text-white'
                        : 'bg-white border-gray-200 text-[#5F6368]'
                    }`}
                    data-testid={`share-invite-role-${key}`}
                  >
                    {SHARING_ROLES[key].label}
                  </button>
                ))}
              </div>
              <ul className="mt-2 space-y-0.5">
                {SHARING_ROLES[role].capabilities.map((c) => (
                  <li key={c} className="text-xs text-[#5F6368]">
                    · {c}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <label className="text-xs font-semibold text-[#1A1A2E] mb-1 block">Périmètre d&apos;accès</label>
              <div className="flex flex-col gap-1.5" data-testid="share-invite-scope">
                {SHARING_SCOPE_OPTIONS.map((option) => (
                  <label
                    key={option.key}
                    className="flex items-center gap-2 text-sm text-[#1A1A2E]"
                  >
                    <input
                      type="radio"
                      name="share-scope"
                      checked={scope === option.key}
                      onChange={() => handleScopeChange(option.key)}
                      data-testid={`share-scope-${option.key}`}
                    />
                    {option.label}
                  </label>
                ))}
              </div>

              {scope === 'selected_organizations' && (
                <div className="mt-2 flex flex-col gap-1" data-testid="share-scope-org-picker">
                  {otherOrganizations.map((org) => (
                    <label key={org.id} className="flex items-center gap-2 text-xs text-[#5F6368]">
                      <input
                        type="checkbox"
                        checked={selectedOtherOrgIds.includes(org.id)}
                        onChange={() => toggleOtherOrg(org.id)}
                      />
                      {org.name}
                    </label>
                  ))}
                </div>
              )}

              {scope === 'whole_portfolio' && (
                <div
                  className="mt-2 rounded-lg border border-amber-200 bg-amber-50 p-3"
                  data-testid="share-scope-whole-portfolio-warning"
                >
                  <p className="text-xs text-amber-800">{WHOLE_PORTFOLIO_CONFIRMATION_TEXT}</p>
                  <label className="flex items-center gap-2 text-xs text-amber-900 mt-2">
                    <input
                      type="checkbox"
                      checked={portfolioConfirmed}
                      onChange={(e) => setPortfolioConfirmed(e.target.checked)}
                      data-testid="share-scope-whole-portfolio-confirm"
                    />
                    Je confirme
                  </label>
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={handleCreateInvitation}
              disabled={!canSubmit}
              className="text-sm font-semibold text-white bg-[#1B73E8] hover:bg-[#0D47A1] rounded-lg px-3 py-2.5 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              data-testid="share-invite-submit"
            >
              Créer l&apos;invitation
            </button>
          </div>
        )}

        {view === 'success' && createdInvitation && (
          <div className="p-5 flex flex-col gap-3" data-testid="share-invite-success">
            <p className="text-sm font-bold text-[#1A1A2E]">Invitation créée</p>

            <div className="rounded-xl border border-blue-100 bg-[#EFF6FF] p-4">
              <p className="text-xs text-[#5F6368]">Code temporaire</p>
              <p
                className="text-lg font-mono font-bold text-[#1A1A2E] tracking-wide"
                data-testid="share-invite-code"
              >
                {createdInvitation.code}
              </p>
              <p className="text-xs text-[#5F6368] mt-1">
                {TEMPORARY_CODE_VALIDITY_LABEL} · {TEMPORARY_CODE_USAGE_LABEL}
              </p>
            </div>

            <div className="text-sm text-[#1A1A2E]">
              <p>
                <span className="text-[#5F6368]">Organisation : </span>
                {scopeSummaryLabel(createdInvitation, entityName)}
              </p>
              <p>
                <span className="text-[#5F6368]">Rôle : </span>
                {SHARING_ROLES[createdInvitation.role].label}
              </p>
            </div>

            <p className="text-xs text-[#5F6368]">
              Cet accès peut être révoqué à tout moment par un administrateur. Ce code temporaire
              n&apos;est pas un mot de passe permanent.
            </p>

            <button
              type="button"
              onClick={() => setPreviewRole(createdInvitation.role)}
              className="text-xs text-[#1B73E8] hover:text-[#0D47A1] underline self-start"
              data-testid="share-invite-preview-link"
            >
              Voir ce que cette personne verra
            </button>

            <div className="flex gap-2 mt-1">
              <button
                type="button"
                onClick={resetInviteForm}
                className="text-xs font-medium text-[#5F6368] hover:text-[#1A1A2E] underline"
              >
                Nouvelle invitation
              </button>
              <button
                type="button"
                onClick={onClose}
                className="text-xs font-semibold text-white bg-[#1B73E8] hover:bg-[#0D47A1] rounded-lg px-3 py-1.5 ml-auto"
              >
                Fermer
              </button>
            </div>
          </div>
        )}
      </div>

      {previewRole && (
        <GuestPreview
          entityId={entityId}
          entityName={entityName}
          role={previewRole}
          onClose={() => setPreviewRole(null)}
        />
      )}
    </div>
  );
}
