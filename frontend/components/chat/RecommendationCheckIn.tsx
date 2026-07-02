'use client';
import { useState } from 'react';
import { submitDecisionFeedback } from '@/lib/api';
import type { RecommendationTracking, DecisionFeedbackStatus } from '@/lib/types';

interface RecommendationCheckInProps {
  reportId: string;
  recommendations: RecommendationTracking[];
  /** Appelé quand l'utilisateur a terminé (ou choisi de passer) — déclenche l'analyse. */
  onDone: () => void;
}

const STATUS_OPTIONS: { status: DecisionFeedbackStatus; label: string }[] = [
  { status: 'done', label: 'Fait' },
  { status: 'partially_done', label: 'Partiellement fait' },
  { status: 'not_done', label: 'Pas fait' },
  { status: 'no_longer_relevant', label: 'Plus pertinent' },
];

// On ne re-demande un bilan que sur les actions qui avaient été marquées
// "planned" (intention déclarée) — pas sur celles déjà closes.
const MAX_DISPLAYED = 3;

export function RecommendationCheckIn({ reportId, recommendations, onDone }: RecommendationCheckInProps) {
  const items = recommendations
    .filter(r => r.status === 'planned')
    .slice(0, MAX_DISPLAYED);

  const [choices, setChoices] = useState<Record<string, DecisionFeedbackStatus>>({});
  const [comments, setComments] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const [finished, setFinished] = useState(false);

  if (items.length === 0 || finished) {
    return null;
  }

  const handleChoice = (rec: RecommendationTracking, status: DecisionFeedbackStatus) => {
    setChoices(prev => ({ ...prev, [rec.id]: status }));
  };

  const save = async (rec: RecommendationTracking) => {
    const status = choices[rec.id];
    if (!status) return;
    setSaving(prev => ({ ...prev, [rec.id]: true }));
    try {
      await submitDecisionFeedback({
        report_id: reportId,
        recommendation_id: rec.id,
        recommendation_text: rec.text,
        recommendation_source: rec.source,
        status,
        comment: comments[rec.id] || undefined,
      });
      setSaved(prev => ({ ...prev, [rec.id]: true }));
    } catch {
      // silencieux — ne bloque pas la suite
      setSaved(prev => ({ ...prev, [rec.id]: true }));
    } finally {
      setSaving(prev => ({ ...prev, [rec.id]: false }));
    }
  };

  const allSaved = items.every(r => saved[r.id]);

  return (
    <div className="rounded-2xl border border-blue-200 bg-blue-50 overflow-hidden max-w-2xl">
      <div className="flex items-center gap-3 px-5 py-3.5 bg-blue-100 border-b border-blue-200">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 bg-[#1B73E8]">
          <span className="text-white text-sm">📋</span>
        </div>
        <div>
          <p className="font-bold text-sm text-[#1A1A2E]">
            Avant de relancer l&apos;analyse, faisons le point sur les dernières actions recommandées.
          </p>
        </div>
      </div>

      <div className="px-5 py-4 space-y-3">
        {items.map((rec) => {
          const choice = choices[rec.id];
          const isSaved = saved[rec.id];

          return (
            <div key={rec.id} className="bg-white rounded-xl border border-blue-100 p-4">
              <p className="text-sm text-[#1A1A2E] leading-relaxed mb-3">{rec.text}</p>

              {!isSaved && (
                <div className="flex flex-wrap gap-2">
                  {STATUS_OPTIONS.map(opt => (
                    <button
                      key={opt.status}
                      onClick={() => handleChoice(rec, opt.status)}
                      disabled={saving[rec.id]}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                        choice === opt.status
                          ? 'bg-[#1B73E8] text-white border-[#1B73E8]'
                          : 'bg-white text-[#1A1A2E] border-gray-200 hover:border-[#1B73E8]'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}

              {!isSaved && choice && (
                <div className="mt-3 flex gap-2">
                  <input
                    type="text"
                    placeholder="Que s'est-il passé ? (optionnel)"
                    value={comments[rec.id] || ''}
                    onChange={(e) => setComments(prev => ({ ...prev, [rec.id]: e.target.value }))}
                    className="flex-1 text-sm px-3 py-1.5 rounded-lg border border-gray-200 focus:outline-none focus:border-[#1B73E8]"
                  />
                  <button
                    onClick={() => save(rec)}
                    disabled={saving[rec.id]}
                    className="px-3 py-1.5 rounded-lg text-xs font-bold bg-[#1B73E8] text-white hover:bg-[#0D47A1] transition-colors disabled:opacity-50"
                  >
                    Valider
                  </button>
                </div>
              )}

              {isSaved && (
                <div className="flex items-center gap-1.5 text-xs text-green-700 font-medium">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                  Merci, c&apos;est noté.
                </div>
              )}
            </div>
          );
        })}

        <div className="flex items-center justify-between pt-1">
          <button
            onClick={() => { setFinished(true); onDone(); }}
            className="text-xs text-[#5F6368] hover:text-[#1A1A2E] underline transition-colors"
          >
            Passer cette étape
          </button>
          <button
            onClick={() => { setFinished(true); onDone(); }}
            disabled={!allSaved}
            className="px-4 py-2 rounded-lg text-xs font-bold bg-[#1B73E8] text-white hover:bg-[#0D47A1] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Continuer vers l&apos;analyse
          </button>
        </div>
      </div>
    </div>
  );
}
