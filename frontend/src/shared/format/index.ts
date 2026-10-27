const MONTHS = [
  "января", "февраля", "марта", "апреля", "мая", "июня",
  "июля", "августа", "сентября", "октября", "ноября", "декабря",
];

/** "2026-10-26" → "26 октября 2026" (year omitted for the current year when short). */
export function formatDate(iso: string, opts: { short?: boolean } = {}): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return iso;
  const [, y, mo, d] = m;
  const base = `${Number(d)} ${MONTHS[Number(mo) - 1]}`;
  if (opts.short && Number(y) === new Date().getFullYear()) return base;
  return `${base} ${y}`;
}

/** "2026-10-26" → "26.10.2026". */
export function formatDateNumeric(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return m ? `${m[3]}.${m[2]}.${m[1]}` : iso;
}

export function todayIso(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

const decimal = new Intl.NumberFormat("ru-RU", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export function formatMinutes(min: number): string {
  return decimal.format(min);
}

/** Seconds → "0:42", "12:05", "1:02:10". */
export function formatClock(totalSeconds: number): string {
  const s = Math.max(0, Math.round(totalSeconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = String(s % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${sec}` : `${m}:${sec}`;
}

/** Russian plural: plural(3, ["голос", "голоса", "голосов"]) → "голоса". */
export function plural(n: number, forms: [string, string, string]): string {
  const a = Math.abs(n) % 100;
  const b = a % 10;
  if (a > 10 && a < 20) return forms[2];
  if (b > 1 && b < 5) return forms[1];
  if (b === 1) return forms[0];
  return forms[2];
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} КБ`;
  const mb = bytes / (1024 * 1024);
  if (mb < 1024) return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: mb < 10 ? 1 : 0 }).format(mb)} МБ`;
  return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 }).format(mb / 1024)} ГБ`;
}

/** Naive server timestamps share one clock, so their difference is safe; seconds or null. */
export function durationSeconds(start: string | null, end: string | null): number | null {
  if (!start || !end) return null;
  const a = Date.parse(start);
  const b = Date.parse(end);
  if (Number.isNaN(a) || Number.isNaN(b)) return null;
  return Math.max(0, (b - a) / 1000);
}

export function capitalize(s: string): string {
  return s ? s[0].toLocaleUpperCase("ru-RU") + s.slice(1) : s;
}

/** Identity line of a lesson: "26 октября 2026 · числительные". */
export function lessonLine(lesson: { date: string; topic: string }): string {
  const date = formatDate(lesson.date);
  return lesson.topic ? `${date} · ${lesson.topic}` : date;
}

/**
 * Seconds since a naive server timestamp. The backend writes local server time without a zone:
 * UTC inside Docker, the machine's own zone when run directly. Read it both ways and keep the
 * smallest non-negative reading — the wrong reading is either negative or off by whole hours.
 */
export function secondsSince(naive: string | null, now: number = Date.now()): number | null {
  if (!naive) return null;
  const base = naive.replace(/([+-]\d{2}:\d{2}|Z)$/, "");
  const asLocal = Date.parse(base);
  const asUtc = Date.parse(`${base}Z`);
  const readings = [asLocal, asUtc]
    .filter((t) => !Number.isNaN(t))
    .map((t) => (now - t) / 1000)
    .filter((s) => s >= -60);
  if (!readings.length) return null;
  return Math.max(0, Math.min(...readings));
}
