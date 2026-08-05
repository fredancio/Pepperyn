'use client';

/**
 * PortfolioHome — Portfolio Intelligence, Incrément 1 (Capability 7).
 *
 * Écran unique : ligne d'orientation + liste de cartes triées par priorité,
 * une carte par client, portant son point le plus prioritaire du Briefing
 * de revue. "Préparer cette revue" ouvre /app/chat avec ce client
 * pré-sélectionné (voir ChatContainer.tsx::searchParams).
 *
 * PÉRIMÈTRE INCRÉMENT 1 (voir PORTFOLIO_HOME_IMPLEMENTATION_PLAN.md) :
 *   - nom du client + titre du point prioritaire + action seulement.
 *   - why_it_matters, temporal_context, compteur multi-points : Incrément 2.
 *   - tri fin par ancienneté, état vide détaillé : Incrément 3.
 *   - écran par défaut à l'ouverture de l'app : Incrément 4 — pour cet
 *     incrément, accessible uniquement par lien direct (/app/portfolio).
 */

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { fetchPortfolio } from '@/lib/arc-api';
import type { PortfolioCard, BriefingPriority } from '@/lib/types';

const PRIORITY_META: Record<BriefingPriority, { icon: string; label: string }> = {
  urgent: { icon: '🔥', label: 'Urgent' },
  to_check: { icon: '⚠️', label: 'À vérifier' },
  done: { icon: '✓', label: 'Fait' },
  closed: { icon: '○', label: 'Clos' },
};

type LoadState = 'loading' | 'loaded' | 'error';

export function PortfolioHome() {
  const router = useRouter();
  const [cards, setCards] = useState<PortfolioCard[]>([]);
  const [state, setState] = useState<LoadState>('loading');

  const load = useCallback(async () => {
    setState('loading');
    try {
      const result = await fetchPortfolio();
      setCards(result);
      setState('loaded');
    } catch {
      // Échec silencieux côté données — le message d'erreur reste sobre,
      // jamais de détail technique exposé à l'utilisateur.
      setCards([]);
      setState('error');
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handlePrepareReview = (entityId: string) => {
    router.push(`/app/chat?entity=${entityId}`);
  };

  return (
    <div className="min-h-screen bg-[#EFF6FF] px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-xl font-extrabold text-[#1A1A2E] mb-1">Portefeuille</h1>
        <p className="text-sm text-[#5F6368] mb-6">
          Vos clients avec un point à traiter, triés par priorité.
        </p>

        {state === 'loading' && (
          <p className="text-sm text-[#5F6368]" data-testid="portfolio-loading">
            Chargement…
          </p>
        )}

        {state === 'error' && (
          <p className="text-sm text-red-600" data-testid="portfolio-error">
            Impossible de charger le portefeuille pour le moment.
          </p>
        )}

        {state === 'loaded' && cards.length === 0 && (
          <div
            className="bg-white rounded-2xl border border-blue-100 p-6 text-center"
            data-testid="portfolio-empty"
          >
            <p className="text-sm text-[#5F6368]">
              Aucun point actif à traiter pour l&apos;instant.
            </p>
          </div>
        )}

        {state === 'loaded' && cards.length > 0 && (
          <div className="space-y-3" data-testid="portfolio-cards">
            {cards.map((card) => {
              const meta = PRIORITY_META[card.top_item.priority];
              return (
                <div
                  key={card.entity_id}
                  className="bg-white rounded-2xl border border-blue-100 p-5 flex items-start justify-between gap-4"
                  data-testid={`portfolio-card-${card.entity_id}`}
                >
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-[#5F6368] flex items-center gap-1">
                      <span aria-hidden="true">{meta.icon}</span> {meta.label}
                    </p>
                    <p className="text-sm font-bold text-[#1A1A2E] mt-0.5">{card.entity_name}</p>
                    <p className="text-sm text-[#5F6368] mt-0.5 truncate">{card.top_item.title}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handlePrepareReview(card.entity_id)}
                    className="shrink-0 text-xs font-semibold text-white bg-[#1B73E8] hover:bg-[#0D47A1] rounded-lg px-3 py-2 transition-colors"
                  >
                    Préparer cette revue
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
