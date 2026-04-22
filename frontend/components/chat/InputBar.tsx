'use client';
import { useState, useRef, KeyboardEvent } from 'react';
import { FileUploadZone } from './FileUploadZone';

interface InputBarProps {
  onSendMessage: (text: string) => void;
  onSendFile: (file: File, context: string, mode: 'quick' | 'complete') => void;
  disabled?: boolean;
  placeholder?: string;
  uploadOnly?: boolean;
  onFileChange?: (file: File | null) => void;
}

export function InputBar({ onSendMessage, onSendFile, disabled, placeholder, uploadOnly, onFileChange }: InputBarProps) {
  const [text, setText] = useState('');
  const [showFileZone, setShowFileZone] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileContext, setFileContext] = useState('');
  const [mode, setMode] = useState<'quick' | 'complete'>('complete');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

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
    onSendFile(selectedFile, fileContext, mode);
    setSelectedFile(null);
    setFileContext('');
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setFileContext('');
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
                  {['Excel (.xlsx)', 'CSV', 'PDF', 'Export ERP'].map(f => (
                    <span key={f} className="text-xs px-2.5 py-1 bg-gray-50 border border-gray-200 rounded-full text-[#5F6368]">{f}</span>
                  ))}
                </div>
                <p className="text-xs text-center text-[#5F6368]/70">
                  Ex: P&amp;L · Budget · Export comptabilité
                </p>
              </div>
            </div>
          ) : (
            /* File selected — info + context */
            <div className="p-4">
              <div className="flex items-center justify-between mb-3 bg-[#EFF6FF] border border-blue-100 rounded-xl px-3 py-2.5">
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
              <input
                type="text"
                value={fileContext}
                onChange={e => setFileContext(e.target.value)}
                placeholder="Contexte optionnel : ex. P&L Q3 2024..."
                className="w-full text-sm bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 text-[#1A1A2E] placeholder:text-[#5F6368]/60 focus:outline-none focus:ring-1 focus:ring-[#1B73E8] focus:border-[#1B73E8] mb-3"
              />
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
            { icon: '🔒', label: 'Suppression possible' },
          ].map(t => (
            <span key={t.label} className="flex items-center gap-1 text-xs text-[#5F6368]">
              <span>{t.icon}</span>
              <span>{t.label}</span>
            </span>
          ))}
        </div>

        <p className="text-center text-xs text-[#5F6368]">
          3 analyses gratuites · sans CB
        </p>
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

            {/* Context input */}
            <input
              type="text"
              value={fileContext}
              onChange={e => setFileContext(e.target.value)}
              placeholder="Contexte optionnel : ex. P&L Q3 2024, comparer avec Q2..."
              className="w-full text-sm bg-white border border-gray-200 rounded-lg px-3 py-2 text-[#1A1A2E] placeholder:text-[#5F6368]/70 focus:outline-none focus:ring-1 focus:ring-[#1B73E8] focus:border-[#1B73E8] mb-3"
            />

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
