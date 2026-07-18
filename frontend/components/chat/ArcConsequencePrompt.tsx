'use client';

/**
 * ArcConsequencePrompt — MVP Arc Décisionnel v16.
 *
 * Présente un candidat conséquence à l'utilisateur et lui demande
 * s'il souhaite relier cette nouvelle analyse à son arc décisionnel.
 *
 * RÈGLE CAUSALE : le texte affiché exprime uniquement des associations
 * temporelles (niveau 3 max). Jamais "a causé" ou "est la conséquence de".
 *
 * Si confirmé → rend ArcLearningCard en ligne pour clore le cycle.
 * Si rejeté   → arc reste en EXECUTION (pas d'abandon).
 */

import { useState } from 'react';
import { confirmConsequenceLink } from '@/lib/arc-api';
import { ArcLearningCard } from './ArcLearningCard';

interface ArcConsequencePromptProps {
  arcId: string;
  analysisId: string;
  hypothesis: string;
  recommendationText: string;
  decisionText?: string | null;
}

type Phase = 'pending' | 'confirming' | 'confirmed' | 'rejected' | 'error';

export function ArcConsequencePrompt({
  arcId,
  analysisId,
  hypothesis,
  recommendationText,
  decisionText,
}: ArcConsequencePromptProps) {
  const [phase, setPhase] = useState<Phase>('pending');
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectionInput, setShowRejectionInput] = useState(false);
  const [learningText, setLearningText] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleConfirm = async () => {
    setPhase('confirming');
    try {
      const result = await confirmConsequenceLink(arcId, analysisId, true);
      setLearningText(result.learning_text ?? null);
      setPhase('confirmed');
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : 'Erreur inconnue');
      setPhase('error');
    }
  };

  const handleReject = async () => {
    setPhase('confirming');
    try {
      await confirmConsequenceLink(arcId, analysisId, false, rejectionReason || undefined);
      setPhase('rejected');
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : 'Erreur inconnue');
      setPhase('error');
    }
  };

  // Phase confirmée → ArcLearningCard prend le relais pour la clôture
  if (phase === 'confirmed') {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-1.5 text-xs text-green-700 font-medium px-1">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </svg>
          Lien confirmé — arc mis à jour.
        </div>
        <ArcLearningCard
          arcId={arcId}
          learningText={learningText ?? ''}
          decisionText={decisionText}
          recommendationText={recommendationText}
        />
      </div>
    );
  }

  if (phase === 'rejected') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium px-1 py-2">
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
        Lien non retenu — votre arc reste ouvert pour de futurs candidats.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 overflow-hidden max-w-2xl">
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-3.5 bg-amber-100 border-b border-amber-200">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 bg-amber-500">
          <span className="text-white text-sm">🔗</span>
        </div>
        <div>
          <p className="font-bold text-sm text-[#1A1A2E]">
            Une évolution a été observée depuis votre décision
          </p>
          <p className="text-xs mt-0.5 text-[#5F6368]">
            Souhaitez-vous relier cette analyse à votre arc décisionnel ?
          </p>
        </div>
      </div>

      <div className="px-5 py-4 space-y-4">
        {/* Rappel de la décision */}
        <div className="bg-white rounded-xl border border-amber-100 p-3">
          <p className="text-xs font-medium text-[#5F6368] mb-1">
            {decisionText ? 'Décision documentée' : 'Recommandation d\'origine'}
          </p>
          <p className="text-sm text-[#1A1A2E] leading-relaxed">
            {decisionText || recommendationText}
          </p>
        </div>

        {/* Hypothèse — association temporelle, jamais causale */}
        <div className="bg-white rounded-xl border border-amber-100 p-3">
          <p className="text-xs font-medium text-[#5F6368] mb-1">Ce que nous observons</p>
          <p className="text-sm text-[#1A1A2E] leading-relaxed">{hypothesis}</p>
          <p className="text-xs text-[#5F6368] mt-2 italic">
            Pepperyn observe une corrélation temporelle — vous seul pouvez confirmer le lien.
          </p>
        </div>

        {/* Boutons */}
        {phase === 'pending' && !showRejectionInput && (
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={handleConfirm}
              className="px-4 py-2 rounded-lg text-xs font-bold bg-amber-500 text-white hover:bg-amber-600 transition-colors"
            >
              Oui, relier à mon arc décisionnel
            </button>
            <button
              onClick={() => setShowRejectionInput(true)}
              className="px-4 py-2 rounded-lg text-xs font-medium border border-gray-200 bg-white text-[#1A1A2E] hover:border-amber-300 transition-colors"
            >
              Non, pas lié
            </button>
          </div>
        )}

        {/* Saisie optionnelle pour le rejet */}
        {showRejectionInput && (
          <div className="space-y-2">
            <input
              type="text"
              placeholder="Pourquoi cette évolution n'est-elle pas liée à votre décision ? (optionnel)"
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              className="w-full text-sm px-3 py-2 rounded-lg border border-gray-200 focus:outline-none focus:border-amber-400"
            />
            <div className="flex gap-2">
              <button
                onClick={handleReject}
                disabled={phase === 'confirming'}
                className="px-4 py-2 rounded-lg text-xs font-bold bg-gray-100 text-[#1A1A2E] hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                Confirmer le rejet
              </button>
              <button
                onClick={() => setShowRejectionInput(false)}
                className="px-3 py-2 text-xs text-[#5F6368] underline"
              >
                Retour
              </button>
            </div>
          </div>
        )}

        {phase === 'confirming' && (
          <p className="text-xs text-[#5F6368]">Enregistrement en cours…</p>
        )}

        {phase === 'error' && (
          <p className="text-xs text-red-600">{errorMsg}</p>
        )}
      </div>
    </div>
  );
}
