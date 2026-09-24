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

  // 204 responses carry no body, so parsing one as JSON would throw on an
  // otherwise successful request.
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

/**
 * Like request(), but also hands back the Response.
 *
 * Pagination totals travel in X-Total-Count rather than the body, so the
 * caller needs the headers. Only used where that matters.
 */
async function requestWithResponse<T>(
  path: string,
  options: RequestInit = {},
  auth = false,
): Promise<{ data: T; response: Response }> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (auth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (response.status === 401) {
    clearToken();
    if (typeof window !== 'undefined') window.location.href = '/auth/login';
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }

  return { data: await response.json(), response };
}

// ══════════════════════════════════════════════
// API TYPES (mirror backend Pydantic schemas)
// ══════════════════════════════════════════════

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export type Role = 'owner' | 'admin' | 'member';

export interface OrgProfile {
  id: string;
  name: string;
  email: string;
  description: string;
  domain_tags: string[];
  logo_url: string;
  created_at: string;
  // Who is signed in, as opposed to which organisation. Optional so an older
  // backend that does not send it still deserialises.
  user_id?: string;
  user_name?: string;
  user_email?: string;
  role?: Role;
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

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'owner' | 'admin' | 'member';
  is_active: boolean;
  has_accepted_invite: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface AuditEntry {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  entity_label: string;
  detail: Record<string, unknown>;
  created_at: string;
}

export interface BulkDecisionResult {
  updated: number;
  skipped: string[];
  status: string;
}

export interface SubmissionFileLink {
  url: string;
  expires_in_seconds: number;
}

/** A page of applicants plus the total, read from the X-Total-Count header. */
export interface ApplicantPage {
  items: ApplicantResponse[];
  total: number;
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

/** Returned by the upload endpoint; `file_url` holds the stored object key. */
export interface FileUploadResponse {
  file_url: string;
  filename: string;
}

/** One question-and-answer pair as stored on the interview transcript. */
export interface TranscriptEntry {
  round: string;
  question: string;
  answer: string;
  timestamp: string;
}

/** Full interview detail, for the recruiter. Extends the summary with the transcript. */
export interface InterviewDetail extends InterviewSummary {
  transcript: TranscriptEntry[];
  applicant_name: string;
  drive_name: string;
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

  changePassword: (data: { current_password: string; new_password: string }) =>
    request<void>('/api/auth/change-password', { method: 'POST', body: JSON.stringify(data) }, true),

  // Always resolves, whether or not the address is registered — the API
  // deliberately does not reveal which, so the UI must not either.
  forgotPassword: (data: { email: string }) =>
    request<void>('/api/auth/forgot-password', { method: 'POST', body: JSON.stringify(data) }),

  resetPassword: (data: { token: string; new_password: string }) =>
    request<void>('/api/auth/reset-password', { method: 'POST', body: JSON.stringify(data) }),

  /**
   * Permanently delete the organisation and everything under it.
   *
   * Owner-only, and the password is required even though the caller is signed
   * in — this erases every drive, candidate, transcript and audit entry, so a
   * borrowed session must not be enough to trigger it.
   */
  deleteAccount: (data: { current_password: string; confirm: boolean }) =>
    request<void>('/api/auth/me', { method: 'DELETE', body: JSON.stringify(data) }, true),

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

  /**
   * Edit a drive. Only the fields sent are applied.
   *
   * `task_type` is not editable server-side: switching a drive between the
   * task and GitHub flows mid-round would strand applicants who already went
   * down the other branch. `link_token` is likewise fixed, so rotating the
   * public link cannot silently break every share and QR code handed out.
   */
  updateDrive: (id: string, data: {
    name?: string;
    domain?: string;
    task_description?: string;
    question_level?: 'beginner' | 'intermediate' | 'advanced';
    apply_deadline?: string;
    task_deadline?: string | null;
    status?: 'active' | 'closed';
  }) => request<DriveResponse>(`/api/drives/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  }, true),

  /**
   * Delete a drive and every applicant under it.
   *
   * Owner-only. The API refuses with 409 when the drive has applicants unless
   * `confirm` is true, so a stray click cannot wipe a live round.
   */
  deleteDrive: (id: string, confirm = false) =>
    request<void>(
      `/api/drives/${id}${confirm ? '?confirm=true' : ''}`,
      { method: 'DELETE' },
      true,
    ),

  /**
   * Page through one drive's applicants.
   *
   * Drive detail embeds only a bounded preview, so this is how a client reads
   * the rest without pulling every candidate in one response.
   */
  listDriveApplicants: async (
    id: string,
    params: { limit?: number; offset?: number } = {},
  ): Promise<ApplicantPage> => {
    const query = new URLSearchParams(
      Object.entries(params)
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => [k, String(v)]),
    ).toString();
    const { data, response } = await requestWithResponse<ApplicantResponse[]>(
      `/api/drives/${id}/applicants${query ? `?${query}` : ''}`, {}, true,
    );
    const total = Number(response.headers.get('X-Total-Count') ?? data.length);
    return { items: data, total: Number.isFinite(total) ? total : data.length };
  },

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
  // Keyed on the submission token from the emailed link, never an applicant id.
  submitTask: (submitToken: string, data: {
    file_url?: string;
    github_url?: string;
    description?: string;
  }) => request<SubmissionResponse>(`/api/submit/${submitToken}`, { method: 'POST', body: JSON.stringify(data) }),

  /**
   * Upload a submission file and return the stored object key.
   *
   * The key is what `submitTask` expects in `file_url` — the server never
   * accepts a client-chosen path. Multipart, so it bypasses `request()`,
   * which forces a JSON content type.
   */
  uploadSubmissionFile: async (
    submitToken: string,
    file: File,
  ): Promise<FileUploadResponse> => {
    const form = new FormData();
    form.append('file', file);

    const res = await fetch(`${API_BASE_URL}/api/submit/${submitToken}/upload`, {
      method: 'POST',
      body: form,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Upload failed: ${res.status}`);
    }
    return res.json();
  },

