import { useEffect, useRef, useState, type ChangeEvent, type DragEvent, type FormEvent } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "./auth";

type Plan = { masks: string[]; mask_count: number };

function sortedMasks(masks: string[]): string[] {
  return [...masks].sort((a, b) => {
    const prefixOrder = a.slice(0, 3).localeCompare(b.slice(0, 3), "en");
    return prefixOrder || a.localeCompare(b, "en");
  });
}
const maxSize = 2 * 1024 * 1024;

function validateCertificate(file: File): string | null {
  const extension = file.name.split(".").pop()?.toLowerCase();
  if (!extension || !["pdf", "docx", "txt"].includes(extension)) return "Поддерживаются PDF, DOCX и TXT.";
  const limit = extension === "pdf" ? maxSize : 1024 * 1024;
  if (file.size === 0 || file.size > limit) return "Файл пустой или превышает допустимый размер.";
  return null;
}

export default function App() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [article, setArticle] = useState("");

  useEffect(() => {
    void supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
      if (!next) { setFile(null); setPlan(null); setArticle(""); }
    });
    return () => data.subscription.unsubscribe();
  }, []);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthBusy(true);
    setAuthError("");
    const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
    if (signInError) setAuthError("Не удалось войти. Проверьте учётные данные.");
    setAuthBusy(false);
  }

  function chooseFile(candidate?: File) {
    if (!candidate) return;
    const issue = validateCertificate(candidate);
    setFile(issue ? null : candidate);
    setPlan(null);
    setArticle("");
    setError(issue ?? "");
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

  async function recognize() {
    if (!session || !file || busy) return;
    setBusy(true); setError(""); setPlan(null);
    const body = new FormData();
    body.append("certificate", file);
    try {
      const response = await fetch("/api/generation/plan", {
        method: "POST", headers: { Authorization: `Bearer ${session.access_token}` },
        cache: "no-store", body,
      });
      if (!response.ok) {
        let message = "Не удалось распознать сертификат.";
        try {
          const payload: unknown = await response.json();
          if (typeof payload === "object" && payload !== null && "detail" in payload && typeof payload.detail === "string") {
            message = payload.detail;
          }
        } catch { /* Ответ сервера может быть не JSON. */ }
        throw new Error(message);
      }
      const result: Plan = await response.json();
      if (!Array.isArray(result.masks) || result.mask_count !== result.masks.length ||
        result.masks.some((mask) => typeof mask !== "string")) throw new Error("Некорректный ответ сервера.");
      setPlan({ ...result, masks: sortedMasks(result.masks) });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ошибка соединения.");
    } finally { setBusy(false); }
  }

  function matchesArticle(value: string): boolean {
    if (!plan) return false;
    const normalized = value.replace(/\u00a0/g, " ").trim().replace(/[a-z]/g, (x) => x.toUpperCase());
    return plan.masks.some((mask) => {
      if (!/^[A-Z0-9]{3}\*{4}$/.test(mask) || normalized.length !== 7) return false;
      return normalized.startsWith(mask.slice(0, 3)) && /^[A-Z0-9]{4}$/.test(normalized.slice(3));
    });
  }

  function downloadMasks() {
    if (!plan) return;
    const csv = ["mask", ...plan.masks].join("\r\n") + "\r\n";
    const objectUrl = URL.createObjectURL(new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = objectUrl; anchor.download = "certificate-masks.csv";
    document.body.appendChild(anchor); anchor.click(); anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  }

  const normalizedArticle = article.replace(/\u00a0/g, " ").trim();
  const articlePresent = normalizedArticle.length > 0;
  return <div className="page">
    <header className="topbar">
      <div className="brand"><span className="brand-mark">Д+</span>
        <span className="brand-name">ДиасАвто<span>+</span></span>
        <span className="brand-divider" /><span className="brand-product">Проверка сертификатов</span>
      </div><span className="environment">Тестовая версия</span>
    </header>
    <main className="main">
      <div className="eyebrow"><span className="eyebrow-dot" /> ИНСТРУМЕНТ ПРОВЕРКИ</div>
      <h1>Проверка артикулов<br />по маскам сертификата</h1>
      <p className="intro">Загрузите сертификат. Система распознает маски HI-LEX и позволит проверить, покрывается ли конкретный артикул сертификатом. Каталог товаров не требуется.</p>
      {!session ? <form className="login-panel" onSubmit={signIn}>
        <h2>Вход в систему</h2><p>Для работы необходима учётная запись.</p>
        <input aria-label="Электронная почта" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Электронная почта" />
        <input aria-label="Пароль" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Пароль" />
        <button className="primary-button" type="submit" disabled={authBusy}>{authBusy ? "Входим…" : "Войти"}</button>
        {authError && <p className="feedback feedback-error" role="alert">{authError}</p>}
      </form> : <>
        <div className="session-bar"><span>Вы вошли в систему</span><button type="button" onClick={() => void supabase.auth.signOut()}>Выйти</button></div>
        <div className="workspace">
          <section className="panel" aria-labelledby="upload-heading">
            <div className="panel-heading"><div><span className="step">01 / СЕРТИФИКАТ</span>
              <h2 id="upload-heading">Загрузка сертификата</h2></div><span className="tag">PDF, DOCX, TXT</span>
            </div>
            <div className={`dropzone${dragging ? " dragging" : ""}`}
              onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)} onDrop={onDrop}>
              <div className="file-icon"><span aria-hidden="true" className="upload-glyph">⇧</span></div>
              <strong>{file ? file.name : "Перетащите сертификат сюда"}</strong>
              <p>{file ? `${(file.size / 1024).toFixed(1)} КБ · готов к распознаванию` : "или выберите файл на компьютере"}</p>
              <button type="button" className="secondary-button" onClick={() => inputRef.current?.click()}>{file ? "Заменить файл" : "Выбрать файл"}</button>
              <input ref={inputRef} type="file" accept=".pdf,.docx,.txt" className="sr-only" aria-label="Выбрать сертификат" onChange={onInputChange} />
            </div>
            <div className="limit"><span>PDF до 2 МБ, DOCX/TXT до 1 МБ</span><span>PDF до 30 страниц</span></div>
            <button type="button" className="primary-button" disabled={!file || busy} onClick={() => void recognize()}>
              {busy ? "Распознаём…" : "Распознать маски"}<span aria-hidden="true">↗</span>
            </button>
            {error && <p className="feedback feedback-error" role="alert">{error}</p>}
          </section>
          <aside className="details">
            <section className="detail-card"><span className="step">02 / ПРАВИЛА</span><h2>HI-LEX CORPORATION</h2>
              <p>Тросы стояночного тормоза</p>
              <div className="rule-number"><strong>38</strong><span>утверждённых<br />масок</span></div>
              <div className="rule-example"><span>ПРИМЕР</span><code>4VB****</code></div>
              <p className="small-note">После фиксированного префикса — четыре символа из A–Z и 0–9. OCR для PDF-сканов не требуется по ТЗ.</p>
            </section>
          </aside>
        </div>
        {plan && <section className="results-panel" aria-label="Результаты распознавания">
          <span className="step">03 / РЕЗУЛЬТАТ</span><h2>Маски сертификата</h2>
          <div className="result-stats">
            <div><span>Найдено масок</span><strong>{plan.mask_count}</strong></div>
            <div><span>Производитель</span><strong className="result-brand">HI-LEX</strong></div>
            <div><span>Режим</span><strong className="result-brand">Правила</strong></div>
          </div>
          <p className="small-note">Это описание множества допустимых артикулов: сами комбинации не генерируются.</p>
          <p className="mask-sort-note">Маски отсортированы по первым трём символам (A–Z, 0–9).</p>
          <div className="mask-list">{plan.masks.map(mask => <code key={mask}>{mask}</code>)}</div>
          <button type="button" className="secondary-button" onClick={downloadMasks}>Скачать список масок (CSV)</button>
          <div className="article-check">
            <h2>Проверить артикул</h2>
            <p className="small-note">Введите артикул, чтобы проверить его соответствие одной из найденных масок.</p>
            <input type="text" value={article} onChange={(e) => setArticle(e.target.value)} placeholder="Например, 4VB12A9" aria-label="Артикул для проверки" />
            {articlePresent && <p role="status" className={`feedback ${matchesArticle(article) ? "feedback-success" : "feedback-error"}`}>
              {matchesArticle(article) ? "Соответствует маске сертификата." : "Не соответствует маскам сертификата или формату артикула."}
            </p>}
          </div>
        </section>}
      </>}
      <footer className="footer">Соответствие маске не подтверждает существование артикула в каталоге производителя.</footer>
    </main>
  </div>;
}
