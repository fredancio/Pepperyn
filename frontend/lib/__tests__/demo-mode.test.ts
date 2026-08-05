/**
 * Garde-fou du mode démo — External User Testing Prototype (2026-08-05).
 *
 * Ces tests sont le seul rempart automatisé contre une activation
 * accidentelle du mode démo en production (Mission 2 du mandat : "Ajouter
 * un garde-fou explicite vérifié par test"). isDemoModeEnabled() lit
 * process.env directement à chaque appel (pas de valeur figée au chargement
 * du module), donc chaque cas peut être testé en manipulant process.env
 * sans réinitialiser les modules.
 */
import { isDemoModeEnabled, DEMO_BANNER_TEXT } from '../demo-mode';

describe('isDemoModeEnabled', () => {
  const ORIGINAL_ENV = process.env;

  beforeEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  afterAll(() => {
    process.env = ORIGINAL_ENV;
  });

  it('est désactivé quand le drapeau démo est absent', () => {
    delete process.env.NEXT_PUBLIC_DEMO_MODE;
    process.env.NEXT_PUBLIC_VERCEL_ENV = 'preview';
    expect(isDemoModeEnabled()).toBe(false);
  });

  it('est désactivé quand le drapeau démo vaut une chaîne autre que "true"', () => {
    process.env.NEXT_PUBLIC_DEMO_MODE = 'yes';
    process.env.NEXT_PUBLIC_VERCEL_ENV = 'preview';
    expect(isDemoModeEnabled()).toBe(false);
  });

  it('est activé quand le drapeau est "true" et l\'environnement est preview', () => {
    process.env.NEXT_PUBLIC_DEMO_MODE = 'true';
    process.env.NEXT_PUBLIC_VERCEL_ENV = 'preview';
    expect(isDemoModeEnabled()).toBe(true);
  });

  it('est activé quand le drapeau est "true" et l\'environnement est absent (dev local)', () => {
    process.env.NEXT_PUBLIC_DEMO_MODE = 'true';
    delete process.env.NEXT_PUBLIC_VERCEL_ENV;
    expect(isDemoModeEnabled()).toBe(true);
  });

  it('est activé quand le drapeau est "true" et l\'environnement est "development"', () => {
    process.env.NEXT_PUBLIC_DEMO_MODE = 'true';
    process.env.NEXT_PUBLIC_VERCEL_ENV = 'development';
    expect(isDemoModeEnabled()).toBe(true);
  });

  it('RÈGLE DE SÉCURITÉ CRITIQUE — reste désactivé en production même si le drapeau démo est positionné à "true"', () => {
    process.env.NEXT_PUBLIC_DEMO_MODE = 'true';
    process.env.NEXT_PUBLIC_VERCEL_ENV = 'production';
    expect(isDemoModeEnabled()).toBe(false);
  });

  it('reste désactivé en production quand le drapeau démo est absent (cas nominal)', () => {
    delete process.env.NEXT_PUBLIC_DEMO_MODE;
    process.env.NEXT_PUBLIC_VERCEL_ENV = 'production';
    expect(isDemoModeEnabled()).toBe(false);
  });

  it('expose un texte de bandeau non vide et stable', () => {
    expect(DEMO_BANNER_TEXT).toBe('Prototype de test — données fictives');
  });
});
