'use client';
import { useState, useRef, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import type { Message, Session } from '@/lib/types';
import { analyzeFile, analyzeText, fetchAnalysesHistory } from '@/lib/api';
import { getCurrentAuthMode, signOutAdmin, clearGuestAuth, getGuestPlan } from '@/lib/auth';
import { supabase } from '@/lib/supabase';
import { MessageBubble, TypingIndicator } from './MessageBubble';
import { InputBar } from './InputBar';
import { PwaInstallButton } from '@/components/ui/PwaInstallButton';
import { Spinner } from '@/components/ui/Spinner';

const MAX_CHAT_QUESTIONS_FREE = 5;

function makeLocalMessage(role: 'user' | 'assistant', content: string, content_type: Message['content_type'] = 'text', metadata?: Record<string, unknown>): Message {
  return {
    id: `local-${Date.now()}-${Math.random()}`,
    session_id: '',
    company_id: '',
    role,
    content,
    content_type,
    metadata,
    created_at: new Date().toISOString(),
  };
}

const WELCOME_MESSAGE: Message = makeLocalMessage(
  'assistant',
  "Bonjour ! Je suis Pepperyn, votre scanner financier IA.\n\nImportez un fichier Excel, CSV ou PDF pour obtenir une analyse structurée en quelques secondes, ou posez-moi directement une question sur vos finances.",
  'text'
);

const QUICK_SUGGESTIONS = [
  { icon: '📊', label: 'Analyser un P&L', text: 'Je voudrais analyser mon compte de résultat' },
  { icon: '💰', label: 'Auditer mon budget', text: 'Peux-tu auditer mon budget et détecter les anomalies ?' },
  { icon: '📈', label: 'Comparer mes marges', text: 'Analyse et compare mes marges par période' },
  { icon: '🔍', label: 'Détecter anomalies', text: 'Détecte les anomalies dans mes données financières' },
];

const LIMIT_MESSAGE = `Vous avez atteint la limite de 5 questions pour cette analyse (version gratuite).

💡 Pour des conversations illimitées, un accès équipe et des exports enrichis, découvrez les versions avancées de Pepperyn (bientôt disponibles).

Ou démarrez une nouvelle analyse avec un nouveau fichier.`;

export function ChatContainer() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [authMode, setAuthMode] = useState<'admin' | 'guest' | null>(null);
  const [plan, setPlan] = useState<string>('free');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [adminName, setAdminName] = useState<string>('');
  // Question counter for free plan (post-analysis)
  const [analysisReceived, setAnalysisReceived] = useState(false);
  const [questionsPostAnalysis, setQuestionsPostAnalysis] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasMessages = messages.length > 1;

  const questionsRestantes = analysisReceived && plan === 'free'
    ? Math.max(0, MAX_CHAT_QUESTIONS_FREE - questionsPostAnalysis)
    : null;

  // Check auth mode
  useEffect(() => {
    async function init() {
      const mode = await getCurrentAuthMode();
      setAuthMode(mode);

      if (mode === 'guest') {
        const p = getGuestPlan();
        if (p) setPlan(p);
        loadSessionHistory();
      } else if (mode === 'admin') {
        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
          const { data: profile } = await supabase
            .from('profiles')
            .select('prenom, company:companies(plan)')
            .eq('id', user.id)
            .single();
          if (profile) {
            setAdminName((profile as { prenom?: string }).prenom || user.email?.split('@')[0] || 'Admin');
            const companyData = (profile as { company?: { plan?: string } }).company;
            if (companyData?.plan) setPlan(companyData.plan);
          }
        }
        loadSessionHistory();
      }
    }
    init();
  }, []);

  const loadSessionHistory = async () => {
    setLoadingSessions(true);
    try {
      const analyses = await fetchAnalysesHistory();
      const mapped: Session[] = analyses.map(a => ({
        id: a.id,
        company_id: '',
        is_admin_session: false,
        titre: a.fichier_nom || `Analyse ${a.type_document || ''}`.trim(),
        is_archived: false,
        created_at: a.created_at,
        updated_at: a.created_at,
      }));
      setSessions(mapped);
    } catch {
      // silently fail
    } finally {
      setLoadingSessions(false);
    }
  };

  const loadSession = async (session: Session) => {
    setSessionId(session.id);
    setSidebarOpen(false);
    setAnalysisReceived(false);
    setQuestionsPostAnalysis(0);
    try {
      const { data } = await supabase
        .from('messages')
        .select('*')
        .eq('session_id', session.id)
        .order('created_at', { ascending: true });
      if (data && data.length > 0) {
        setMessages(data);
        // Check if session had an analysis
        const hasAnalysis = data.some(m => m.content_type === 'analysis');
        if (hasAnalysis) setAnalysisReceived(true);
      }
    } catch {
      // silently fail
    }
  };

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSendMessage = useCallback(async (text: string) => {
    // Check question limit for free plan
    if (analysisReceived && plan === 'free' && questionsPostAnalysis >= MAX_CHAT_QUESTIONS_FREE) {
      const limitMsg = makeLocalMessage('assistant', LIMIT_MESSAGE, 'text');
      setMessages(prev => [...prev, limitMsg]);
      return;
    }

    const userMsg = makeLocalMessage('user', text, 'text');
    setMessages(prev => [...prev, userMsg]);

    // Increment counter if post-analysis
    if (analysisReceived && plan === 'free') {
      setQuestionsPostAnalysis(prev => prev + 1);
    }

    setIsTyping(true);

    try {
      const result = await analyzeText(text, sessionId);

      if (result.session_id) setSessionId(result.session_id);

      const assistantMsg = makeLocalMessage('assistant', result.response || result.message || 'Analyse terminée.', 'text');
      setMessages(prev => [...prev, assistantMsg]);

      if (result.analysis) {
        const analysisMsg = makeLocalMessage('assistant', '', 'analysis', result.analysis);
        setMessages(prev => [...prev, analysisMsg]);
        setAnalysisReceived(true);
        setQuestionsPostAnalysis(0);
      }
    } catch (err) {
      const errMsg = makeLocalMessage('assistant', `Désolé, une erreur est survenue : ${err instanceof Error ? err.message : 'Erreur inconnue'}. Veuillez réessayer.`, 'error');
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setIsTyping(false);
    }
  }, [sessionId, analysisReceived, plan, questionsPostAnalysis]);

  const handleSendFile = useCallback(async (file: File, context: string, mode: 'quick' | 'complete') => {
    // Check question limit for free plan
    if (analysisReceived && plan === 'free' && questionsPostAnalysis >= MAX_CHAT_QUESTIONS_FREE) {
      const limitMsg = makeLocalMessage('assistant', LIMIT_MESSAGE, 'text');
      setMessages(prev => [...prev, limitMsg]);
      return;
    }

    const userMsg = makeLocalMessage('user', `📎 ${file.name}${context ? `\n\nContexte : ${context}` : ''}`, 'file');
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const result = await analyzeFile(file, context, mode, sessionId);
      if (result.session_id) setSessionId(result.session_id);

      if (result.message) {
        const textMsg = makeLocalMessage('assistant', result.message, 'text');
        setMessages(prev => [...prev, textMsg]);
      }

      if (result.result) {
        const analysisMsg = makeLocalMessage('assistant', '', 'analysis', {
          ...result.result,
          id: result.analyse_id || result.result.id || null,
          _questionsRestantes: MAX_CHAT_QUESTIONS_FREE,
          _memoryInsight: result.memory_insight || null,
        });
        setMessages(prev => [...prev, analysisMsg]);
        setAnalysisReceived(true);
        setQuestionsPostAnalysis(0);
        // Refresh sidebar history
        loadSessionHistory();
      } else {
        const fallbackMsg = makeLocalMessage('assistant', result.response || 'Analyse terminée avec succès.', 'text');
        setMessages(prev => [...prev, fallbackMsg]);
      }
    } catch (err) {
      const errMsg = makeLocalMessage('assistant', `Erreur lors de l'analyse : ${err instanceof Error ? err.message : 'Erreur inconnue'}. Vérifiez votre fichier et réessayez.`, 'error');
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setIsTyping(false);
    }
  }, [sessionId, analysisReceived, plan, questionsPostAnalysis]);

  const handleSignOut = async () => {
    if (authMode === 'admin') {
      await signOutAdmin();
    } else {
      clearGuestAuth();
    }
    router.push('/register');
  };

  const today = new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const isInputBlocked = analysisReceived && plan === 'free' && questionsPostAnalysis >= MAX_CHAT_QUESTIONS_FREE;

  return (
    <div className="flex h-screen bg-[#EFF6FF] overflow-hidden">
      {/* Sidebar */}
      {authMode !== null && (
        <>
          {/* Mobile overlay */}
          {sidebarOpen && (
            <div
              className="fixed inset-0 bg-black/40 z-30 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          {/* Sidebar panel */}
          <aside className={`
            fixed lg:relative inset-y-0 left-0 z-40 lg:z-auto
            w-72 bg-white border-r border-gray-100 flex flex-col
            transition-transform duration-300 ease-in-out
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          `}>
            {/* Sidebar header */}
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <img src="/favicon.png?v=4" alt="Pepperyn" className="w-12 h-12 object-contain" />
                <div>
                  <span className="font-bold text-[#1A1A2E] text-sm block leading-none">Pepperyn IA</span>
                  <span className="text-xs text-[#5F6368]">Financial Control Center</span>
                </div>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden w-7 h-7 flex items-center justify-center text-[#5F6368] hover:text-[#1A1A2E]"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* New chat button */}
            <div className="p-3">
              <button
                onClick={() => {
                  setMessages([WELCOME_MESSAGE]);
                  setSessionId(undefined);
                  setSidebarOpen(false);
                  setAnalysisReceived(false);
                  setQuestionsPostAnalysis(0);
                }}
                className="w-full flex items-center gap-2 px-3 py-2.5 bg-[#1B73E8] text-white rounded-xl text-sm font-medium hover:bg-[#0D47A1] transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Nouvelle analyse
              </button>
            </div>

            {/* Sessions list */}
            <div className="flex-1 overflow-y-auto p-3">
              <p className="text-xs font-semibold text-[#5F6368] px-2 mb-2 uppercase tracking-wide">
                Historique
              </p>
              {loadingSessions ? (
                <div className="flex justify-center py-4">
                  <Spinner size="sm" />
                </div>
              ) : sessions.length === 0 ? (
                <p className="text-xs text-[#5F6368] px-2 py-2">Aucune session précédente</p>
              ) : (
                <div className="flex flex-col gap-1">
                  {sessions.map(session => (
                    <button
                      key={session.id}
                      onClick={() => loadSession(session)}
                      className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-colors ${
                        sessionId === session.id
                          ? 'bg-[#EFF6FF] text-[#1B73E8] font-medium'
                          : 'text-[#1A1A2E] hover:bg-gray-50'
                      }`}
                    >
                      <p className="truncate font-medium text-xs">{session.titre || 'Analyse sans titre'}</p>
                      <p className="text-xs text-[#5F6368] mt-0.5">
                        {new Date(session.updated_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Sidebar footer */}
            <div className="p-3 border-t border-gray-100 flex flex-col gap-1">
              <Link
                href="/app/settings"
                className="flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm text-[#5F6368] hover:bg-gray-50 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Paramètres
              </Link>
              <button
                onClick={handleSignOut}
                className="flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm text-red-500 hover:bg-red-50 transition-colors w-full text-left"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Se déconnecter
              </button>
            </div>
          </aside>
        </>
      )}

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-gray-100 px-4 py-3 flex items-center gap-3 shadow-sm">
          {/* Hamburger (admin only, mobile) */}
          {authMode === 'admin' && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden w-9 h-9 flex items-center justify-center text-[#5F6368] hover:bg-gray-100 rounded-xl transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          )}

          {/* Logo — hidden on desktop when sidebar is visible (admin) */}
          <div className={`flex items-center gap-2 ${authMode === 'admin' ? 'lg:hidden' : ''}`}>
            <img src="/favicon.png?v=4" alt="Pepperyn" className="w-14 h-14 object-contain" />
            <div className="hidden sm:block">
              <span className="font-bold text-[#1A1A2E] text-sm block leading-none">Pepperyn IA</span>
              <span className="text-xs text-[#5F6368]">Financial Control Center</span>
            </div>
          </div>

          {/* Date */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-[#1A1A2E] truncate hidden sm:block capitalize">{today}</p>
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-2">
            {/* Plan badge */}
            <div className={`hidden sm:flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-semibold ${
              plan === 'premium' ? 'bg-amber-100 text-amber-700' :
              plan === 'standard' || plan === 'standard_beta' ? 'bg-blue-100 text-blue-700' :
              'bg-gray-100 text-[#5F6368]'
            }`}>
              {plan === 'premium' ? '⭐' : plan === 'standard' || plan === 'standard_beta' ? '🚀' : '🆓'}
              <span className="capitalize">{plan === 'standard_beta' ? 'Beta' : plan}</span>
            </div>

            <PwaInstallButton />

            {authMode === 'admin' && (
              <Link
                href="/app/settings"
                className="w-9 h-9 flex items-center justify-center text-[#5F6368] hover:bg-gray-100 rounded-xl transition-colors"
                title="Paramètres"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </Link>
            )}

            {/* Avatar / logout */}
            <button
              onClick={handleSignOut}
              className="w-9 h-9 bg-[#1B73E8] rounded-full flex items-center justify-center text-white font-bold text-sm hover:bg-[#0D47A1] transition-colors"
              title="Se déconnecter"
            >
              {authMode === 'admin' ? (adminName?.[0]?.toUpperCase() || 'A') : 'G'}
            </button>
          </div>
        </header>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto">
          {!hasMessages ? (
            /* Empty state — product-driven UX */
            <div className="h-full overflow-y-auto">
              <div className="flex flex-col items-center justify-center min-h-full px-4 py-8 gap-5 max-w-lg mx-auto w-full">

                {/* Logo + Greeting label */}
                <div className="text-center">
                  <img src="/favicon.png?v=4" alt="Pepperyn" className="w-16 h-16 mx-auto mb-3 object-contain" />
                  {adminName && (
                    <p className="text-xs font-medium text-[#5F6368] uppercase tracking-widest mb-1">
                      Bonjour, {adminName}
                    </p>
                  )}
                </div>

                {/* Headline simplifiée */}
                <div className="text-center">
                  <h2 className="text-xl font-extrabold text-[#1A1A2E] leading-tight">
                    Importez vos données financières
                  </h2>
                </div>

                {/* Upload + CTA + trust */}
                <div className="w-full">
                  <InputBar
                    onSendMessage={handleSendMessage}
                    onSendFile={handleSendFile}
                    disabled={isTyping}
                    placeholder="uploadez un fichier"
                    uploadOnly={true}
                    onFileChange={setUploadedFile}
                  />
                </div>

                {/* Value proof */}
                <div className="flex flex-wrap justify-center gap-4 text-xs text-[#5F6368]">
                  {['✔ Analyse structurée', '✔ Recommandations concrètes', '✔ Aucun blabla inutile'].map(v => (
                    <span key={v} className="font-medium">{v}</span>
                  ))}
                </div>

                {/* Versions payantes */}
                <p className="text-xs text-[#5F6368]/60 text-center italic">
                  ✨ Bien d&apos;autres options seront disponibles dans les versions payantes à venir !
                </p>
              </div>
            </div>
          ) : (
            /* Conversation messages */
            <div className="flex flex-col gap-4 p-4 md:p-6 max-w-4xl mx-auto w-full">
              {messages.map(msg => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  questionsRestantes={
                    msg.content_type === 'analysis' && plan === 'free'
                      ? questionsRestantes
                      : null
                  }
                />
              ))}
              {isTyping && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Question counter banner (free plan, post-analysis) */}
        {analysisReceived && plan === 'free' && questionsRestantes !== null && (
          <div className={`px-4 py-2 border-t text-center text-xs ${
            questionsRestantes === 0
              ? 'bg-red-50 border-red-100 text-red-600'
              : questionsRestantes <= 2
              ? 'bg-amber-50 border-amber-100 text-amber-700'
              : 'bg-[#EFF6FF] border-blue-100 text-[#5F6368]'
          }`}>
            {questionsRestantes === 0
              ? '⚠️ Limite atteinte — Démarrez une nouvelle analyse ou découvrez les versions avancées'
              : `Questions restantes dans cette session : ${questionsRestantes}/${MAX_CHAT_QUESTIONS_FREE}`
            }
          </div>
        )}

        {/* Input bar — affiché en bas uniquement en mode conversation */}
        {hasMessages && (
          <>
            <InputBar
              onSendMessage={handleSendMessage}
              onSendFile={handleSendFile}
              disabled={isTyping || isInputBlocked}
              placeholder={
                isInputBlocked
                  ? 'Limite de questions atteinte — démarrez une nouvelle analyse'
                  : 'Posez une question de suivi...'
              }
            />
            <p className="text-center text-xs text-[#5F6368]/50 pb-2 italic">
              ✨ Bien d'autres options seront disponibles dans les versions payantes à venir !
            </p>
          </>
        )}
      </div>
    </div>
  );
}
