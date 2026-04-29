const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getAuthHeaders(): Promise<Record<string, string>> {
  if (typeof window === 'undefined') return {};

  // Try guest token first
  const guestToken = sessionStorage.getItem('pepperyn_guest_token');
  if (guestToken) {
    return {
      'Authorization': `Bearer ${guestToken}`,
      'X-Auth-Type': 'guest',
    };
  }

  // Try admin Supabase token
  const { supabase } = await import('./supabase');
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    return {
      'Authorization': `Bearer ${session.access_token}`,
      'X-Auth-Type': 'admin',
    };
  }

  return {};
}

export async function loginWithPin(pin: string) {
  const res = await fetch(`${API_URL}/api/auth/pin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pin }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Code PIN incorrect');
  }
  return res.json();
}

export async function analyzeFile(
  file: File,
  context: string,
  mode: 'quick' | 'complete' = 'complete',
  sessionId?: string
) {
  const headers = await getAuthHeaders();
  const formData = new FormData();
  formData.append('file', file);
  formData.append('context', context);
  formData.append('mode', mode);
  if (sessionId) formData.append('session_id', sessionId);

  const res = await fetch(`${API_URL}/api/analyze`, {
    method: 'POST',
    headers,
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Erreur lors de l'analyse");
  }
  return res.json();
}

export async function analyzeText(
  query: string,
  sessionId?: string
) {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/analyze/text`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id: sessionId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || "Erreur lors de l'analyse");
  }
  return res.json();
}

export async function updatePin(newPin: string) {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/admin/update-pin`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_pin: newPin }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur lors de la mise à jour du PIN');
  }
  return res.json();
}

export async function downloadExcel(analyseId: string): Promise<Blob> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/export/${analyseId}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur lors du téléchargement Excel');
  }
  return res.blob();
}

export async function downloadPdf(analyseId: string): Promise<Blob> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/export-pdf/${analyseId}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur lors du téléchargement PDF');
  }
  return res.blob();
}

export async function downloadPptx(analyseId: string): Promise<Blob> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/export-pptx/${analyseId}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erreur lors du téléchargement PowerPoint');
  }
  return res.blob();
}

export async function fetchAnalysesHistory(): Promise<Array<{
  id: string;
  fichier_nom: string;
  type_document: string;
  created_at: string;
  score_confiance: number;
}>> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_URL}/api/analyses/history`, { headers });
  if (!res.ok) return [];
  const data = await res.json();
  return data.analyses || [];
}
