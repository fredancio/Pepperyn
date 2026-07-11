'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';

const SUPER_ADMIN_EMAIL = 'fredanciaux16@gmail.com';
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const PLAN_COLORS: Record<string, string> = {
  free:       'bg-gray-100 text-gray-600',
  pro:        'bg-blue-100 text-blue-700',
  power:      'bg-purple-100 text-purple-700',
  scale:      'bg-orange-100 text-orange-700',
  enterprise: 'bg-green-100 text-green-700',
};

const PLAN_BAR_COLORS: Record<string, string> = {
  enterprise: 'bg-green-500',
  scale:      'bg-orange-500',
  power:      'bg-purple-500',
  pro:        'bg-blue-500',
  free:       'bg-gray-300',
};

interface WeekPoint { week: string; label: string; count: number; }
interface PlanFunnel { plan: string; count: number; mrr: number; }
interface TopCompany { company_id: string; plan: string; analyses_total: number; }

interface GrowthData {
  kpis: {
    mrr_estimate: number;
    total_companies: number;
    new_companies_month: number;
    activation_rate: number;
    analyses_this_month: number;
    paying_companies: number;
  };
  weekly_signups: WeekPoint[];
  weekly_analyses: WeekPoint[];
  plan_funnel: PlanFunnel[];
  top_companies: TopCompany[];
}

