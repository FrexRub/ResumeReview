import type {
  ActiveVacancy,
  AuthResponse,
  ParsedVacancy,
  StoredVacancy,
  VacancyResume,
} from "../types";

const API_BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
let accessToken: string | null = null;
let refreshPromise: Promise<AuthResponse> | null = null;
let onSessionExpired: (() => void) | null = null;

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function readError(payload: unknown): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0] && typeof detail[0] === "object") {
      const message = (detail[0] as { msg?: unknown }).msg;
      if (typeof message === "string") return message.replace(/^Value error, /, "");
    }
  }
  return "Не удалось выполнить запрос";
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T;
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(readError(payload), response.status);
  return payload as T;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function setSessionExpiredHandler(handler: (() => void) | null): void {
  onSessionExpired = handler;
}

export function refreshSession(): Promise<AuthResponse> {
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE}/api/auth/refresh`, {
      method: "POST",
      credentials: "include",
    })
      .then(parseResponse<AuthResponse>)
      .then((session) => {
        setAccessToken(session.access_token);
        return session;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

async function request<T>(path: string, init: RequestInit = {}, canRetry = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });

  if (response.status === 401 && canRetry && !path.startsWith("/api/auth/")) {
    try {
      await refreshSession();
      return request<T>(path, init, false);
    } catch {
      setAccessToken(null);
      onSessionExpired?.();
      throw new ApiError("Сессия завершена. Войдите снова.", 401);
    }
  }
  return parseResponse<T>(response);
}

export function login(username: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>(
    "/api/auth/login",
    { method: "POST", body: JSON.stringify({ username, password }) },
    false,
  ).then((session) => {
    setAccessToken(session.access_token);
    return session;
  });
}

export async function logout(): Promise<void> {
  try {
    await request<void>("/api/auth/logout", { method: "POST" }, false);
  } finally {
    setAccessToken(null);
  }
}

export function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  return request<void>("/api/users/me/change-password", {
    method: "POST",
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}

export function parseVacancy(file: File): Promise<ParsedVacancy> {
  const formData = new FormData();
  formData.append("file", file);
  return request<ParsedVacancy>("/api/vacancies/parse", { method: "POST", body: formData });
}

export function saveVacancy(content: string, filename: string): Promise<StoredVacancy> {
  return request<StoredVacancy>("/api/vacancies", {
    method: "POST",
    body: JSON.stringify({ content, filename }),
  });
}

export function getActiveVacancy(): Promise<ActiveVacancy | null> {
  return request<ActiveVacancy | null>("/api/vacancies/active");
}

export function deactivateActiveVacancy(): Promise<StoredVacancy> {
  return request<StoredVacancy>("/api/vacancies/active", { method: "PATCH" });
}

export function getActiveVacancyResumes(): Promise<VacancyResume[]> {
  return request<VacancyResume[]>("/api/vacancies/active/resumes");
}

export function markResumeViewed(resumeId: string): Promise<void> {
  return request<void>(
    `/api/vacancies/resumes/${encodeURIComponent(resumeId)}/viewed`,
    { method: "PATCH" },
  );
}

function downloadFilename(response: Response): string {
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const encodedName = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
  if (encodedName) {
    try {
      return decodeURIComponent(encodedName);
    } catch {
      // Fall back to the ASCII filename below.
    }
  }
  return disposition.match(/filename="([^"]+)"/i)?.[1] ?? "resume";
}

export async function downloadResume(
  resumeId: string,
  canRetry = true,
): Promise<void> {
  const headers = new Headers();
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  const path = `/api/vacancies/resumes/${encodeURIComponent(resumeId)}/download`;
  const response = await fetch(`${API_BASE}${path}`, {
    headers,
    credentials: "include",
  });

  if (response.status === 401 && canRetry) {
    try {
      await refreshSession();
      return downloadResume(resumeId, false);
    } catch {
      setAccessToken(null);
      onSessionExpired?.();
      throw new ApiError("Сессия завершена. Войдите снова.", 401);
    }
  }
  if (!response.ok) {
    await parseResponse<void>(response);
    return;
  }

  const blobUrl = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = downloadFilename(response);
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(blobUrl), 0);
}
