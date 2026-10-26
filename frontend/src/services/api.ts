import type {
  User, AuthResponse, ResumeListItem, ResumeDetail,
  JobListItem, JobDetail, MatchListItem, MatchDetail,
  RoadmapListItem, RoadmapDetail, RoadmapItem, AuditEvent
} from '../types';

const API_BASE = '/api/v1';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('skillbridge_token');
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set('Authorization', `Token ${token}`);
  }

  // Do not set Content-Type if uploading FormData (browser handles boundary automatically)
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem('skillbridge_token');
    localStorage.removeItem('skillbridge_user');
    if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
      window.location.href = '/login';
    }
  }

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.error || errorJson.detail || JSON.stringify(errorJson);
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Auth
  register: (data: any) => request<AuthResponse>('/auth/register/', { method: 'POST', body: JSON.stringify(data) }),
  login: (data: any) => request<AuthResponse>('/auth/login/', { method: 'POST', body: JSON.stringify(data) }),
  logout: () => request<{ message: string }>('/auth/logout/', { method: 'POST' }),
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
};
