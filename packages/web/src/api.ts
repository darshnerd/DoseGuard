const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface ResolvedDrug {
  query: string;
  matched: boolean;
  rxcui: string | null;
  name: string | null;
  ingredient_rxcui: string | null;
  ingredient_name: string | null;
}

export interface Interaction {
  ingredient_a: string;
  ingredient_b: string;
  severity: string;
  description: string;
}

export interface Ingredient {
  ingredient: string;
  rxcui: string | null;
}

export interface DrugHit {
  name: string;
  normalized: string;
  kind: string;
  manufacturer?: string | null;
  score?: number;
}

export interface Medication {
  id: number;
  name: string;
  start_date: string;
  duration_days: number | null;
  ingredients: Ingredient[];
}

export interface DayStat {
  date: string;
  expected: number;
  taken: number;
}

export interface CheckResponse {
  drugs: string[];
  ingredients: string[];
  conflict_found: boolean;
  interactions: Interaction[];
}

export interface ScanResponse {
  detected: ResolvedDrug[];
  ingredients: string[];
  conflict_found: boolean;
  interactions: Interaction[];
}

export interface ScanRecord {
  id: number;
  drugs: string[];
  conflict_found: boolean;
  interaction_count: number;
  created_at: string;
}

export interface Profile {
  id: number;
  email: string;
  full_name: string | null;
  age: number | null;
  sex: string | null;
}

export type Slot = "morning" | "afternoon" | "evening" | "night";
export type DoseStatus = "taken" | "skipped" | "overdue" | "upcoming";

export interface TodayItem {
  medication_id: number;
  name: string;
  status: DoseStatus;
}

export interface TodaySlot {
  slot: Slot;
  items: TodayItem[];
  warnings: string[];
}

export interface TodayResponse {
  date: string;
  slots: TodaySlot[];
  adherence: number;
}

export interface ScheduleOut {
  medication_id: number;
  name: string;
  slots: Slot[];
}

export interface Adherence {
  percent: number;
  taken: number;
  expected: number;
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("email");
}

async function refreshTokens(): Promise<boolean> {
  const refresh = localStorage.getItem("refresh_token");
  if (!refresh) return false;
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return true;
}

async function request(path: string, options: RequestInit = {}, retry = true): Promise<Response> {
  const headers = new Headers(options.headers);
  const access = localStorage.getItem("access_token");
  if (access) headers.set("Authorization", `Bearer ${access}`);

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    if (retry && (await refreshTokens())) {
      return request(path, options, false);
    }
    // refresh failed → session is dead: clear and bounce to login
    clearTokens();
    if (window.location.pathname !== "/login") {
      window.location.assign("/login");
    }
  }
  return res;
}

async function detail(res: Response, fallback: string): Promise<string> {
  try {
    return (await res.json()).detail ?? fallback;
  } catch {
    return fallback;
  }
}

export const api = {
  isLoggedIn: () => !!localStorage.getItem("access_token"),
  getEmail: () => localStorage.getItem("email"),
  clearTokens,

  async register(email: string, password: string) {
    const res = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error(await detail(res, "Registration failed"));
  },

  async login(email: string, password: string) {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: email, password }),
    });
    if (!res.ok) throw new Error(await detail(res, "Login failed"));
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    localStorage.setItem("email", email);
},

  async logout() {
    await request("/auth/logout", { method: "POST" });
    clearTokens();
  },

  async listMedications(): Promise<Medication[]> {
    const res = await request("/medications");
    if (!res.ok) throw new Error(await detail(res, "Failed to load medications"));
    return res.json();
  },

  async addMedication(name: string, drugs?: string[], durationDays?: number | null): Promise<Medication> {
    const res = await request("/medications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, drugs, duration_days: durationDays ?? null }),
    });
    if (!res.ok) throw new Error(await detail(res, "Failed to add medication"));
    return res.json();
  },

  async updateMedication(
    id: number,
    data: { name?: string; duration_days?: number | null }
  ): Promise<Medication> {
    const res = await request(`/medications/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await detail(res, "Failed to update medication"));
    return res.json();
  },

  async getHistory(days = 30): Promise<DayStat[]> {
    const res = await request(`/tracking/history?days=${days}`);
    if (!res.ok) throw new Error(await detail(res, "Failed to load history"));
    return res.json();
  },

  async deleteMedication(id: number) {
    const res = await request(`/medications/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(await detail(res, "Failed to delete"));
  },

  async checkMyMedications(): Promise<CheckResponse> {
    const res = await request("/medications/check");
    if (!res.ok) throw new Error(await detail(res, "Check failed"));
    return res.json();
  },

  async scan(file: File): Promise<ScanResponse> {
    const form = new FormData();
    form.append("image", file);
    const res = await request("/scan", { method: "POST", body: form });
    if (!res.ok) throw new Error(await detail(res, "Scan failed"));
    return res.json();
  },

  async listScans(): Promise<ScanRecord[]> {
    const res = await request("/scans");
    if (!res.ok) throw new Error(await detail(res, "Failed to load scans"));
    return res.json();
  },

  async deleteScan(id: number) {
    const res = await request(`/scans/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(await detail(res, "Failed to delete scan"));
  },

  async checkInteractions(drugs: string[]): Promise<CheckResponse> {
    const res = await request("/interactions/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ drugs }),
    });
    if (!res.ok) throw new Error(await detail(res, "Check failed"));
    return res.json();
  },

  async getProfile(): Promise<Profile> {
    const res = await request("/me");
    if (!res.ok) throw new Error(await detail(res, "Failed to load profile"));
    return res.json();
  },

  async updateProfile(data: Partial<Omit<Profile, "id" | "email">>): Promise<Profile> {
    const res = await request("/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await detail(res, "Failed to update profile"));
    return res.json();
  },

  async getToday(): Promise<TodayResponse> {
    const res = await request("/tracking/today");
    if (!res.ok) throw new Error(await detail(res, "Failed to load today"));
    return res.json();
  },

  async getSchedule(): Promise<ScheduleOut[]> {
    const res = await request("/tracking/schedule");
    if (!res.ok) throw new Error(await detail(res, "Failed to load schedule"));
    return res.json();
  },

  async setSchedule(medId: number, slots: Slot[]): Promise<ScheduleOut> {
    const res = await request(`/tracking/schedule/${medId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slots }),
    });
    if (!res.ok) throw new Error(await detail(res, "Failed to save schedule"));
    return res.json();
  },

  async logDose(medId: number, slot: Slot, status: "taken" | "skipped") {
    const res = await request("/tracking/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ medication_id: medId, slot, status }),
    });
    if (!res.ok) throw new Error(await detail(res, "Failed to log dose"));
    return res.json();
  },

  async getAdherence(): Promise<Adherence> {
    const res = await request("/tracking/adherence");
    if (!res.ok) throw new Error(await detail(res, "Failed to load adherence"));
    return res.json();
  },

  async searchDrugs(q: string): Promise<DrugHit[]> {
    const res = await request(`/drugs/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) return [];
    return res.json();
  },

};