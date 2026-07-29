import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { PasswordPanel } from "../components/PasswordPanel";
import { VacancyUploader } from "../components/VacancyUploader";
import styles from "./DashboardPage.module.css";

export function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/", { replace: true });
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <a className={styles.brand} href="/dashboard"><span>RR</span>ResumeReview</a>
        <div className={styles.account}>
          <div><span>Пользователь</span><strong>{user?.username}</strong></div>
          <button type="button" onClick={handleLogout}>Выйти</button>
        </div>
      </header>

      <main className={styles.main}>
        <section className={styles.intro}>
          <div>
            <span className={styles.kicker}>Рабочее пространство / 01</span>
            <h1>Добрый день, <em>{user?.username}</em></h1>
          </div>
          <p>Начните с документа вакансии. Мы извлечем текст и подготовим его к следующему этапу анализа.</p>
        </section>

        <div className={styles.workspace}>
          <VacancyUploader />
          <aside className={styles.sidebar}>
            <section className={styles.progress}>
              <p>Маршрут разбора</p>
              <ol>
                <li className={styles.active}><span>01</span><div><strong>Вакансия</strong><small>Загрузка и извлечение текста</small></div></li>
                <li><span>02</span><div><strong>Резюме</strong><small>Следующий этап проекта</small></div></li>
                <li><span>03</span><div><strong>Сопоставление</strong><small>Следующий этап проекта</small></div></li>
              </ol>
            </section>
            <PasswordPanel />
          </aside>
        </div>
      </main>
      <footer className={styles.footer}><span>ResumeReview</span><span>Закрытое рабочее пространство · 2026</span></footer>
    </div>
  );
}
