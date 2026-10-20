import { useEffect, useRef, useState, type ChangeEvent, type DragEvent, type FormEvent } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "./auth";

const MAX_FILE_BYTES = 2 * 1024 * 1024;
const ACCEPTED_EXTENSIONS = [".csv", ".xlsx"];

type RequestState = "idle" | "loading" | "success" | "error";

function validateFile(file: File): string | null {
  const extension = "." + (file.name.split(".").pop()?.toLowerCase() ?? "");
  if (!ACCEPTED_EXTENSIONS.includes(extension)) {
    return "Поддерживаются только каталоги CSV и XLSX.";
  }
  if (file.size === 0 || file.size > MAX_FILE_BYTES) {
    return "Размер файла должен быть больше 0 и не превышать 2 МБ.";
  }
  return null;
}

function FileIcon() {
  return (
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none" aria-hidden="true">
      <path d="M7 3.75h10l6 6V25a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5.75a2 2 0 0 1 2-2Z" stroke="currentColor" strokeWidth="1.5" />
      <path d="M17 3.75v6h6M10 16h10M10 20h7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export default function App() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);

  useEffect(() => {
    void supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data } = supabase.auth.onAuthStateChange((_event, next) => setSession(next));
    return () => data.subscription.unsubscribe();
  }, []);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthBusy(true);
    setAuthError("");
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) setAuthError("Не удалось войти. Проверьте учётные данные.");
    setAuthBusy(false);
  }
  const [file, setFile] = useState<File | null>(null);
  const [certificate, setCertificate] = useState<File | null>(null);
  const certificateInputRef = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<RequestState>("idle");
  const [message, setMessage] = useState("");
  const [dragging, setDragging] = useState(false);

  function chooseFile(candidate?: File) {
    if (!candidate) return;
    const error = validateFile(candidate);
    setFile(error ? null : candidate);
    setState(error ? "error" : "idle");
    setMessage(error ?? "");
  }

  function onInputChange(event: ChangeEvent<HTMLInputElement>) {
    chooseFile(event.target.files?.[0]);
    event.target.value = "";
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    chooseFile(event.dataTransfer.files[0]);
  }

  async function submit() {
    if (!file || state === "loading" || !session) return;
    setState("loading");
    setMessage("");
    const form = new FormData();
    form.append("file", file);
    if (certificate) form.append("certificate", certificate);
    try {
      const response = await fetch("/api/validate", {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
        body: form,
        cache: "no-store",
      });
      if (!response.ok) {
        let detail = "Не удалось обработать каталог.";
        try {
          const error: unknown = await response.json();
          if (
            typeof error === "object" &&
            error !== null &&
            "detail" in error &&
            typeof error.detail === "string"
          ) {
            detail = error.detail;
          }
        } catch {
          // Сервер может вернуть ответ не в формате JSON.
        }
        throw new Error(detail);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "validation-report.xlsx";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      setState("success");
      setMessage("Проверка завершена. Отчёт скачан на устройство.");
    } catch (error) {
      setState("error");
      setMessage(error instanceof Error ? error.message : "Ошибка соединения с сервером.");
    }
  }

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">Д+</span>
          <span className="brand-name">ДиасАвто<span>+</span></span>
          <span className="brand-divider" />
          <span className="brand-product">Проверка сертификатов</span>
        </div>
        <span className="environment">Тестовая версия</span>
      </header>

      <main className="main">
        <div className="eyebrow"><span className="eyebrow-dot" /> ИНСТРУМЕНТ ПРОВЕРКИ</div>
        <h1>Проверка артикулов<br />по маскам сертификатов</h1>
        <p className="intro">Загрузите каталог производителя. Система проверит артикулы по утверждённым маскам HI-LEX и сформирует Excel-отчёт.</p>

        {!session ? (
          <form className="login-panel" onSubmit={signIn}>
            <h2>Вход в систему</h2>
            <p>Для проверки файлов необходима учётная запись.</p>
            <input aria-label="Электронная почта" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Электронная почта" />
            <input aria-label="Пароль" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Пароль" />
            <button className="primary-button" type="submit" disabled={authBusy}>{authBusy ? "Проверка…" : "Войти"}</button>
            {authError && <p className="feedback feedback-error" role="alert">{authError}</p>}
          </form>
        ) : <><div className="session-bar"><span>Вы вошли в систему</span><button type="button" onClick={() => void supabase.auth.signOut()}>Выйти</button></div>
        <div className="workspace">
          <section className="panel" aria-labelledby="upload-heading">
            <div className="panel-heading">
              <div>
                <span className="step">01 / ЗАГРУЗКА</span>
                <h2 id="upload-heading">Каталог товаров</h2>
              </div>
              <span className="tag">CSV, XLSX</span>
            </div>
            <div className="certificate-upload">
              <strong>Сертификат с масками</strong>
              <p>Необязательно. DOCX или TXT, максимум 1 МБ. Без сертификата используются все 38 утверждённых масок.</p>
              <input ref={certificateInputRef} className="sr-only" type="file" accept=".docx,.txt" aria-label="Выбрать сертификат" onChange={(event) => {
                const selected = event.target.files?.[0];
                event.target.value = "";
                if (!selected) return;
                const ext = selected.name.split(".").pop()?.toLowerCase();
                if (!["docx", "txt"].includes(ext || "") || selected.size === 0 || selected.size > 1024 * 1024) {
                  setCertificate(null);
                  setState("error");
                  setMessage("Сертификат должен быть DOCX/TXT размером до 1 МБ.");
                  return;
                }
                setCertificate(selected);
                setState("idle");
                setMessage("");
              }} />
              <button type="button" className="secondary-button" onClick={() => certificateInputRef.current?.click()}>
                {certificate ? certificate.name : "Выбрать сертификат"}
              </button>
              {certificate && <button type="button" className="secondary-button" onClick={() => setCertificate(null)}>Убрать</button>}
            </div>
            <div
              className={`dropzone${dragging ? " dragging" : ""}`}
              onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
            >
              <div className="file-icon"><FileIcon /></div>
              <strong>{file ? file.name : "Перетащите файл сюда"}</strong>
              <p>{file ? `${(file.size / 1024).toFixed(1)} КБ · готов к проверке` : "или выберите файл на компьютере"}</p>
              <button className="secondary-button" type="button" onClick={() => inputRef.current?.click()}>
                {file ? "Заменить файл" : "Выбрать файл"}
              </button>
              <input
                ref={inputRef}
                type="file"
                accept=".csv,.xlsx"
                className="sr-only"
                aria-label="Выбрать каталог товаров"
                onChange={onInputChange}
              />
            </div>
            <div className="limit">
              <span>Максимальный размер — 2 МБ</span>
              <span>До 10 000 строк</span>
            </div>
            <button className="primary-button" type="button" onClick={submit} disabled={!file || state === "loading"}>
              {state === "loading" ? "Проверяем каталог…" : "Проверить каталог"}
              <span aria-hidden="true">↗</span>
            </button>
            {message && (
              <p className={`feedback ${state === "error" ? "feedback-error" : "feedback-success"}`} role="status">
                {message}
              </p>
            )}
          </section>

          <aside className="details">
            <section className="detail-card">
              <span className="step">02 / ПРАВИЛА ПРОВЕРКИ</span>
              <h2>HI-LEX CORPORATION</h2>
              <p>Тросы стояночного тормоза</p>
              <div className="rule-number"><strong>38</strong><span>утверждённых<br />масок</span></div>
              <div className="rule-example"><span>ПРИМЕР МАСКИ</span><code>4VB****</code></div>
              <p className="small-note">Каждая звёздочка — одна цифра 0–9 или латинская буква A–Z. Артикул содержит ровно 7 символов.</p>
            </section>
            <section className="detail-card format-card">
              <span className="step">ФОРМАТ КАТАЛОГА</span>
              <p>Первая строка файла должна содержать три столбца:</p>
              <div className="fields"><code>article</code><code>manufacturer</code><code>product_group</code></div>
              <p className="small-note">Результат: два листа Excel — подходящие позиции и исключения с причинами.</p>
            </section>
          </aside>
        </div>
        </>}
        <footer className="footer">Проверка формата не подтверждает наличие артикула в каталоге производителя.</footer>
      </main>
    </div>
  );
}
