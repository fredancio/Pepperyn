'use client';

/**
 * PortfolioHome — Portfolio Intelligence, Incréments 1 + 2 (Capability 7),
 * évolution "écran d'accueil quotidien" (2026-08-05).
 *
 * Écran unique : résumé de situation + liste de cartes triées par priorité,
 * une carte par client, portant son point le plus prioritaire du Briefing
 * de revue. "Préparer cette revue" ouvre /app/chat avec ce client
 * pré-sélectionné (voir ChatContainer.tsx::searchParams).
 *
 * RÈGLE DE CETTE ÉVOLUTION : uniquement de la présentation. Aucun nouveau
 * calcul, aucun nouvel appel réseau, aucune donnée inventée — le résumé de
 * situation et l'enrichissement des cartes ne font que réorganiser/agréger
 * ce que `cards` (PortfolioCard[], déjà reçu de fetchPortfolio()) contient
 * déjà. L'ordre des cartes, les priorités et tri restent entièrement
 * décidés par build_portfolio_briefing() côté backend — inchangé.
 *
 * Hiérarchie de la carte (Incrément 2 + évolution accueil quotidien) :
 * organisation + priorité (même ligne, priorité au nom de l'organisation) →
 * titre du point → contexte (ancienneté, why_it_matters si distinct,
 * nombre de sujets actifs) → action. Une seule action, jamais de menu,
 * filtre, score, widget, donnée financière, bouton d'abandon ni aperçu du
 * briefing.
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
 *   - date de dernière revue / dernière analyse, nombre de décisions
 *     confirmées distinct du nombre de sujets actifs : pas de champ
 *     backend correspondant aujourd'hui — volontairement non affiché
 *     plutôt qu'approximé (voir rapport de validation associé).
 *
 * Organisation Sharing Demo (2026-08-05) : point d'entrée "Partager
 * l'organisation" ajouté sur chaque carte, strictement gardé par
 * isDemoModeEnabled() — ce composant est partagé avec /app/portfolio (vrai
 * portefeuille authentifié) et la simulation de partage n'a aucun sens ni
 * autorisation d'apparaître hors du prototype de démonstration. Action
 * volontairement secondaire (lien texte discret, pas un bouton plein) pour
 * ne jamais concurrencer "Préparer cette revue" comme second CTA principal.
 * Aucune autre modification de la carte, du tri ou des données.
 */

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { fetchPortfolio } from '@/lib/arc-api';
import { isDemoModeEnabled } from '@/lib/demo-mode';
import { ShareOrganizationPanel } from '@/components/sharing/ShareOrganizationPanel';
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
  const [shareTarget, setShareTarget] = useState<{ id: string; name: string } | null>(null);
  const demoMode = isDemoModeEnabled();

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

  // Résumé de situation — pure agrégation côté client de `cards`, déjà reçu
  // de fetchPortfolio(). Aucun nouveau calcul métier : les 3 catégories
  // reprennent exactement les priorités déjà décidées par le backend
  // (BRIEFING_PRIORITY_ORDER / _arc_to_briefing_item) ; "closed" n'apparaît
  // jamais ici car build_portfolio_briefing() ne produit jamais de carte
  // dont le point principal est clos.
  const urgentCount = cards.filter((c) => c.top_item.priority === 'urgent').length;
  const toCheckCount = cards.filter((c) => c.top_item.priority === 'to_check').length;
  const doneCount = cards.filter((c) => c.top_item.priority === 'done').length;
  const summaryParts = [
    urgentCount > 0 ? `${urgentCount} urgente${urgentCount > 1 ? 's' : ''}` : null,
    toCheckCount > 0 ? `${toCheckCount} à vérifier` : null,
    doneCount > 0 ? `${doneCount} apprentissage${doneCount > 1 ? 's' : ''} à valider` : null,
  ].filter((p): p is string => p !== null);

  return (
    <div className="min-h-screen bg-[#EFF6FF] px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-xl font-extrabold text-[#1A1A2E] mb-1">Portefeuille</h1>

        {state === 'loaded' && cards.length > 0 && (
          <div className="mb-6" data-testid="portfolio-summary">
            <p className="text-sm text-[#1A1A2E]">
              <span className="font-semibold">{cards.length}</span> organisation
              {cards.length > 1 ? 's' : ''} demande{cards.length > 1 ? 'nt' : ''} votre attention.
            </p>
            {summaryParts.length > 0 && (
              <p className="text-xs text-[#5F6368] mt-1">{summaryParts.join(' · ')}</p>
            )}
          </div>
        )}

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
                    {/* 1 + 2. Organisation d'abord (regard), priorité juste à côté */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-bold text-[#1A1A2E] truncate">{card.entity_name}</p>
                      <span className="shrink-0 inline-flex items-center gap-1 text-xs font-semibold text-[#5F6368]">
                        <span aria-hidden="true">{meta.icon}</span> {meta.label}
                      </span>
                    </div>
                    {/* 3. Titre du point principal */}
                    <p className="text-sm text-[#5F6368] mt-1 truncate">{card.top_item.title}</p>
                    {/* 4. Contexte — regroupé : ancienneté, why_it_matters, sujets actifs */}
                    <div className="mt-1.5 space-y-1">
                      <p
                        className="text-xs text-[#5F6368]"
                        data-testid={`portfolio-temporal-${card.entity_id}`}
                      >
                        {card.top_item.temporal_context}
                      </p>
                      {/* why_it_matters — uniquement quand distinct (décidé côté backend) */}
                      {card.why_it_matters_display && (
                        <p
                          className="text-xs text-[#1A1A2E]"
                          data-testid={`portfolio-why-${card.entity_id}`}
                        >
                          {card.why_it_matters_display}
                        </p>
                      )}
                      {/* Sujets actifs — uniquement si d'autres points actifs existent :
                          un seul sujet actif n'ajoute aucune information au-delà du
                          titre déjà affiché ci-dessus. */}
                      {card.other_active_count > 0 && (
                        <p
                          className="text-xs text-[#5F6368]"
                          data-testid={`portfolio-counter-${card.entity_id}`}
                        >
                          <span className="inline-block px-1.5 py-0.5 rounded-full bg-gray-50 border border-gray-200">
                            +{card.other_active_count} autre{card.other_active_count > 1 ? 's' : ''} point
                            {card.other_active_count > 1 ? 's' : ''} à suivre
                          </span>
                        </p>
                      )}
                    </div>
                  </div>
                  {/* 7. Action principale + (démo uniquement) action secondaire de partage */}
                  <div className="shrink-0 flex flex-col items-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => handlePrepareReview(card.entity_id)}
                      className="text-xs font-semibold text-white bg-[#1B73E8] hover:bg-[#0D47A1] rounded-lg px-3 py-2 transition-colors"
                    >
                      Préparer cette revue
                    </button>
                    {demoMode && (
                      <button
                        type="button"
                        onClick={() => setShareTarget({ id: card.entity_id, name: card.entity_name })}
                        className="text-[11px] font-medium text-[#5F6368] hover:text-[#1B73E8] underline-offset-2 hover:underline"
                        data-testid={`portfolio-share-${card.entity_id}`}
                      >
                        Partager l&apos;organisation
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {demoMode && shareTarget && (
          <ShareOrganizationPanel
            entityId={shareTarget.id}
            entityName={shareTarget.name}
            onClose={() => setShareTarget(null)}
          />
        )}
      </div>
    </div>
  );
}
