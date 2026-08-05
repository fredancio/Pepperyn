/**
 * Garantie de COMPILATION — External User Testing Prototype (2026-08-05).
 *
 * Suite à la revue de Fred sur PORTFOLIO_EXTERNAL_PROTOTYPE_REVIEW.md
 * section 7 : quand NEXT_PUBLIC_DEMO_MODE=true, aucune vraie variable
 * NEXT_PUBLIC_SUPABASE_* ne doit être inlinée dans le bundle, quelle que
 * soit la configuration d'environnement Vercel. next.config.js écrase ces
 * variables par une valeur factice avant que Next.js ne construise son
 * DefinePlugin — ce test exécute directement ce module et vérifie l'effet
 * sur process.env, sans avoir besoin d'un build Next.js complet.
 *
 * Preuve complémentaire par build réel (manuelle, documentée dans
 * PORTFOLIO_EXTERNAL_PROTOTYPE_REVIEW.md) : grep de .next/static après
 * `next build` avec NEXT_PUBLIC_DEMO_MODE=true confirme l'absence totale
 * de la vraie URL/clé dans les fichiers statiques générés.
 */
describe('next.config.js — garantie de compilation (mode démo)', () => {
  const ORIGINAL_ENV = process.env;

  beforeEach(() => {
    process.env = { ...ORIGINAL_ENV };
    jest.resetModules();
  });

  afterAll(() => {
    process.env = ORIGINAL_ENV;
  });

  it('écrase NEXT_PUBLIC_SUPABASE_URL et NEXT_PUBLIC_SUPABASE_ANON_KEY quand NEXT_PUBLIC_DEMO_MODE=true', () => {
    process.env.NEXT_PUBLIC_DEMO_MODE = 'true';
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://real-project-id.supabase.co';
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'real-anon-key-value';

    require('../next.config.js');

    expect(process.env.NEXT_PUBLIC_SUPABASE_URL).not.toBe('https://real-project-id.supabase.co');
    expect(process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY).not.toBe('real-anon-key-value');
    expect(process.env.NEXT_PUBLIC_SUPABASE_URL).toBe('https://demo-mode-disabled.invalid');
    expect(process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY).toBe('demo-mode-disabled');
  });

  it('ne touche jamais les variables Supabase quand NEXT_PUBLIC_DEMO_MODE est absent (build réel inchangé)', () => {
    delete process.env.NEXT_PUBLIC_DEMO_MODE;
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://real-project-id.supabase.co';
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'real-anon-key-value';

    require('../next.config.js');

    expect(process.env.NEXT_PUBLIC_SUPABASE_URL).toBe('https://real-project-id.supabase.co');
    expect(process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY).toBe('real-anon-key-value');
  });

  it('ne touche jamais les variables Supabase quand NEXT_PUBLIC_DEMO_MODE="false"', () => {
    process.env.NEXT_PUBLIC_DEMO_MODE = 'false';
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://real-project-id.supabase.co';
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'real-anon-key-value';

    require('../next.config.js');

    expect(process.env.NEXT_PUBLIC_SUPABASE_URL).toBe('https://real-project-id.supabase.co');
    expect(process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY).toBe('real-anon-key-value');
  });
});
