export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  created_at: string;
}

export interface AuthResponse {
  token: string;
  user: User;
  message?: string;
}

export interface ResumeSection {
  id: string;
  section_type: string;
  section_type_display: string;
  content: string;
  structured_metadata: Record<string, any>;
  order_index: number;
}

export interface ResumeSkill {
  id: string;
  skill_name: string;
  category: string;
  evidence_text: string;
  extraction_method: string;
  confidence: number;
}

export interface ResumeListItem {
  id: string;
  title: string;
  original_filename: string;
  file_size_bytes: number;
  mime_type: string;
  parsing_status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  parsing_status_display: string;
  error_details: string;
  skills_count: number;
  created_at: string;
  updated_at: string;
}

export interface ResumeDetail extends ResumeListItem {
  raw_text: string;
  sections: ResumeSection[];
  skills: ResumeSkill[];
}

export interface JobRequirement {
  id: string;
  skill_name: string;
  category: string;
  is_mandatory: boolean;
  importance_weight: number;
  evidence_text: string;
}

export interface JobListItem {
  id: string;
  title: string;
  company_name: string;
  source_url: string;
  requirements_count: number;
  created_at: string;
  updated_at: string;
}

export interface JobDetail extends JobListItem {
  description: string;
  requirements: JobRequirement[];
}

export interface MatchSkillResult {
  id: string;
  skill_name: string;
  status: 'MATCHED' | 'RELATED' | 'MISSING' | 'NEEDS_REVIEW';
  status_display: string;
  is_mandatory: boolean;
  match_value: number;
  supporting_evidence: string;
}

export interface MatchListItem {
  id: string;
  resume: string;
  job: string;
  resume_title: string;
  job_title: string;
  company_name: string;
  overall_score: number;
  weighted_coverage_score: number;
  coverage_score: number;
  semantic_score: number;
  used_fallback: boolean;
  created_at: string;
}

export interface MatchDetail extends MatchListItem {
  model_version: string;
  scoring_config_version: string;
  weights_used: Record<string, number>;
  structured_explanation: {
    summary?: string;
    matched_count?: number;
    missing_count?: number;
    formula?: string;
    disclaimer?: string;
    warnings?: string[];
  };
  skill_results: MatchSkillResult[];
  matched_skills: MatchSkillResult[];
  related_skills: MatchSkillResult[];
  missing_skills: MatchSkillResult[];
  needs_review_skills: MatchSkillResult[];
}

export interface RoadmapResource {
  title: string;
  url: string;
  type: string;
}

export interface RoadmapItem {
  id: string;
  skill_name: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  priority_display: string;
  estimated_weeks: number;
  rationale: string;
  suggested_project: string;
  resources: RoadmapResource[];
  is_completed: boolean;
  completed_at: string | null;
  order_index: number;
}

export interface RoadmapDetail {
  id: string;
  match: string;
  title: string;
  target_role: string;
  match_score: number;
  items: RoadmapItem[];
  completed_items_count: number;
  total_items_count: number;
  created_at: string;
  updated_at: string;
}

export interface RoadmapListItem {
  id: string;
  match: string;
  title: string;
  target_role: string;
  match_score: number;
  completed_items_count: number;
  total_items_count: number;
  created_at: string;
  updated_at: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  timestamp: string;
  metadata: Record<string, any>;
}
