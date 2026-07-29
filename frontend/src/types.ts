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
