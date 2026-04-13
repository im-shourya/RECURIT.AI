const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── Token helpers ──
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('recruit_ai_token');
}

export function setToken(token: string) {
  localStorage.setItem('recruit_ai_token', token);
}

export function clearToken() {
  localStorage.removeItem('recruit_ai_token');
}

// ── Typed fetch wrapper ──
async function request<T>(
  path: string,
  options: RequestInit = {},
  auth: boolean = false,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (auth) {
    const token = getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/auth/login';
    }
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }

  return res.json();
}

// ══════════════════════════════════════════════
// API TYPES (mirror backend Pydantic schemas)
// ══════════════════════════════════════════════

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface OrgProfile {
  id: string;
  name: string;
  email: string;
  description: string;
  domain_tags: string[];
  logo_url: string;
  created_at: string;
}

export interface DriveResponse {
  id: string;
  org_id: string;
  name: string;
  domain: string;
  task_type: 'task' | 'github';
  task_description: string;
  question_level: 'beginner' | 'intermediate' | 'advanced';
  apply_deadline: string;
  task_deadline: string | null;
  link_token: string;
  qr_code_url: string;
  status: 'active' | 'closed';
  created_at: string;
  applicant_count: number;
}

export interface ApplicantResponse {
  id: string;
  drive_id: string;
  name: string;
  email: string;
  reg_no: string;
  skills: string[];
  primary_domain: string;
  github_url: string;
  status: string;
  applied_at: string;
  submission?: SubmissionResponse | null;
  interview?: InterviewSummary | null;
}

export interface DriveDetailResponse extends DriveResponse {
  organisation_name: string;
  applicants: ApplicantResponse[];
}

export interface DrivePublicResponse {
  id: string;
  name: string;
  domain: string;
  task_type: 'task' | 'github';
  task_description: string;
  question_level: string;
  apply_deadline: string;
  task_deadline: string | null;
  organisation_name: string;
  organisation_logo: string;
  status: string;
}

export interface SubmissionResponse {
  id: string;
  applicant_id: string;
  file_url: string;
  github_url: string;
  description: string;
  repolens_analysis: Record<string, unknown>;
  submitted_at: string;
}

export interface InterviewConfig {
  interview_id: string;
  applicant_name: string;
  drive_name: string;
  domain: string;
  question_level: string;
  task_type: string;
  repolens_analysis: Record<string, unknown>;
  max_duration_seconds: number;
}

export interface InterviewAnswerResponse {
  next_question: string;
  round_name: string;
  is_last: boolean;
}

export interface InterviewEndResponse {
  total_score: number;
  score_intro: number;
  score_project: number;
  score_domain: number;
  message: string;
}

export interface InterviewSummary {
  id: string;
  token: string;
  started_at: string | null;
  ended_at: string | null;
  recording_url: string;
  score_intro: number;
  score_project: number;
  score_domain: number;
  total_score: number;
  malpractice_flags: unknown[];
}

export interface ChartDataPoint {
  name: string;
  value: number;
}

export interface AnalyticsResponse {
  total_drives: number;
  active_drives: number;
  total_applicants: number;
  total_interviews: number;
  avg_score: number;
  score_distribution: ChartDataPoint[];
  domain_distribution: ChartDataPoint[];
  status_distribution: ChartDataPoint[];
  recent_trend: ChartDataPoint[];
}

// ══════════════════════════════════════════════
// API METHODS
// ══════════════════════════════════════════════

export const api = {
  // ── Auth ──
  register: (data: {
    name: string;
    email: string;
    password: string;
    description?: string;
  }) => request<TokenResponse>('/api/auth/register', { method: 'POST', body: JSON.stringify(data) }),

  login: (data: { email: string; password: string }) =>
    request<TokenResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify(data) }),

  getMe: () => request<OrgProfile>('/api/auth/me', {}, true),

  updateMe: (data: {
    name?: string;
    description?: string;
    domain_tags?: string[];
    logo_url?: string;
  }) => request<OrgProfile>('/api/auth/me', { method: 'PATCH', body: JSON.stringify(data) }, true),

  // ── Drives (authed) ──
  createDrive: (data: {
    name: string;
    domain: string;
    task_type: string;
    task_description?: string;
    question_level?: string;
    apply_deadline: string;
    task_deadline?: string | null;
  }) => request<DriveResponse>('/api/drives', { method: 'POST', body: JSON.stringify(data) }, true),

  listDrives: () => request<DriveResponse[]>('/api/drives', {}, true),

  getDrive: (id: string) => request<DriveDetailResponse>(`/api/drives/${id}`, {}, true),

  updateDriveStatus: (id: string, status: 'active' | 'closed') =>
    request<DriveResponse>(`/api/drives/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }, true),

  // ── Apply (public) ──
  getDriveForApply: (token: string) =>
    request<DrivePublicResponse>(`/api/apply/${token}`),

  submitApplication: (token: string, data: {
    name: string;
    email: string;
    reg_no?: string;
    skills: string[];
    primary_domain: string;
    github_url?: string;
  }) => request<ApplicantResponse>(`/api/apply/${token}`, { method: 'POST', body: JSON.stringify(data) }),

  // ── Submit (public) ──
  submitTask: (applicantId: string, data: {
    file_url?: string;
    github_url?: string;
    description?: string;
  }) => request<SubmissionResponse>(`/api/submit/${applicantId}`, { method: 'POST', body: JSON.stringify(data) }),

  // ── Interview (public) ──
  getInterviewConfig: (token: string) =>
    request<InterviewConfig>(`/api/interview/${token}`),

  startInterview: (token: string) =>
    request<{ interview_id: string; message: string }>(`/api/interview/${token}/start`, { method: 'POST', body: '{}' }),

  submitAnswer: (token: string, data: {
    question_text: string;
    answer_text: string;
    round_name: string;
  }) => request<InterviewAnswerResponse>(`/api/interview/${token}/answer`, { method: 'POST', body: JSON.stringify(data) }),

  endInterview: (token: string, recording_url: string = '') =>
    request<InterviewEndResponse>(`/api/interview/${token}/end`, {
      method: 'POST',
      body: JSON.stringify({ recording_url }),
    }),

  // ── Analytics (authed) ──
  getAnalytics: () => request<AnalyticsResponse>('/api/analytics/dashboard', {}, true),
};
