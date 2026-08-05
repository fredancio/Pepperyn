'use client';

/**
 * Chat / Review Briefing — External User Testing Prototype (2026-08-05).
 *
 * Parcours testable (Mission 4) : arrivée depuis Portfolio Home avec un
 * client pré-sélectionné (`?entity=`), Review Briefing immédiatement
 * visible, un exemple de rapport déjà généré, "Préparer cette question"
 * préremplit le champ de saisie sans jamais l'envoyer automatiquement.
 *
 * Composé à partir des mêmes composants réels que le chat authentifié
 * (ReviewBriefing, MessageBubble, AnalysisResult, InputBar — tous
 * byte-identiques) mais SANS réutiliser ChatContainer.tsx : ce dernier
 * porte l'authentification Supabase, la facturation Stripe et l'historique
 * réel, hors périmètre et hors sécurité pour un prototype public sans
 * connexion. Cette page reconstitue uniquement le sous-ensemble nécessaire
 * au parcours testable, en mémoire, sans aucun appel réseau réel.
 */
import { Suspense, useCallback, useMemo, useRef, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { ReviewBriefing } from '@/components/chat/ReviewBriefing';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { InputBar, type PrefillToken } from '@/components/chat/InputBar';
import { DemoBanner } from '@/components/demo/DemoBanner';
import { getDemoEntityName } from '@/lib/demo-data';
import type { Message } from '@/lib/types';

const DEMO_COMPANY_ID = 'demo-company';
const DEMO_SESSION_ID = 'demo-session';

/**
 * Exemple de rapport déjà généré — Mission 4, point 10. Libellé honnête
 * explicite ("Exemple de rapport") : jamais présenté comme une analyse
 * réelle, jamais associé à une vraie donnée financière d'un vrai client.
 */
function buildExampleAnalysis(clientName: string): Record<string, unknown> {
  return {
    id: 'demo-analysis-example',
    type_document: 'ANALYSE FINANCIÈRE',
    score_confiance: 92,
    resume_executif:
      `**Exemple de rapport** — illustration du résultat d'une analyse Pepperyn pour ${clientName} ` +
      `(donnée fictive, prototype de démonstration). La rentabilité opérationnelle se maintient sur ` +
      `le trimestre, portée par une maîtrise des coûts fixes malgré un léger tassement du chiffre d'affaires.`,
    diagnostic_revenus: 'Chiffre d\'affaires stable (+1,2 % sur 3 mois), porté par le segment récurrent.',
    diagnostic_couts: 'Charges externes en légère hausse (+3 %), compensées par la baisse des frais de structure.',
    diagnostic_marges: 'Marge opérationnelle à 14,8 %, en ligne avec la moyenne du secteur.',
    ce_qui_a_change: [
      'Renégociation partielle avec le fournisseur principal engagée ce trimestre.',
      'Un nouveau poste de charge récurrent est apparu (abonnement logiciel de gestion).',
    ],
    opportunites_v3: [
      'Marge de manœuvre sur le poste achats si la renégociation aboutit.',
      'Trésorerie disponible pour un investissement mesuré au prochain trimestre.',
    ],
    plan_action: [
      'Confirmer l\'issue de la renégociation fournisseur avant la fin du trimestre.',
      'Suivre l\'effet du nouveau logiciel de gestion sur les charges récurrentes.',
    ],
    score_rentabilite: 7,
    score_risque: 3,
    score_structure: 8,
    decision: 'À surveiller — aucune alerte critique, un point de vigilance à confirmer.',
    synthese:
      `Exemple de rapport — aperçu de démonstration pour ${clientName}. Aucune donnée réelle, ` +
      `aucune analyse n'a été exécutée dans ce prototype.`,
    excel_export_nom: 'exemple_rapport_demo.xlsx',
  };
}

function makeMessage(partial: Partial<Message> & Pick<Message, 'role' | 'content_type' | 'content'>): Message {
  return {
    id: `demo-${Math.random().toString(36).slice(2)}`,
    session_id: DEMO_SESSION_ID,
    company_id: DEMO_COMPANY_ID,
    created_at: new Date().toISOString(),
    ...partial,
  };
}

export default function DemoChatPage() {
  // useSearchParams() exige une frontière Suspense en génération statique
  // (Next.js App Router) — même convention que les autres pages client de
  // ce dépôt qui lisent des query params.
  return (
    <Suspense fallback={null}>
      <DemoChatPageInner />
    </Suspense>
  );
}

function DemoChatPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const entityId = searchParams.get('entity') || undefined;
  const clientName = (entityId && getDemoEntityName(entityId)) || 'cette organisation';

  const [messages, setMessages] = useState<Message[]>(() => [
    makeMessage({
      role: 'assistant',
      content_type: 'analysis',
      content: '',
      metadata: buildExampleAnalysis(clientName),
    }),
  ]);
  const [prefillToken, setPrefillToken] = useState<PrefillToken | null>(null);
  const prefillCounterRef = useRef(0);

  const handlePrepareQuestion = useCallback((question: string) => {
    prefillCounterRef.current += 1;
    setPrefillToken({ id: prefillCounterRef.current, text: question });
  }, []);

  // Jamais d'appel réseau réel : la "réponse" est un texte fixe expliquant
  // la nature du prototype — aucun appel LLM, aucune écriture Supabase.
  const handleSendMessage = useCallback((text: string) => {
    setMessages((prev) => [
      ...prev,
      makeMessage({ role: 'user', content_type: 'text', content: text }),
      makeMessage({
        role: 'assistant',
        content_type: 'text',
        content:
          'Aperçu de démonstration — ce prototype ne traite aucune question réelle. ' +
          'Dans Pepperyn, cette question serait répondue à partir de vos données financières.',
      }),
    ]);
  }, []);

  const handleSendFile = useCallback(() => {
    setMessages((prev) => [
      ...prev,
      makeMessage({
        role: 'assistant',
        content_type: 'text',
        content:
          'Aperçu de démonstration — l\'envoi de fichiers est désactivé dans ce prototype. ' +
          'Aucun fichier n\'est transmis ni analysé.',
      }),
    ]);
  }, []);

  const questionsRestantes = useMemo(() => null, []);

  return (
    <div className="min-h-screen bg-[#EFF6FF] flex flex-col">
      <DemoBanner />

      <div className="border-b border-blue-100 bg-white px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <button
            type="button"
            onClick={() => router.push('/demo/portfolio')}
            className="text-xs font-medium text-[#1B73E8] hover:text-[#0D47A1]"
            data-testid="demo-back-to-portfolio"
          >
            ← Portefeuille
          </button>
          <p className="text-sm font-bold text-[#1A1A2E]" data-testid="demo-chat-client-name">
            {clientName}
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="flex flex-col gap-4 p-4 md:p-6 max-w-4xl mx-auto w-full">
          <ReviewBriefing entityId={entityId} onPrepareQuestion={handlePrepareQuestion} />
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              plan="pro"
              questionsRestantes={questionsRestantes}
            />
          ))}
        </div>
      </div>

      <InputBar
        onSendMessage={handleSendMessage}
        onSendFile={handleSendFile}
        placeholder="Posez une question de suivi..."
        prefillToken={prefillToken}
      />
    </div>
  );
}
