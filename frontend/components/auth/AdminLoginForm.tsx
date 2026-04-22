'use client';
import { useState } from 'react';
import { signInAdmin } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import Link from 'next/link';

export function AdminLoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) { setError('Veuillez remplir tous les champs'); return; }
    setLoading(true);
    setError('');
    try {
      await signInAdmin(email, password);
      router.push('/app/chat');
    } catch {
      setError('Email ou mot de passe incorrect');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full">
      <Input
        label="Email"
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        placeholder="vous@entreprise.com"
        autoComplete="email"
        required
      />
      <Input
        label="Mot de passe"
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        placeholder="••••••••"
        autoComplete="current-password"
        required
      />

      <div className="flex justify-end">
        <Link href="/forgot-password" className="text-sm text-[#1B73E8] hover:underline">
          Mot de passe oublié ?
        </Link>
      </div>

      {error && <p className="text-sm text-red-500 text-center">{error}</p>}

      <Button type="submit" loading={loading} className="w-full" size="lg">
        {loading ? 'Connexion...' : 'Se connecter →'}
      </Button>

      <p className="text-center text-sm text-[#5F6368]">
        Pas encore de compte ?{' '}
        <Link href="/register" className="text-[#1B73E8] hover:underline font-medium">
          S&apos;inscrire
        </Link>
      </p>
    </form>
  );
}
