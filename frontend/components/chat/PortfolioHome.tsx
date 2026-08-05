'use client';

/**
 * PortfolioHome — Portfolio Intelligence, Incréments 1 + 2 (Capability 7).
 *
 * Écran unique : ligne d'orientation + liste de cartes triées par priorité,
 * une carte par client, portant son point le plus prioritaire du Briefing
 * de revue. "Préparer cette revue" ouvre /app/chat avec ce client
 * pré-sélectionné (voir ChatContainer.tsx::searchParams).
 *
 * Hiérarchie de la carte (Incrément 2, Mission 6 — voir
 * docs/Product/portfolio-card-review/) : priorité → nom du client → titre
 * du point → contexte temporel → why_it_matters (si distinct) → compteur
 * (si > 1) → action. Une seule action, jamais de menu, filtre, score,
 * widget, donnée financière, bouton d'abandon ni aperçu du briefing.
 *
 * Contexte temporel toujours factuel (déjà garanti côté backend par
 * _arc_to_briefing_item — jamais d'injonction du type "à traiter
 * aujourd'hui"). Ce composant ne fait qu'afficher les champs déjà
 * calculés, aucune génération de texte ici.
 *
 * PÉRIMÈTRE RESTANT HORS DE CET INCRÉMENT :
 *   - tri fin par ancienneté déjà appliqué côté backend (Mission 4) ;
 *     état vide honnête plus détaillé reste Incrément 3.
 *   - écran par défaut à l'ouverture de l'app : Incrément 4 — pour cet
 *     incrément, accessible uniquement par lien direct (/app/portfolio).
 */

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { fetchPortfolio } from '@/lib/arc-api';
import { isDemoModeEnabled } from '@/lib/demo-mode';
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
    // External User Testing Prototype (2026-08-05) : en mode démo, navigue
    // vers la route de démonstration (aucune authentification, aucun accès
    // réel) plutôt que /app/chat. Seul point de wiring modifié dans ce
    // composant — hiérarchie, tri et rendu des cartes restent inchangés.
    const base = isDemoModeEnabled() ? '/demo/chat' : '/app/chat';
    router.push(`${base}?entity=${entityId}`);
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
                    {/* 1. Priorité */}
                    <p className="text-xs font-semibold text-[#5F6368] flex items-center gap-1">
                      <span aria-hidden="true">{meta.icon}</span> {meta.label}
                    </p>
                    {/* 2. Nom du client */}
                    <p className="text-sm font-bold text-[#1A1A2E] mt-0.5">{card.entity_name}</p>
                    {/* 3. Titre du point principal */}
                    <p className="text-sm text-[#5F6368] mt-0.5 truncate">{card.top_item.title}</p>
                    {/* 4. Contexte temporel — texte factuel déjà généré côté backend */}
                    <p
                      className="text-xs text-[#5F6368] mt-1"
                      data-testid={`portfolio-temporal-${card.entity_id}`}
                    >
                      {card.top_item.temporal_context}
                    </p>
                    {/* 5. why_it_matters — uniquement quand distinct (décidé côté backend) */}
                    {card.why_it_matters_display && (
                      <p
                        className="text-xs text-[#1A1A2E] mt-1.5"
                        data-testid={`portfolio-why-${card.entity_id}`}
                      >
                        {card.why_it_matters_display}
                      </p>
                    )}
                    {/* 6. Compteur — uniquement si d'autres points actifs existent */}
                    {card.other_active_count > 0 && (
                      <p
                        className="text-xs text-[#5F6368] mt-1.5"
                        data-testid={`portfolio-counter-${card.entity_id}`}
                      >
                        +{card.other_active_count} autre{card.other_active_count > 1 ? 's' : ''} point
                        {card.other_active_count > 1 ? 's' : ''} à suivre
                      </p>
                    )}
                  </div>
                  {/* 7. Action unique */}
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
