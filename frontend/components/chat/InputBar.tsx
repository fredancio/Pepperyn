'use client';
import { useState, useRef, KeyboardEvent } from 'react';
import { FileUploadZone } from './FileUploadZone';
import { GuidedOnboarding } from './GuidedOnboarding';

interface InputBarProps {
  onSendMessage: (text: string) => void;
  onSendFile: (file: File, context: string, mode: 'quick' | 'complete', analysisPeriodMonths: number, targetDate: string) => void;
  disabled?: boolean;
  placeholder?: string;
  uploadOnly?: boolean;
  onFileChange?: (file: File | null) => void;
  plan?: string;
}

type TargetPreset = 'end_year' | 'plus_6m' | 'plus_12m' | 'custom';

function computeTargetDate(preset: TargetPreset, customDate: string): string {
  const now = new Date();
  if (preset === 'end_year') return `${now.getFullYear()}-12-31`;
  if (preset === 'plus_6m') {
    const d = new Date(now); d.setMonth(d.getMonth() + 6);
    return d.toISOString().split('T')[0];
  }
  if (preset === 'plus_12m') {
    const d = new Date(now); d.setFullYear(d.getFullYear() + 1);
    return d.toISOString().split('T')[0];
  }
  // custom — customDate is YYYY-MM, convert to last day of that month
  if (customDate) {
    const [y, m] = customDate.split('-').map(Number);
    const lastDay = new Date(y, m, 0).getDate();
    return `${y}-${String(m).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
  }
  return '';
}

export function InputBar({ onSendMessage, onSendFile, disabled, placeholder, uploadOnly, onFileChange, plan = 'free' }: InputBarProps) {
  const [text, setText] = useState('');
  const [showFileZone, setShowFileZone] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [mode, setMode] = useState<'quick' | 'complete'>('complete');
  const [showGuide, setShowGuide] = useState(false);
  // Période couverte par le fichier (en mois)
  const [analysisPeriodMonths, setAnalysisPeriodMonths] = useState<number>(12);
  const [isPeriodCustom, setIsPeriodCustom] = useState<boolean>(false);
  const [periodCustomMonths, setPeriodCustomMonths] = useState<number>(18);
  // Objectif de projection
  const [targetPreset, setTargetPreset] = useState<TargetPreset>('plus_12m');
  const [targetCustomDate, setTargetCustomDate] = useState<string>('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const currentYear = new Date().getFullYear();

  const handleSendText = () => {
    if (!text.trim() || disabled) return;
    onSendMessage(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    // Auto-resize textarea
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setShowFileZone(false);
    onFileChange?.(file);
  };

  const handleSendFile = () => {
    if (!selectedFile || disabled) return;
    const targetDate = computeTargetDate(targetPreset, targetCustomDate);
    onSendFile(selectedFile, '', mode, analysisPeriodMonths, targetDate);
    setSelectedFile(null);
    setTargetPreset('plus_12m');
    setTargetCustomDate('');
    setAnalysisPeriodMonths(12);
    setIsPeriodCustom(false);
    setPeriodCustomMonths(18);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    onFileChange?.(null);
  };

  // Mode uploadOnly — zone de dépôt + "Lancer l'analyse" toujours visible
  if (uploadOnly) {
    return (
      <div className="flex flex-col gap-3">
        {/* Upload zone or file preview */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          {!selectedFile ? (
            /* Upload zone enhanced */
            <div>
              <FileUploadZone onFileSelect={handleFileSelect} disabled={disabled} />
              {/* Formats + examples */}
              <div className="px-4 pb-4 flex flex-col gap-2">
                <div className="flex flex-wrap gap-1.5 justify-center">
                  {['Excel (.xlsx)', 'CSV', 'Export ERP'].map(f => (
                    <span key={f} className="text-xs px-2.5 py-1 bg-gray-50 border border-gray-200 rounded-full text-[#5F6368]">{f}</span>
                  ))}
                </div>
                <p className="text-xs text-center text-[#5F6368]/70">
                  Ex: P&amp;L · Budget · Export comptabilité
                </p>
              </div>
            </div>
          ) : (
            /* File selected — period + target + mode */
            <div className="p-4 flex flex-col gap-4">
              {/* File chip */}
              <div className="flex items-center justify-between bg-[#EFF6FF] border border-blue-100 rounded-xl px-3 py-2.5">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-[#1B73E8]/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[#1A1A2E] truncate max-w-[200px]">{selectedFile.name}</p>
                    <p className="text-xs text-[#5F6368]">{(selectedFile.size / 1024).toFixed(0)} Ko · prêt à analyser</p>
                  </div>
                </div>
                <button onClick={handleRemoveFile} className="w-7 h-7 flex items-center justify-center text-[#5F6368] hover:text-red-500 transition-colors flex-shrink-0">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Période couverte */}
              <div>
                <p className="text-xs font-semibold text-[#1A1A2E] mb-2">
                  📅 Vos données couvrent quelle période ?
                </p>
                <div className="flex gap-1.5 flex-wrap">
                  {Array.from({length: 12}, (_, i) => i + 1).map(m => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => { setIsPeriodCustom(false); setAnalysisPeriodMonths(m); }}
                      className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
                        !isPeriodCustom && analysisPeriodMonths === m
                          ? 'bg-[#1B73E8] border-[#1B73E8] text-white shadow-sm'
                          : 'bg-white border-gray-200 text-[#5F6368] hover:border-[#1B73E8]/50 hover:text-[#1A1A2E]'
                      }`}
                    >
                      {m === 12 ? '12 mois (année)' : `${m} mois`}
                    </button>
                  ))}
                  <button
                    type="button"
                    onClick={() => { setIsPeriodCustom(true); setAnalysisPeriodMonths(periodCustomMonths); }}
                    className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
                      isPeriodCustom
                        ? 'bg-[#1B73E8] border-[#1B73E8] text-white shadow-sm'
                        : 'bg-white border-gray-200 text-[#5F6368] hover:border-[#1B73E8]/50 hover:text-[#1A1A2E]'
                    }`}
                  >
                    + de 12 mois
                  </button>
                </div>
                {isPeriodCustom && (
                  <div className="mt-2 flex items-center gap-2">
                    <input
                      type="number"
                      min={13}
                      max={120}
                      value={periodCustomMonths}
                      onChange={e => {
                        const v = Math.max(13, Math.min(120, Number(e.target.value) || 13));
                        setPeriodCustomMonths(v);
                        setAnalysisPeriodMonths(v);
                      }}
                      className="w-20 text-sm bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-[#1A1A2E] focus:outline-none focus:ring-1 focus:ring-[#1B73E8] focus:border-[#1B73E8]"
                    />
                    <span className="text-xs text-[#5F6368]">mois (ex : 18 = 1 an et demi, 24 = 2 ans…)</span>
                  </div>
                )}
              </div>

              {/* Objectif */}
              <div>
                <p className="text-xs font-semibold text-[#1A1A2E] mb-2">
                  🎯 Jusqu&apos;à quand souhaitez-vous projeter vos objectifs ?
                </p>
                <div className="flex gap-1.5 flex-wrap">
                  {([
                    { preset: 'end_year' as TargetPreset, label: `Fin ${currentYear}` },
                    { preset: 'plus_6m'  as TargetPreset, label: '+6 mois' },
                    { preset: 'plus_12m' as TargetPreset, label: '+12 mois' },
                    { preset: 'custom'   as TargetPreset, label: 'Date libre' },
                  ]).map(({ preset, label }) => (
                    <button
                      key={preset}
                      type="button"
                      onClick={() => setTargetPreset(preset)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
                        targetPreset === preset
                          ? 'bg-[#1B73E8] border-[#1B73E8] text-white shadow-sm'
                          : 'bg-white border-gray-200 text-[#5F6368] hover:border-[#1B73E8]/50 hover:text-[#1A1A2E]'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                {targetPreset === 'custom' && (
                  <input
                    type="month"
                    value={targetCustomDate}
                    onChange={e => setTargetCustomDate(e.target.value)}
                    min={`${currentYear}-01`}
                    max={`${currentYear + 5}-12`}
                    className="mt-2 w-full text-sm bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-[#1A1A2E] focus:outline-none focus:ring-1 focus:ring-[#1B73E8] focus:border-[#1B73E8]"
                  />
                )}
              </div>

              {/* Mode rapide / complet */}
              <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
                {(['quick', 'complete'] as const).map(m => (
                  <button key={m} onClick={() => setMode(m)}
                    className={`flex-1 px-3 py-1.5 text-xs font-medium rounded transition-all duration-150 ${mode === m ? 'bg-white text-[#1B73E8] shadow-sm' : 'text-[#5F6368] hover:text-[#1A1A2E]'}`}>
                    {m === 'quick' ? '⚡ Rapide' : '🔍 Analyse complète'}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* CTA — toujours visible, désactivé si pas de fichier */}
        <button
          onClick={handleSendFile}
          disabled={!selectedFile || disabled}
          className="w-full py-4 bg-[#1B73E8] text-white rounded-2xl font-bold text-base hover:bg-[#0D47A1] transition-all duration-200 shadow-lg shadow-blue-500/20 disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none"
        >
          {disabled ? 'Analyse en cours...' : 'Lancer l\'analyse'}
        </button>

        {/* Trust — sur une seule ligne */}
        <div className="flex items-center justify-center gap-4 flex-wrap">
          {[
            { icon: '🔒', label: 'Données chiffrées' },
            { icon: '🔒', label: 'Jamais revendues' },
            { icon: '🔒', label: 'Suppression intégrale possible à tout moment' },
          ].map(t => (
            <span key={t.label} className="flex items-center gap-1 text-xs text-[#5F6368]">
              <span>{t.icon}</span>
              <span>{t.label}</span>
            </span>
          ))}
        </div>

        {plan === 'free' && (
          <p className="text-center text-xs text-[#5F6368]">
            1 analyse gratuite · sans CB
          </p>
        )}

        {/* Bouton guide de démarrage */}
        <div>
          <button
            onClick={() => setShowGuide(v => !v)}
            className="w-full flex items-center justify-center px-4 py-2.5 bg-white border border-[#1B73E8]/40 rounded-xl text-sm text-[#1B73E8] font-medium hover:bg-[#EFF6FF] hover:border-[#1B73E8]/70 transition-all"
          >
            {showGuide
              ? 'Fermer le guide de démarrage'
              : 'Fichiers complexes ou première analyse ? Je vous guide pas à pas →'}
          </button>

          {showGuide && (
            <div className="mt-2">
              <GuidedOnboarding onClose={() => setShowGuide(false)} />
            </div>
          )}
        </div>

        {/* Bouton guide de préparation */}
        <a
          href="/guide-donnees"
          className="w-full flex flex-col px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl hover:bg-amber-100 hover:border-amber-300 transition-all group"
        >
          <span className="text-xs text-amber-800 font-semibold">Un fichier bien structuré, c&apos;est une analyse fiable et exploitable.</span>
          <span className="text-xs text-amber-700 group-hover:underline mt-0.5">Consulter le guide de préparation des données →</span>
        </a>
      </div>
    );
  }

  return (
    <div className="border-t border-gray-100 bg-white pb-safe">
      {/* File upload zone */}
      {showFileZone && !selectedFile && (
        <div className="p-4 border-b border-gray-100">
          <FileUploadZone onFileSelect={handleFileSelect} disabled={disabled} />
        </div>
      )}

      {/* Selected file preview */}
      {selectedFile && (
        <div className="px-4 pt-4">
          <div className="bg-[#EFF6FF] border border-blue-100 rounded-xl p-3">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 bg-[#1B73E8]/10 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-[#1A1A2E] truncate max-w-[200px]">{selectedFile.name}</p>
                  <p className="text-xs text-[#5F6368]">{(selectedFile.size / 1024).toFixed(0)} Ko</p>
                </div>
              </div>
              <button
                onClick={handleRemoveFile}
                className="w-7 h-7 flex items-center justify-center text-[#5F6368] hover:text-red-500 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Période + Objectif (compact pour le mode conversation) */}
            <div className="flex flex-wrap gap-1 mb-2">
              <span className="text-xs text-[#5F6368] self-center mr-1">Période :</span>
              {Array.from({length: 12}, (_, i) => i + 1).map(m => (
                <button key={m} type="button" onClick={() => { setIsPeriodCustom(false); setAnalysisPeriodMonths(m); }}
                  className={`px-2 py-0.5 text-xs rounded border transition-all ${!isPeriodCustom && analysisPeriodMonths === m ? 'bg-[#1B73E8] border-[#1B73E8] text-white' : 'bg-white border-gray-200 text-[#5F6368]'}`}>
                  {`${m}m`}
                </button>
              ))}
              <button type="button" onClick={() => { setIsPeriodCustom(true); setAnalysisPeriodMonths(periodCustomMonths); }}
                className={`px-2 py-0.5 text-xs rounded border transition-all ${isPeriodCustom ? 'bg-[#1B73E8] border-[#1B73E8] text-white' : 'bg-white border-gray-200 text-[#5F6368]'}`}>
                +12m
              </button>
              <span className="text-xs text-[#5F6368] self-center ml-2 mr-1">Objectif :</span>
              {([
                { preset: 'end_year' as TargetPreset, label: `Fin ${currentYear}` },
                { preset: 'plus_6m'  as TargetPreset, label: '+6m' },
                { preset: 'plus_12m' as TargetPreset, label: '+12m' },
                { preset: 'custom'   as TargetPreset, label: '📅' },
              ]).map(({ preset, label }) => (
                <button key={preset} type="button" onClick={() => setTargetPreset(preset)}
                  className={`px-2 py-0.5 text-xs rounded border transition-all ${targetPreset === preset ? 'bg-[#1B73E8] border-[#1B73E8] text-white' : 'bg-white border-gray-200 text-[#5F6368]'}`}>
                  {label}
                </button>
              ))}
            </div>
            {isPeriodCustom && (
              <div className="flex items-center gap-2 mt-1 mb-1">
                <input
                  type="number"
                  min={13}
                  max={120}
                  value={periodCustomMonths}
                  onChange={e => {
                    const v = Math.max(13, Math.min(120, Number(e.target.value) || 13));
                    setPeriodCustomMonths(v);
                    setAnalysisPeriodMonths(v);
                  }}
                  className="w-16 text-xs bg-white border border-gray-200 rounded-lg px-2 py-1 text-[#1A1A2E] focus:outline-none focus:ring-1 focus:ring-[#1B73E8]"
                />
                <span className="text-xs text-[#5F6368]">mois</span>
              </div>
            )}
            {targetPreset === 'custom' && (
              <input type="month" value={targetCustomDate} onChange={e => setTargetCustomDate(e.target.value)}
                min={`${currentYear}-01`} max={`${currentYear + 5}-12`}
                className="w-full text-xs bg-white border border-gray-200 rounded-lg px-2 py-1.5 text-[#1A1A2E] focus:outline-none focus:ring-1 focus:ring-[#1B73E8] mb-2" />
            )}

            {/* Mode toggle + send */}
            <div className="flex items-center justify-between gap-3">
              <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
                {(['quick', 'complete'] as const).map(m => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    className={`px-3 py-1.5 text-xs font-medium rounded transition-all duration-150 ${
                      mode === m
                        ? 'bg-white text-[#1B73E8] shadow-sm'
                        : 'text-[#5F6368] hover:text-[#1A1A2E]'
                    }`}
                  >
                    {m === 'quick' ? '⚡ Rapide' : '🔍 Complet'}
                  </button>
                ))}
              </div>

              <button
                onClick={handleSendFile}
                disabled={disabled}
                className="flex items-center gap-2 px-4 py-2 bg-[#1B73E8] text-white text-sm font-medium rounded-xl hover:bg-[#0D47A1] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17H3a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2h-2" />
                </svg>
                Analyser
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Text input row */}
      <div className="flex items-end gap-2 p-3">
        {/* File upload button */}
        <button
          onClick={() => { setShowFileZone(!showFileZone); setSelectedFile(null); }}
          disabled={disabled}
          className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${
            showFileZone
              ? 'bg-[#1B73E8] text-white'
              : 'bg-gray-100 text-[#5F6368] hover:bg-gray-200'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
          title="Joindre un fichier"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
        </button>

        {/* Textarea */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={handleTextChange}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder={placeholder || 'Posez une question ou décrivez ce que vous cherchez...'}
            rows={1}
            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm text-[#1A1A2E] placeholder:text-[#5F6368]/70 focus:outline-none focus:ring-2 focus:ring-[#1B73E8] focus:border-[#1B73E8] resize-none overflow-y-auto disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] max-h-[160px] transition-all"
            style={{ height: '44px' }}
          />
        </div>

        {/* Send button */}
        <button
          onClick={handleSendText}
          disabled={!text.trim() || disabled}
          className="flex-shrink-0 w-10 h-10 bg-[#1B73E8] text-white rounded-xl flex items-center justify-center hover:bg-[#0D47A1] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          title="Envoyer (Entrée)"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>

      <p className="text-center text-xs text-[#5F6368]/60 pb-2">
        Entrée pour envoyer · Maj+Entrée pour nouvelle ligne
      </p>
    </div>
  );
}
