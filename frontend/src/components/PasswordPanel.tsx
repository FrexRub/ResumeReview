import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { LockIcon } from "./Icons";
import styles from "./PasswordPanel.module.css";

const PASSWORD_PATTERN = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!"#$%&'()*+,\-./:;<=>?@[\]^_`{|}~]).{8,128}$/;

export function PasswordPanel() {
  const { changePassword } = useAuth();
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!currentPassword || !newPassword || !confirmation) {
      setError("Заполните все поля");
      return;
    }
    if (!PASSWORD_PATTERN.test(newPassword)) {
      setError("Нужно минимум 8 символов, заглавная и строчная буквы, цифра и спецсимвол");
      return;
    }
    if (newPassword !== confirmation) {
      setError("Новые пароли не совпадают");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await changePassword(currentPassword, newPassword);
      navigate("/?passwordChanged=true", { replace: true });
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Не удалось изменить пароль");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.wrapper}>
      <button
        className={styles.trigger}
        type="button"
        aria-expanded={expanded}
        aria-controls="password-panel"
        onClick={() => setExpanded((value) => !value)}
      >
        <LockIcon size={14} />
        <span>Сменить пароль</span>
      </button>

      {expanded && (
        <section id="password-panel" className={styles.card} aria-labelledby="security-title">
          <div className={styles.heading}>
            <div className={styles.icon}><LockIcon /></div>
            <div><p>Безопасность</p><h2 id="security-title">Смена пароля</h2></div>
          </div>
          <p className={styles.copy}>После сохранения потребуется войти с новым паролем.</p>
          <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <label>Текущий пароль<input type="password" autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} disabled={submitting} /></label>
          <label>Новый пароль<input type="password" autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} disabled={submitting} /></label>
          <label>Повторите пароль<input type="password" autoComplete="new-password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} disabled={submitting} /></label>
          <p className={styles.hint}>8+ символов · A–Z · a–z · цифра · спецсимвол</p>
          <div className={styles.error} role="alert" aria-live="polite">{error}</div>
          <div className={styles.actions}>
            <button type="button" onClick={() => { setExpanded(false); setError(""); }} disabled={submitting}>Отмена</button>
            <button type="submit" disabled={submitting}>{submitting ? "Сохраняем…" : "Сохранить"}</button>
          </div>
        </form>
        </section>
      )}
    </div>
  );
}
