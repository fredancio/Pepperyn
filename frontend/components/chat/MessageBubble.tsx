import type { Message, RecommendationTracking } from '@/lib/types';
import { AnalysisResult } from './AnalysisResult';
import { CoachingMessage } from './CoachingMessage';
import { FeedbackCard } from './FeedbackCard';
import { RecommendationCheckIn } from './RecommendationCheckIn';
import { ArcConsequencePrompt } from './ArcConsequencePrompt';

// ─── Renderer Markdown léger ────────────────────────────────────────────────
// Interprète ##, **bold**, - list items, ✓ checkmarks
// Sans dépendance externe.

function renderInline(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const re = /\*\*(.+?)\*\*/g;
  let last = 0, m;
  let key = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    parts.push(<strong key={key++} className="font-semibold text-[#1A1A2E]">{m[1]}</strong>);
    last = re.lastIndex;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

function MarkdownContent({ text }: { text: string }) {
  const lines = text.split('\n');
  const nodes: React.ReactNode[] = [];
  let listItems: string[] = [];
  let idx = 0;

  const flushList = () => {
    if (listItems.length === 0) return;
    nodes.push(
      <ul key={`ul-${idx++}`} className="mt-1 mb-1 space-y-0.5 pl-1">
        {listItems.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-[#1A1A2E] leading-snug">
            <span className="mt-[3px] flex-shrink-0 w-1.5 h-1.5 rounded-full bg-[#1B73E8] opacity-70" />
            <span>{renderInline(item)}</span>
          </li>
        ))}
      </ul>
    );
    listItems = [];
  };

  for (const raw of lines) {
    const line = raw.trimEnd();

    // H1 : # Titre
    if (/^#\s+/.test(line)) {
      flushList();
      const title = line.replace(/^#+\s+/, '');
      nodes.push(
        <p key={idx++} className="text-sm font-bold text-[#1A1A2E] mt-1 mb-0.5">
          {renderInline(title)}
        </p>
      );
      continue;
    }

    // H3 : ### Titre
    if (/^###\s+/.test(line)) {
      flushList();
      const title = line.replace(/^#+\s+/, '');
      nodes.push(
        <p key={idx++} className="text-xs font-semibold text-[#1A1A2E] mt-2 mb-0.5">
          {renderInline(title)}
        </p>
      );
      continue;
    }

    // H2 : ## Titre
    if (/^##\s+/.test(line)) {
      flushList();
      const title = line.replace(/^#+\s+/, '');
      nodes.push(
        <p key={idx++} className="text-xs font-bold text-[#1B73E8] uppercase tracking-wide mt-3 mb-0.5">
          {renderInline(title)}
        </p>
      );
      continue;
    }

    // Liste : "- item" ou "✓ item"
    if (/^[-•✓✔]\s+/.test(line)) {
      listItems.push(line.replace(/^[-•✓✔]\s+/, ''));
      continue;
    }

    // Ligne vide
    if (line.trim() === '') {
      flushList();
      continue;
    }

    // Paragraphe normal
    flushList();
    nodes.push(
      <p key={idx++} className="text-sm text-[#1A1A2E] leading-relaxed">
        {renderInline(line)}
      </p>
    );
  }
  flushList();

  return <div className="space-y-0.5">{nodes}</div>;
}

interface MessageBubbleProps {
  message: Message;
  questionsRestantes?: number | null;
  plan?: string;
  /** Appelé quand l'utilisateur a terminé (ou passé) le bilan pré-analyse. */
  onCheckInDone?: () => void;
  /** Appelé quand l'utilisateur clique sur un suggested_quick_prompt (Commit 8). */
  onQuickPromptClick?: (text: string) => void;
}

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

export function MessageBubble({ message, questionsRestantes, plan = 'free', onCheckInDone, onQuickPromptClick }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  // Cartes de feedback post-rapport — "Que comptez-vous faire ?"
  if (message.content_type === 'feedback_request' && message.metadata) {
    const meta = message.metadata as { report_id: string; recommendations: RecommendationTracking[] };
    return (
      <div className="flex items-start gap-3 max-w-[92%] animate-slide-up">
        <div className="w-8 h-8 bg-[#1B73E8] rounded-full flex-shrink-0 flex items-center justify-center mt-1 shadow-sm">
          <span className="text-white text-xs font-bold">P</span>
        </div>
        <div className="flex-1">
          <FeedbackCard reportId={meta.report_id} recommendations={meta.recommendations} />
          <p className="text-xs text-[#5F6368] mt-1 ml-1">{formatTime(message.created_at)}</p>
        </div>
      </div>
    );
  }

  // Arc Décisionnel MVP v16 — candidat conséquence détecté après analyse
  if (message.content_type === 'arc_consequence_prompt' && message.metadata) {
    const meta = message.metadata as {
      candidates: Array<{
        arc_id: string;
        analysis_id: string;
        hypothesis: string;
        recommendation_text: string;
        decision_text?: string | null;
      }>;
    };
    const c = meta.candidates?.[0];
    if (!c) return null;
    return (
      <div className="flex items-start gap-3 max-w-[92%] animate-slide-up">
        <div className="w-8 h-8 bg-amber-500 rounded-full flex-shrink-0 flex items-center justify-center mt-1 shadow-sm">
          <span className="text-white text-xs font-bold">🔗</span>
        </div>
        <div className="flex-1">
          <ArcConsequencePrompt
            arcId={c.arc_id}
            analysisId={c.analysis_id}
            hypothesis={c.hypothesis}
            recommendationText={c.recommendation_text}
            decisionText={c.decision_text}
          />
          <p className="text-xs text-[#5F6368] mt-1 ml-1">{formatTime(message.created_at)}</p>
        </div>
      </div>
    );
  }

  // Bilan pré-analyse — "Avant de relancer l'analyse, faisons le point..."
  if (message.content_type === 'recommendation_checkin' && message.metadata) {
    const meta = message.metadata as { report_id: string; recommendations: RecommendationTracking[] };
    return (
      <div className="flex items-start gap-3 max-w-[92%] animate-slide-up">
        <div className="w-8 h-8 bg-[#1B73E8] rounded-full flex-shrink-0 flex items-center justify-center mt-1 shadow-sm">
          <span className="text-white text-xs font-bold">P</span>
        </div>
        <div className="flex-1">
          <RecommendationCheckIn
            reportId={meta.report_id}
            recommendations={meta.recommendations}
            onDone={onCheckInDone || (() => {})}
          />
          <p className="text-xs text-[#5F6368] mt-1 ml-1">{formatTime(message.created_at)}</p>
        </div>
      </div>
    );
  }

  if (message.content_type === 'analysis' && message.metadata) {
    const meta = message.metadata as Record<string, unknown>;

    // Coaching qualité : rendu spécial bienveillant
    if (meta.type_document === 'COACHING_QUALITE') {
      return (
        <div className="flex items-start gap-3 max-w-[96%] animate-slide-up">
          <div className="w-8 h-8 bg-amber-400 rounded-full flex-shrink-0 flex items-center justify-center mt-1 shadow-sm">
            <span className="text-white text-xs">🔍</span>
          </div>
          <div className="flex-1">
            <CoachingMessage
              filename={meta._filename as string | undefined}
              issues={(meta.coaching_issues as string[]) || (meta.problemes_critiques as string[]) || []}
              copilotPrompt={meta.copilot_prompt as string | undefined}
            />
            <p className="text-xs text-[#5F6368] mt-1 ml-1">{formatTime(message.created_at)}</p>
          </div>
        </div>
      );
    }

    // Fichier analysé avec limitations : coaching discret au-dessus de l'analyse
    const hasWarningCoaching = Boolean(
      meta.data_quality &&
      (meta.data_quality as Record<string, unknown>).status === 'warning' &&
      (meta.copilot_prompt || ((meta.coaching_issues as string[]) ?? []).length > 0)
    );

    return (
      <div className="flex items-start gap-3 max-w-[92%] animate-slide-up">
        {/* Bot avatar */}
        <div className="w-8 h-8 bg-[#1B73E8] rounded-full flex-shrink-0 flex items-center justify-center mt-1 shadow-sm">
          <span className="text-white text-xs font-bold">P</span>
        </div>
        <div className="flex-1 space-y-3">
          {hasWarningCoaching && (
            <CoachingMessage
              filename={meta._filename as string | undefined}
              issues={(meta.coaching_issues as string[]) || []}
              copilotPrompt={meta.copilot_prompt as string | undefined}
              variant="warning"
            />
          )}
          <AnalysisResult data={meta} questionsRestantes={questionsRestantes} plan={plan} />
          <p className="text-xs text-[#5F6368] mt-1 ml-1">{formatTime(message.created_at)}</p>
        </div>
      </div>
    );
  }

  if (isUser) {
    return (
      <div className="flex justify-end animate-slide-up">
        <div className="max-w-[75%] md:max-w-[60%]">
          <div className="bg-[#1B73E8] text-white rounded-2xl rounded-tr-none px-4 py-3 shadow-sm">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          </div>
          <p className="text-xs text-[#5F6368] mt-1 text-right mr-1">{formatTime(message.created_at)}</p>
        </div>
      </div>
    );
  }

  if (isAssistant) {
    // ── Suggested quick prompts (V2 Conversation Engine — Commit 8) ───────────
    // Présents uniquement sur le message d'accueil post-analyse.
    // Effacés dans ChatContainer dès qu'un bouton est cliqué (anti-doublon).
    const quickPrompts = (message.metadata?.quick_prompts as string[] | undefined) ?? [];
    const hasPrompts = quickPrompts.length > 0 && typeof onQuickPromptClick === 'function';

    return (
      <div className="flex items-start gap-3 max-w-[85%] md:max-w-[70%] animate-slide-up">
        {/* Bot avatar */}
        <div className="w-8 h-8 bg-[#1B73E8] rounded-full flex-shrink-0 flex items-center justify-center mt-1 shadow-sm">
          <span className="text-white text-xs font-bold">P</span>
        </div>
        <div>
          <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm border border-gray-100">
            <MarkdownContent text={message.content} />
          </div>
          {hasPrompts && (
            <div className="mt-2 flex flex-wrap gap-2">
              {quickPrompts.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => onQuickPromptClick!(prompt)}
                  className="text-xs bg-white border border-[#1B73E8]/40 text-[#1B73E8] rounded-full px-3 py-1.5 hover:bg-[#EFF6FF] hover:border-[#1B73E8] transition-colors font-medium shadow-sm"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}
          <p className="text-xs text-[#5F6368] mt-1 ml-1">{formatTime(message.created_at)}</p>
        </div>
      </div>
    );
  }

  return null;
}

export function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 animate-fade-in">
      <div className="w-8 h-8 bg-[#1B73E8] rounded-full flex-shrink-0 flex items-center justify-center shadow-sm">
        <span className="text-white text-xs font-bold">P</span>
      </div>
      <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm border border-gray-100">
        <div className="flex gap-1 items-center">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    </div>
  );
}
