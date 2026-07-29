import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { PropsWithChildren } from "react";

import * as api from "../api/client";
import type { User } from "../types";

export interface AuthContextValue {
  user: User | null;
  initializing: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    let active = true;
    api
      .refreshSession()
      .then((session) => {
        if (active) setUser(session.user);
      })
      .catch(() => {
        api.setAccessToken(null);
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setInitializing(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    api.setSessionExpiredHandler(() => setUser(null));
    return () => api.setSessionExpiredHandler(null);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const session = await api.login(username, password);
    setUser(session.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
    }
  }, []);

  const changePassword = useCallback(async (currentPassword: string, newPassword: string) => {
    await api.changePassword(currentPassword, newPassword);
    api.setAccessToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, initializing, login, logout, changePassword }),
    [user, initializing, login, logout, changePassword],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
