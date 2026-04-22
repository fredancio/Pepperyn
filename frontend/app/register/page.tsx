'use client';
import { useState } from 'react';
import { signUpAdmin } from '@/lib/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import Link from 'next/link';

type Step = 'form' | 'confirmation';

const BUSINESS_MODELS = [
  { value: 'produits', label: 'Vente de produits' },
  { value: 'services', label: 'Vente de services' },
  { value: 'mixte', label: 'Mixte' },
  { value: 'autre', label: 'Autre' },
];

export default function RegisterPage() {
  const [step, setStep] = useState<Step>('form');
  const [prenom, setPrenom] = useState('');
  const [email, setEmail] = useState('');
  const [industry, setIndustry] = useState('');
  const [businessModel, setBusinessModel] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [acceptCgu, setAcceptCgu] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prenom || !email || !industry || !businessModel || !password) {
      setError('Veuillez remplir tous les champs');
      return;
    }
    if (!acceptCgu) {
      setError('Veuillez accepter les CGU et la politique de confidentialité');
      return;
    }
    if (password !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas');
      return;
    }
    if (password.length < 8) {
      setError('Le mot de passe doit contenir au moins 8 caractères');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await signUpAdmin(email, password, prenom, industry, businessModel);
      setStep('confirmation');
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'inscription");
    } finally {
      setLoading(false);
    }
  };

  if (step === 'confirmation') {
    return (
      <div className="min-h-screen bg-[#EFF6FF] flex flex-col items-center justify-center px-4 py-12">
        <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 border border-gray-100 text-center">
          {/* Logo */}
          <img src="/favicon.png?v=4" alt="Pepperyn" className="w-20 h-20 mx-auto mb-4 object-contain" />

          {/* Success icon */}
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>

          <h2 className="text-2xl font-bold text-[#1A1A2E] mb-2">
            ✅ Votre espace Pepperyn est créé !
          </h2>
          <p className="text-[#5F6368] mb-6">
            Bienvenue, <strong>{prenom}</strong>. Votre espace est prêt.
          </p>

          {/* Email verification notice */}
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6 text-left">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-amber-800">Vérifiez votre email</p>
                <p className="text-xs text-amber-700 mt-0.5">
                  Un lien de confirmation a été envoyé à <strong>{email}</strong>. Cliquez dessus pour activer votre compte.
                </p>
              </div>
            </div>
          </div>

          <Button
            size="lg"
            className="w-full"
            onClick={() => window.location.href = '/app/chat'}
          >
            Accéder à Pepperyn →
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#EFF6FF] flex flex-col items-center justify-center px-4 py-12">
      {/* Logo */}
      <div className="mb-8 flex flex-col items-center gap-3">
        <img src="/favicon.png?v=4" alt="Pepperyn" className="w-20 h-20 object-contain" />
        <div className="text-center">
          <h1 className="text-2xl font-bold text-[#1A1A2E]">Créer votre espace entreprise</h1>
          <p className="text-sm text-[#5F6368]">Commencez avec 3 analyses gratuites</p>
        </div>
      </div>

      {/* Card */}
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">

          {/* Prénom */}
          <Input
            label="Votre prénom"
            type="text"
            value={prenom}
            onChange={e => setPrenom(e.target.value)}
            placeholder="Marie"
            autoComplete="given-name"
            required
          />

          {/* Industrie */}
          <Input
            label="Industrie"
            type="text"
            value={industry}
            onChange={e => setIndustry(e.target.value)}
            placeholder="Ex : SaaS, Retail, Industrie..."
            required
          />

          {/* Business Model */}
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[#1A1A2E]">Business Model</label>
            <select
              value={businessModel}
              onChange={e => setBusinessModel(e.target.value)}
              required
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm text-[#1A1A2E] bg-white focus:outline-none focus:ring-2 focus:ring-[#1B73E8] focus:border-transparent"
            >
              <option value="">Sélectionnez...</option>
              {BUSINESS_MODELS.map(bm => (
                <option key={bm.value} value={bm.value}>{bm.label}</option>
              ))}
            </select>
          </div>

          {/* Email */}
          <Input
            label="Adresse email professionnelle"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="vous@entreprise.com"
            autoComplete="email"
            required
          />

          {/* Mot de passe */}
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[#1A1A2E]">Mot de passe</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Minimum 8 caractères"
                autoComplete="new-password"
                required
                className="w-full border border-gray-200 rounded-xl px-4 py-3 pr-10 text-sm text-[#1A1A2E] focus:outline-none focus:ring-2 focus:ring-[#1B73E8] focus:border-transparent"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#5F6368] hover:text-[#1A1A2E]"
              >
                {showPassword ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Confirmer mot de passe */}
          <Input
            label="Confirmer le mot de passe"
            type="password"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="new-password"
            required
          />

          {/* CGU checkbox */}
          <div className="flex items-start gap-2.5">
            <input
              type="checkbox"
              id="accept-cgu"
              checked={acceptCgu}
              onChange={e => setAcceptCgu(e.target.checked)}
              className="mt-1 w-4 h-4 rounded border-gray-300 text-[#1B73E8] focus:ring-[#1B73E8] cursor-pointer"
            />
            <label htmlFor="accept-cgu" className="text-sm text-[#5F6368] leading-snug cursor-pointer">
              J'accepte les{' '}
              <Link href="/legal/cgu" target="_blank" className="text-[#1B73E8] hover:underline">CGU</Link>
              {' '}et la{' '}
              <Link href="/legal/confidentialite" target="_blank" className="text-[#1B73E8] hover:underline">politique de confidentialité</Link>
            </label>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Plan info */}
          <div className="bg-[#EFF6FF] border border-blue-100 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-1">
              <svg className="w-4 h-4 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm font-medium text-[#1B73E8]">Plan gratuit inclus</span>
            </div>
            <p className="text-xs text-[#5F6368]">3 analyses offertes · Pas de carte bancaire requise</p>
          </div>

          <Button type="submit" loading={loading} className="w-full" size="lg">
            {loading ? 'Création de votre espace...' : 'Créer mon espace →'}
          </Button>

          <p className="text-center text-sm text-[#5F6368]">
            Déjà un compte ?{' '}
            <Link href="/login" className="text-[#1B73E8] hover:underline font-medium">
              Se connecter
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
