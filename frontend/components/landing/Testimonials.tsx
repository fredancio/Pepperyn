'use client';
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import type { BetaTestimonial } from '@/lib/types';

const fallbackTestimonials: BetaTestimonial[] = [
  {
    id: '1',
    prenom: 'Sophie',
    poste: 'DAF — Groupe Retail',
    contenu: "Pepperyn m'a économisé 3h par semaine sur mes reportings. L'analyse du P&L est aussi précise que ce que je produisais manuellement, en 50x moins de temps.",
    note: 5,
    is_published: true,
    created_at: new Date().toISOString(),
  },
  {
    id: '2',
    prenom: 'Marc',
    poste: 'Contrôleur de Gestion — SaaS Scale-up',
    contenu: "La détection d'anomalies est bluffante. Il a trouvé une erreur de comptabilisation que j'avais manquée depuis 3 mois. La plateforme paye pour ça seul.",
    note: 5,
    is_published: true,
    created_at: new Date().toISOString(),
  },
  {
    id: '3',
    prenom: 'Isabelle',
    poste: 'Dirigeante — PME Industrie',
    contenu: "Je ne suis pas financière mais maintenant je comprends vraiment mes chiffres. Les recommandations sont claires, actionnables, et j'ai pu prendre de meilleures décisions.",
    note: 5,
    is_published: true,
    created_at: new Date().toISOString(),
  },
];

function StarRating({ note }: { note: number }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map(s => (
        <svg
          key={s}
          className={`w-4 h-4 ${s <= note ? 'text-amber-400 fill-current' : 'text-gray-200 fill-current'}`}
          viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
    </div>
  );
}

export function Testimonials() {
  const [testimonials, setTestimonials] = useState<BetaTestimonial[]>(fallbackTestimonials);

  useEffect(() => {
    async function fetchTestimonials() {
      const { data, error } = await supabase
        .from('beta_testimonials')
        .select('*')
        .eq('is_published', true)
        .order('created_at', { ascending: false })
        .limit(6);

      if (!error && data && data.length > 0) {
        setTestimonials(data);
      }
    }
    fetchTestimonials();
  }, []);

  return (
    <section className="py-20 lg:py-28 bg-white" id="temoignages">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-full mb-4">
            <svg className="w-4 h-4 text-amber-500 fill-current" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            <span className="text-sm font-medium text-amber-700">Ils nous font confiance</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] mb-4">
            Ce que disent nos utilisateurs bêta
          </h2>
          <p className="text-lg text-[#5F6368] max-w-2xl mx-auto">
            Rejoignez les équipes financières qui gagnent des heures chaque semaine
          </p>
        </div>

        {/* Testimonials grid */}
        <div className="grid md:grid-cols-3 gap-6">
          {testimonials.map((t, index) => (
            <div
              key={t.id}
              className="flex flex-col gap-4 p-6 bg-[#EFF6FF] rounded-2xl border border-blue-100 hover:shadow-md transition-shadow duration-200"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              {/* Stars */}
              <StarRating note={t.note} />

              {/* Content */}
              <blockquote className="text-[#1A1A2E] text-sm leading-relaxed flex-1">
                &ldquo;{t.contenu}&rdquo;
              </blockquote>

              {/* Author */}
              <div className="flex items-center gap-3 pt-2 border-t border-blue-100">
                <div className="w-9 h-9 bg-[#1B73E8] rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                  {t.prenom[0].toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-semibold text-[#1A1A2E]">{t.prenom}</p>
                  {t.poste && (
                    <p className="text-xs text-[#5F6368]">{t.poste}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Stats bar */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { value: '95%', label: 'de satisfaction utilisateurs' },
            { value: '3h', label: 'économisées par semaine en moyenne' },
            { value: '60s', label: "temps moyen d'analyse" },
            { value: '50+', label: 'équipes financières actives' },
          ].map((stat, i) => (
            <div key={i} className="text-center p-5 bg-[#EFF6FF] rounded-2xl border border-blue-100">
              <p className="text-3xl font-extrabold text-[#1B73E8] mb-1">{stat.value}</p>
              <p className="text-sm text-[#5F6368]">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
