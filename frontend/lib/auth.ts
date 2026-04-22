'use client';
import { supabase } from './supabase';

const GUEST_TOKEN_KEY = 'pepperyn_guest_token';
const GUEST_COMPANY_KEY = 'pepperyn_guest_company';
const GUEST_PLAN_KEY = 'pepperyn_guest_plan';

// ── Admin auth ──────────────────────────────────────────────

export async function signInAdmin(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
  return data;
}

export async function signUpAdmin(
  email: string,
  password: string,
  prenom: string,
  industry: string,
  businessModel: string
) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: { prenom, industry, business_model: businessModel },
    },
  });
  if (error) throw error;
  return data;
}

export async function signOutAdmin() {
  await supabase.auth.signOut();
}

export async function getAdminSession() {
  const { data: { session } } = await supabase.auth.getSession();
  return session;
}

export async function getAdminUser() {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
}

export async function getAdminProfile() {
  const user = await getAdminUser();
  if (!user) return null;
  const { data } = await supabase
    .from('profiles')
    .select('*, company:companies(*)')
    .eq('id', user.id)
    .single();
  return data;
}

// ── Guest auth (PIN) ────────────────────────────────────────

export function saveGuestAuth(token: string, companyId: string, plan: string) {
  if (typeof window === 'undefined') return;
  sessionStorage.setItem(GUEST_TOKEN_KEY, token);
  sessionStorage.setItem(GUEST_COMPANY_KEY, companyId);
  sessionStorage.setItem(GUEST_PLAN_KEY, plan);
}

export function getGuestToken(): string | null {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem(GUEST_TOKEN_KEY);
}

export function getGuestCompanyId(): string | null {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem(GUEST_COMPANY_KEY);
}

export function getGuestPlan(): string | null {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem(GUEST_PLAN_KEY);
}

export function clearGuestAuth() {
  if (typeof window === 'undefined') return;
  sessionStorage.removeItem(GUEST_TOKEN_KEY);
  sessionStorage.removeItem(GUEST_COMPANY_KEY);
  sessionStorage.removeItem(GUEST_PLAN_KEY);
}

export function isGuestAuthenticated(): boolean {
  return !!getGuestToken();
}

// ── Unified auth check ───────────────────────────────────────

export async function isAuthenticated(): Promise<boolean> {
  if (isGuestAuthenticated()) return true;
  const session = await getAdminSession();
  return !!session;
}

export async function getCurrentAuthMode(): Promise<'admin' | 'guest' | null> {
  const session = await getAdminSession();
  if (session) return 'admin';
  if (isGuestAuthenticated()) return 'guest';
  return null;
}
