import type {
  User, AuthResponse, ResumeListItem, ResumeDetail,
  JobListItem, JobDetail, MatchListItem, MatchDetail,
  RoadmapListItem, RoadmapDetail, RoadmapItem, AuditEvent,
  FAQ, FAQCategory, SupportTicket, GitHubInsight, ErrorRegistryItem
} from '../types';

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string)?.replace(/\/+$/, '') || '/api/v1';

let guestSessionPromise: Promise<string> | null = null;

export async function ensureSessionToken(): Promise<string> {
  const existingToken = localStorage.getItem('skillbridge_token');
  if (existingToken) {
    return existingToken;
  }

  // Deduplicate concurrent guest session initializations
  if (guestSessionPromise) {
    return guestSessionPromise;
  }

  guestSessionPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/guest-session/`);
      if (response.ok) {
        const data = await response.json();
        if (data.token) {
          localStorage.setItem('skillbridge_token', data.token);
          localStorage.setItem('skillbridge_is_guest', 'true');
          localStorage.setItem(
            'skillbridge_user',
            JSON.stringify({ id: data.user_id, email: 'Guest Session', first_name: 'Guest' })
          );
          return data.token as string;
        }
      }
    } catch {
      // ignore network errors on init
    } finally {
      guestSessionPromise = null;
    }
    return '';
  })();

  return guestSessionPromise;
}

async function request<T>(endpoint: string, options: RequestInit = {}, isRetry = false): Promise<T> {
  let token = localStorage.getItem('skillbridge_token');

  // If unauthenticated and calling an operation that needs session tracking, initialize guest session
  const requiresSession =
    endpoint.startsWith('/resumes') ||
    endpoint.startsWith('/matches') ||
    endpoint.startsWith('/roadmaps') ||
    (endpoint.startsWith('/jobs') && options.method && options.method !== 'GET');

  if (!token && requiresSession) {
    token = await ensureSessionToken();
  }

  const headers = new Headers(options.headers || {});
  const isGuest = localStorage.getItem('skillbridge_is_guest') === 'true';

  if (token) {
    headers.set('Authorization', `Token ${token}`);
    if (isGuest) {
      headers.set('X-Guest-Token', token);
    }
  }

  // Do not set Content-Type if uploading FormData (browser handles boundary automatically)
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const isAssistantEndpoint = endpoint.startsWith('/assistant/');
  const timeoutMs = isAssistantEndpoint ? 50000 : 30000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
      signal: options.signal || controller.signal,
    });
  } catch (netErr: any) {
    if (netErr.name === 'AbortError') {
      throw new Error(
        `Request timed out after ${timeoutMs / 1000}s. The SkillBridge backend may be waking up or temporarily busy. Please retry.`
      );
    }
    if (isAssistantEndpoint) {
      throw new Error(
        'The assistant is temporarily unavailable. Your message is still here. Please try again shortly.'
      );
    }
    // Clean transformation for browser-level network failures (avoids raw "Failed to fetch")
    throw new Error(
      'Unable to connect to SkillBridge server. The service may be waking up from sleep or experiencing network latency. Please retry.'
    );
  } finally {
    clearTimeout(timeoutId);
  }

  if (response.status === 401) {
    // If a guest session was expired or purged, refresh guest token once and retry
    if (isGuest && !isRetry) {
      localStorage.removeItem('skillbridge_token');
      localStorage.removeItem('skillbridge_is_guest');
      localStorage.removeItem('skillbridge_user');
      const newToken = await ensureSessionToken();
      if (newToken) {
        return request<T>(endpoint, options, true);
      }
    }

    // Only redirect to login if the user had a registered account that expired
    if (!isGuest) {
      localStorage.removeItem('skillbridge_token');
      localStorage.removeItem('skillbridge_user');
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        window.location.href = '/login';
      }
    }
  }

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.error || errorJson.detail || errorJson.message || JSON.stringify(errorJson);
    } catch {
      if (response.status === 502 || response.status === 503 || response.status === 504) {
        errorDetail = `SkillBridge service is temporarily unavailable (HTTP ${response.status}). Please retry in a few moments.`;
      }
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Session & Auth
  isGuest: () => localStorage.getItem('skillbridge_is_guest') === 'true',
  ensureGuestSession: () => ensureSessionToken(),
  discardGuestSession: async () => {
    const isGuest = localStorage.getItem('skillbridge_is_guest') === 'true';
    const token = localStorage.getItem('skillbridge_token');
    if (isGuest && token) {
      try {
        await fetch(`${API_BASE}/auth/guest-session/`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Token ${token}`,
            'X-Guest-Token': token,
          },
        });
      } catch {
        // ignore
      }
    }
    localStorage.removeItem('skillbridge_token');
    localStorage.removeItem('skillbridge_is_guest');
    localStorage.removeItem('skillbridge_user');
  },

  register: async (data: any) => {
    const isGuest = localStorage.getItem('skillbridge_is_guest') === 'true';
    const guestToken = localStorage.getItem('skillbridge_token');
    const payload = isGuest && guestToken ? { ...data, guest_token: guestToken } : data;

    const resp = await request<AuthResponse>('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    localStorage.removeItem('skillbridge_is_guest');
    return resp;
  },

  login: async (data: any) => {
    const isGuest = localStorage.getItem('skillbridge_is_guest') === 'true';
    const guestToken = localStorage.getItem('skillbridge_token');
    const payload = isGuest && guestToken ? { ...data, guest_token: guestToken } : data;

    const resp = await request<AuthResponse>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    localStorage.removeItem('skillbridge_is_guest');
    return resp;
  },

  logout: async () => {
    const isGuest = localStorage.getItem('skillbridge_is_guest') === 'true';
    if (!isGuest) {
      try {
        await request<{ message: string }>('/auth/logout/', { method: 'POST' });
      } catch {
        // ignore
      }
    }
    localStorage.removeItem('skillbridge_token');
    localStorage.removeItem('skillbridge_is_guest');
    localStorage.removeItem('skillbridge_user');
    return { message: 'Logged out successfully' };
  },

  getCurrentUser: () => request<User>('/auth/me/'),

  // Resumes
  getResumes: () => request<ResumeListItem[]>('/resumes/'),
  getResume: (id: string) => request<ResumeDetail>(`/resumes/${id}/`),
  uploadResume: (formData: FormData) => request<ResumeDetail>('/resumes/', { method: 'POST', body: formData }),
  updateResumeSkills: (id: string, skills: string[]) => request<ResumeDetail>(`/resumes/${id}/skills/`, {
    method: 'POST',
    body: JSON.stringify({ skills }),
  }),
  deleteResume: (id: string) => request<{ message: string }>(`/resumes/${id}/`, { method: 'DELETE' }),

  // Jobs
  getJobs: () => request<JobListItem[]>('/jobs/'),
  getJob: (id: string) => request<JobDetail>(`/jobs/${id}/`),
  createJob: (data: { title: string; company_name?: string; description: string; source_url?: string }) =>
    request<JobDetail>('/jobs/', { method: 'POST', body: JSON.stringify(data) }),
  deleteJob: (id: string) => request<{ message: string }>(`/jobs/${id}/`, { method: 'DELETE' }),

  // Matches
  getMatches: () => request<MatchListItem[]>('/matches/'),
  getMatch: (id: string) => request<MatchDetail>(`/matches/${id}/`),
  createMatch: (resumeId: string, jobId: string) =>
    request<MatchDetail>('/matches/', {
      method: 'POST',
      body: JSON.stringify({ resume_id: resumeId, job_id: jobId }),
    }),
  deleteMatch: (id: string) => request<{ message: string }>(`/matches/${id}/`, { method: 'DELETE' }),
  getReportUrl: (matchId: string) => `${API_BASE}/matches/${matchId}/report/`,

  // Roadmaps
  getRoadmaps: () => request<RoadmapListItem[]>('/roadmaps/'),
  getRoadmap: (id: string) => request<RoadmapDetail>(`/roadmaps/${id}/`),
  createRoadmap: (matchId: string) =>
    request<RoadmapDetail>('/roadmaps/', {
      method: 'POST',
      body: JSON.stringify({ match_id: matchId }),
    }),
  toggleRoadmapItem: (roadmapId: string, itemId: string, isCompleted: boolean) =>
    request<RoadmapItem>(`/roadmaps/${roadmapId}/items/${itemId}/`, {
      method: 'PATCH',
      body: JSON.stringify({ is_completed: isCompleted }),
    }),
  deleteRoadmap: (id: string) => request<{ message: string }>(`/roadmaps/${id}/`, { method: 'DELETE' }),

  // Audit
  getAuditEvents: () => request<AuditEvent[]>('/audit/events/'),

  // FAQ
  getFAQs: (params?: { q?: string; category?: string }) => {
    const query = new URLSearchParams();
    if (params?.q) query.append('q', params.q);
    if (params?.category) query.append('category', params.category);
    const qs = query.toString();
    return request<FAQ[]>(`/faq/${qs ? `?${qs}` : ''}`);
  },
  getFAQCategories: () => request<FAQCategory[]>('/faq/categories/'),

  // Support
  getSupportTickets: () => request<SupportTicket[]>('/support/'),
  createSupportTicket: (data: {
    contact_email?: string;
    subject: string;
    description: string;
    category?: string;
    priority?: string;
    conversation_id?: string;
  }) => request<SupportTicket>('/support/', { method: 'POST', body: JSON.stringify(data) }),
  lookupSupportTicket: (ticketNumber: string, email: string) =>
    request<SupportTicket>(`/support/lookup/?ticket_number=${encodeURIComponent(ticketNumber)}&email=${encodeURIComponent(email)}`),

  // Assistant & Chat
  sendAssistantChat: (data: {
    message: string;
    conversation_id?: string;
    guest_session_id?: string;
    action?: string;
    email?: string;
    subject?: string;
    description?: string;
  }) => request<{
    conversation_id: string;
    guest_session_id?: string;
    answer: string;
    mode: string;
    model?: string;
    grounded_faqs?: string[];
    can_create_ticket?: boolean;
    ticket_created?: boolean;
    ticket_number?: string;
    ticket_id?: string;
    persisted_to_mongo?: boolean;
    persisted_user_message?: boolean;
    persisted_assistant_message?: boolean;
  }>('/assistant/chat/', { method: 'POST', body: JSON.stringify(data) }),
  sendAssistantFeedback: (data: { conversation_id: string; rating: number; comment?: string }) =>
    request<{ message: string; conversation_id: string; persisted_to_mongo: boolean }>(
      '/assistant/feedback/',
      { method: 'POST', body: JSON.stringify(data) }
    ),

  // GitHub Insights
  getGitHubInsights: (username: string) =>
    request<GitHubInsight>(`/integrations/github/?username=${encodeURIComponent(username)}`),

  // Error Code Registry
  getErrorRegistry: () => request<{ count: number; errors: ErrorRegistryItem[] }>('/errors/'),

  // Health Check
  checkHealth: () => request<{ status: string }>('/health/'),
};
