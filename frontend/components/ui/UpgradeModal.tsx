'use client';
import { useEffect } from 'react';
import type { Feature, FeatureMeta } from '@/lib/featureGate';
import { FEATURE_META } from '@/lib/featureGate';
import Link from 'next/link';

interface UpgradeModalProps {
  feature: Feature;
  onClose: () => void;
}

const PLAN_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  PRO:   { bg: 'bg-blue-600',   text: 'text-white',  border: 'border-blue-200' },
  POWER: { bg: 'bg-amber-500',  text: 'text-white',  border: 'border-amber-200' },
  SCALE: { bg: 'bg-purple-600', text: 'text-white',  border: 'border-purple-200' },
};

export function UpgradeModal({ feature, onClose }: UpgradeModalProps) {
  const meta: FeatureMeta | null = FEATURE_META[feature];
  if (!meta) return null;

  const colors = PLAN_COLORS[meta.requiredPlan] ?? PLAN_COLORS.PRO;

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">

        {/* Header */}
        <div className="bg-[#0A2540] p-6 relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-7 h-7 flex items-center justify-center text-slate-400 hover:text-white transition-colors rounded-lg hover:bg-white/10"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <div className="text-4xl mb-3">{meta.emoji}</div>
          <h2 className="text-white font-extrabold text-xl leading-tight mb-1">
            {meta.label}
          </h2>
          <p className="text-slate-300 text-sm leading-snug">{meta.description}</p>
        </div>

        {/* Plan badge */}
        <div className={`px-6 py-3 flex items-center gap-3 border-b ${colors.border} bg-opacity-5`}>
          <span className={`px-3 py-1 rounded-full text-xs font-bold ${colors.bg} ${colors.text}`}>
            {meta.requiredPlan}
          </span>
          <span className="text-sm text-[#5F6368]">
            Disponible à partir de <span className="font-semibold text-[#1A1A2E]">{meta.requiredPlanPrice}</span>
          </span>
        </div>

        {/* Benefits */}
        <div className="p-6">
          <p className="text-xs font-semibold text-[#5F6368] uppercase tracking-widest mb-3">
            Inclus dans le plan {meta.requiredPlan}
          </p>
          <ul className="flex flex-col gap-2 mb-6">
            {meta.benefits.map((b, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <svg className="w-4 h-4 flex-shrink-0 mt-0.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-[#1A1A2E]">{b}</span>
              </li>
            ))}
          </ul>

          {/* CTAs */}
          <div className="flex flex-col gap-2">
            <Link
              href="/upgrade"
              onClick={onClose}
              className={`w-full py-3 rounded-xl font-bold text-sm text-center transition-all ${colors.bg} ${colors.text} hover:opacity-90`}
            >
              Voir les plans et tarifs →
            </Link>
            <button
              onClick={onClose}
              className="w-full py-2.5 rounded-xl text-sm text-[#5F6368] hover:bg-gray-50 transition-colors"
            >
              Continuer avec mon plan actuel
            </button>
          </div>
        </div>

        {/* Bottom reassurance */}
        <div className="px-6 pb-4 text-center">
          <p className="text-xs text-[#5F6368] italic">
            Sans engagement · Annulable à tout moment · Aucune carte bancaire requise pour l&apos;essai
          </p>
        </div>
      </div>
    </div>
  );
}
