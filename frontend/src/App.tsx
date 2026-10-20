import { useEffect, useRef, useState, type ChangeEvent, type DragEvent } from "react";

type Plan = { masks: string[]; mask_count: number };

function sortedMasks(masks: string[]): string[] {
  return [...masks].sort((a, b) => {
    const prefixOrder = a.slice(0, 3).localeCompare(b.slice(0, 3), "en");
    return prefixOrder || a.localeCompare(b, "en");
  });
}
const apiBase = "";
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
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [article, setArticle] = useState("");
  const [showAllowedMasks, setShowAllowedMasks] = useState(false);
  const [approvedMasks, setApprovedMasks] = useState<string[]>([]);
  const [rulesError, setRulesError] = useState("");
  const [checkResult, setCheckResult] = useState<boolean | null>(null);
  const [checkBusy, setCheckBusy] = useState(false);
  const [checkError, setCheckError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    void fetch(`${apiBase}/api/rules/hi-lex`, {
      signal: controller.signal,
      cache: "no-store",
    }).then(async (response) => {
      if (!response.ok) throw new Error("Не удалось загрузить разрешённые маски.");
      const data: { masks: string[]; count: number } = await response.json();
      if (!Array.isArray(data.masks) || data.count !== data.masks.length) {
        throw new Error("Некорректный список масок.");
      }
      setApprovedMasks(sortedMasks(data.masks));
    }).catch((cause: unknown) => {
      if (!controller.signal.aborted) setRulesError(cause instanceof Error ? cause.message : "Ошибка загрузки масок.");
    });
    return () => controller.abort();
  }, []);

  function chooseFile(candidate?: File) {
    if (!candidate) return;
    const issue = validateCertificate(candidate);
    setFile(issue ? null : candidate);
    setPlan(null);
    setArticle("");
    setCheckResult(null);
    setCheckError("");
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
    if (!file || busy) return;
    setBusy(true); setError(""); setPlan(null);
    const body = new FormData();
    body.append("certificate", file);
    try {
      const response = await fetch(`${apiBase}/api/generation/plan`, {
        method: "POST",
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
      setCheckResult(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ошибка соединения.");
    } finally { setBusy(false); }
  }

  async function checkArticle() {
    if (!plan || !file || !article.trim() || checkBusy) return;
    setCheckBusy(true);
    setCheckError("");
    setCheckResult(null);
    try {
      const body = new FormData();
      body.append("article", article);
      body.append("certificate", file);
      const response = await fetch(`${apiBase}/api/rules/check`, {
        method: "POST",
        cache: "no-store",
        body,
      });
      if (!response.ok) throw new Error("Не удалось проверить артикул.");
      const payload: { matches: boolean } = await response.json();
      if (typeof payload.matches !== "boolean") throw new Error("Некорректный ответ сервера.");
      setCheckResult(payload.matches);
    } catch (cause) {
      setCheckError(cause instanceof Error ? cause.message : "Ошибка соединения.");
    } finally {
      setCheckBusy(false);
    }
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
              <div className="allowed-masks-wrap"
                onMouseEnter={() => setShowAllowedMasks(true)}
                onMouseLeave={() => setShowAllowedMasks(false)}>
                <button type="button" className="rule-number rule-number-button"
                  aria-expanded={showAllowedMasks}
                  aria-controls="approved-hi-lex-masks"
                  onClick={() => setShowAllowedMasks((open) => !open)}>
                  <strong>{approvedMasks.length || "—"}</strong>
                  <span>утверждённых<br />масок<br /><small>Наведите или нажмите</small></span>
                </button>
                {showAllowedMasks && (
                  <div id="approved-hi-lex-masks" className="allowed-masks-popover">
                    <strong>Разрешённые маски HI-LEX</strong>
                    {rulesError && <p role="alert">{rulesError}</p>}
                    <div className="allowed-masks-items">{approvedMasks.map((mask) => <code key={mask}>{mask}</code>)}</div>
                  </div>
                )}
              </div>
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
            <input type="text" value={article} onChange={(e) => { setArticle(e.target.value); setCheckResult(null); setCheckError(""); }} placeholder="Например, 4VB12A9" aria-label="Артикул для проверки" />
            <button type="button" className="secondary-button" disabled={!article.trim() || checkBusy} onClick={() => void checkArticle()}>{checkBusy ? "Проверяем…" : "Проверить артикул"}</button>
            {checkResult !== null && <p role="status" className={`feedback ${checkResult ? "feedback-success" : "feedback-error"}`}>
              {checkResult ? "Соответствует маске сертификата." : "Не соответствует маскам сертификата или формату артикула."}
            </p>}
            {checkError && <p role="alert" className="feedback feedback-error">{checkError}</p>}
          </div>
        </section>}
      <footer className="footer">Соответствие маске не подтверждает существование артикула в каталоге производителя.</footer>
    </main>
  </div>;
}
