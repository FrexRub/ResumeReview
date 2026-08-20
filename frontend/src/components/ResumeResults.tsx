import { useCallback, useEffect, useState } from "react";

import { ApiError, downloadResume, getActiveVacancyResumes } from "../api/client";
import type { VacancyResume } from "../types";
import styles from "./ResumeResults.module.css";

function displayValue(value: string | number | null): string {
  if (value === null || value === "") return "—";
  return String(value);
}

interface ResumeFieldProps {
  label: string;
  value: string | number | null;
  accent?: boolean;
}

function ResumeField({ label, value, accent = false }: ResumeFieldProps) {
  return (
    <div className={`${styles.field} ${accent ? styles.accentField : ""}`}>
      <dt>{label}</dt>
      <dd>{displayValue(value)}</dd>
    </div>
  );
}

export function ResumeResults() {
  const [resumes, setResumes] = useState<VacancyResume[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState("");

  const loadResumes = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await getActiveVacancyResumes();
      setResumes(result);
      setCurrentIndex(0);
    } catch (reason) {
      setResumes([]);
      setError(
        reason instanceof ApiError
          ? reason.message
          : "Не удалось загрузить резюме",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadResumes();
  }, [loadResumes]);

  const currentResume = resumes[currentIndex];
  const canNavigate = resumes.length > 1;

  useEffect(() => {
    setDownloadError("");
  }, [currentResume?.id]);

  async function handleResumeDownload() {
    if (!currentResume) return;
    setDownloading(true);
    setDownloadError("");
    try {
      await downloadResume(currentResume.id);
    } catch (reason) {
      setDownloadError(
        reason instanceof ApiError
          ? reason.message
          : "Не удалось получить резюме",
      );
    } finally {
      setDownloading(false);
    }
  }

  function showPrevious() {
    setCurrentIndex((index) => (index - 1 + resumes.length) % resumes.length);
  }

  function showNext() {
    setCurrentIndex((index) => (index + 1) % resumes.length);
  }

  return (
    <section className={styles.card} aria-labelledby="resume-results-title">
      <div className={styles.header}>
        <div>
          <p>Выборка кандидатов</p>
          <h2 id="resume-results-title">Резюме</h2>
        </div>
        {!loading && !error && resumes.length > 0 && (
          <div className={styles.navigation} aria-label="Переключение резюме">
            <button type="button" onClick={showPrevious} disabled={!canNavigate} aria-label="Предыдущее резюме">←</button>
            <span aria-live="polite">
              {String(currentIndex + 1).padStart(2, "0")} / {String(resumes.length).padStart(2, "0")}
            </span>
            <button type="button" onClick={showNext} disabled={!canNavigate} aria-label="Следующее резюме">→</button>
          </div>
        )}
      </div>

      {loading && <p className={styles.state} role="status">Загружаем данные кандидатов…</p>}

      {!loading && error && (
        <div className={styles.state} role="alert">
          <p>{error}</p>
          <button type="button" onClick={() => void loadResumes()}>Повторить</button>
        </div>
      )}

      {!loading && !error && resumes.length === 0 && (
        <p className={styles.state}>Для активной вакансии пока нет непросмотренных резюме.</p>
      )}

      {!loading && !error && currentResume && (
        <dl className={styles.fields} key={currentResume.id}>
          <ResumeField label="Вакансия" value={currentResume.title_vacancy} />
          <ResumeField label="Желаемая позиция" value={currentResume.desired_position} />
          <ResumeField label="Рейтинг кандидата" value={currentResume.candidate_rating} accent />
          <ResumeField label="Уровень соответствия" value={currentResume.score_label} />
          <ResumeField label="Резюме кандидата" value={currentResume.summary_resume} />
          <ResumeField label="Рекомендация" value={currentResume.recommendation} />
          <ResumeField label="Основание рекомендации" value={currentResume.recommendation_reason} />
          <ResumeField label="Резюме для руководителя" value={currentResume.executive_summary} />
          <ResumeField label="Краткий вывод" value={currentResume.short_conclusion} />
        </dl>
      )}

      {!loading && !error && currentResume && (
        <div className={styles.downloadArea}>
          <button
            className={styles.downloadButton}
            type="button"
            onClick={() => void handleResumeDownload()}
            disabled={!currentResume.url_resume || downloading}
          >
            {downloading ? "Получаем резюме…" : "Получение резюме"}
          </button>
          {downloadError && (
            <p className={styles.downloadError} role="alert">
              {downloadError}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
