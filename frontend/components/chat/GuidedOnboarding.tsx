'use client';
import { useState } from 'react';
import Link from 'next/link';

interface Step {
  id: string;
  question: string;
  choices: { label: string; value: string; emoji: string }[];
}

const STEPS: Step[] = [
  {
    id: 'what',
    question: 'Qu\'est-ce que vous souhaitez analyser ?',
    choices: [
      { label: 'Mon compte de résultat ou P&L', value: 'pl', emoji: '📊' },
      { label: 'Mon bilan et une analyse financière complète', value: 'complete', emoji: '📈' },
      { label: 'Mon budget ou prévisionnel', value: 'budget', emoji: '🎯' },
      { label: 'Ma trésorerie ou cash flow', value: 'cashflow', emoji: '💰' },
      { label: 'Je ne sais pas encore', value: 'unknown', emoji: '🤔' },
    ],
  },
  {
    id: 'source',
    question: 'D\'où vient votre fichier ?',
    choices: [
      { label: 'Mon expert-comptable me l\'a envoyé', value: 'accountant', emoji: '👔' },
      { label: 'Il vient d\'un logiciel (Exact, Odoo, Sage…)', value: 'software', emoji: '💻' },
      { label: 'Je l\'ai créé moi-même dans Excel', value: 'self', emoji: '✏️' },
      { label: 'Je n\'ai pas encore de fichier', value: 'none', emoji: '📂' },
    ],
  },
];

const COPILOT_TIP = "✨ **Astuce Copilot** : Si votre fichier est complexe ou mal structuré, ouvrez-le dans Excel 365, cliquez sur le bouton **Copilot** (✨ en haut à droite du ruban), et demandez-lui : *\"Restructure ce tableau en compte de résultat mensuel clair avec des en-têtes explicites\"*. En 30 secondes, votre fichier sera propre et prêt pour Pepperyn. [En savoir plus](/guide-donnees)";

const GUIDANCE: Record<string, Record<string, string>> = {
  pl: {
    accountant: "Votre comptable vous a envoyé un compte de résultat — c'est parfait ! Assurez-vous qu'il est en format **.xlsx** (pas PDF). S'il est en PDF, demandez-lui la version Excel. Uploadez directement ce fichier dans Pepperyn.\n\n" + COPILOT_TIP,
    software: "Depuis votre logiciel, exportez le **Compte de résultat** ou **P&L** en Excel (.xlsx). Dans **Exact Online** : Rapports → Compte de résultat → Exporter. Dans **Odoo** : Comptabilité → Rapports → Bilan des revenus → Excel. Dans **Sage** : Analyse → P&L → Export.\n\n" + COPILOT_TIP,
    self: "Si vous avez créé votre P&L vous-même, assurez-vous que : **ligne 1** = en-têtes (Jan, Fév, Mar…), **colonne A** = noms des postes (CA, Charges, Résultat…), et que les cellules contiennent des chiffres.\n\n" + COPILOT_TIP,
    none: "Pas de problème ! Consultez notre [guide de préparation](/guide-donnees) — il vous explique étape par étape comment obtenir le bon fichier depuis votre comptable ou votre logiciel.\n\n" + COPILOT_TIP,
  },
  complete: {
    accountant: "Votre comptable peut vous transmettre à la fois votre **bilan** et votre **compte de résultat** (P&L) — demandez les deux en format **.xlsx** (pas PDF). Uploadez les deux fichiers dans Pepperyn pour une analyse financière complète : rentabilité, structure financière et équilibre du bilan.\n\n" + COPILOT_TIP,
    software: "Exportez votre **bilan** et votre **compte de résultat** depuis votre logiciel en Excel (.xlsx). Dans **Exact Online** : Rapports → Bilan / Compte de résultat → Exporter. Dans **Odoo** : Comptabilité → Rapports → Bilan / Bilan des revenus → Excel. Dans **Sage** : Analyse → Bilan / P&L → Export.\n\n" + COPILOT_TIP,
    self: "Pour une analyse complète, préparez deux fichiers (ou deux onglets) : un pour le **bilan** (actif / passif) et un pour le **compte de résultat** (charges / produits). Respectez le format : **ligne 1** = en-têtes (Jan, Fév, Mar…), **colonne A** = noms des postes, et des cellules au format nombre.\n\n" + COPILOT_TIP,
    none: "Pas de problème ! Consultez notre [guide de préparation](/guide-donnees) — il vous explique comment obtenir votre bilan et votre compte de résultat auprès de votre comptable ou de votre logiciel, pour une analyse financière complète.\n\n" + COPILOT_TIP,
  },
  budget: {
    accountant: "Demandez à votre comptable un export Excel de votre **budget vs réalisé** avec 3 colonnes : Poste | Budget | Réel. Pepperyn détectera automatiquement les écarts et les expliquera.\n\n" + COPILOT_TIP,
    software: "Exportez depuis votre logiciel le rapport **Budget vs Réel** ou **Prévisionnel vs Réalisé** en Excel. La plupart des logiciels ont cette fonction dans la section Rapports ou Analyses.\n\n" + COPILOT_TIP,
    self: "Pour un budget, structurez votre fichier en 3 colonnes minimum : **Poste** | **Budget prévu** | **Réalisé**. Ajoutez les mois en colonnes si vous avez un suivi mensuel.\n\n" + COPILOT_TIP,
    none: "Consultez notre [guide de préparation](/guide-donnees) pour savoir comment créer ou obtenir un fichier budget adapté.\n\n" + COPILOT_TIP,
  },
  cashflow: {
    accountant: "Demandez à votre comptable un **tableau de flux de trésorerie** en Excel. Si vous n'en avez pas, un export de votre compte bancaire en CSV fonctionne aussi.\n\n" + COPILOT_TIP,
    software: "Exportez le **tableau de trésorerie** ou **cash flow** de votre logiciel. Dans la plupart des ERP : Comptabilité → Rapports de trésorerie → Export Excel.\n\n" + COPILOT_TIP,
    self: "Structurez votre fichier avec : **Date** | **Catégorie** | **Entrée** | **Sortie** | **Solde**. Chaque ligne = un flux. Pepperyn identifiera les tendances et les risques.\n\n" + COPILOT_TIP,
    none: "Exportez votre **historique bancaire** en Excel ou CSV depuis votre banque en ligne. Pepperyn peut analyser directement un relevé bancaire structuré.\n\n" + COPILOT_TIP,
  },
  unknown: {
    accountant: "Uploadez le fichier reçu — Pepperyn détectera automatiquement de quoi il s'agit. Si le fichier est en PDF, demandez la version Excel à votre comptable.\n\n" + COPILOT_TIP,
    software: "Exportez n'importe quel rapport financier de votre logiciel en Excel. Pepperyn reconnaît automatiquement le type de document et adapte son analyse.\n\n" + COPILOT_TIP,
    self: "Uploadez votre fichier tel quel. Pepperyn analysera sa structure et vous guidera si quelque chose doit être amélioré.\n\n" + COPILOT_TIP,
    none: "Consultez notre [guide de préparation](/guide-donnees) — il vous explique exactement comment obtenir le bon fichier depuis votre comptable ou votre logiciel.\n\n" + COPILOT_TIP,
  },
};

