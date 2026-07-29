import { Navigate, Route, Routes } from "react-router-dom";
import type { ReactElement } from "react";

import { useAuth } from "./auth/AuthContext";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import styles from "./App.module.css";

function ProtectedRoute({ children }: { children: ReactElement }) {
  const { user, initializing } = useAuth();
  if (initializing) return <LoadingScreen />;
  if (!user) return <Navigate to="/" replace />;
  return children;
}

function LoadingScreen() {
  return (
    <div className={styles.loading} role="status">
      <span>RR</span>
      <p>Открываем рабочее пространство…</p>
    </div>
  );
}

export default function App() {
  const { initializing } = useAuth();
  if (initializing) return <LoadingScreen />;

  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
