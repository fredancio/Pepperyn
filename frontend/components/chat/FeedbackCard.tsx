'use client';
import { useState } from 'react';
import { submitDecisionFeedback, submitV1GovernedDecision, submitV1GovernedFollowup, submitV1GovernedIntention } from '@/lib/api';
import type { RecommendationTracking, DecisionFeedbackStatus } from '@/lib/types';

interface FeedbackCardProps {
  reportId: string;
  recommendations: RecommendationTracking[];
  governedV1?: boolean;
}

type IntentionChoice = 'planned' | 'rejected' | 'unsure' | 'no_longer_relevant';
type DecisionKind = 'accepted_conditional' | 'modified' | 'rejected';
type FollowupStatus = 'pending_validation' | 'in_progress' | 'blocked' | 'completed' | 'not_pursued';

const INTENTION_OPTIONS: { choice: IntentionChoice; label: string; status: DecisionFeedbackStatus }[] = [
  { choice: 'planned', label: 'Je vais appliquer', status: 'planned' },
  { choice: 'rejected', label: 'Je ne vais pas appliquer', status: 'rejected' },
  { choice: 'unsure', label: 'Je ne sais pas encore', status: 'unsure' },
  { choice: 'no_longer_relevant', label: "Ce n'est pas pertinent", status: 'no_longer_relevant' },
];

// Affiche au maximum les 3 recommandations prioritaires pour ne pas
// surcharger la page de chat.
const MAX_DISPLAYED = 3;

/** Supprime les marqueurs Markdown **bold** du texte brut. */
function stripMarkdown(text: string): string {
  return text.replace(/\*\*/g, '');
}

