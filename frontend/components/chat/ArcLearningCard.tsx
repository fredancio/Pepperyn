'use client';

/**
 * ArcLearningCard — MVP Arc Décisionnel v16.
 *
 * Présente le learning proposé par Pepperyn et permet à l'utilisateur
 * de le valider ou le modifier pour fermer l'arc (CLOSED).
 *
 * GUARD DE FERMETURE : si decision_text est NULL, une étape de confirmation
 * rétrospective est affichée AVANT la validation du learning.
 * RÈGLE : Recommendation + Execution ≠ Decision documentée.
 * Un arc ne peut être CLOSED sans decision_text.
 *
 * Phases :
 *   1. [Si decision_text NULL] Confirmation rétrospective de la décision
 *   2. Validation / modification du learning
 *   3. Arc CLOSED
 */

import { useState } from 'react';
import { validateLearning } from '@/lib/arc-api';

interface ArcLearningCardProps {
  arcId: string;
  learningText: string;
  decisionText?: string | null;
  recommendationText: string;  // pré-remplit la confirmation si decision_text NULL
}

type Phase = 'decision_confirmation' | 'learning_review' | 'saving' | 'closed' | 'error';

export function ArcLearningCard({
  arcId,
  learningText: initialLearningText,
  decisionText: initialDecisionText,
  recommendationText,
}: ArcLearningCardProps) {
  // Si decision_text existe déjà, on va directement à la review du learning
  const startPhase: Phase = !initialDecisionText
    ? 'decision_confirmation'
    : 'learning_review';

  const [phase, setPhase] = useState<Phase>(startPhase);
  const [decisionInput, setDecisionInput] = useState(recommendationText);
  const [learningInput, setLearningInput] = useState(initialLearningText);
  const [isEditing, setIsEditing] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [closedAt, setClosedAt] = useState<string | null>(null);

  const confirmedDecisionText = initialDecisionText || null;

  const handleDecisionConfirm = () => {
    if (!decisionInput.trim()) return;
    setPhase('learning_review');
  };

  const handleValidate = async () => {
    setPhase('saving');
    try {
      const result = await validateLearning(arcId, {
        action: isEditing ? 'modify' : 'validate',
        learning_text: learningInput,
        // Si decision_text était NULL, on envoie la version confirmée ici
        decision_text: (confirmedDecisionText ?? decisionInput.trim()) || undefined,
      });
      setClosedAt(result.closed_at);
      setPhase('closed');
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : 'Erreur inconnue');
      setPhase('error');
    }
  };

  // ── Phase : confirmation rétrospective de la décision ────────────────────
  if (phase === 'decision_confirmation') {
    return (
      <div className="rounded-2xl border border-purple-200 bg-purple-50 overflow-hidden max-w-2xl">
        <div className="flex items-center gap-3 px-5 py-3.5 bg-purple-100 border-b border-purple-200">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 bg-purple-600">
            <span className="text-white text-sm">📝</span>
          </div>
          <div>
            <p className="font-bold text-sm text-[#1A1A2E]">
              Pour mémoire, quelle décision aviez-vous finalement prise ?
            </p>
            <p className="text-xs mt-0.5 text-[#5F6368]">
              Requis pour clore cet arc et l&apos;intégrer au Capital Décisionnel.
            </p>
          </div>
        </div>

        <div className="px-5 py-4 space-y-3">
          <p className="text-xs text-[#5F6368]">
            Recommandation d&apos;origine (pré-remplie — modifiez si votre décision était différente)
          </p>
          <textarea
            value={decisionInput}
            onChange={(e) => setDecisionInput(e.target.value)}
            rows={3}
            className="w-full text-sm px-3 py-2 rounded-lg border border-purple-200 focus:outline-none focus:border-purple-400 resize-none"
          />
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={handleDecisionConfirm}
              disabled={!decisionInput.trim()}
              className="px-4 py-2 rounded-lg text-xs font-bold bg-purple-600 text-white hover:bg-purple-700 transition-colors disabled:opacity-40"
            >
              C&apos;était bien ma décision
            </button>
          </div>
          <p className="text-xs text-[#5F6368] italic">
            Ce texte deviendra immuable une fois confirmé (audit trail décisionnel).
          </p>
        </div>
      </div>
    );
  }

  // ── Phase : validation du learning ──────────────────────────────────────
  if (phase === 'learning_review') {
    return (
      <div className="rounded-2xl border border-pink-200 bg-pink-50 overflow-hidden max-w-2xl">
        <div className="flex items-center gap-3 px-5 py-3.5 bg-pink-100 border-b border-pink-200">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 bg-pink-600">
            <span className="text-white text-sm">🎓</span>
          </div>
          <div>
            <p className="font-bold text-sm text-[#1A1A2E]">
              Apprentissage de cet arc décisionnel
            </p>
            <p className="text-xs mt-0.5 text-[#5F6368]">
              Validez ou corrigez — cet apprentissage rejoindra votre Capital Décisionnel.
            </p>
          </div>
        </div>

        <div className="px-5 py-4 space-y-4">
          {isEditing ? (
            <textarea
              value={learningInput}
              onChange={(e) => setLearningInput(e.target.value)}
              rows={6}
              className="w-full text-sm px-3 py-2 rounded-lg border border-pink-200 focus:outline-none focus:border-pink-400 resize-none"
            />
          ) : (
            <div className="bg-white rounded-xl border border-pink-100 p-4">
              <p className="text-sm text-[#1A1A2E] leading-relaxed whitespace-pre-wrap">
                {learningInput}
              </p>
            </div>
          )}

          <div className="flex gap-2 flex-wrap">
            <button
              onClick={handleValidate}
              className="px-4 py-2 rounded-lg text-xs font-bold bg-pink-600 text-white hover:bg-pink-700 transition-colors"
            >
              Valider et clore l&apos;arc
            </button>
            {!isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 rounded-lg text-xs font-medium border border-pink-200 bg-white text-[#1A1A2E] hover:border-pink-400 transition-colors"
              >
                Modifier
              </button>
            )}
            {isEditing && (
              <button
                onClick={() => setIsEditing(false)}
                className="px-3 py-2 text-xs text-[#5F6368] underline"
              >
                Annuler
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ── Phase : sauvegarde ───────────────────────────────────────────────────
  if (phase === 'saving') {
    return (
      <div className="flex items-center gap-2 text-xs text-[#5F6368] px-1 py-3">
        <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
        </svg>
        Clôture de l&apos;arc en cours…
      </div>
    );
  }

  // ── Phase : arc CLOSED ───────────────────────────────────────────────────
  if (phase === 'closed') {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 px-5 py-4 max-w-2xl">
        <div className="flex items-center gap-2 text-sm font-bold text-[#1A1A2E] mb-1">
          <span className="text-lg">🔒</span> Arc décisionnel clôturé
        </div>
        <p className="text-xs text-[#5F6368]">
          Cet arc est désormais intégré à votre Capital Décisionnel.
          Il est immuable et servira de référence pour vos futures décisions.
        </p>
        {closedAt && (
          <p className="text-xs text-[#5F6368] mt-1">
            Fermé le {new Date(closedAt).toLocaleDateString('fr-FR', {
              day: 'numeric', month: 'long', year: 'numeric',
            })}
          </p>
        )}
      </div>
    );
  }

  // ── Phase : erreur ───────────────────────────────────────────────────────
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-3 max-w-2xl">
      <p className="text-xs text-red-700">{errorMsg || 'Une erreur est survenue.'}</p>
      <button
        onClick={() => setPhase(startPhase)}
        className="text-xs text-red-600 underline mt-1"
      >
        Réessayer
      </button>
    </div>
  );
}
