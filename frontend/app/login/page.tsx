'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { signInAdmin } from '@/lib/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import Link from 'next/link';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Veuillez remplir tous les champs');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await signInAdmin(email, password);
      router.replace('/app/chat');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Email ou mot de passe incorrect');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#EFF6FF] flex flex-col items-center justify-center px-4 py-12">
      {/* Logo */}
      <div className="mb-8 flex flex-col items-center gap-3">
        <img src="/favicon.png?v=4" alt="Pepperyn" className="w-20 h-20 object-contain" />
        <div className="text-center">
          <h1 className="text-2xl font-bold text-[#1A1A2E]">Connexion à votre espace</h1>
          <p className="text-sm text-[#5F6368]">Accédez à vos analyses financières</p>
        </div>
      </div>

      {/* Card */}
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">

          <Input
            label="Adresse email"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="vous@entreprise.com"
            autoComplete="email"
            required
          />

          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-[#1A1A2E]">Mot de passe</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Votre mot de passe"
                autoComplete="current-password"
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

          <div className="flex justify-end">
            <Link href="/forgot-password" className="text-sm text-[#1B73E8] hover:underline">
              Mot de passe oublié ?
            </Link>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <Button type="submit" loading={loading} className="w-full" size="lg">
            {loading ? 'Connexion...' : 'Se connecter →'}
          </Button>

          <p className="text-center text-sm text-[#5F6368]">
            Pas encore de compte ?{' '}
            <Link href="/register" className="text-[#1B73E8] hover:underline font-medium">
              Créer mon espace
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
