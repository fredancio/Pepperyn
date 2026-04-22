'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { signOutAdmin, getCurrentAuthMode } from '@/lib/auth';
import { updatePin } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Spinner } from '@/components/ui/Spinner';
import type { Company, Profile } from '@/lib/types';

interface AdminProfile extends Profile {
  company: Company;
}

export default function SettingsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<AdminProfile | null>(null);

  // PIN state
  const [showPin, setShowPin] = useState(false);
  const [showChangePinModal, setShowChangePinModal] = useState(false);
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [pinError, setPinError] = useState('');
  const [pinSuccess, setPinSuccess] = useState('');
  const [savingPin, setSavingPin] = useState(false);

  // Analytics state
  const [analysisCount] = useState<number>(0);

  // Delete account state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletingAccount, setDeletingAccount] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  useEffect(() => {
    async function init() {
      const mode = await getCurrentAuthMode();
      if (mode !== 'admin') {
        router.replace('/app/chat');
        return;
      }
      await loadProfile();
    }
    init();
  }, [router]);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) { router.replace('/login'); return; }

      const { data } = await supabase
        .from('profiles')
        .select('*, company:companies(*)')
        .eq('id', user.id)
        .single();

      if (data) setProfile(data as AdminProfile);
    } catch {
      // handle error
    } finally {
      setLoading(false);
    }
  };

  const handleSavePin = async () => {
    if (newPin.length !== 4 || !/^\d{4}$/.test(newPin)) {
      setPinError('Le PIN doit contenir exactement 4 chiffres');
      return;
    }
    if (newPin !== confirmPin) {
      setPinError('Les codes PIN ne correspondent pas');
      return;
    }

    setSavingPin(true);
    setPinError('');
    setPinSuccess('');
    try {
      await updatePin(newPin);
      setPinSuccess('PIN mis à jour avec succès !');
      setShowChangePinModal(false);
      setNewPin('');
      setConfirmPin('');
      await loadProfile();
    } catch (err) {
      setPinError(err instanceof Error ? err.message : 'Erreur lors de la mise à jour du PIN');
    } finally {
      setSavingPin(false);
    }
  };

  const handleSignOut = async () => {
    await signOutAdmin();
    router.push('/login');
  };

  const handleDeleteAccount = async () => {
    setDeletingAccount(true);
    setDeleteError('');
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('Session expirée, veuillez vous reconnecter.');

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/account`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || 'Erreur lors de la suppression du compte');
      }

      // Déconnexion locale puis redirection
      await signOutAdmin();
      router.push('/login');
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Une erreur est survenue');
      setDeletingAccount(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#EFF6FF] flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  const company = profile?.company;
  const planLabels: Record<string, string> = {
    free: 'Gratuit',
    standard: 'Standard',
    standard_beta: 'Standard Bêta',
    premium: 'Premium',
  };

  return (
    <div className="min-h-screen bg-[#EFF6FF]">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/app/chat" className="w-9 h-9 flex items-center justify-center text-[#5F6368] hover:bg-gray-100 rounded-xl transition-colors">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-[#1B73E8] rounded-xl flex items-center justify-center shadow-sm">
                <img src="/favicon.png?v=4" alt="Pepperyn" className="w-8 h-8 object-contain" />
              </div>
              <h1 className="font-bold text-[#1A1A2E] text-base">Paramètres</h1>
            </div>
          </div>
          <button
            onClick={handleSignOut}
            className="flex items-center gap-2 text-sm text-red-500 hover:text-red-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span className="hidden sm:block">Se déconnecter</span>
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8 flex flex-col gap-6">
        {/* Account info */}
        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
            <h2 className="font-semibold text-[#1A1A2E] flex items-center gap-2">
              <svg className="w-4 h-4 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              Informations du compte
            </h2>
          </div>
          <div className="p-6 grid sm:grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-[#5F6368] font-medium mb-1">Prénom</p>
              <p className="text-sm font-semibold text-[#1A1A2E]">{profile?.prenom || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-[#5F6368] font-medium mb-1">Email</p>
              <p className="text-sm font-semibold text-[#1A1A2E]">{profile?.email || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-[#5F6368] font-medium mb-1">Entreprise</p>
              <p className="text-sm font-semibold text-[#1A1A2E]">{company?.name || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-[#5F6368] font-medium mb-1">Membre depuis</p>
              <p className="text-sm font-semibold text-[#1A1A2E]">
                {profile?.created_at ? new Date(profile.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }) : '—'}
              </p>
            </div>
          </div>
        </section>

        {/* Plan info */}
        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
            <h2 className="font-semibold text-[#1A1A2E] flex items-center gap-2">
              <svg className="w-4 h-4 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
              Abonnement
            </h2>
          </div>
          <div className="p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-bold ${
                    company?.plan === 'premium' ? 'bg-amber-100 text-amber-700' :
                    company?.plan === 'standard' || company?.plan === 'standard_beta' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-[#5F6368]'
                  }`}>
                    {planLabels[company?.plan || 'free'] || company?.plan || 'Gratuit'}
                  </span>
                  {company?.is_beta && (
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                      Bêta #{company.beta_slot_number}
                    </span>
                  )}
                </div>
                <p className="text-sm text-[#5F6368]">
                  {company?.subscription_status === 'active' ? 'Abonnement actif' : 'Plan gratuit'}
                </p>
              </div>
              {company?.plan === 'free' && (
                <Link href="/#tarifs" className="text-sm text-[#1B73E8] font-medium hover:underline">
                  Passer à Standard →
                </Link>
              )}
            </div>

            {/* Usage stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-[#EFF6FF] rounded-xl p-4 text-center">
                <p className="text-2xl font-extrabold text-[#1B73E8]">{company?.analyses_restantes ?? '—'}</p>
                <p className="text-xs text-[#5F6368] mt-0.5">Analyses restantes</p>
              </div>
              <div className="bg-[#EFF6FF] rounded-xl p-4 text-center">
                <p className="text-2xl font-extrabold text-[#1B73E8]">{company?.analyses_totales_effectuees ?? analysisCount}</p>
                <p className="text-xs text-[#5F6368] mt-0.5">Analyses réalisées</p>
              </div>
            </div>
          </div>
        </section>

        {/* PIN management */}
        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
            <h2 className="font-semibold text-[#1A1A2E] flex items-center gap-2">
              <svg className="w-4 h-4 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Code PIN invité
            </h2>
          </div>
          <div className="p-6">
            <p className="text-sm text-[#5F6368] mb-5">
              Partagez ce code avec votre équipe pour qu&apos;ils puissent se connecter à Pepperyn sans créer de compte.
            </p>

            {/* PIN display */}
            <div className="flex items-center gap-4 mb-5">
              <div className="flex gap-2">
                {(company?.pin_code || '****').split('').map((digit, i) => (
                  <div
                    key={i}
                    className="w-12 h-14 bg-[#EFF6FF] border-2 border-[#1B73E8]/20 rounded-xl flex items-center justify-center text-xl font-bold text-[#1A1A2E]"
                  >
                    {showPin ? digit : '•'}
                  </div>
                ))}
              </div>
              <button
                onClick={() => setShowPin(!showPin)}
                className="text-[#5F6368] hover:text-[#1A1A2E] transition-colors p-2"
                title={showPin ? 'Masquer le PIN' : 'Afficher le PIN'}
              >
                {showPin ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 4.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>

            {pinSuccess && (
              <div className="mb-4 bg-green-50 border border-green-200 rounded-xl px-4 py-3">
                <p className="text-sm text-green-700 font-medium">{pinSuccess}</p>
              </div>
            )}

            <div className="flex gap-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  if (company?.pin_code) {
                    navigator.clipboard.writeText(company.pin_code);
                  }
                }}
              >
                <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copier
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => { setShowChangePinModal(true); setPinError(''); setNewPin(''); setConfirmPin(''); }}
              >
                <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
                Changer le PIN
              </Button>
            </div>
          </div>
        </section>

        {/* Danger zone */}
        <section className="bg-white rounded-2xl border border-red-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-red-100 bg-red-50">
            <h2 className="font-semibold text-red-700 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Zone sensible
            </h2>
          </div>
          <div className="p-6">
            <p className="text-sm text-[#5F6368] mb-5">
              La clôture de votre compte est irréversible. Toutes vos données (analyses, historique, paramètres) seront définitivement supprimées.
            </p>
            <button
              onClick={() => { setShowDeleteModal(true); setDeleteError(''); }}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-red-200 text-red-600 text-sm font-medium hover:bg-red-50 hover:border-red-300 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Clôturer mon compte
            </button>
          </div>
        </section>

        {/* Analytics */}
        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
            <h2 className="font-semibold text-[#1A1A2E] flex items-center gap-2">
              <svg className="w-4 h-4 text-[#1B73E8]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Utilisation &amp; Analytics
            </h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: 'Total analyses', value: company?.analyses_totales_effectuees ?? 0, icon: '📊' },
                { label: 'Analyses restantes', value: company?.analyses_restantes ?? 0, icon: '🔢' },
                { label: 'Plan actuel', value: planLabels[company?.plan || 'free'] || '—', icon: '⭐', isText: true },
                { label: 'Statut', value: company?.subscription_status === 'active' ? 'Actif' : 'Inactif', icon: '✅', isText: true },
              ].map((stat, i) => (
                <div key={i} className="bg-[#EFF6FF] rounded-xl p-4">
                  <p className="text-xl mb-1">{stat.icon}</p>
                  <p className={`font-extrabold text-[#1B73E8] ${stat.isText ? 'text-base' : 'text-2xl'}`}>
                    {stat.value}
                  </p>
                  <p className="text-xs text-[#5F6368] mt-0.5">{stat.label}</p>
                </div>
              ))}
            </div>

            {/* Usage bar */}
            {company?.analyses_restantes !== undefined && company?.analyses_totales_effectuees !== undefined && (
              <div className="mt-5">
                <div className="flex justify-between text-xs text-[#5F6368] mb-1.5">
                  <span>Analyses utilisées ce mois</span>
                  <span>
                    {company.analyses_totales_effectuees} / {company.analyses_totales_effectuees + company.analyses_restantes}
                  </span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#1B73E8] rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(100, (company.analyses_totales_effectuees / (company.analyses_totales_effectuees + company.analyses_restantes)) * 100)}%`
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        </section>
      </main>

      {/* Delete Account Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => !deletingAccount && setShowDeleteModal(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h3 className="text-lg font-bold text-[#1A1A2E]">Clôturer mon compte</h3>
            </div>

            <p className="text-sm text-[#5F6368] mb-2">
              Êtes-vous certain de vouloir clôturer votre compte ?
            </p>
            <p className="text-sm text-red-600 font-medium mb-5">
              Toutes vos données ainsi que votre historique d&apos;analyses seront définitivement et irréversiblement effacés.
            </p>

            {deleteError && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
                <p className="text-sm text-red-700">{deleteError}</p>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                disabled={deletingAccount}
                className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-[#1A1A2E] hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Annuler
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deletingAccount}
                className="flex-1 px-4 py-2.5 rounded-xl bg-red-600 text-white text-sm font-medium hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {deletingAccount ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                    Suppression…
                  </>
                ) : 'Oui, supprimer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Change PIN Modal */}
      {showChangePinModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowChangePinModal(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-[#1A1A2E] mb-4">Changer le code PIN</h3>

            <div className="flex flex-col gap-4">
              <Input
                label="Nouveau PIN (4 chiffres)"
                type="number"
                value={newPin}
                onChange={e => {
                  const v = e.target.value.replace(/\D/g, '').slice(0, 4);
                  setNewPin(v);
                }}
                placeholder="1234"
                maxLength={4}
              />
              <Input
                label="Confirmer le PIN"
                type="number"
                value={confirmPin}
                onChange={e => {
                  const v = e.target.value.replace(/\D/g, '').slice(0, 4);
                  setConfirmPin(v);
                }}
                placeholder="1234"
                maxLength={4}
              />

              {pinError && (
                <p className="text-sm text-red-500">{pinError}</p>
              )}

              <div className="flex gap-3">
                <Button
                  variant="ghost"
                  className="flex-1"
                  onClick={() => setShowChangePinModal(false)}
                >
                  Annuler
                </Button>
                <Button
                  className="flex-1"
                  loading={savingPin}
                  onClick={handleSavePin}
                  disabled={newPin.length !== 4 || confirmPin.length !== 4}
                >
                  Sauvegarder
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
