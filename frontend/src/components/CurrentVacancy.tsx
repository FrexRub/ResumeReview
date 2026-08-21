import { useCallback, useEffect, useState } from "react";

import {
  ApiError,
  deactivateActiveVacancy,
  getActiveVacancy,
} from "../api/client";
import type { ActiveVacancy } from "../types";
import { DocumentIcon } from "./Icons";
import styles from "./CurrentVacancy.module.css";

interface CurrentVacancyProps {
  refreshKey?: number;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date(value));
}

export function CurrentVacancy({ refreshKey = 0 }: CurrentVacancyProps) {
  const [vacancy, setVacancy] = useState<ActiveVacancy | null>(null);
  const [loading, setLoading] = useState(true);
  const [deactivating, setDeactivating] = useState(false);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  const loadVacancy = useCallback(async () => {
    setLoading(true);
    setError("");
    setActionError("");
    try {
      setVacancy(await getActiveVacancy());
    } catch (reason) {
      setVacancy(null);
      setError(
        reason instanceof ApiError
          ? reason.message
          : "Не удалось загрузить текущую вакансию",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadVacancy();
  }, [loadVacancy, refreshKey]);

  async function handleDeactivate() {
    setDeactivating(true);
    setActionError("");
    try {
      await deactivateActiveVacancy();
      setVacancy(null);
    } catch (reason) {
      setActionError(
        reason instanceof ApiError
          ? reason.message
          : "Не удалось деактивировать вакансию",
      );
    } finally {
      setDeactivating(false);
    }
  }

  return (
    <section className={styles.card} aria-labelledby="current-vacancy-title">
      <div className={styles.header}>
        <div className={styles.marker} aria-hidden="true">
          <span />
          ACTIVE
        </div>
        <div className={styles.heading}>
          <p>Активная запись</p>
          <h2 id="current-vacancy-title">Текущая вакансия</h2>
        </div>
        <DocumentIcon size={28} />
      </div>

      {loading && (
        <p className={styles.state} role="status">
          Загружаем текст текущей вакансии…
        </p>
      )}

      {!loading && error && (
        <div className={styles.state} role="alert">
          <p>{error}</p>
          <button type="button" onClick={() => void loadVacancy()}>
            Повторить
          </button>
        </div>
      )}

      {!loading && !error && !vacancy && (
        <p className={styles.state}>
          Активная вакансия пока не выбрана. Разберите документ и добавьте его в подбор кандидатов.
        </p>
      )}

      {!loading && !error && vacancy && (
        <article className={styles.content}>
          <div className={styles.meta}>
            <div>
              <span>Документ</span>
              <strong>{vacancy.filename}</strong>
            </div>
            <div>
              <span>Добавлена</span>
              <strong>{formatDate(vacancy.created_at)}</strong>
            </div>
            <button
              className={styles.status}
              type="button"
              onClick={() => void handleDeactivate()}
              disabled={deactivating}
              aria-label="Деактивировать текущую вакансию"
            >
              {deactivating ? "Отключаем…" : "Активна"}
            </button>
          </div>
          {actionError && (
            <p className={styles.actionError} role="alert">{actionError}</p>
          )}
          <div className={styles.text} aria-label="Текст текущей вакансии">
            {vacancy.content}
          </div>
        </article>
      )}
    </section>
  );
}
