import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { api, ApiError, STEPS } from "../../shared/api";
import type { Lesson, StepName } from "../../shared/api";
import { durationSeconds, lessonLine, plural, secondsSince } from "../../shared/format";
import { Icon, Notice, PageHead } from "../../shared/ui";
import { StepRow } from "./StepRow";
import "./progress.css";

interface ProgressViewProps {
  lesson: Lesson;
  onLesson: (lesson: Lesson) => void;
  settingsHref: string;
  /** Voices are already marked but the lesson still waits for the worker. */
  speakersMarked?: boolean;
  onEditSpeakers?: () => void;
}

/** Steps that measure the tutor, not the machine, stay off the time scale. */
const UNTIMED: ReadonlySet<StepName> = new Set(["await_speakers"]);

function looksLikeKeyProblem(text: string): boolean {
  return /ключ|настройк/i.test(text);
}

export function ProgressView({ lesson, onLesson, settingsHref, speakersMarked, onEditSpeakers }: ProgressViewProps) {
  const [retrying, setRetrying] = useState(false);
  const [retryError, setRetryError] = useState<string | null>(null);
  const runningStep = STEPS.find((n) => lesson.steps[n].status === "running");

  /* The running step's slab grows by the second between polls. */
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!runningStep) return;
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, [runningStep]);

  const durations = new Map<StepName, number | null>();
  for (const name of STEPS) {
    const st = lesson.steps[name];
    let secs: number | null = null;
    if (!UNTIMED.has(name)) {
      secs = st.status === "running" ? secondsSince(st.started_at, now) : durationSeconds(st.started_at, st.finished_at);
    }
    durations.set(name, secs);
  }
  const longest = Math.max(1, ...[...durations.values()].map((d) => d ?? 0));

  const finished = STEPS.filter((n) => ["done", "skipped"].includes(lesson.steps[n].status)).length;
  const failedStep = STEPS.find((n) => lesson.steps[n].status === "failed");
  const waitingInQueue = !failedStep && !runningStep && (lesson.status === "queued" || speakersMarked);

  async function retry() {
    setRetrying(true);
    setRetryError(null);
    try {
      onLesson(await api.retry(lesson.id));
    } catch (e) {
      setRetryError(e instanceof ApiError ? e.message : "Не получилось перезапустить. Попробуйте ещё раз.");
    } finally {
      setRetrying(false);
    }
  }

  let footnote: ReactNode = null;
  if (failedStep) {
    footnote = null;
  } else if (waitingInQueue) {
    footnote = (
      <Notice title="Урок в очереди">
        Программа разбирает уроки по одному. Этот начнётся сам, как только освободится место.
      </Notice>
    );
  } else {
    footnote = (
      <Notice title="Вкладку можно закрыть">
        Разбор идёт на этом компьютере и продолжится без браузера. Обычно он занимает 15–20 минут. Компьютер
        не выключайте.
      </Notice>
    );
  }

  return (
    <>
      <PageHead
        title={failedStep ? "Обработка остановилась" : "Обработка"}
        lead={
          <>
            {lessonLine(lesson)}
            <span className="progress__count num">
              {" "}
              · готово {finished} {plural(finished, ["шаг", "шага", "шагов"])} из {STEPS.length}
            </span>
          </>
        }
      />

      <ol className="steps" aria-label="Шаги обработки">
        {STEPS.map((name) => {
          const st = lesson.steps[name];
          const seconds = durations.get(name) ?? null;
          const marked = name === "await_speakers" && speakersMarked && st.status === "pending";
          const shown = marked ? { ...st, status: "done" as const } : st;
          const note =
            name === "await_speakers" && (st.status === "done" || marked) ? "отмечено" : undefined;
          return (
            <StepRow
              key={name}
              name={name}
              state={shown}
              seconds={seconds}
              share={seconds != null ? seconds / longest : 0}
              note={note}
            >
              {st.status === "failed" && (
                <div className="step-error" role="alert">
                  <p className="step-error__text">{st.error_ru || "Шаг не удался."}</p>
                  {retryError && <p className="step-error__retry">{retryError}</p>}
                  <div className="step-error__actions">
                    <button type="button" className="btn btn--primary" onClick={retry} disabled={retrying}>
                      {retrying ? <span className="btn__spinner" aria-hidden="true" /> : <Icon name="retry" />}
                      {retrying ? "Перезапускаем…" : "Повторить"}
                    </button>
                    {looksLikeKeyProblem(st.error_ru ?? "") && (
                      <a className="btn" href={settingsHref}>
                        Открыть настройки
                      </a>
                    )}
                  </div>
                  <p className="step-error__hint">Готовые шаги не повторяются: разбор продолжится с этого места.</p>
                </div>
              )}
            </StepRow>
          );
        })}
      </ol>

      {speakersMarked && onEditSpeakers && (
        <p className="progress__edit">
          Голоса отмечены.{" "}
          <button type="button" className="link-button" onClick={onEditSpeakers}>
            Изменить разметку
          </button>
        </p>
      )}

      {footnote && <div className="progress__foot">{footnote}</div>}
    </>
  );
}