interface GuidedOnboardingProps {
  onClose?: () => void;
}

export function GuidedOnboarding({ onClose }: GuidedOnboardingProps) {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [done, setDone] = useState(false);

  const currentStep = STEPS[step];
  const guidance = done
    ? GUIDANCE[answers.what]?.[answers.source] || ''
    : null;

  const handleChoice = (value: string) => {
    const newAnswers = { ...answers, [currentStep.id]: value };
    setAnswers(newAnswers);
    if (step < STEPS.length - 1) {
      setStep(step + 1);
    } else {
      setDone(true);
    }
  };

  const renderGuidance = (text: string) => {
    // Simple markdown: **bold**, [link](url)
    const parts = text.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      if (linkMatch) {
        return <Link key={i} href={linkMatch[2]} className="text-[#1B73E8] underline">{linkMatch[1]}</Link>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="rounded-2xl border border-[#1B73E8]/20 bg-[#EFF6FF] overflow-hidden max-w-lg">

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 bg-[#1B73E8] ">
        <div className="flex items-center gap-2.5">
          <span className="text-white text-lg">🧭</span>
          <p className="font-bold text-white text-sm">Guide de démarrage</p>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-white/70 hover:text-white transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      <div className="px-5 py-4">
        {!done ? (
          <>
            {/* Progress */}
            <div className="flex gap-1.5 mb-4">
              {STEPS.map((_, i) => (
                <div
                  key={i}
                  className={`h-1 flex-1 rounded-full transition-all ${i <= step ? 'bg-[#1B73E8]' : 'bg-blue-200'}`}
                />
              ))}
            </div>

            <p className="font-semibold text-[#1A1A2E] text-sm mb-3">
              {currentStep.question}
            </p>

            <div className="flex flex-col gap-2">
              {currentStep.choices.map((choice) => (
                <button
                  key={choice.value}
                  onClick={() => handleChoice(choice.value)}
                  className="flex items-center gap-3 px-4 py-3 bg-white rounded-xl border border-blue-100 hover:border-[#1B73E8] hover:bg-white transition-all text-left group"
                >
                  <span className="text-lg">{choice.emoji}</span>
                  <span className="text-sm text-[#1A1A2E] group-hover:text-[#1B73E8] font-medium">{choice.label}</span>
                </button>
              ))}
            </div>
          </>
        ) : (
          <>
            {/* Résultat */}
            <div className="flex items-start gap-2.5 mb-4">
              <span className="text-xl flex-shrink-0">✅</span>
              <p className="text-sm text-[#1A1A2E] leading-relaxed font-medium">
                Voici exactement ce que vous devez faire :
              </p>
            </div>

            <div className="bg-white rounded-xl border border-[#1B73E8]/20 p-4 mb-4">
              <p className="text-sm text-[#1A1A2E] leading-relaxed">
                {guidance && renderGuidance(guidance)}
              </p>
            </div>

            <div className="flex flex-col gap-2">
              <p className="text-xs font-semibold text-[#5F6368] uppercase tracking-wide mb-1">
                Ressources utiles
              </p>
              <Link
                href="/guide-donnees"
                className="flex items-center gap-2.5 px-4 py-2.5 bg-white rounded-xl border border-blue-100 hover:border-[#1B73E8] transition-all group"
              >
                <span className="text-base">📖</span>
                <span className="text-sm text-[#1B73E8] font-medium group-hover:underline">
                  Guide complet de préparation des données
                </span>
              </Link>
              <button
                onClick={() => { setStep(0); setAnswers({}); setDone(false); }}
                className="text-xs text-[#5F6368] hover:text-[#1A1A2E] transition-colors mt-1"
              >
                ← Recommencer le guide
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
