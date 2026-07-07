'use client';

import { useState } from 'react';

/* ─── Types ─────────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'decisions', label: 'Décisions' },
  { id: 'temps',     label: 'Temps économisé' },
  { id: 'valeur',    label: 'Valeur créée' },
  { id: 'risque',    label: 'Risque réduit' },
  { id: 'codir',     label: 'CODIR préparés' },
] as const;

type TabId = typeof TABS[number]['id'];

interface Card {
  prefix?: string;
  value: string;
  title: string;
  benefit: string;
  detail: string;
  activeTabs: TabId[];
}

/* ─── Data ───────────────────────────────────────────────────────────────── */
const CARDS: Card[] = [
  {
    value:      '3',
    title:      'Décisions prioritaires',
    benefit:    'Vous savez immédiatement quoi faire en premier.',
    detail:     'Au lieu de parcourir des dizaines de pages de reporting.',
    activeTabs: ['decisions', 'risque'],
  },
  {
    prefix:     'Jusqu\'à',
    value:      '~30 h',
    title:      'Récupérées chaque semaine',
    benefit:    'Moins de préparation. Plus de décisions.',
    detail:     'Pour une équipe financière de 4 personnes.',
    activeTabs: ['temps'],
  },
  {
    prefix:     'ROI en',
    value:      '< 1 mois',
    title:      'Retour sur investissement',
    benefit:    'Une seule bonne décision peut amortir l\'abonnement.',
    detail:     'Potentiel estimé, pas une garantie.',
    activeTabs: ['valeur', 'risque'],
  },
  {
    value:      '3',
    title:      'Livrables exécutifs',
    benefit:    'Executive Report · Board Deck · Financial Model',
    detail:     'Des supports directement exploitables pour votre CODIR.',
    activeTabs: ['codir'],
  },
];

/* ─── Component ──────────────────────────────────────────────────────────── */
export function ProofSection() {
  const [activeTab, setActiveTab] = useState<TabId | null>(null);

  function handleTab(id: TabId) {
    setActiveTab(prev => (prev === id ? null : id));
  }

  return (
    <section className="py-20 lg:py-24 bg-[#F8FAFF] border-t border-[#1B73E8]/10">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* ── Header ── */}
        <div className="text-center mb-14">
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight max-w-2xl mx-auto">
            Ce qui change dès la première analyse.
          </h2>
        </div>

        {/* ── Cards grid ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-px bg-gray-100 rounded-2xl overflow-hidden shadow-sm mb-10">
          {CARDS.map((card) => {
            const isHighlighted = activeTab !== null && card.activeTabs.includes(activeTab);
            const isDimmed      = activeTab !== null && !card.activeTabs.includes(activeTab);

            return (
              <div
                key={card.title}
                className="bg-white px-6 py-10 flex flex-col items-center text-center gap-1.5 transition-opacity duration-200"
                style={{
                  opacity:    isDimmed ? 0.38 : 1,
                  boxShadow:  isHighlighted ? 'inset 0 0 0 2px #1B73E8' : undefined,
                }}
              >
                {/* Qualifier prefix */}
                {card.prefix && (
                  <span className="text-[11px] font-medium text-[#9aa5b4] uppercase tracking-widest leading-none">
                    {card.prefix}
                  </span>
                )}

                {/* Main metric */}
                <span className="text-4xl font-extrabold text-[#1B73E8] tracking-tight leading-none">
                  {card.value}
                </span>

                {/* Benefit title */}
                <span className="text-[13px] font-semibold text-[#1A1A2E] leading-snug max-w-[180px] mt-0.5">
                  {card.title}
                </span>

                {/* Primary detail */}
                <span className="text-xs text-[#5F6368] leading-snug max-w-[180px]">
                  {card.benefit}
                </span>

                {/* Secondary detail — always visible, reinforced when tab active */}
                <span
                  className="text-[11px] leading-snug max-w-[180px] transition-all duration-200"
                  style={{ color: isHighlighted ? '#1B73E8' : '#9aa5b4' }}
                >
                  {card.detail}
                </span>
              </div>
            );
          })}
        </div>

        {/* ── Interactive tabs ── */}
        <div className="flex flex-wrap items-center justify-center gap-3">
          {TABS.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleTab(tab.id)}
                className="px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 cursor-pointer"
                style={{
                  background:  isActive ? '#1B73E8' : 'white',
                  color:       isActive ? 'white'   : '#1A1A2E',
                  border:      isActive ? '1px solid #1B73E8' : '1px solid #e5e7eb',
                  boxShadow:   isActive
                    ? '0 2px 10px rgba(27,115,232,0.30)'
                    : '0 1px 2px rgba(0,0,0,0.05)',
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

      </div>
    </section>
  );
}