  // ── Interview (public) ──
  getInterviewConfig: (token: string) =>
    request<InterviewConfig>(`/api/interview/${token}`),

  /**
   * Upload the captured interview recording.
   *
   * Not gated on link expiry server-side: a candidate finishing on the
   * boundary must still be able to upload what they just recorded.
   */
  uploadInterviewRecording: async (token: string, file: Blob, filename = 'interview.webm') => {
    const form = new FormData();
    form.append('file', file, filename);

    const res = await fetch(`${API_BASE_URL}/api/interview/${token}/recording`, {
      method: 'POST',
      body: form,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Recording upload failed: ${res.status}`);
    }
  },

  /**
   * Full interview detail for a recruiter — transcript, scores, flags.
   *
   * Authenticated and scoped to the calling organisation: an unknown token
   * and another organisation's token both return 404.
   */
  getInterviewDetail: (token: string) =>
    request<InterviewDetail>(`/api/interview/${token}/detail`, {}, true),

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
  // ── Applicants (organisation) ──
  listApplicants: async (params: {
    drive_id?: string;
    status?: string;
    q?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<ApplicantPage> => {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '') as [string, string][],
    ).toString();
    const { data, response } = await requestWithResponse<ApplicantResponse[]>(
      `/api/applicants${query ? `?${query}` : ''}`, {}, true,
    );
    // Falls back to the page length if the header is missing — which happens
    // when a proxy strips it, and is better than showing "of 0".
    const total = Number(response.headers.get('X-Total-Count') ?? data.length);
    return { items: data, total: Number.isFinite(total) ? total : data.length };
  },

  getApplicant: (id: string) =>
    request<ApplicantResponse>(`/api/applicants/${id}`, {}, true),

  decideApplicant: (id: string, decision: 'selected' | 'rejected') =>
    request<{ id: string; status: string; result_email_sent: boolean }>(
      `/api/applicants/${id}/decision`,
      { method: 'POST', body: JSON.stringify({ decision }) },
      true,
    ),

  bulkDecision: (applicant_ids: string[], decision: 'selected' | 'rejected') =>
    request<BulkDecisionResult>(
      '/api/applicants/bulk-decision',
      { method: 'POST', body: JSON.stringify({ applicant_ids, decision }) },
      true,
    ),

  resendEmail: (id: string, type: 'applied' | 'task' | 'interview' | 'result') =>
    request<void>(
      `/api/applicants/${id}/resend-email`,
      { method: 'POST', body: JSON.stringify({ type }) },
      true,
    ),

  getSubmissionFileLink: (id: string) =>
    request<SubmissionFileLink>(`/api/applicants/${id}/submission-file`, {}, true),

  deleteApplicant: (id: string) =>
    request<void>(`/api/applicants/${id}`, { method: 'DELETE' }, true),

  /**
   * CSV export.
   *
   * Fetched as a blob rather than linked directly, because the endpoint needs
   * the Authorization header and a plain <a href> cannot send one.
   */
  exportApplicants: async (params: { drive_id?: string; status?: string; q?: string } = {}) => {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '') as [string, string][],
    ).toString();
    const res = await fetch(`${API_BASE_URL}/api/applicants/export${query ? `?${query}` : ''}`, {
      headers: { Authorization: `Bearer ${getToken() ?? ''}` },
    });
    if (!res.ok) throw new Error(`Export failed: ${res.status}`);
    return res.blob();
  },

  // ── Team ──
  listTeam: () => request<TeamMember[]>('/api/team', {}, true),

  inviteMember: (data: { name?: string; email: string; role: 'admin' | 'member' }) =>
    request<TeamMember>('/api/team', { method: 'POST', body: JSON.stringify(data) }, true),

  updateMemberRole: (id: string, role: 'owner' | 'admin' | 'member') =>
    request<TeamMember>(`/api/team/${id}`, { method: 'PATCH', body: JSON.stringify({ role }) }, true),

  removeMember: (id: string) =>
    request<void>(`/api/team/${id}`, { method: 'DELETE' }, true),

  // ── Audit ──
  listAudit: (params: { action?: string; entity_id?: string; limit?: number } = {}) => {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '') as [string, string][],
    ).toString();
    return request<AuditEntry[]>(`/api/audit${query ? `?${query}` : ''}`, {}, true);
  },

  // ── Candidate self-service ──
  getOwnStatus: (submitToken: string) =>
    request<{
      name: string;
      drive_name: string;
      organisation_name: string;
      status: string;
      applied_at: string;
      task_deadline: string | null;
      has_submitted: boolean;
      interview_completed: boolean;
      decision: string | null;
    }>(`/api/status/${submitToken}`),

  getAnalytics: () => request<AnalyticsResponse>('/api/analytics/dashboard', {}, true),
};
