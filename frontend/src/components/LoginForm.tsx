import { useState } from "react";
import type { FormEvent } from "react";

import { ApiError } from "../api/client";
import { ArrowIcon } from "./Icons";
import styles from "./LoginForm.module.css";

interface LoginFormProps {
  onSubmit: (username: string, password: string) => Promise<void>;
}

export function LoginForm({ onSubmit }: LoginFormProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!username.trim() || !password) {
      setError("Введите имя пользователя и пароль");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await onSubmit(username.trim(), password);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Не удалось войти. Попробуйте еще раз.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <div className={styles.heading}>
        <span className={styles.kicker}>Личный кабинет</span>
        <h2>Продолжить работу</h2>
        <p>Войдите в защищенное пространство разбора вакансий.</p>
      </div>

      <label className={styles.field}>
        <span>Имя пользователя</span>
        <input
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          disabled={submitting}
        />
      </label>

      <label className={styles.field}>
        <span>Пароль</span>
        <input
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          disabled={submitting}
        />
      </label>

      <div className={styles.message} role="alert" aria-live="polite">
        {error}
      </div>

      <button className={styles.submit} type="submit" disabled={submitting}>
        <span>{submitting ? "Проверяем данные…" : "Войти в кабинет"}</span>
        {!submitting && <ArrowIcon />}
      </button>
      <p className={styles.note}>Доступ выдает администратор сервиса.</p>
    </form>
  );
}
