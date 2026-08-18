export interface User {
  id: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  registered_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  user: User;
}

export interface ParsedVacancy {
  status: string;
  filename: string | null;
  mime_type: string | null;
  source_type: string;
  characters: number;
  text: string;
  warnings: string[];
}

export interface StoredVacancy {
  id: number;
  created_at: string;
  is_active: boolean;
}

export interface VacancyResume {
  id: string;
  title_vacancy: string | null;
  desired_position: string | null;
  summary_resume: string | null;
  score_label: string | null;
  candidate_rating: number | null;
  recommendation: string | null;
  recommendation_reason: string | null;
  executive_summary: string | null;
  short_conclusion: string | null;
  url_resume: string | null;
  viewed: boolean;
}
