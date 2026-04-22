'use client';
import { useState } from 'react';
import { supabase } from '@/lib/supabase';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import Link from 'next/link';

type Step = 'form' | 'sent';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<Step>('form');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError('Veuillez entrer votre email');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/reset-password`,
      });
      if (resetError) throw resetError;
      setStep('sent');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#EFF6FF] flex flex-col items-center justify-center px-4 py-12">
      {/* Logo */}
      <div className="mb-8 flex flex-col items-center gap-3">
        <div className="w-14 h-14 bg-[#1B73E8] rounded-2xl flex items-center justify-center shadow-lg">
          <img src="/favicon.png?v=4" alt="Pepperyn" className="w-12 h-12 object-contain" />
        </div>
      </div>

      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
        {step === 'sent' ? (
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-[#1A1A2E] mb-2">Email envoyé !</h2>
            <p className="text-[#5F6368] text-sm mb-6">
              Un lien de réinitialisation a été envoyé à <strong>{email}</strong>.
              Vérifiez vos spams si vous ne le trouvez pas.
            </p>
            <Button
              onClick={() => setStep('form')}
              variant="secondary"
              className="w-full"
              size="lg"
            >
              Renvoyer un email
            </Button>
            <Link
              href="/login"
              className="mt-4 block text-sm text-[#1B73E8] hover:underline"
            >
              Retour à la connexion
            </Link>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <h2 className="text-xl font-bold text-[#1A1A2E]">Mot de passe oublié</h2>
              <p className="text-sm text-[#5F6368] mt-1">
                Entrez votre email et nous vous enverrons un lien de réinitialisation
              </p>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <Input
                label="Email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="vous@entreprise.com"
                autoComplete="email"
                required
              />

              {error && (
                <p className="text-sm text-red-500">{error}</p>
              )}

              <Button type="submit" loading={loading} className="w-full" size="lg">
                {loading ? 'Envoi en cours...' : 'Envoyer le lien →'}
              </Button>

              <Link
                href="/login"
                className="text-center text-sm text-[#5F6368] hover:text-[#1B73E8] transition-colors"
              >
                ← Retour à la connexion
              </Link>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
