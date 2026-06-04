'use client';
import { useState } from 'react';
import Link from 'next/link';

interface CoachingMessageProps {
  filename?: string;
  issues: string[];
  copilotPrompt?: string;
  canAnalyzePartially?: boolean;
  onAnalyzeAnyway?: () => void;
  variant?: 'blocked' | 'warning'; // warning = analyse effectuée mais avec limitations
}

export function CoachingMessage({
  filename,
  issues,
  copilotPrompt,
  canAnalyzePartially = false,
  onAnalyzeAnyway,
  variant = 'blocked',
}: CoachingMessageProps) {
  const [copied, setCopied] = useState(false);
  const [collapsed, setCollapsed] = useState(variant === 'warning'); // warning = réduit par défaut

  const isWarning = variant === 'warning';

  const handleCopy = async () => {
    if (!copilotPrompt) return;
    await navigator.clipboard.writeText(copilotPrompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className={`rounded-2xl border overflow-hidden max-w-2xl ${isWarning ? 'border-blue-200 bg-blue-50' : 'border-amber-200 bg-amber-50'}`}>

      {/* Header — cliquable pour réduire/expand en mode warning */}
      <div
        className={`flex items-center gap-3 px-5 py-3.5 border-b ${isWarning ? 'bg-blue-100 border-blue-200 cursor-pointer hover:bg-blue-200/60 transition-colors' : 'bg-amber-100 border-amber-200'}`}
        onClick={isWarning ? () => setCollapsed(v => !v) : undefined}
      >
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${isWarning ? 'bg-[#1B73E8]' : 'bg-amber-400'}`}>
          <span className="text-white text-sm">{isWarning ? '💬' : '🔍'}</span>
        </div>
        <div className="flex-1">
          <p className={`font-bold text-sm ${isWarning ? 'text-[#1A1A2E]' : 'text-amber-900'}`}>
            {isWarning ? 'Note sur la qualité de votre fichier' : 'Analyse préliminaire de votre fichier'}
          </p>
          {filename && <p className={`text-xs mt-0.5 font-medium ${isWarning ? 'text-[#5F6368]' : 'text-amber-700'}`}>{filename}</p>}
        </div>
        {isWarning && (
          <span className={`text-xs text-[#1B73E8] font-medium flex-shrink-0`}>
            {collapsed ? 'Voir le conseil →' : '← Réduire'}
          </span>
        )}
      </div>

      {!collapsed && <div className="px-5 py-4 space-y-4">

        {/* Message d'intro */}
        <p className={`text-sm leading-relaxed ${isWarning ? 'text-[#1A1A2E]' : 'text-amber-900'}`}>
          {isWarning
            ? <>J&apos;ai analysé votre fichier avec les données disponibles. Quelques éléments ont limité la précision sur certains points — <strong>c&apos;est courant et facilement corrigeable</strong> pour la prochaine analyse.</>
            : <>J&apos;ai examiné la structure de votre fichier avant de lancer l&apos;analyse. Il comporte quelques lacunes — <strong>rien d&apos;insurmontable, c&apos;est très courant</strong> — que je préfère vous signaler plutôt que de produire un résultat approximatif.</>
          }
        </p>

        {/* Problèmes détectés */}
        {issues.length > 0 && (
          <div className={`bg-white rounded-xl border p-4 ${isWarning ? 'border-blue-200' : 'border-amber-200'}`}>
            <p className={`text-xs font-bold uppercase tracking-wide mb-2 ${isWarning ? 'text-[#1B73E8]' : 'text-amber-800'}`}>
              Ce que j&apos;ai identifié
            </p>
            <ul className="space-y-1.5">
              {issues.map((issue, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-[#1A1A2E]">
                  <span className="text-amber-500 flex-shrink-0 mt-0.5">⚠️</span>
                  <span>{issue}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Pourquoi — uniquement pour les fichiers bloqués */}
        {!isWarning && (
          <p className="text-sm text-amber-800 leading-relaxed bg-white rounded-xl border border-amber-100 px-4 py-3">
            Plutôt que de vous livrer une analyse approximative qui pourrait induire en erreur vos décisions,
            je préfère vous guider pour corriger la structure. Cela prend 2 minutes et transforme
            la qualité de l&apos;analyse qui suivra.
          </p>
        )}

        {/* Prompt Copilot — l'action principale */}
        {copilotPrompt && (
          <div className="bg-[#1A1A2E] rounded-xl overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10">
              <div>
                <p className="text-xs font-bold text-white">Prompt prêt à l&apos;emploi</p>
                <p className="text-xs text-slate-400 mt-0.5">À coller dans Microsoft Copilot (Excel) ou ChatGPT avec votre fichier</p>
              </div>
              <button
                onClick={handleCopy}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  copied
                    ? 'bg-green-500 text-white'
                    : 'bg-[#1B73E8] text-white hover:bg-[#0D47A1]'
                }`}
              >
                {copied ? (
                  <>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                    Copié !
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copier le prompt
                  </>
                )}
              </button>
            </div>
            <div className="px-4 py-3 max-h-40 overflow-y-auto">
              <p className="text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap">
                {copilotPrompt}
              </p>
            </div>
          </div>
        )}

        {/* Étapes suivantes */}
        <div className="space-y-2">
          <p className="text-xs font-bold text-amber-800 uppercase tracking-wide">Que faire maintenant ?</p>
          <div className="space-y-2">
            <div className="flex items-start gap-3 p-3 bg-white rounded-xl border border-amber-100">
              <span className="w-5 h-5 bg-[#1B73E8] text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">1</span>
              <p className="text-sm text-[#1A1A2E]">
                {copilotPrompt
                  ? "Copiez le prompt ci-dessus et collez-le dans Copilot (Excel 365) ou ChatGPT en joignant votre fichier"
                  : "Ouvrez votre fichier dans Excel et ajoutez des en-têtes clairs à chaque colonne"}
              </p>
            </div>
            <div className="flex items-start gap-3 p-3 bg-white rounded-xl border border-amber-100">
              <span className="w-5 h-5 bg-[#1B73E8] text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">2</span>
              <p className="text-sm text-[#1A1A2E]">
                Consultez notre{' '}
                <Link href="/guide-donnees" className="text-[#1B73E8] underline font-medium hover:no-underline">
                  guide de préparation des données
                </Link>{' '}
                — 5 étapes illustrées, aucune compétence Excel requise
              </p>
            </div>
            <div className="flex items-start gap-3 p-3 bg-white rounded-xl border border-amber-100">
              <span className="w-5 h-5 bg-[#1B73E8] text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">3</span>
              <p className="text-sm text-[#1A1A2E]">
                Une fois votre fichier restructuré, uploadez-le à nouveau — l&apos;analyse prendra 60 secondes
              </p>
            </div>
          </div>
        </div>

        {/* Option analyse partielle */}
        {canAnalyzePartially && onAnalyzeAnyway && (
          <div className="border-t border-amber-200 pt-3">
            <button
              onClick={onAnalyzeAnyway}
              className="text-xs text-amber-700 hover:text-amber-900 underline transition-colors"
            >
              Analyser quand même avec les données disponibles (résultats partiels)
            </button>
          </div>
        )}

      </div>}
    </div>
  );
}
