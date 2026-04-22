import type { Message } from '@/lib/types';
import { AnalysisResult } from './AnalysisResult';

interface MessageBubbleProps {
  message: Message;
  questionsRestantes?: number | null;
}

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

export function MessageBubble({ message, questionsRestantes }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  if (message.content_type === 'analysis' && message.metadata) {
    return (
      <div className="flex items-start gap-3 max-w-[92%] animate-slide-up">
        {/* Bot avatar */}
        <div className="w-8 h-8 bg-[#1B73E8] rounded-full flex-shrink-0 flex items-center justify-center mt-1 shadow-sm">
          <span className="text-white text-xs font-bold">P</span>
        </div>
        <div className="flex-1">
          <AnalysisResult data={message.metadata as Record<string, unknown>} questionsRestantes={questionsRestantes} />
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
    return (
      <div className="flex items-start gap-3 max-w-[85%] md:max-w-[70%] animate-slide-up">
        {/* Bot avatar */}
        <div className="w-8 h-8 bg-[#1B73E8] rounded-full flex-shrink-0 flex items-center justify-center mt-1 shadow-sm">
          <span className="text-white text-xs font-bold">P</span>
        </div>
        <div>
          <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm border border-gray-100">
            <p className="text-sm text-[#1A1A2E] leading-relaxed whitespace-pre-wrap">{message.content}</p>
          </div>
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