export function FeedbackCard({ reportId, recommendations, governedV1 = false }: FeedbackCardProps) {
  const items = recommendations
    .filter(r => r.priority === 'haute')
    .concat(recommendations.filter(r => r.priority !== 'haute'))
    .slice(0, MAX_DISPLAYED);

  const [choices, setChoices] = useState<Record<string, IntentionChoice>>(() =>
    Object.fromEntries(items.filter(item => item.status).map(item => [item.id, item.status as IntentionChoice])),
  );
  const [comments, setComments] = useState<Record<string, string>>(() =>
    Object.fromEntries(items.filter(item => item.comment).map(item => [item.id, item.comment as string])),
  );
  const [saved, setSaved] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(items.filter(item => item.status).map(item => [item.id, true])),
  );
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  // Arc Décisionnel MVP v16 — trace si un arc a été créé pour cette recommandation
  const [arcTracked, setArcTracked] = useState<Record<string, boolean>>({});
  const [decisionKinds, setDecisionKinds] = useState<Record<string, DecisionKind>>({});
  const [decisionTexts, setDecisionTexts] = useState<Record<string, string>>({});
  const [acknowledged, setAcknowledged] = useState<Record<string, boolean>>({});
  const [decided, setDecided] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(items.filter(item => item.decision_confirmed_at).map(item => [item.id, true])),
  );
  const [decisionErrors, setDecisionErrors] = useState<Record<string, string>>({});
  const [followupStatuses, setFollowupStatuses] = useState<Record<string, FollowupStatus>>({});
  const [followupNotes, setFollowupNotes] = useState<Record<string, string>>({});
  const [followupPrerequisites, setFollowupPrerequisites] = useState<Record<string, boolean>>({});
  const [followups, setFollowups] = useState(() =>
    Object.fromEntries(items.filter(item => item.followup).map(item => [item.id, item.followup!])),
  );
  const [followupErrors, setFollowupErrors] = useState<Record<string, string>>({});

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
      const response = governedV1
        ? await submitV1GovernedIntention({
            analysis_id: reportId,
            recommendation_id: rec.id,
            status: option.status as 'planned' | 'unsure' | 'rejected' | 'no_longer_relevant',
            comment: comment || undefined,
          })
        : await submitDecisionFeedback({
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

  const confirmDecision = async (rec: RecommendationTracking) => {
    const kind = decisionKinds[rec.id];
    const decisionText = (decisionTexts[rec.id] || '').trim();
    if (!kind || !decisionText) {
      setDecisionErrors(prev => ({ ...prev, [rec.id]: 'Choisissez une décision et expliquez-la.' }));
      return;
    }
    if (kind !== 'rejected' && (rec.prerequisite_validation?.length ?? 0) > 0 && !acknowledged[rec.id]) {
      setDecisionErrors(prev => ({ ...prev, [rec.id]: 'Confirmez que les validations restent requises.' }));
      return;
    }
    setSaving(prev => ({ ...prev, [rec.id]: true }));
    setDecisionErrors(prev => ({ ...prev, [rec.id]: '' }));
    try {
      await submitV1GovernedDecision({
        analysis_id: reportId,
        recommendation_id: rec.id,
        decision_kind: kind,
        decision_text: decisionText,
        prerequisites_acknowledged: kind === 'rejected' ? false : Boolean(acknowledged[rec.id]),
      });
      setDecided(prev => ({ ...prev, [rec.id]: true }));
    } catch (error) {
      setDecisionErrors(prev => ({
        ...prev,
        [rec.id]: error instanceof Error ? error.message : 'Confirmation indisponible.',
      }));
    } finally {
      setSaving(prev => ({ ...prev, [rec.id]: false }));
    }
  };

  const recordFollowup = async (rec: RecommendationTracking) => {
    const status = followupStatuses[rec.id];
    const note = (followupNotes[rec.id] || '').trim();
    if (!status || !note) {
      setFollowupErrors(prev => ({ ...prev, [rec.id]: 'Choisissez un état et ajoutez une note professionnelle.' }));
      return;
    }
    if (status === 'completed' && (rec.prerequisite_validation?.length ?? 0) > 0 && !followupPrerequisites[rec.id]) {
      setFollowupErrors(prev => ({ ...prev, [rec.id]: 'Confirmez que les validations préalables sont accomplies.' }));
      return;
    }
    setSaving(prev => ({ ...prev, [rec.id]: true }));
    setFollowupErrors(prev => ({ ...prev, [rec.id]: '' }));
    try {
      await submitV1GovernedFollowup({
        analysis_id: reportId,
        recommendation_id: rec.id,
        followup_status: status,
        professional_note: note,
        prerequisites_confirmed_complete: Boolean(followupPrerequisites[rec.id]),
      });
      setFollowups(prev => ({ ...prev, [rec.id]: {
        followup_status: status,
        professional_note: note,
        prerequisites_confirmed_complete: Boolean(followupPrerequisites[rec.id]),
        confirmation_source: 'explicit',
        recorded_at: new Date().toISOString(),
      } }));
    } catch (error) {
      setFollowupErrors(prev => ({ ...prev, [rec.id]: error instanceof Error ? error.message : 'Suivi indisponible.' }));
    } finally {
      setSaving(prev => ({ ...prev, [rec.id]: false }));
    }
  };

  return (
    <div className="rounded-2xl border border-blue-200 bg-blue-50 overflow-hidden max-w-2xl">
      <div className="flex items-center gap-3 px-5 py-3.5 bg-blue-100 border-b border-blue-200">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 bg-[#1B73E8]">
          <span className="text-white text-sm">🎯</span>
        </div>
        <div>
          <p className="font-bold text-sm text-[#1A1A2E]">
            {governedV1 ? 'Quelle est votre intention ?' : 'Que comptez-vous faire ?'}
          </p>
          <p className="text-xs mt-0.5 text-[#5F6368]">
            {governedV1
              ? 'Votre réponse est enregistrée comme une intention, jamais comme une décision confirmée.'
              : 'Une réponse rapide m\'aide à adapter mes prochaines recommandations.'}
          </p>
        </div>
      </div>

      <div className="px-5 py-4 space-y-3">
        {items.map((rec) => {
          const choice = choices[rec.id];
          const isSaved = saved[rec.id];
          const needsComment = choice === 'rejected' || choice === 'unsure' || choice === 'no_longer_relevant';
          const isDecided = decided[rec.id];
          const decisionKind = decisionKinds[rec.id];
          const shownDecisionKind = rec.decision_kind || decisionKind;
          const shownDecisionText = rec.decision_text || decisionTexts[rec.id];
          const followup = followups[rec.id];

          return (
            <div key={rec.id} className="bg-white rounded-xl border border-blue-100 p-4">
              <p className="text-sm text-[#1A1A2E] leading-relaxed mb-3">{stripMarkdown(rec.text)}</p>

              {governedV1 && rec.rationale && (
                <div className="mb-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-700">
                  <span className="font-semibold">Pourquoi cette recommandation : </span>
                  {stripMarkdown(rec.rationale)}
                </div>
              )}

              {governedV1 && (rec.prerequisite_validation?.length ?? 0) > 0 && (
                <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                  <p className="text-xs font-semibold text-amber-900">Validations requises avant toute décision</p>
                  <ul className="mt-1 list-disc space-y-1 pl-4 text-xs text-amber-900">
                    {rec.prerequisite_validation!.map((item) => (
                      <li key={item}>{stripMarkdown(item)}</li>
                    ))}
                  </ul>
                </div>
              )}

              {governedV1 && (rec.fact_ids?.length ?? 0) > 0 && (
                <p className="mb-3 text-[11px] text-[#5F6368]">
                  Références factuelles : {rec.fact_ids!.join(', ')}
                </p>
              )}

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
                    {governedV1 ? 'Intention enregistrée — aucune décision confirmée.' : 'Merci, c\'est noté.'}
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

              {governedV1 && isSaved && !isDecided && (
                <div className="mt-4 border-t border-blue-100 pt-4">
                  <p className="text-sm font-semibold text-[#1A1A2E]">Formaliser une décision professionnelle</p>
                  <p className="mt-1 text-xs text-[#5F6368]">
                    Cette confirmation est explicite, distincte de votre intention et ne crée aucun arc décisionnel.
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {([
                      ['accepted_conditional', 'Retenir sous conditions'],
                      ['modified', 'Adapter'],
                      ['rejected', 'Ne pas retenir'],
                    ] as const).map(([kind, label]) => (
                      <button key={kind} type="button" onClick={() => setDecisionKinds(prev => ({ ...prev, [rec.id]: kind }))}
                        className={`rounded-lg border px-3 py-1.5 text-xs font-medium ${decisionKind === kind ? 'border-[#1B73E8] bg-[#1B73E8] text-white' : 'border-gray-200 bg-white'}`}>
                        {label}
                      </button>
                    ))}
                  </div>
                  <textarea aria-label="Motivation de la décision" value={decisionTexts[rec.id] || ''}
                    onChange={(event) => setDecisionTexts(prev => ({ ...prev, [rec.id]: event.target.value }))}
                    placeholder="Motivation professionnelle obligatoire"
                    className="mt-3 min-h-20 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                  {decisionKind !== 'rejected' && (rec.prerequisite_validation?.length ?? 0) > 0 && (
                    <label className="mt-2 flex items-start gap-2 text-xs text-amber-900">
                      <input type="checkbox" checked={Boolean(acknowledged[rec.id])}
                        onChange={(event) => setAcknowledged(prev => ({ ...prev, [rec.id]: event.target.checked }))} />
                      Je confirme que cette décision reste conditionnée aux validations ci-dessus.
                    </label>
                  )}
                  {decisionErrors[rec.id] && <p className="mt-2 text-xs text-red-700">{decisionErrors[rec.id]}</p>}
                  <button type="button" onClick={() => void confirmDecision(rec)} disabled={saving[rec.id]}
                    className="mt-3 rounded-lg bg-[#1A1A2E] px-3 py-2 text-xs font-bold text-white disabled:opacity-50">
                    Confirmer explicitement la décision
                  </button>
                </div>
              )}

              {governedV1 && isDecided && (
                <div className="mt-4 rounded-lg border border-green-200 bg-green-50 px-3 py-3 text-xs text-green-900">
                  <p className="font-semibold">Décision professionnelle confirmée explicitement</p>
                  <p className="mt-1">{shownDecisionKind === 'accepted_conditional' ? 'Retenue sous conditions' : shownDecisionKind === 'modified' ? 'Adaptée' : 'Non retenue'}</p>
                  {shownDecisionText && <p className="mt-1">{shownDecisionText}</p>}
                  <p className="mt-2 text-green-800">Aucun arc décisionnel n’a été créé.</p>
                </div>
              )}

              {governedV1 && isDecided && !followup && (
                <div className="mt-4 border-t border-blue-100 pt-4">
                  <p className="text-sm font-semibold text-[#1A1A2E]">Enregistrer le premier point de suivi</p>
                  <p className="mt-1 text-xs text-[#5F6368]">
                    Ce constat est explicite et immuable. Il ne modifie pas la décision et ne crée aucun arc décisionnel.
                  </p>
                  <label className="mt-3 block text-xs font-medium text-[#1A1A2E]" htmlFor={`followup-status-${rec.id}`}>État constaté</label>
                  <select id={`followup-status-${rec.id}`} aria-label="État du suivi"
                    value={followupStatuses[rec.id] || ''}
                    onChange={(event) => setFollowupStatuses(prev => ({ ...prev, [rec.id]: event.target.value as FollowupStatus }))}
                    className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm">
                    <option value="">Sélectionner</option>
                    <option value="pending_validation">En attente des validations</option>
                    <option value="in_progress">En cours</option>
                    <option value="blocked">Bloqué</option>
                    <option value="completed">Terminé</option>
                    <option value="not_pursued">Non poursuivi</option>
                  </select>
                  <textarea aria-label="Note professionnelle de suivi" value={followupNotes[rec.id] || ''}
                    onChange={(event) => setFollowupNotes(prev => ({ ...prev, [rec.id]: event.target.value }))}
                    placeholder="Éléments observés, obstacle ou prochaine vérification"
                    className="mt-3 min-h-20 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm" />
                  {followupStatuses[rec.id] === 'completed' && (rec.prerequisite_validation?.length ?? 0) > 0 && (
                    <label className="mt-2 flex items-start gap-2 text-xs text-amber-900">
                      <input type="checkbox" checked={Boolean(followupPrerequisites[rec.id])}
                        onChange={(event) => setFollowupPrerequisites(prev => ({ ...prev, [rec.id]: event.target.checked }))} />
                      Je confirme explicitement que les validations préalables sont accomplies.
                    </label>
                  )}
                  {followupErrors[rec.id] && <p className="mt-2 text-xs text-red-700">{followupErrors[rec.id]}</p>}
                  <button type="button" onClick={() => void recordFollowup(rec)} disabled={saving[rec.id]}
                    className="mt-3 rounded-lg bg-[#1A1A2E] px-3 py-2 text-xs font-bold text-white disabled:opacity-50">
                    Enregistrer explicitement le suivi
                  </button>
                </div>
              )}

              {governedV1 && followup && (
                <div className="mt-4 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-3 text-xs text-indigo-900">
                  <p className="font-semibold">Premier point de suivi enregistré explicitement</p>
                  <p className="mt-1">{{ pending_validation: 'En attente des validations', in_progress: 'En cours', blocked: 'Bloqué', completed: 'Terminé', not_pursued: 'Non poursuivi' }[followup.followup_status]}</p>
                  <p className="mt-1">{followup.professional_note}</p>
                  <p className="mt-2 text-indigo-800">Décision inchangée — aucun arc décisionnel créé.</p>
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
