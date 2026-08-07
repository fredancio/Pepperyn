'use client';

/**
 * ReviewBriefing — Capability 3 (Monthly Review Engine), Incrément 2.
 *
 * Synthèse opérationnelle des décisions actives suivies avec un client :
 * priorité, contexte temporel, pourquoi ça compte, questions prêtes à poser
 * pendant la revue.
 *
 * RÈGLES (voir REVIEW_BRIEFING_IMPLEMENTATION_PLAN.md) :
 *   - Périmètre : uniquement les DecisionArc actifs — jamais d'échéances
 *     comptables/fiscales, jamais de notes libres, jamais d'agrégation
 *     multi-clients.
 *   - "Ne plus suivre" ne signifie jamais que le sujet est réglé/résolu/
 *     exécuté — uniquement que le suivi s'arrête (transition abandoned).
 *     L'arc n'est jamais supprimé, l'historique reste intact.
 *   - Aucune carte "Clos" ne reçoit de question ni d'action "Ne plus suivre"
 *     (rien d'ouvert à discuter sur un sujet déjà clos).
 *   - Retourne null s'il n'y a aucun élément actif — pas de bandeau vide.
 */

import { useCallback, useEffect, useState } from 'react';
import { ABANDON_REASON_CHOICES, abandonArc, fetchReviewBriefing } from '@/lib/arc-api';
import type { BriefingItem } from '@/lib/types';

interface ReviewBriefingProps {
  entityId?: string;
  /** Appelé quand l'utilisateur clique "Préparer cette question" — ne déclenche jamais d'envoi. */
  onPrepareQuestion?: (question: string) => void;
}

type AbandonUiState = 'idle' | 'choosing_reason' | 'saving' | 'error';

const PRIORITY_META: Record<BriefingItem['priority'], { icon: string; label: string }> = {
  urgent: { icon: '🔥', label: 'Urgent' },
  to_check: { icon: '⚠️', label: 'À vérifier' },
  done: { icon: '✓', label: 'Fait' },
  closed: { icon: '○', label: 'Clos' },
};

