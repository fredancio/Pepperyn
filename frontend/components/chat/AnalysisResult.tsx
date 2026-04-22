'use client';
import { useState } from 'react';
import type { AnalysisResult as AnalysisResultType } from '@/lib/types';
import { downloadExcel, downloadPdf, downloadPptx } from '@/lib/api';

type ExportFormat = 'excel' | 'pdf' | 'pptx' | null;

/**
 * Renders a string containing basic markdown (**bold**, *italic*, `code`)
 * as React inline elements. Used to display AI-generated text properly.
 */
function InlineMarkdown({ text }: { text: string }) {
  // Split on **bold**, *italic*, `code`, and separators like ~~~ or ---
  const parts: React.ReactNode[] = [];
  // Remove standalone separators (---, ~~~)
  const cleaned = text.replace(/^[-~]{3,}\s*$/gm, '').trim();
  // Tokenise: **bold**, *italic*, `code`
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = regex.exec(cleaned)) !== null) {
    if (match.index > lastIndex) {
      parts.push(cleaned.slice(lastIndex, match.index));
    }
    if (match[2]) {
      parts.push(<strong key={key++}>{match[2]}</strong>);
    } else if (match[3]) {
      parts.push(<em key={key++}>{match[3]}</em>);
    } else if (match[4]) {
      parts.push(<code key={key++} className="bg-gray-100 px-1 rounded text-xs font-mono">{match[4]}</code>);
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < cleaned.length) {
    parts.push(cleaned.slice(lastIndex));
  }
  return <>{parts}</>;
}

interface AnalysisResultProps {
  data: Record<string, unknown>;
  questionsRestantes?: number | null;
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M€`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}k€`;
  return `${value.toFixed(0)}€`;
}

function formatPct(value: number): string {
  return `${value.toFixed(1)}%`;
}

function ScoreCircle({ label, value }: { label: string; value: number }) {
  const color = value >= 8 ? '#2E7D32' : value >= 5 ? '#FF6B35' : '#DC2626';
  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className="w-14 h-14 rounded-full flex items-center justify-center border-4 font-bold text-lg"
        style={{ borderColor: color, color }}
      >
        {value}
      </div>
      <p className="text-xs text-[#5F6368] text-center">{label}</p>
    </div>
  );
}

