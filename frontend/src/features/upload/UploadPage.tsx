import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useApp } from "../../app/AppContext";
import { href, navigate } from "../../app/router";
import { api, ApiError } from "../../shared/api";
import type { Lesson } from "../../shared/api";
import { todayIso } from "../../shared/format";
import { useDocumentTitle, usePolling } from "../../shared/hooks";
import { Notice, PageHead, Slab } from "../../shared/ui";
import { DropZone, isAccepted } from "./DropZone";
import { LessonList } from "./LessonList";
import "./upload.css";

const PEOPLE = [2, 3, 4, 5, 6, 7, 8];

export function UploadPage() {
  useDocumentTitle("Новый урок");
  const { keysReady, setOffline } = useApp();
  const [file, setFile] = useState<File | null>(null);
  const [date, setDate] = useState(todayIso);
  const [topic, setTopic] = useState("");
  const [people, setPeople] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [lessons, setLessons] = useState<Lesson[] | null>(null);
  const abort = useRef<AbortController | null>(null);

  const loadLessons = useCallback(async () => {
    try {
      setLessons(await api.lessons());
      setOffline(false);
    } catch (e) {
      if (e instanceof ApiError && e.status === 0) setOffline(true);
    }
  }, [setOffline]);

  useEffect(() => {
    loadLessons();
    return () => abort.current?.abort();
  }, [loadLessons]);

  const busy = Boolean(lessons?.some((l) => l.status === "running" || l.status === "queued"));
  usePolling(loadLessons, 4000, busy);

  const uploading = progress !== null;

  function pick(f: File) {
    if (!isAccepted(f)) {
      setError("Этот файл не подойдёт. Нужна запись в формате mp4, m4a, mp3, wav или webm.");
      return;
    }
    setError(null);
    setFile(f);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!file) {
      setError("Сначала выберите запись урока.");
      return;
    }
    setError(null);
    setProgress(0);
    abort.current = new AbortController();
    try {
      const lesson = await api.createLesson(
        { file, date, topic, people: people ? Number(people) : null },
        setProgress,
        abort.current.signal,
      );
      navigate(href.lesson(lesson.id));
    } catch (err) {
      if (!(err instanceof ApiError && err.status === -1)) {
        setError(err instanceof ApiError ? err.message : "Не получилось загрузить запись.");
      }
      setProgress(null);
    }
  }

  const share = progress ?? 0;
  const percent = Math.round(share * 100);

  return (
    <>
      <PageHead
        title="Новый урок"
        lead="Загрузите запись урока. Через пару минут программа попросит отметить, кто есть кто, и дальше всё сделает сама."
      />

      {keysReady === false && (
        <div className="upload__nudge">
          <Notice
            tone="attention"
            title="Сначала добавьте ключи"
            action={
              <a className="btn btn--small" href={href.settings}>
                Открыть настройки
              </a>
            }
          >
            Без ключей ElevenLabs и Gemini разбор не начнётся. Это делается один раз.
          </Notice>
        </div>
      )}

      <form className="upload" onSubmit={submit} noValidate>
        <DropZone
          file={file}
          disabled={uploading}
          invalid={Boolean(error) && !file}
          describedBy={error ? "upload-error" : undefined}
          onFile={pick}
        />

        <div className="upload__fields">
          <div className="field">
            <label className="field__label" htmlFor="lesson-date">
              Дата урока
            </label>
            <input
              id="lesson-date"
              className="input num"
              type="date"
              value={date}
              disabled={uploading}
              max={todayIso()}
              onChange={(e) => setDate(e.target.value || todayIso())}
            />
          </div>
          <div className="field upload__topic">
            <label className="field__label" htmlFor="lesson-topic">
              Тема <small>— необязательно</small>
            </label>
            <input
              id="lesson-topic"
              className="input"
              placeholder="например, Числительные"
              value={topic}
              maxLength={120}
              disabled={uploading}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>
          <div className="field">
            <label className="field__label" htmlFor="lesson-people">
              Сколько человек на записи
            </label>
            <select
              id="lesson-people"
              className="select"
              value={people}
              disabled={uploading}
              aria-describedby="people-hint"
              onChange={(e) => setPeople(e.target.value)}
            >
              <option value="">Не знаю</option>
              {PEOPLE.map((n) => (
                <option key={n} value={n}>
                  {n}, вместе с вами
                </option>
              ))}
            </select>
            <p className="field__hint" id="people-hint">
              Помогает точнее разделить голоса.
            </p>
          </div>
        </div>

        {error && (
          <p className="field__error upload__error" id="upload-error" role="alert">
            {error}
          </p>
        )}

        <div className="upload__actions">
          {uploading ? (
            <div className="upload__progress" role="status">
              <div className="upload__progress-line">
                <span>{share >= 1 ? "Сохраняем запись…" : "Загружаем запись…"}</span>
                <span className="num">{percent}%</span>
              </div>
              <Slab tone="ochre" share={share} label={`Загружено ${percent}%`} />
              <button type="button" className="btn btn--quiet btn--small" onClick={() => abort.current?.abort()}>
                Отменить
              </button>
            </div>
          ) : (
            <>
              <button type="submit" className="btn btn--primary" disabled={keysReady === false}>
                Начать
              </button>
              {keysReady === false && <span className="upload__why">Сначала ключи в настройках</span>}
            </>
          )}
        </div>
      </form>

      <LessonList lessons={lessons} />
    </>
  );
}