export function ReviewBriefing({ entityId, onPrepareQuestion }: ReviewBriefingProps) {
  const [items, setItems] = useState<BriefingItem[] | null>(null);
  const [abandonState, setAbandonState] = useState<Record<string, AbandonUiState>>({});
  const [abandonError, setAbandonError] = useState<Record<string, string>>({});
  const [pendingReasonKey, setPendingReasonKey] = useState<Record<string, string | undefined>>({});
  // Evidence Ledger Consumer #1 — replié par défaut, purement discret :
  // ne doit jamais rivaliser visuellement avec le contenu principal du
  // Briefing (why_it_matters / questions_to_ask).
  const [evidenceExpanded, setEvidenceExpanded] = useState<Record<string, boolean>>({});

  const loadBriefing = useCallback(async () => {
    try {
      const result = await fetchReviewBriefing(entityId);
      setItems(result);
    } catch {
      // Échec silencieux — le briefing est un enrichissement, jamais un bloqueur
      // de la conversation. On n'affiche simplement rien.
      setItems([]);
    }
  }, [entityId]);

  useEffect(() => {
    loadBriefing();
  }, [loadBriefing]);

  const handleStopTracking = (arcId: string) => {
    setAbandonState((prev) => ({ ...prev, [arcId]: 'choosing_reason' }));
  };

  const handleCancelStopTracking = (arcId: string) => {
    setAbandonState((prev) => {
      const next = { ...prev };
      delete next[arcId];
      return next;
    });
  };

  const handleConfirmStopTracking = async (arcId: string, reasonKey?: string) => {
    if (!items) return;
    const previousItems = items;
    const effectiveReasonKey = reasonKey ?? pendingReasonKey[arcId];

    setPendingReasonKey((prev) => ({ ...prev, [arcId]: effectiveReasonKey }));
    setAbandonState((prev) => ({ ...prev, [arcId]: 'saving' }));
    // Retrait optimiste de la carte.
    setItems((prev) => (prev ? prev.filter((i) => i.arc_id !== arcId) : prev));

    try {
      const reasonLabel = effectiveReasonKey ? ABANDON_REASON_CHOICES[effectiveReasonKey] : undefined;
      await abandonArc(arcId, reasonLabel);
      setAbandonState((prev) => {
        const next = { ...prev };
        delete next[arcId];
        return next;
      });
    } catch (e) {
      // Échec → la carte réapparaît, jamais de perte silencieuse.
      setItems(previousItems);
      setAbandonState((prev) => ({ ...prev, [arcId]: 'error' }));
      setAbandonError((prev) => ({
        ...prev,
        [arcId]: e instanceof Error ? e.message : 'Erreur inconnue',
      }));
    }
  };

  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div
      className="rounded-2xl border border-indigo-200 bg-indigo-50 overflow-hidden max-w-2xl mb-4"
      data-testid="review-briefing"
    >
      <div className="px-5 py-3.5 bg-indigo-100 border-b border-indigo-200">
        <p className="font-bold text-sm text-[#1A1A2E]">Briefing de revue</p>
        <p className="text-xs mt-0.5 text-[#5F6368]">
          Points issus des recommandations et décisions suivies avec ce client.
        </p>
      </div>

      <div className="divide-y divide-indigo-100">
        {items.map((item) => {
          const meta = PRIORITY_META[item.priority];
          const state = abandonState[item.arc_id] ?? 'idle';
          const isClosed = item.priority === 'closed';

          return (
            <div
              key={item.arc_id}
              className="px-5 py-4"
              data-testid={`briefing-card-${item.arc_id}`}
            >
              <div className="flex items-start gap-2">
                <span className="text-sm" aria-hidden="true">{meta.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-[#5F6368]">{meta.label}</p>
                  <p className="text-sm font-bold text-[#1A1A2E] mt-0.5">{item.title}</p>
                  <p className="text-xs text-[#5F6368] mt-0.5">{item.temporal_context}</p>

                  {item.why_it_matters && (
                    <p className="text-xs text-[#1A1A2E] mt-2">{item.why_it_matters}</p>
                  )}

                  {item.evidence_support &&
                    (item.evidence_support.impacts.length > 0 || item.evidence_support.sheets.length > 0) && (
                      <div className="mt-2">
                        <button
                          type="button"
                          onClick={() =>
                            setEvidenceExpanded((prev) => ({ ...prev, [item.arc_id]: !prev[item.arc_id] }))
                          }
                          className="text-xs font-medium text-indigo-600 hover:text-indigo-800 underline"
                          data-testid={`evidence-toggle-${item.arc_id}`}
                        >
                          {evidenceExpanded[item.arc_id] ? "Masquer les éléments de l'analyse source" : "Éléments de l'analyse source"}
                        </button>

                        {evidenceExpanded[item.arc_id] && (
                          <div
                            className="mt-1.5 rounded-lg border border-indigo-100 bg-white p-2.5 space-y-1"
                            data-testid={`evidence-support-${item.arc_id}`}
                          >
                            {item.evidence_support.impacts.map((impact, idx) => (
                              <p key={idx} className="text-xs text-[#1A1A2E]">
                                {impact.metric_type_label} : {impact.amount.toLocaleString('fr-FR')} {impact.currency}
                                <span className="text-[#5F6368]"> — {impact.qualifier}</span>
                              </p>
                            ))}
                            {item.evidence_support.sheets.length > 0 && (
                              <p className="text-xs text-[#5F6368]">
                                Source{item.evidence_support.sheets.length > 1 ? 's' : ''} : {item.evidence_support.sheets.join(', ')}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                  {item.questions_to_ask.length > 0 && (
                    <div className="mt-3 space-y-1.5">
                      {item.questions_to_ask.map((question, idx) => (
                        <div key={idx} className="flex items-center gap-2 flex-wrap">
                          <p className="text-xs italic text-[#1A1A2E]">« {question} »</p>
                          {onPrepareQuestion && (
                            <button
                              type="button"
                              onClick={() => onPrepareQuestion(question)}
                              className="text-xs font-medium text-indigo-600 hover:text-indigo-800 underline"
                            >
                              Préparer cette question
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {!isClosed && state === 'idle' && (
                    <button
                      type="button"
                      onClick={() => handleStopTracking(item.arc_id)}
                      className="mt-3 text-xs font-medium text-[#5F6368] hover:text-[#1A1A2E] underline"
                    >
                      Ne plus suivre
                    </button>
                  )}

                  {state === 'choosing_reason' && (
                    <div className="mt-3 rounded-lg border border-indigo-200 bg-white p-3 space-y-2">
                      <p className="text-xs text-[#1A1A2E]">
                        Ce point restera conservé dans l&apos;historique, mais ne figurera plus
                        parmi les sujets actifs de vos prochaines revues.
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {Object.entries(ABANDON_REASON_CHOICES).map(([key, label]) => (
                          <button
                            key={key}
                            type="button"
                            onClick={() => handleConfirmStopTracking(item.arc_id, key)}
                            className="px-2.5 py-1 rounded-md text-xs border border-indigo-200 bg-indigo-50 hover:bg-indigo-100 text-[#1A1A2E]"
                          >
                            {label}
                          </button>
                        ))}
                      </div>
                      <button
                        type="button"
                        onClick={() => handleCancelStopTracking(item.arc_id)}
                        className="text-xs text-[#5F6368] underline"
                      >
                        Annuler
                      </button>
                    </div>
                  )}

                  {state === 'saving' && (
                    <p className="mt-3 text-xs text-[#5F6368]">Retrait en cours…</p>
                  )}

                  {state === 'error' && (
                    <div className="mt-3 text-xs text-red-600">
                      {abandonError[item.arc_id] || 'Erreur lors du retrait.'}
                      <button
                        type="button"
                        onClick={() => handleConfirmStopTracking(item.arc_id)}
                        className="ml-2 underline"
                      >
                        Réessayer
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
