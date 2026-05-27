'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';

const SUPER_ADMIN_EMAIL = 'fredanciaux16@gmail.com';
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const PLAN_COLORS: Record<string, string> = {
  free: 'bg-gray-100 text-gray-600',
  pro: 'bg-blue-100 text-blue-700',
  power: 'bg-purple-100 text-purple-700',
  scale: 'bg-orange-100 text-orange-700',
  enterprise: 'bg-green-100 text-green-700',
};

const PLAN_LABELS: Record<string, string> = {
  free: 'FREE',
  pro: 'PRO',
  power: 'POWER',
  scale: 'SCALE',
  enterprise: 'ENTERPRISE',
};

interface Company {
  company_id: string;
  company_name: string;
  plan: string;
  created_at: string;
  email: string;
  contact_name: string;
  analyses_this_month: number;
  analyses_total: number;
}

interface Summary {
  total_companies: number;
  by_plan: Record<string, number>;
  total_analyses_this_month: number;
}

export default function AdminCRMPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [companies, setCompanies] = useState<Company[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [search, setSearch] = useState('');
  const [filterPlan, setFilterPlan] = useState('all');

  useEffect(() => {
    async function load() {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) { router.push('/login'); return; }

      const email = session.user.email || '';
      if (email.toLowerCase() !== SUPER_ADMIN_EMAIL.toLowerCase()) {
        router.push('/app/chat');
        return;
      }

      try {
        const res = await fetch(`${API_URL}/api/superadmin/stats`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (!res.ok) throw new Error(`Erreur ${res.status}`);
        const data = await res.json();
        setCompanies(data.data || []);
        setSummary(data.summary || null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Erreur inconnue');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [router]);

  const filtered = companies.filter(c => {
    const matchPlan = filterPlan === 'all' || c.plan === filterPlan;
    const q = search.toLowerCase();
    const matchSearch = !q ||
      c.company_name.toLowerCase().includes(q) ||
      c.email.toLowerCase().includes(q) ||
      c.contact_name.toLowerCase().includes(q);
    return matchPlan && matchSearch;
  });

  const formatDate = (iso: string) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  if (loading) return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
      <div className="text-[#5F6368] text-sm">Chargement…</div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
      <div className="text-red-500 text-sm">Erreur : {error}</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#F8FAFC] p-6">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[#1A1A2E]">CRM Pepperyn</h1>
            <p className="text-sm text-[#5F6368] mt-0.5">Vue super-admin — toutes les companies</p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="text-xs text-[#1B73E8] hover:underline"
          >
            ↻ Actualiser
          </button>
        </div>

        {/* Summary cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <div className="text-2xl font-bold text-[#1A1A2E]">{summary.total_companies}</div>
              <div className="text-xs text-[#5F6368] mt-1">Companies inscrites</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <div className="text-2xl font-bold text-[#1B73E8]">{summary.total_analyses_this_month}</div>
              <div className="text-xs text-[#5F6368] mt-1">Analyses ce mois</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <div className="text-2xl font-bold text-purple-600">
                {(summary.by_plan.pro || 0) + (summary.by_plan.power || 0) + (summary.by_plan.scale || 0) + (summary.by_plan.enterprise || 0)}
              </div>
              <div className="text-xs text-[#5F6368] mt-1">Plans payants</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <div className="text-2xl font-bold text-gray-400">{summary.by_plan.free || 0}</div>
              <div className="text-xs text-[#5F6368] mt-1">Plan FREE</div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap gap-3 items-center">
          <input
            type="text"
            placeholder="Rechercher par nom, email…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-[#1B73E8]/30"
          />
          <select
            value={filterPlan}
            onChange={e => setFilterPlan(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1B73E8]/30"
          >
            <option value="all">Tous les plans</option>
            {['free', 'pro', 'power', 'scale', 'enterprise'].map(p => (
              <option key={p} value={p}>{PLAN_LABELS[p]}</option>
            ))}
          </select>
          <span className="text-xs text-[#5F6368]">{filtered.length} résultat{filtered.length !== 1 ? 's' : ''}</span>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-[#F8FAFC]">
                <th className="text-left px-4 py-3 font-medium text-[#5F6368]">Company</th>
                <th className="text-left px-4 py-3 font-medium text-[#5F6368]">Contact</th>
                <th className="text-left px-4 py-3 font-medium text-[#5F6368]">Plan</th>
                <th className="text-left px-4 py-3 font-medium text-[#5F6368]">Inscrit le</th>
                <th className="text-right px-4 py-3 font-medium text-[#5F6368]">Analyses / mois</th>
                <th className="text-right px-4 py-3 font-medium text-[#5F6368]">Total analyses</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-[#5F6368] text-sm">
                    Aucune company trouvée
                  </td>
                </tr>
              ) : (
                filtered.map((c, i) => (
                  <tr
                    key={c.company_id}
                    className={`border-b border-gray-50 hover:bg-blue-50/30 transition-colors ${i % 2 === 0 ? '' : 'bg-gray-50/40'}`}
                  >
                    <td className="px-4 py-3 font-medium text-[#1A1A2E]">
                      {c.company_name || <span className="text-gray-400 italic">Sans nom</span>}
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-[#1A1A2E]">{c.contact_name || <span className="text-gray-400">—</span>}</div>
                      <div className="text-xs text-[#5F6368]">{c.email || '—'}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${PLAN_COLORS[c.plan] || 'bg-gray-100 text-gray-600'}`}>
                        {PLAN_LABELS[c.plan] || c.plan.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[#5F6368]">{formatDate(c.created_at)}</td>
                    <td className="px-4 py-3 text-right font-medium text-[#1B73E8]">
                      {c.analyses_this_month}
                    </td>
                    <td className="px-4 py-3 text-right text-[#1A1A2E]">
                      {c.analyses_total}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}
