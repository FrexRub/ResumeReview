import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { LoginForm } from "../components/LoginForm";
import { DocumentIcon } from "../components/Icons";
import { useAuth } from "../auth/AuthContext";
import styles from "./LoginPage.module.css";

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const passwordChanged = new URLSearchParams(location.search).get("passwordChanged") === "true";

  if (user) return <Navigate to="/dashboard" replace />;

  async function handleLogin(username: string, password: string) {
    await login(username, password);
    navigate("/dashboard", { replace: true });
  }

  return (
    <main className={styles.page}>
      <header className={styles.topbar}>
        <a className={styles.brand} href="/" aria-label="ResumeReview — главная">
          <span className={styles.brandMark}>RR</span>
          <span>ResumeReview</span>
        </a>
        <span className={styles.edition}>Рабочая версия · 01</span>
      </header>

      {passwordChanged && (
        <div className={styles.success} role="status">
          Пароль изменен. Войдите с новыми данными.
        </div>
      )}

      <section className={styles.hero}>
        <div className={styles.story}>
          <span className={styles.issue}>КАРЬЕРА / БЕЗ ШУМА</span>
          <h1>
            Вакансия говорит
            <br />
            <em>больше, чем кажется.</em>
          </h1>
          <p className={styles.lead}>
            Превращаем документы с требованиями в чистый текст — основу для точного,
            аргументированного разбора резюме.
          </p>
          <div className={styles.rule} />
          <div className={styles.features}>
            <article>
              <span>01</span>
              <DocumentIcon />
              <h2>Загрузите документ</h2>
              <p>PDF, DOCX и другие рабочие форматы до 20 МБ.</p>
            </article>
            <article>
              <span>02</span>
              <div className={styles.typeGlyph}>Aa</div>
              <h2>Получите чистый текст</h2>
              <p>Структурированный результат без ручного копирования.</p>
            </article>
          </div>
        </div>
        <LoginForm onSubmit={handleLogin} />
      </section>

      <footer className={styles.footer}>
        <span>Инструмент осознанного карьерного выбора</span>
        <span>2026</span>
      </footer>
    </main>
  );
}
