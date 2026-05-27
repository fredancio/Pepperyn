'use client';
import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const DEFIS = [
  'Analyse financière manuelle & chronophage',
  'Reporting multi-entités ou multi-périodes',
  'Suivi de trésorerie & cash flow',
  'Consolidation de données ERP / CRM',
  'Pilotage de marges et rentabilité',
  'Alertes et projections financières',
  'Autre',
];

const TAILLES = [
  '1 personne (solo CFO / dirigeant)',
  '2 à 5 personnes',
  '5 à 20 personnes',
  'Plus de 20 personnes',
];

const IA_OPTIONS = [
  'Oui, nous utilisons déjà des outils IA',
  'Non, mais nous évaluons des solutions',
  'Non, pas encore',
];

export default function ContactPage() {
  const [form, setForm] = useState({
    prenom_nom: '',
    email: '',
    entreprise: '',
    taille_equipe: '',
    defis: [] as string[],
    utilise_ia: '',
    message: '',
    souhaite_contact: true,
  });
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const toggle = (item: string) => {
    setForm(f => ({
      ...f,
      defis: f.defis.includes(item)
        ? f.defis.filter(d => d !== item)
        : [...f.defis, item],
    }));
  };

  const handleSubmit = async () => {
    if (!form.email || !form.prenom_nom) {
      setError('Merci de renseigner votre nom et email.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (data.success) setSubmitted(true);
      else setError('Une erreur est survenue. Réessayez ou écrivez-nous à info@finflate.com');
    } catch {
      setError('Impossible de soumettre. Écrivez-nous à info@finflate.com');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-[#EFF6FF] flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-xl p-10 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-[#1A1A2E] mb-2">Demande reçue !</h2>
          <p className="text-[#5F6368] mb-6">
            Merci <strong>{form.prenom_nom.split(' ')[0]}</strong>. Notre équipe revient vers vous sous 24h ouvrées.
          </p>
          <Link href="/" className="inline-block px-6 py-3 bg-[#1B73E8] text-white rounded-xl font-semibold text-sm hover:bg-[#0D47A1] transition-colors">
            Retour à l&apos;accueil
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#EFF6FF]">
      {/* Nav */}
      <nav className="bg-white border-b border-gray-100 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <img src="/favicon.png" alt="Pepperyn" className="w-8 h-8 object-contain" />
            <span className="font-bold text-[#1A1A2E] text-lg">Pepperyn</span>
            <span className="text-xs text-[#5F6368] hidden sm:inline">Financial Control Center</span>
          </Link>
          <Link href="/upgrade" className="text-sm text-[#1B73E8] hover:underline">← Voir les plans</Link>
        </div>
      </nav>

      <div className="max-w-2xl mx-auto px-4 py-12">

        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-4">
            <span className="text-sm font-medium text-[#1B73E8]">Plan SCALE — Sur-mesure</span>
          </div>
          <h1 className="text-3xl font-extrabold text-[#1A1A2E] mb-2">Parlons de votre projet</h1>
          <p className="text-[#5F6368]">Dites-nous où vous en êtes — nous reviendrons avec une proposition adaptée à votre organisation.</p>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-2 mb-8">
          {[1, 2].map(s => (
            <div key={s} className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${step >= s ? 'bg-[#1B73E8]' : 'bg-gray-200'}`} />
          ))}
          <span className="text-xs text-[#5F6368] ml-2">{step}/2</span>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 space-y-6">

          {step === 1 && (
            <>
              <h2 className="text-lg font-bold text-[#1A1A2E]">Votre identité</h2>

              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#5F6368] mb-1.5 uppercase tracking-wide">Prénom & Nom *</label>
                  <input
                    type="text"
                    placeholder="Marie Dupont"
                    value={form.prenom_nom}
                    onChange={e => setForm(f => ({ ...f, prenom_nom: e.target.value }))}
                    className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#1B73E8]/30 focus:border-[#1B73E8]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#5F6368] mb-1.5 uppercase tracking-wide">Email professionnel *</label>
                  <input
                    type="email"
                    placeholder="marie@entreprise.com"
                    value={form.email}
                    onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                    className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#1B73E8]/30 focus:border-[#1B73E8]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#5F6368] mb-1.5 uppercase tracking-wide">Entreprise</label>
                <input
                  type="text"
                  placeholder="Nom de votre société"
                  value={form.entreprise}
                  onChange={e => setForm(f => ({ ...f, entreprise: e.target.value }))}
                  className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#1B73E8]/30 focus:border-[#1B73E8]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#5F6368] mb-3 uppercase tracking-wide">Taille de votre équipe financière</label>
                <div className="grid sm:grid-cols-2 gap-2">
                  {TAILLES.map(t => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setForm(f => ({ ...f, taille_equipe: t }))}
                      className={`px-4 py-3 rounded-xl text-sm text-left border-2 transition-all ${
                        form.taille_equipe === t
                          ? 'border-[#1B73E8] bg-[#EFF6FF] text-[#1B73E8] font-semibold'
                          : 'border-gray-200 text-[#1A1A2E] hover:border-gray-300'
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={() => {
                  if (!form.prenom_nom || !form.email) { setError('Nom et email requis.'); return; }
                  setError('');
                  setStep(2);
                }}
                className="w-full py-3.5 bg-[#1B73E8] text-white rounded-xl font-bold text-sm hover:bg-[#0D47A1] transition-colors"
              >
                Continuer →
              </button>
            </>
          )}

          {step === 2 && (
            <>
              <h2 className="text-lg font-bold text-[#1A1A2E]">Vos défis & contexte</h2>

              <div>
                <label className="block text-xs font-semibold text-[#5F6368] mb-3 uppercase tracking-wide">Quels sont vos défis actuels ? (plusieurs choix possibles)</label>
                <div className="flex flex-col gap-2">
                  {DEFIS.map(d => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => toggle(d)}
                      className={`px-4 py-3 rounded-xl text-sm text-left border-2 transition-all flex items-center gap-3 ${
                        form.defis.includes(d)
                          ? 'border-[#1B73E8] bg-[#EFF6FF] text-[#1B73E8]'
                          : 'border-gray-200 text-[#1A1A2E] hover:border-gray-300'
                      }`}
                    >
                      <span className={`w-4 h-4 rounded flex-shrink-0 border-2 flex items-center justify-center ${form.defis.includes(d) ? 'border-[#1B73E8] bg-[#1B73E8]' : 'border-gray-300'}`}>
                        {form.defis.includes(d) && <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7"/></svg>}
                      </span>
                      {d}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#5F6368] mb-3 uppercase tracking-wide">Utilisez-vous déjà des outils IA ?</label>
                <div className="flex flex-col gap-2">
                  {IA_OPTIONS.map(o => (
                    <button
                      key={o}
                      type="button"
                      onClick={() => setForm(f => ({ ...f, utilise_ia: o }))}
                      className={`px-4 py-3 rounded-xl text-sm text-left border-2 transition-all ${
                        form.utilise_ia === o
                          ? 'border-[#1B73E8] bg-[#EFF6FF] text-[#1B73E8] font-semibold'
                          : 'border-gray-200 text-[#1A1A2E] hover:border-gray-300'
                      }`}
                    >
                      {o}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#5F6368] mb-1.5 uppercase tracking-wide">Message (optionnel)</label>
                <textarea
                  placeholder="Décrivez votre contexte, vos outils actuels, vos contraintes..."
                  value={form.message}
                  onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
                  rows={3}
                  className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#1B73E8]/30 focus:border-[#1B73E8] resize-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#5F6368] mb-3 uppercase tracking-wide">Souhaitez-vous être contacté·e ?</label>
                <div className="flex gap-3">
                  {[
                    { label: 'Oui, contactez-moi', value: true },
                    { label: 'Non, je vous recontacte', value: false },
                  ].map(opt => (
                    <button
                      key={String(opt.value)}
                      type="button"
                      onClick={() => setForm(f => ({ ...f, souhaite_contact: opt.value }))}
                      className={`flex-1 px-4 py-3 rounded-xl text-sm border-2 font-medium transition-all ${
                        form.souhaite_contact === opt.value
                          ? 'border-[#1B73E8] bg-[#EFF6FF] text-[#1B73E8]'
                          : 'border-gray-200 text-[#1A1A2E] hover:border-gray-300'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {error && <p className="text-red-500 text-sm">{error}</p>}

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(1)}
                  className="px-5 py-3 border-2 border-gray-200 text-[#5F6368] rounded-xl text-sm font-medium hover:border-gray-300 transition-colors"
                >
                  ← Retour
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="flex-1 py-3 bg-[#1B73E8] text-white rounded-xl font-bold text-sm hover:bg-[#0D47A1] transition-colors disabled:opacity-60"
                >
                  {submitting ? 'Envoi…' : 'Envoyer ma demande →'}
                </button>
              </div>
            </>
          )}

          {error && step === 1 && <p className="text-red-500 text-sm">{error}</p>}
        </div>

        <p className="text-center text-xs text-[#5F6368] mt-6">
          Vos données sont confidentielles et ne seront jamais revendues.{' '}
          <Link href="/legal/confidentialite" className="underline hover:text-[#1B73E8]">Politique de confidentialité</Link>
        </p>
      </div>
    </div>
  );
}