function CollapseSection({ title, count, color, children, defaultOpen = true }: {
  title: string;
  count?: number;
  color: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-100 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${color}`} />
          <span className="text-sm font-semibold text-[#1A1A2E]">{title}</span>
          {count !== undefined && (
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              color.includes('red') ? 'bg-red-100 text-red-700' :
              color.includes('amber') ? 'bg-amber-100 text-amber-700' :
              color.includes('green') ? 'bg-green-100 text-green-700' :
              'bg-blue-100 text-blue-700'
            }`}>
              {count}
            </span>
          )}
        </div>
        <svg
          className={`w-4 h-4 text-[#5F6368] transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && <div className="p-4">{children}</div>}
    </div>
  );
}

export function AnalysisResult({ data, questionsRestantes }: AnalysisResultProps) {
  const result = data as unknown as AnalysisResultType & {
    resume_executif?: string;
    diagnostic_revenus?: string;
    diagnostic_couts?: string;
    diagnostic_marges?: string;
    ce_qui_a_change?: string[];
    alertes?: string[];
    problemes_critiques?: string[];
    opportunites_v3?: string[];
    plan_action?: string[];
    score_rentabilite?: number;
    score_risque?: number;
    score_structure?: number;
    decision?: string;
    memory_insight?: string;
    _questionsRestantes?: number;
    _memoryInsight?: string | null;
  };

  const [downloading, setDownloading] = useState<ExportFormat>(null);
  const [chosenFormat, setChosenFormat] = useState<ExportFormat>(null);
  const [exportError, setExportError] = useState<string>('');

  // Detect v3 format
  const isV3 = !!(result.resume_executif || result.decision || (result.problemes_critiques && result.problemes_critiques.length > 0));

  // Memory insight from metadata
  const memoryInsight = result.memory_insight || result._memoryInsight || null;
  const qRestantes = questionsRestantes !== undefined && questionsRestantes !== null
    ? questionsRestantes
    : (result._questionsRestantes ?? null);

  const triggerDownload = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownload = async (format: 'excel' | 'pdf' | 'pptx') => {
    if (!result.id || downloading) return;
    setExportError('');
    setDownloading(format);
    try {
      let blob: Blob;
      let filename: string;
      const base = result.excel_export_nom?.replace(/\.xlsx$/, '') || `pepperyn_analyse_${result.id.slice(0, 8)}`;

      if (format === 'excel') {
        blob = await downloadExcel(result.id);
        filename = `${base}.xlsx`;
      } else if (format === 'pdf') {
        blob = await downloadPdf(result.id);
        filename = `${base}.pdf`;
      } else {
        blob = await downloadPptx(result.id);
        filename = `${base}.pptx`;
      }

      triggerDownload(blob, filename);
      setChosenFormat(format);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Erreur inconnue';
      setExportError(msg);
    } finally {
      setDownloading(null);
    }
  };

  if (isV3) {
    /* ═══════════════════════════════════════
       V3 LAYOUT — Structure complète v3
    ═══════════════════════════════════════ */
    return (
      <div className="bg-white rounded-2xl rounded-tl-none shadow-sm border border-blue-100 overflow-hidden w-full max-w-2xl">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#1B73E8] to-[#0D47A1] px-5 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xs px-2 py-1 bg-white/20 rounded-lg text-white font-medium">
                {result.type_document || 'ANALYSE'}
              </span>
              <span className="text-blue-200 text-xs">
                Score de confiance : {result.score_confiance || 0}%
              </span>
            </div>
            {chosenFormat && (
              <span className="text-xs px-2 py-1 bg-white/20 rounded-lg text-white font-medium">
                ✓ {chosenFormat.toUpperCase()} téléchargé
              </span>
            )}
          </div>
        </div>

        <div className="p-4 flex flex-col gap-4">

          {/* Résumé Exécutif */}
          {result.resume_executif && (
            <div className="border-l-4 border-[#1B73E8] pl-4 py-2">
              <h3 className="font-bold text-[#1B73E8] text-sm mb-2">📊 RÉSUMÉ EXÉCUTIF</h3>
              <p className="text-sm text-[#1A1A2E] leading-relaxed"><InlineMarkdown text={result.resume_executif} /></p>
            </div>
          )}

          {/* Synthèse (fallback) */}
          {!result.resume_executif && result.synthese && (
            <div className="border-l-4 border-[#1B73E8] pl-4 py-2">
              <h3 className="font-bold text-[#1B73E8] text-sm mb-2">📊 RÉSUMÉ EXÉCUTIF</h3>
              <p className="text-sm text-[#1A1A2E] leading-relaxed"><InlineMarkdown text={result.synthese} /></p>
            </div>
          )}

          {/* Diagnostic Financier */}
          {(result.diagnostic_revenus || result.diagnostic_couts || result.diagnostic_marges || result.marges) && (
            <CollapseSection title="💹 DIAGNOSTIC FINANCIER" color="bg-blue-500">
              <div className="flex flex-col gap-2 text-sm text-[#1A1A2E]">
                {result.diagnostic_revenus && (
                  <div><span className="font-semibold">Revenus :</span> <InlineMarkdown text={result.diagnostic_revenus} /></div>
                )}
                {result.diagnostic_couts && (
                  <div><span className="font-semibold">Coûts :</span> <InlineMarkdown text={result.diagnostic_couts} /></div>
                )}
                {result.diagnostic_marges && (
                  <div><span className="font-semibold">Marges :</span> <InlineMarkdown text={result.diagnostic_marges} /></div>
                )}
                {!result.diagnostic_revenus && result.marges && (
                  <div className="grid grid-cols-3 gap-3 mt-2">
                    {[
                      { label: 'Marge brute', value: result.marges.brute_pct !== undefined ? formatPct(result.marges.brute_pct) : '—', sub: result.marges.brute !== undefined ? formatCurrency(result.marges.brute) : '' },
                      { label: 'Marge opér.', value: result.marges.operationnelle_pct !== undefined ? formatPct(result.marges.operationnelle_pct) : '—', sub: result.marges.operationnelle !== undefined ? formatCurrency(result.marges.operationnelle) : '' },
                      { label: 'Marge nette', value: result.marges.nette_pct !== undefined ? formatPct(result.marges.nette_pct) : '—', sub: result.marges.nette !== undefined ? formatCurrency(result.marges.nette) : '' },
                    ].map((kpi, i) => (
                      <div key={i} className="bg-gray-50 rounded-xl p-3 text-center">
                        <p className="text-xs text-[#5F6368] mb-1">{kpi.label}</p>
                        <p className="text-lg font-bold text-[#1A1A2E]">{kpi.value}</p>
                        {kpi.sub && <p className="text-xs text-[#5F6368]">{kpi.sub}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CollapseSection>
          )}

          {/* CE QUI A CHANGÉ */}
          {result.ce_qui_a_change && result.ce_qui_a_change.length > 0 && (
            <CollapseSection title="🔄 CE QUI A CHANGÉ" color="bg-amber-500">
              <div className="flex flex-col gap-2">
                {result.ce_qui_a_change.map((item, i) => (
                  <div key={i} className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-100 rounded-lg text-sm text-[#1A1A2E]">
                    <span className="flex-shrink-0">🔄</span>
                    <span><InlineMarkdown text={item} /></span>
                  </div>
                ))}
              </div>
            </CollapseSection>
          )}

          {/* ALERTES */}
          {result.alertes && result.alertes.length > 0 && (
            <CollapseSection title="⚠️ ALERTES" count={result.alertes.length} color="bg-orange-500">
              <div className="flex flex-col gap-2">
                {result.alertes.map((alerte, i) => (
                  <div key={i} className="flex items-start gap-2 p-3 bg-orange-50 border border-orange-200 rounded-lg text-sm text-[#1A1A2E]">
                    <span className="flex-shrink-0">⚠️</span>
                    <span><InlineMarkdown text={alerte} /></span>
                  </div>
                ))}
              </div>
            </CollapseSection>
          )}

          {/* Problèmes Critiques */}
          {result.problemes_critiques && result.problemes_critiques.length > 0 && (
            <CollapseSection
              title="🔴 PROBLÈMES CRITIQUES"
              count={result.problemes_critiques.length}
              color="bg-red-500"
            >
              <div className="flex flex-col gap-2">
                {result.problemes_critiques.map((p, i) => (
                  <div key={i} className="flex items-start gap-2 p-3 bg-red-50 border border-red-100 rounded-lg text-sm text-[#1A1A2E]">
                    <span className="text-red-500 flex-shrink-0">🔴</span>
                    <span><InlineMarkdown text={p.replace(/^🔴\s*/, '')} /></span>
                  </div>
                ))}
              </div>
            </CollapseSection>
          )}

          {/* Fallback: Anomalies (old format) */}
          {(!result.problemes_critiques || result.problemes_critiques.length === 0) && result.anomalies && result.anomalies.length > 0 && (
            <CollapseSection title="🔴 PROBLÈMES DÉTECTÉS" count={result.anomalies.length} color="bg-red-500">
              <div className="flex flex-col gap-2">
                {result.anomalies.map((anomaly, i) => (
                  <div key={i} className={`flex items-start gap-2 p-3 rounded-lg text-sm ${
                    anomaly.severity === 'high' ? 'bg-red-50 border border-red-100' :
                    anomaly.severity === 'medium' ? 'bg-amber-50 border border-amber-100' :
                    'bg-gray-50 border border-gray-100'
                  }`}>
                    <span>🔴</span>
                    <div>
                      <p className="text-[#1A1A2E]">{anomaly.description}</p>
                      {anomaly.impact && <p className="text-xs text-[#5F6368] mt-0.5">Impact : {anomaly.impact}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </CollapseSection>
          )}

          {/* Opportunités v3 */}
          {result.opportunites_v3 && result.opportunites_v3.length > 0 && (
            <CollapseSection
              title="🟢 OPPORTUNITÉS"
              count={result.opportunites_v3.length}
              color="bg-green-500"
            >
              <div className="flex flex-col gap-2">
                {result.opportunites_v3.map((o, i) => (
                  <div key={i} className="flex items-start gap-2 p-3 bg-green-50 border border-green-100 rounded-lg text-sm text-[#1A1A2E]">
                    <span className="text-green-500 flex-shrink-0">🟢</span>
                    <span><InlineMarkdown text={o.replace(/^🟢\s*/, '')} /></span>
                  </div>
                ))}
              </div>
            </CollapseSection>
          )}

          {/* Fallback: Opportunités (old format) */}
          {(!result.opportunites_v3 || result.opportunites_v3.length === 0) && result.opportunites && result.opportunites.length > 0 && (
            <CollapseSection title="🟢 OPPORTUNITÉS" count={result.opportunites.length} color="bg-green-500">
              <div className="flex flex-col gap-2">
                {result.opportunites.map((opp, i) => (
                  <div key={i} className="flex items-start gap-2 p-3 bg-green-50 border border-green-100 rounded-lg text-sm">
                    <span>🟢</span>
                    <div>
                      <p className="text-[#1A1A2E]">{opp.description}</p>
                      {opp.potentiel && <p className="text-xs text-[#5F6368] mt-0.5">Potentiel : {opp.potentiel}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </CollapseSection>
          )}

          {/* Plan d'action */}
          {result.plan_action && result.plan_action.length > 0 && (
            <CollapseSection title="🎯 PLAN D'ACTION" color="bg-[#1B73E8]">
              <div className="flex flex-col gap-2">
                {result.plan_action.map((action, i) => {
                  const isHaute = action.toLowerCase().includes('priorité haute') || action.toLowerCase().includes('priorité: haute');
                  const isMoyenne = action.toLowerCase().includes('priorité moyenne') || action.toLowerCase().includes('priorité: moyenne');
                  return (
                    <div key={i} className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-100 rounded-lg text-sm">
                      <span className={`px-1.5 py-0.5 rounded text-xs font-bold flex-shrink-0 mt-0.5 ${
                        isHaute ? 'bg-red-100 text-red-700' :
                        isMoyenne ? 'bg-amber-100 text-amber-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {isHaute ? 'HAUTE' : isMoyenne ? 'MOY.' : '—'}
                      </span>
                      <span className="text-[#1A1A2E]"><InlineMarkdown text={action} /></span>
                    </div>
                  );
                })}
              </div>
            </CollapseSection>
          )}

          {/* Fallback: Recommandations (old format) */}
          {(!result.plan_action || result.plan_action.length === 0) && result.recommandations && result.recommandations.length > 0 && (
            <CollapseSection title="🎯 RECOMMANDATIONS" count={result.recommandations.length} color="bg-[#1B73E8]">
              <div className="flex flex-col gap-3">
                {result.recommandations.map((rec, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-100 rounded-lg">
                    <div className={`px-2 py-0.5 rounded text-xs font-bold flex-shrink-0 ${
                      rec.priorite === 'haute' ? 'bg-red-100 text-red-700' :
                      rec.priorite === 'moyenne' ? 'bg-amber-100 text-amber-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {rec.priorite.toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-[#1A1A2E] font-medium">{rec.action}</p>
                      <div className="flex gap-3 mt-1">
                        {rec.impact_estime && <span className="text-xs text-[#5F6368]">Impact : {rec.impact_estime}</span>}
                        {rec.delai && <span className="text-xs text-[#5F6368]">Délai : {rec.delai}</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CollapseSection>
          )}

          {/* Scores /10 */}
          {(result.score_rentabilite != null || result.score_risque != null || result.score_structure != null) && (
            <div className="flex justify-around py-4 border border-gray-100 rounded-xl">
              {result.score_rentabilite != null && (
                <ScoreCircle label="Rentabilité" value={result.score_rentabilite as number} />
              )}
              {result.score_risque != null && (
                <ScoreCircle label="Risque" value={result.score_risque as number} />
              )}
              {result.score_structure != null && (
                <ScoreCircle label="Structure" value={result.score_structure as number} />
              )}
            </div>
          )}

          {/* Décision */}
          {result.decision && (
            <div className="bg-[#EFF6FF] border border-[#1B73E8]/30 rounded-xl p-4">
              <h3 className="font-bold text-[#1B73E8] text-sm mb-2">⚡ DÉCISION</h3>
              <p className="text-sm text-[#1A1A2E] font-medium leading-relaxed"><InlineMarkdown text={result.decision as string} /></p>
            </div>
          )}

          {/* Memory Insight */}
          {memoryInsight && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <h3 className="font-bold text-amber-800 text-sm mb-2">🔥 CE QUI A CHANGÉ</h3>
              <p className="text-sm text-amber-900 leading-relaxed">{memoryInsight}</p>
            </div>
          )}

          {/* Export buttons */}
          {result.id && (
            <div className="flex flex-col gap-2">
              {/* Info — un seul format */}
              {!chosenFormat && (
                <p className="text-center text-xs text-[#5F6368] mb-1">
                  Choisissez votre format d'export — <strong>un seul choix possible</strong> par analyse
                </p>
              )}
              {chosenFormat && (
                <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-xl px-4 py-2.5">
                  <span className="text-green-600 text-sm font-semibold">✓ Export {chosenFormat.toUpperCase()} téléchargé</span>
                  <span className="text-xs text-[#5F6368] ml-auto">Les autres formats sont verrouillés</span>
                </div>
              )}

              {exportError && (
                <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-2.5">
                  <p className="text-xs text-red-600">{exportError}</p>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {/* Excel */}
                <button
                  onClick={() => handleDownload('excel')}
                  disabled={!!downloading || (!!chosenFormat && chosenFormat !== 'excel')}
                  className={`py-3 rounded-xl text-sm font-medium flex flex-col items-center justify-center gap-1 transition-colors
                    ${chosenFormat === 'excel'
                      ? 'bg-green-100 border-2 border-green-400 text-green-800 cursor-default'
                      : chosenFormat !== null
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed opacity-50'
                        : 'bg-[#1B73E8] text-white hover:bg-[#0D47A1] disabled:opacity-60'
                    }`}
                >
                  <span className="text-lg">📊</span>
                  <span className="text-xs">
                    {downloading === 'excel' ? 'Génération...' : chosenFormat === 'excel' ? '✓ Excel' : 'Excel (.xlsx)'}
                  </span>
                </button>

                {/* PDF */}
                <button
                  onClick={() => handleDownload('pdf')}
                  disabled={!!downloading || (!!chosenFormat && chosenFormat !== 'pdf')}
                  className={`py-3 rounded-xl text-sm font-medium flex flex-col items-center justify-center gap-1 transition-colors
                    ${chosenFormat === 'pdf'
                      ? 'bg-green-100 border-2 border-green-400 text-green-800 cursor-default'
                      : chosenFormat !== null
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed opacity-50'
                        : 'bg-red-600 text-white hover:bg-red-700 disabled:opacity-60'
                    }`}
                >
                  <span className="text-lg">📄</span>
                  <span className="text-xs">
                    {downloading === 'pdf' ? 'Génération...' : chosenFormat === 'pdf' ? '✓ PDF' : 'PDF (.pdf)'}
                  </span>
                </button>

                {/* PowerPoint */}
                <button
                  onClick={() => handleDownload('pptx')}
                  disabled={!!downloading || (!!chosenFormat && chosenFormat !== 'pptx')}
                  className={`py-3 rounded-xl text-sm font-medium flex flex-col items-center justify-center gap-1 transition-colors
                    ${chosenFormat === 'pptx'
                      ? 'bg-green-100 border-2 border-green-400 text-green-800 cursor-default'
                      : chosenFormat !== null
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed opacity-50'
                        : 'bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-60'
                    }`}
                >
                  <span className="text-lg">📑</span>
                  <span className="text-xs">
                    {downloading === 'pptx' ? 'Génération...' : chosenFormat === 'pptx' ? '✓ PowerPoint' : 'PowerPoint'}
                  </span>
                </button>
              </div>
            </div>
          )}

          {/* Compteur questions restantes */}
          {qRestantes !== null && (
            <p className="text-center text-xs text-[#5F6368]">
              Questions restantes dans cette session : {qRestantes}/{5}
            </p>
          )}
        </div>
      </div>
    );
  }

  /* ═══════════════════════════════════════
     LAYOUT CLASSIQUE (ancien format JSON)
  ═══════════════════════════════════════ */
  return (
    <div className="bg-white rounded-2xl rounded-tl-none shadow-sm border border-gray-100 overflow-hidden w-full max-w-2xl">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#1B73E8] to-[#0D47A1] px-5 py-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white font-semibold text-sm">Analyse financière complète</p>
            <p className="text-blue-200 text-xs mt-0.5">
              {result.type_document} · Confiance : {Math.round(result.score_confiance * 100)}%
            </p>
          </div>
          <div className="flex items-center gap-2">
            {chosenFormat && (
              <span className="text-xs px-2 py-1 bg-white/20 rounded-lg text-white font-medium">
                ✓ {chosenFormat.toUpperCase()}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="p-4 flex flex-col gap-4">
        {result.synthese && (
          <div className="bg-[#EFF6FF] border border-blue-100 rounded-xl p-4">
            <p className="text-sm font-semibold text-[#1A1A2E] mb-1.5">Synthèse exécutive</p>
            <p className="text-sm text-[#5F6368] leading-relaxed">{result.synthese}</p>
          </div>
        )}

        {result.marges && (
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Marge brute', value: result.marges.brute_pct !== undefined ? formatPct(result.marges.brute_pct) : '—', sub: result.marges.brute !== undefined ? formatCurrency(result.marges.brute) : '' },
              { label: 'Marge opér.', value: result.marges.operationnelle_pct !== undefined ? formatPct(result.marges.operationnelle_pct) : '—', sub: result.marges.operationnelle !== undefined ? formatCurrency(result.marges.operationnelle) : '' },
              { label: 'Marge nette', value: result.marges.nette_pct !== undefined ? formatPct(result.marges.nette_pct) : '—', sub: result.marges.nette !== undefined ? formatCurrency(result.marges.nette) : '' },
            ].map((kpi, i) => (
              <div key={i} className="bg-gray-50 rounded-xl p-3 text-center">
                <p className="text-xs text-[#5F6368] mb-1">{kpi.label}</p>
                <p className="text-lg font-bold text-[#1A1A2E]">{kpi.value}</p>
                {kpi.sub && <p className="text-xs text-[#5F6368]">{kpi.sub}</p>}
              </div>
            ))}
          </div>
        )}

        {result.anomalies && result.anomalies.length > 0 && (
          <CollapseSection title="Anomalies détectées" count={result.anomalies.length} color="bg-red-500">
            <div className="flex flex-col gap-2">
              {result.anomalies.map((anomaly, i) => (
                <div key={i} className={`flex items-start gap-2 p-3 rounded-lg text-sm ${
                  anomaly.severity === 'high' ? 'bg-red-50 border border-red-100' :
                  anomaly.severity === 'medium' ? 'bg-amber-50 border border-amber-100' :
                  'bg-gray-50 border border-gray-100'
                }`}>
                  <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                    anomaly.severity === 'high' ? 'bg-red-500' :
                    anomaly.severity === 'medium' ? 'bg-amber-500' : 'bg-gray-400'
                  }`} />
                  <div>
                    <p className="text-[#1A1A2E]">{anomaly.description}</p>
                    {anomaly.impact && <p className="text-xs text-[#5F6368] mt-0.5">Impact : {anomaly.impact}</p>}
                  </div>
                </div>
              ))}
            </div>
          </CollapseSection>
        )}

        {result.recommandations && result.recommandations.length > 0 && (
          <CollapseSection title="Recommandations" count={result.recommandations.length} color="bg-[#1B73E8]">
            <div className="flex flex-col gap-3">
              {result.recommandations.map((rec, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-100 rounded-lg">
                  <div className={`px-2 py-0.5 rounded text-xs font-bold flex-shrink-0 ${
                    rec.priorite === 'haute' ? 'bg-red-100 text-red-700' :
                    rec.priorite === 'moyenne' ? 'bg-amber-100 text-amber-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {rec.priorite.toUpperCase()}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-[#1A1A2E] font-medium">{rec.action}</p>
                    <div className="flex gap-3 mt-1">
                      {rec.impact_estime && <span className="text-xs text-[#5F6368]">Impact : {rec.impact_estime}</span>}
                      {rec.delai && <span className="text-xs text-[#5F6368]">Délai : {rec.delai}</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CollapseSection>
        )}

        {memoryInsight && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <h3 className="font-bold text-amber-800 text-sm mb-2">🔥 CE QUI A CHANGÉ</h3>
            <p className="text-sm text-amber-900 leading-relaxed">{memoryInsight}</p>
          </div>
        )}

        {qRestantes !== null && (
          <p className="text-center text-xs text-[#5F6368]">
            Questions restantes dans cette session : {qRestantes}/{5}
          </p>
        )}
      </div>
    </div>
  );
}