// ── Mini bar chart (inline SVG, no deps) ──────────────────────────────────
function BarChart({
  data,
  color = '#1B73E8',
  height = 80,
}: {
  data: WeekPoint[];
  color?: string;
  height?: number;
}) {
  const max = Math.max(...data.map(d => d.count), 1);
  const w = 100 / data.length;
  const gap = 0.8;

  return (
    <div className="w-full" style={{ height }}>
      <svg viewBox={`0 0 100 ${height}`} preserveAspectRatio="none" className="w-full h-full">
        {data.map((d, i) => {
          const barH = (d.count / max) * (height - 12);
          const x = i * w + gap / 2;
          return (
            <g key={d.week}>
              <rect
                x={x}
                y={height - 12 - barH}
                width={w - gap}
                height={barH || 1}
                fill={color}
                fillOpacity={d.count === 0 ? 0.15 : 0.85}
                rx="1"
              />
              {i % 3 === 0 && (
                <text
                  x={x + (w - gap) / 2}
                  y={height - 2}
                  textAnchor="middle"
                  fontSize="4"
                  fill="#9CA3AF"
                >
                  {d.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// ── KPI Card ──────────────────────────────────────────────────────────────
function KpiCard({
  label,
  value,
  sub,
  color = 'text-[#1A1A2E]',
}: {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-[#5F6368] mt-1">{label}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  );
}

// ── Admin nav ─────────────────────────────────────────────────────────────
function AdminNav({ active }: { active: 'crm' | 'growth' }) {
  return (
    <div className="flex gap-1 bg-gray-100 rounded-lg p-1 text-sm">
      <a
        href="/admin"
        className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
          active === 'crm'
            ? 'bg-white text-[#1A1A2E] shadow-sm'
            : 'text-[#5F6368] hover:text-[#1A1A2E]'
        }`}
      >
        CRM
      </a>
      <a
        href="/admin/growth"
        className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
          active === 'growth'
            ? 'bg-white text-[#1A1A2E] shadow-sm'
            : 'text-[#5F6368] hover:text-[#1A1A2E]'
        }`}
      >
        Growth
      </a>
    </div>
  );
}

// ── Page principale ───────────────────────────────────────────────────────
export default function GrowthDashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState<GrowthData | null>(null);

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
        const res = await fetch(`${API_URL}/api/superadmin/growth`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (!res.ok) throw new Error(`Erreur ${res.status}`);
        const json = await res.json();
        setData(json);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Erreur inconnue');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [router]);

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

  if (!data) return null;

  const { kpis, weekly_signups, weekly_analyses, plan_funnel, top_companies } = data;
  const totalCompaniesForFunnel = Math.max(kpis.total_companies, 1);

  return (
    <div className="min-h-screen bg-[#F8FAFC] p-6">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[#1A1A2E]">Growth Dashboard</h1>
            <p className="text-sm text-[#5F6368] mt-0.5">Lecture seule · Mise à jour en temps réel</p>
          </div>
          <div className="flex items-center gap-3">
            <AdminNav active="growth" />
            <button
              onClick={() => window.location.reload()}
              className="text-xs text-[#1B73E8] hover:underline"
            >
              ↻ Actualiser
            </button>
          </div>
        </div>

        {/* KPI cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <KpiCard
            label="MRR estimé"
            value={`${kpis.mrr_estimate.toLocaleString('fr-FR')} €`}
            color="text-green-600"
          />
          <KpiCard
            label="Companies totales"
            value={kpis.total_companies}
          />
          <KpiCard
            label="Nouvelles ce mois"
            value={`+${kpis.new_companies_month}`}
            color="text-[#1B73E8]"
          />
          <KpiCard
            label="Plans payants"
            value={kpis.paying_companies}
            sub={`${Math.round(kpis.paying_companies / Math.max(kpis.total_companies, 1) * 100)}% du total`}
            color="text-purple-600"
          />
          <KpiCard
            label="Taux d'activation"
            value={`${kpis.activation_rate}%`}
            sub="≥1 analyse réalisée"
            color={kpis.activation_rate >= 60 ? 'text-green-600' : 'text-amber-600'}
          />
          <KpiCard
            label="Analyses ce mois"
            value={kpis.analyses_this_month}
            color="text-[#1B73E8]"
          />
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          {/* Weekly signups */}
          <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-sm font-semibold text-[#1A1A2E]">Acquisitions</div>
                <div className="text-xs text-[#5F6368]">Nouvelles companies · 12 semaines</div>
              </div>
              <div className="text-lg font-bold text-[#1B73E8]">
                {weekly_signups.reduce((s, d) => s + d.count, 0)}
              </div>
            </div>
            <BarChart data={weekly_signups} color="#1B73E8" height={90} />
          </div>

          {/* Weekly analyses */}
          <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-sm font-semibold text-[#1A1A2E]">Engagement</div>
                <div className="text-xs text-[#5F6368]">Analyses complétées · 12 semaines</div>
              </div>
              <div className="text-lg font-bold text-purple-600">
                {weekly_analyses.reduce((s, d) => s + d.count, 0)}
              </div>
            </div>
            <BarChart data={weekly_analyses} color="#9333EA" height={90} />
          </div>
        </div>

        {/* Plan funnel + Top companies */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          {/* Plan funnel */}
          <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <div className="text-sm font-semibold text-[#1A1A2E] mb-4">Entonnoir plans</div>
            <div className="space-y-3">
              {plan_funnel.map(({ plan, count, mrr }) => {
                const pct = Math.round(count / totalCompaniesForFunnel * 100);
                return (
                  <div key={plan}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex px-1.5 py-0.5 rounded text-xs font-semibold ${PLAN_COLORS[plan] || 'bg-gray-100 text-gray-600'}`}>
                          {plan.toUpperCase()}
                        </span>
                        <span className="text-sm text-[#1A1A2E] font-medium">{count}</span>
                        <span className="text-xs text-[#5F6368]">({pct}%)</span>
                      </div>
                      <span className="text-xs font-medium text-green-700">
                        {mrr > 0 ? `${mrr.toLocaleString('fr-FR')} €/mois` : '—'}
                      </span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${PLAN_BAR_COLORS[plan] || 'bg-gray-400'}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="mt-4 pt-3 border-t border-gray-100 flex justify-between text-xs">
              <span className="text-[#5F6368]">MRR total estimé</span>
              <span className="font-bold text-green-700">
                {kpis.mrr_estimate.toLocaleString('fr-FR')} €/mois
              </span>
            </div>
          </div>

          {/* Top companies */}
          <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <div className="text-sm font-semibold text-[#1A1A2E] mb-4">
              Top companies <span className="text-xs font-normal text-[#5F6368] ml-1">par analyses totales</span>
            </div>
            <div className="space-y-2">
              {top_companies.length === 0 ? (
                <div className="text-xs text-[#5F6368] py-4 text-center">Aucune donnée</div>
              ) : (
                top_companies.map((c, i) => {
                  const maxCount = top_companies[0]?.analyses_total || 1;
                  const pct = Math.round(c.analyses_total / maxCount * 100);
                  return (
                    <div key={c.company_id} className="flex items-center gap-3">
                      <span className="text-xs text-[#5F6368] w-4 text-right">{i + 1}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-xs font-mono text-[#5F6368] truncate max-w-[120px]">
                            {c.company_id.slice(0, 8)}…
                          </span>
                          <span className={`inline-flex px-1 py-0.5 rounded text-[10px] font-semibold ${PLAN_COLORS[c.plan] || 'bg-gray-100 text-gray-600'}`}>
                            {c.plan.toUpperCase()}
                          </span>
                        </div>
                        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-[#1B73E8] rounded-full"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                      <span className="text-xs font-semibold text-[#1A1A2E] w-6 text-right">
                        {c.analyses_total}
                      </span>
                    </div>
                  );
                })
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
