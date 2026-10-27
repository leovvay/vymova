import { useEffect, useId, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../../shared/api";
import type { Lesson, SpeakerLabels, Voice } from "../../shared/api";
import { lessonLine, plural } from "../../shared/format";
import { Notice, PageHead } from "../../shared/ui";
import { useSamplePlayer } from "./useSamplePlayer";
import { VoiceRow } from "./VoiceRow";
import type { RowProblems, RowState } from "./VoiceRow";
import "./speakers.css";

interface SpeakersFormProps {
  lesson: Lesson;
  knownNames: string[];
  /** Labels already sent once (editing before the worker picks them up). */
  initial?: SpeakerLabels | null;
  onSubmitted: (lesson: Lesson, labels: SpeakerLabels) => void;
  onCancel?: () => void;
}

function initialRows(voices: Voice[], initial?: SpeakerLabels | null): Record<string, RowState> {
  const out: Record<string, RowState> = {};
  for (const v of voices) {
    const saved = initial?.[v.speaker_id];
    if (saved) out[v.speaker_id] = { role: saved.role, name: saved.name ?? "" };
    else out[v.speaker_id] = { role: v.suggested_role, name: v.suggested_name ?? "" };
  }
  return out;
}

function validate(voices: Voice[], rows: Record<string, RowState>) {
  const problems: Record<string, RowProblems> = {};
  let anyStudent = false;
  for (const v of voices) {
    const r = rows[v.speaker_id];
    if (!r?.role) problems[v.speaker_id] = { role: "Выберите, кто это." };
    else if (r.role === "student") {
      anyStudent = true;
      if (!r.name.trim()) problems[v.speaker_id] = { name: "Впишите имя студента." };
    }
  }
  let summary: string | null = null;
  if (Object.keys(problems).length) summary = "Не все голоса отмечены — посмотрите подсказки выше.";
  else if (!anyStudent) summary = "Отметьте хотя бы одного студента — иначе разбирать нечего.";
  return { problems, summary };
}

export function SpeakersForm({ lesson, knownNames, initial, onSubmitted, onCancel }: SpeakersFormProps) {
  const [voices, setVoices] = useState<Voice[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [rows, setRows] = useState<Record<string, RowState>>({});
  const [showProblems, setShowProblems] = useState(false);
  const [sending, setSending] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const player = useSamplePlayer();
  const namesListId = useId();

  useEffect(() => {
    let alive = true;
    api.voices(lesson.id).then(
      (v) => {
        if (!alive) return;
        if (!v) setLoadError("Голоса ещё не найдены. Обновите страницу через минуту.");
        else {
          setVoices(v);
          setRows(initialRows(v, initial));
        }
      },
      (e) => alive && setLoadError(e instanceof ApiError ? e.message : "Не удалось загрузить голоса."),
    );
    return () => {
      alive = false;
    };
  }, [lesson.id, initial]);

  const scale = useMemo(() => Math.max(0.1, ...(voices ?? []).map((v) => v.minutes)), [voices]);

  const suggestions = useMemo(() => {
    const typed = Object.values(rows)
      .filter((r) => r.role === "student")
      .map((r) => r.name.trim());
    return [...new Set([...knownNames, ...typed].filter(Boolean))].sort((a, b) => a.localeCompare(b, "ru"));
  }, [rows, knownNames]);

  const { problems, summary } = useMemo(() => validate(voices ?? [], rows), [voices, rows]);

  function mergedWith(speakerId: string): number[] {
    const me = rows[speakerId];
    if (!voices || me?.role !== "student" || !me.name.trim()) return [];
    const key = me.name.trim().toLocaleLowerCase("ru-RU");
    return voices
      .map((v, i) => ({ v, n: i + 1 }))
      .filter(({ v }) => v.speaker_id !== speakerId)
      .filter(({ v }) => {
        const r = rows[v.speaker_id];
        return r?.role === "student" && r.name.trim().toLocaleLowerCase("ru-RU") === key;
      })
      .map(({ n }) => n);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setServerError(null);
    if (summary) {
      setShowProblems(true);
      return;
    }
    const labels: SpeakerLabels = {};
    for (const v of voices ?? []) {
      const r = rows[v.speaker_id];
      if (!r?.role) continue;
      labels[v.speaker_id] = { role: r.role, name: r.role === "student" ? r.name.trim() : null };
    }
    setSending(true);
    try {
      const updated = await api.labelSpeakers(lesson.id, labels);
      onSubmitted(updated, labels);
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Не получилось сохранить. Попробуйте ещё раз.");
    } finally {
      setSending(false);
    }
  }

  const count = voices?.length ?? 0;

  return (
    <>
      <PageHead title="Кто есть кто" lead={lessonLine(lesson)} />

      {loadError && <Notice tone="error" title={loadError} />}

      {voices && (
        <form className="speakers" onSubmit={submit} noValidate>
          <p className="speakers__intro">
            В записи {count} {plural(count, ["голос", "голоса", "голосов"])}. Послушайте фрагменты и отметьте, кто
            говорит. Длина полосы — сколько человек говорил; жёлтая полоса — голос ещё не отмечен.
          </p>

          <datalist id={namesListId}>
            {suggestions.map((n) => (
              <option key={n} value={n} />
            ))}
          </datalist>

          <div className="speakers__list">
            {voices.map((v, i) => (
              <VoiceRow
                key={v.speaker_id}
                lessonId={lesson.id}
                voice={v}
                index={i + 1}
                scale={scale}
                state={rows[v.speaker_id] ?? { role: null, name: "" }}
                problems={showProblems ? problems[v.speaker_id] ?? {} : {}}
                mergedWith={mergedWith(v.speaker_id)}
                namesListId={namesListId}
                player={player}
                onChange={(next) => setRows((prev) => ({ ...prev, [v.speaker_id]: next }))}
              />
            ))}
          </div>

          <p className="speakers__hint">
            Если программа разделила одного человека на два голоса, дайте им одно имя — в отчёте это будет один
            студент. Имена запоминаются: в следующий раз программа подставит их сама.
          </p>

          {showProblems && summary && <Notice tone="error" title={summary} live />}
          {serverError && <Notice tone="error" title={serverError} live />}

          <div className="speakers__actions">
            <button type="submit" className="btn btn--primary" disabled={sending}>
              {sending && <span className="btn__spinner" aria-hidden="true" />}
              {sending ? "Сохраняем…" : "Разобрать"}
            </button>
            {onCancel && (
              <button type="button" className="btn btn--quiet" onClick={onCancel} disabled={sending}>
                Отмена
              </button>
            )}
          </div>
        </form>
      )}

      {!voices && !loadError && <p className="loading-line">Загружаем голоса…</p>}
    </>
  );
}
