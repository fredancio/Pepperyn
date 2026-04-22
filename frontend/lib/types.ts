export type Plan = 'free' | 'standard' | 'standard_beta' | 'premium';

export interface Company {
  id: string;
  name: string;
  admin_user_id: string;
  pin_code: string;
  plan: Plan;
  analyses_restantes: number;
  analyses_totales_effectuees: number;
  stripe_customer_id?: string;
  stripe_subscription_id?: string;
  subscription_status: string;
  is_beta: boolean;
  beta_slot_number?: number;
  created_at: string;
  updated_at: string;
}

export interface Profile {
  id: string;
  email: string;
  prenom?: string;
  company_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  company_id: string;
  user_id?: string;
  guest_token?: string;
  is_admin_session: boolean;
  titre: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  session_id: string;
  company_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  content_type: 'text' | 'analysis' | 'file' | 'error';
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface AnalysisResult {
  id?: string;
  type_document: string;
  score_confiance: number;
  revenus?: {
    total?: number;
    breakdown?: Array<{ label: string; value: number; variation?: number }>;
    evolution?: string;
  };
  couts?: {
    total?: number;
    breakdown?: Array<{ label: string; value: number; pourcentage?: number }>;
  };
  marges?: {
    brute?: number;
    brute_pct?: number;
    operationnelle?: number;
    operationnelle_pct?: number;
    nette?: number;
    nette_pct?: number;
  };
  anomalies?: Array<{
    description: string;
    severity: 'high' | 'medium' | 'low';
    impact?: string;
  }>;
  risques?: Array<{ description: string; probabilite?: string; impact?: string }>;
  opportunites?: Array<{ description: string; potentiel?: string }>;
  recommandations?: Array<{
    priorite: 'haute' | 'moyenne' | 'basse';
    action: string;
    impact_estime?: string;
    delai?: string;
  }>;
  synthese?: string;
  excel_export_url?: string;
  excel_export_nom?: string;
}

export interface GuestAuth {
  access_token: string;
  token_type: 'guest';
  company_id: string;
  plan: Plan;
}

export type AuthMode = 'guest' | 'admin';

export interface BetaTestimonial {
  id: string;
  prenom: string;
  poste?: string;
  contenu: string;
  note: number;
  is_published: boolean;
  created_at: string;
}
