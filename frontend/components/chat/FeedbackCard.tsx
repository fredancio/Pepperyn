'use client';
import { useState } from 'react';
import { submitDecisionFeedback } from '@/lib/api';
import type { RecommendationTracking, DecisionFeedbackStatus } from '@/lib/types';

interface FeedbackCardProps {
  reportId: string;
  recommendations: RecommendationTracking[];
}

type IntentionChoice = 'planned' | 'rejected' | 'unsure' | 'no_longer_relevant';

const INTENTION_OPTIONS: { choice: IntentionChoice; label: string; status: DecisionFeedbackStatus }[] = [
  { choice: 'planned', label: 'Je vais appliquer', status: 'planned' },
  { choice: 'rejected', label: 'Je ne vais pas appliquer', status: 'rejected' },
  { choice: 'unsure', label: 'Je ne sais pas encore', status: 'planned' },
  { choice: 'no_longer_relevant', label: "Ce n'est pas pertinent", status: 'no_longer_relevant' },
];

// Affiche au maximum les 3 recommandations prioritaires pour ne pas
// surcharger la page de chat.
const MAX_DISPLAYED = 3;

/** Supprime les marqueurs Markdown **bold** du texte brut. */
function stripMarkdown(text: string): string {
  return text.replace(/\*\*/g, '');
}

export function FeedbackCard({ reportId, recommendations }: FeedbackCardProps) {
  const items = recommendations
    .filter(r => r.priority === 'haute')
    .concat(recommendations.filter(r => r.priority !== 'haute'))
    .slice(0, MAX_DISPLAYED);

  const [choices, setChoices] = useState<Record<string, IntentionChoice>>({});
  const [comments, setComments] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  // Arc Décisionnel MVP v16 — trace si un arc a été créé pour cette recommandation
  const [arcTracked, setArcTracked] = useState<Record<string, boolean>>({});

  if (items.length === 0) return null;

  const handleChoice = (rec: RecommendationTracking, choice: IntentionChoice) => {
    setChoices(prev => ({ ...prev, [rec.id]: choice }));
    // Pour "Je vais appliquer", pas de commentaire nécessaire -> on enregistre direct.
    if (choice === 'planned') {
      void save(rec, choice, '');
    }
  };

  const save = async (rec: RecommendationTracking, choice: IntentionChoice, comment: string) => {
    const option = INTENTION_OPTIONS.find(o => o.choice === choice);
    if (!option) return;
    setSaving(prev => ({ ...prev, [rec.id]: true }));
    try {
      const response = await submitDecisionFeedback({
        report_id: reportId,
        recommendation_id: rec.id,
        recommendation_text: rec.text,
        recommendation_source: rec.source,
        status: option.status,
        comment: comment || undefined,
      });
      setSaved(prev => ({ ...prev, [rec.id]: true }));
      // Arc Décisionnel MVP v16 : si le backend a créé un arc, afficher "Décision tracée ✓"
      if (response.arc_created) {
        setArcTracked(prev => ({ ...prev, [rec.id]: true }));
      }
    } catch {
      // silencieux — pas bloquant pour l'utilisateur
    } finally {
      setSaving(prev => ({ ...prev, [rec.id]: false }));
    }
  };

  const allSaved = items.every(r => saved[r.id]);

  return (
    <div className="rounded-2xl border border-blue-200 bg-blue-50 overflow-hidden max-w-2xl">
      <div className="flex items-center gap-3 px-5 py-3.5 bg-blue-100 border-b border-blue-200">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 bg-[#1B73E8]">
          <span className="text-white text-sm">🎯</span>
        </div>
        <div>
          <p className="font-bold text-sm text-[#1A1A2E]">Que comptez-vous faire ?</p>
          <p className="text-xs mt-0.5 text-[#5F6368]">
            Une réponse rapide m&apos;aide à adapter mes prochaines recommandations.
          </p>
        </div>
      </div>

      <div className="px-5 py-4 space-y-3">
        {items.map((rec) => {
          const choice = choices[rec.id];
          const isSaved = saved[rec.id];
          const needsComment = choice === 'rejected' || choice === 'unsure' || choice === 'no_longer_relevant';

          return (
            <div key={rec.id} className="bg-white rounded-xl border border-blue-100 p-4">
              <p className="text-sm text-[#1A1A2E] leading-relaxed mb-3">{stripMarkdown(rec.text)}</p>

              {!isSaved && (
                <div className="flex flex-wrap gap-2">
                  {INTENTION_OPTIONS.map(opt => (
                    <button
                      key={opt.choice}
                      onClick={() => handleChoice(rec, opt.choice)}
                      disabled={saving[rec.id]}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                        choice === opt.choice
                          ? 'bg-[#1B73E8] text-white border-[#1B73E8]'
                          : 'bg-white text-[#1A1A2E] border-gray-200 hover:border-[#1B73E8]'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}

              {!isSaved && needsComment && (
                <div className="mt-3 flex gap-2">
                  <input
                    type="text"
                    placeholder="Pourquoi ? (optionnel)"
                    value={comments[rec.id] || ''}
                    onChange={(e) => setComments(prev => ({ ...prev, [rec.id]: e.target.value }))}
                    className="flex-1 text-sm px-3 py-1.5 rounded-lg border border-gray-200 focus:outline-none focus:border-[#1B73E8]"
                  />
                  <button
                    onClick={() => save(rec, choice!, comments[rec.id] || '')}
                    disabled={saving[rec.id]}
                    className="px-3 py-1.5 rounded-lg text-xs font-bold bg-[#1B73E8] text-white hover:bg-[#0D47A1] transition-colors disabled:opacity-50"
                  >
                    Valider
                  </button>
                </div>
              )}

              {isSaved && (
                <div className="flex items-center gap-3 text-xs flex-wrap">
                  <div className="flex items-center gap-1.5 text-green-700 font-medium">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                    Merci, c&apos;est noté.
                  </div>
                  {/* Arc Décisionnel MVP v16 : confirmation non-intrusive de la traçabilité */}
                  {arcTracked[rec.id] && (
                    <div className="flex items-center gap-1 text-amber-700 font-medium">
                      <span>🔗</span>
                      <span>Décision tracée</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {allSaved && (
          <p className="text-xs text-[#5F6368] text-center pt-1">
            Vos réponses sont prises en compte pour vos prochaines analyses.
          </p>
        )}
      </div>
    </div>
  );
}
