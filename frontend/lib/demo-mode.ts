/**
 * Mode démo — External User Testing Prototype (2026-08-05).
 *
 * Garde-fou central : décide si le mode démo est actif. Toute fonction de
 * lib/arc-api.ts et lib/api.ts qui doit rester strictement isolée (aucun
 * appel Supabase, aucun appel LLM, aucune écriture) consulte cette seule
 * fonction avant de faire quoi que ce soit.
 *
 * RÈGLE DE SÉCURITÉ (non négociable) : le mode démo ne peut JAMAIS s'activer
 * en production, même si NEXT_PUBLIC_DEMO_MODE est positionné par erreur
 * dans les réglages d'environnement Production de Vercel. C'est un
 * garde-fou en profondeur, indépendant de la configuration humaine —
 * vérifié par test (voir __tests__/demo-mode.test.ts).
 *
 * process.env.VERCEL_ENV est fourni automatiquement par Vercel à la
 * construction ('production' | 'preview' | 'development') — jamais 'production'
 * sur une Preview Deployment, donc jamais en conflit avec un usage légitime
 * du mode démo sur une branche prototype.
 */
export function isDemoModeEnabled(): boolean {
  const flagRequested = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';
  const isProductionEnvironment = process.env.NEXT_PUBLIC_VERCEL_ENV === 'production';
  return flagRequested && !isProductionEnvironment;
}

/** Libellé du bandeau d'identification — Mission 7. Jamais modifiable en runtime. */
export const DEMO_BANNER_TEXT = 'Prototype de test — données fictives';
