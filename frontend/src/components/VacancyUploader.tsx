import { useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";

import { ApiError, parseVacancy, saveVacancy } from "../api/client";
import type { ParsedVacancy } from "../types";
import { DocumentIcon, UploadIcon } from "./Icons";
import styles from "./VacancyUploader.module.css";

const MAX_FILE_SIZE = 20 * 1024 * 1024;
const ACCEPTED_EXTENSIONS = ["pdf", "docx", "doc", "rtf", "xls", "txt", "csv", "html", "htm", "json", "xml"];

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.ceil(bytes / 1024)} КБ`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`;
}

function validateFile(file: File): string | null {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (!ACCEPTED_EXTENSIONS.includes(extension)) return "Этот формат пока не поддерживается";
  if (file.size > MAX_FILE_SIZE) return "Файл превышает допустимый размер 20 МБ";
  if (file.size === 0) return "Файл пуст";
  return null;
}

interface VacancyUploaderProps {
  onSaved?: () => void;
}

export function VacancyUploader({ onSaved }: VacancyUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ParsedVacancy | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState("");

  function chooseFile(nextFile?: File) {
    if (!nextFile) return;
    const validationError = validateFile(nextFile);
    setError(validationError ?? "");
    setFile(validationError ? null : nextFile);
    setResult(null);
    setSaved(false);
    setSaveError("");
  }

  function handleInput(event: ChangeEvent<HTMLInputElement>) {
    chooseFile(event.target.files?.[0]);
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    chooseFile(event.dataTransfer.files[0]);
  }

  async function handleParse() {
    if (!file) return;
    setLoading(true);
    setError("");
    setSaved(false);
    setSaveError("");
    try {
      setResult(await parseVacancy(file));
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Не удалось обработать файл");
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!result?.text.trim() || !file || saving || saved) return;
    setSaving(true);
    setSaveError("");
    try {
      await saveVacancy(result.text, result.filename ?? file.name);
      setSaved(true);
      onSaved?.();
    } catch (reason) {
      setSaveError(
        reason instanceof ApiError
          ? reason.message
          : "Не удалось добавить вакансию в подбор кандидатов",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className={styles.card} aria-labelledby="vacancy-title">
      <div className={styles.cardHeading}>
        <span className={styles.index}>01</span>
        <div>
          <p className={styles.eyebrow}>Исходные данные</p>
          <h2 id="vacancy-title">Документ вакансии</h2>
        </div>
        <DocumentIcon size={30} />
      </div>

      <div
        className={`${styles.dropzone} ${dragging ? styles.dragging : ""}`}
        onDragEnter={(event) => { event.preventDefault(); setDragging(true); }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <UploadIcon />
        <p><strong>Перетащите файл сюда</strong><br />или выберите его на компьютере</p>
        <button type="button" className={styles.fileButton} onClick={() => inputRef.current?.click()}>
          Выбрать файл
        </button>
        <input
          ref={inputRef}
          className={styles.hiddenInput}
          type="file"
          accept={ACCEPTED_EXTENSIONS.map((item) => `.${item}`).join(",")}
          onChange={handleInput}
          aria-label="Выбрать файл вакансии"
        />
        <span className={styles.formats}>PDF, DOCX, DOC, RTF, XLS, TXT, CSV, HTML, JSON, XML · до 20 МБ</span>
      </div>

      {file && (
        <div className={styles.selected}>
          <DocumentIcon />
          <div><strong>{file.name}</strong><span>{formatBytes(file.size)}</span></div>
          <button type="button" onClick={() => { setFile(null); setResult(null); }}>Убрать</button>
        </div>
      )}

      <div className={styles.message} role="alert" aria-live="polite">{error}</div>

      <button className={styles.parseButton} type="button" onClick={handleParse} disabled={!file || loading}>
        {loading ? "Извлекаем текст…" : "Разобрать документ"}
      </button>

      {result && (
        <div className={styles.result} aria-live="polite">
          <div className={styles.resultTop}>
            <div><span>Файл</span><strong>{result.filename ?? file?.name}</strong></div>
            <div><span>Формат</span><strong>{result.source_type.toUpperCase()}</strong></div>
            <div><span>Символов</span><strong>{result.characters.toLocaleString("ru-RU")}</strong></div>
          </div>
          {result.warnings.length > 0 && (
            <div className={styles.warnings}><strong>Предупреждения:</strong> {result.warnings.join(" · ")}</div>
          )}
          <div className={styles.textHeading}><span>Извлеченный текст</span><span>Готово</span></div>
          <pre className={styles.textPreview}>{result.text}</pre>
          <div className={styles.saveArea}>
            <button
              className={styles.saveButton}
              type="button"
              onClick={handleSave}
              disabled={!result.text.trim() || saving || saved}
            >
              {saving
                ? "Добавляем в подбор…"
                : saved
                  ? "Добавлено в подбор кандидатов"
                  : "Добавить в подбор кандидатов"}
            </button>
            <div
              className={saveError ? styles.saveError : styles.saveStatus}
              role={saveError ? "alert" : "status"}
              aria-live="polite"
            >
              {saveError || (saved ? "Текст вакансии сохранён и готов к подбору кандидатов." : "")}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
