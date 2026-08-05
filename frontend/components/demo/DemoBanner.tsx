'use client';

/**
 * Bandeau d'identification du prototype — External User Testing Prototype
 * (2026-08-05), Mission 7.
 *
 * Doit rester visuellement secondaire et ne jamais concurrencer la
 * hiérarchie du Portfolio ou du Review Briefing (règle explicite du
 * mandat) : une seule ligne fine, discrète, en haut de la page, jamais
 * un encart imposant ni une modale.
 *
 * Porte aussi le lien de feedback (Mission 6) — option B du mandat : un
 * lien mailto: préformaté, le moins intrusif des trois options proposées.
 * Aucune donnée de feedback n'est stockée dans Pepperyn : le message part
 * directement du client de messagerie du testeur, jamais via un formulaire
 * ou une écriture Supabase.
 */
import { DEMO_BANNER_TEXT } from '@/lib/demo-mode';

const FEEDBACK_MAILTO =
  'mailto:fredanciaux16@gmail.com' +
  '?subject=' + encodeURIComponent('Retour — Prototype de test Pepperyn') +
  '&body=' + encodeURIComponent(
    'Merci de tester ce prototype de démonstration.\n\n' +
    "Qu'avez-vous compris en premier ? Qu'est-ce qui vous a semblé peu clair ?\n\n"
  );

export function DemoBanner() {
  return (
    <div
      className="w-full bg-amber-50 border-b border-amber-200 py-1.5 px-4 flex items-center justify-center gap-3 flex-wrap"
      data-testid="demo-banner"
    >
      <p className="text-xs font-medium text-amber-800">
        <span aria-hidden="true">🧪</span> {DEMO_BANNER_TEXT}
      </p>
      <a
        href={FEEDBACK_MAILTO}
        className="text-xs font-medium text-amber-700 underline hover:text-amber-900"
        data-testid="demo-feedback-link"
      >
        Donner mon retour
      </a>
    </div>
  );
}
