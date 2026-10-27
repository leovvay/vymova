import { useCallback, useEffect, useState } from "react";
import { useApp } from "./AppContext";
import { href } from "./router";
import { api, ApiError } from "../shared/api";
import type { Lesson, SpeakerLabels } from "../shared/api";
import { useDocumentTitle, usePolling } from "../shared/hooks";
import { Icon, PageHead } from "../shared/ui";
import { ProgressView } from "../features/progress";
import { ResultView } from "../features/results";
import { SpeakersForm } from "../features/speakers";

const TITLES: Record<Lesson["status"], string> = {
  queued: "Обработка",
  running: "Обработка",
  awaiting_speakers: "Кто есть кто",
  failed: "Обработка остановилась",
  done: "Разбор готов",
};

/** Polls one lesson every 2 s and shows the screen its status calls for. */
export function LessonPage({ id }: { id: string }) {
  const { info, refreshInfo, setOffline } = useApp();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [missing, setMissing] = useState(false);
  /** speakers.json while the lesson still reads awaiting_speakers: undefined = not checked yet. */
  const [marked, setMarked] = useState<SpeakerLabels | null | undefined>(undefined);
  const [editing, setEditing] = useState(false);

  useDocumentTitle(missing ? "Урок не найден" : lesson ? TITLES[lesson.status] : "Урок");

  const load = useCallback(async () => {
    try {
      setLesson(await api.lesson(id));
      setOffline(false);
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) setMissing(true);
      else if (e instanceof ApiError && e.status === 0) setOffline(true);
    }
  }, [id, setOffline]);

  useEffect(() => {
    load();
  }, [load]);

  usePolling(load, 2000, !missing && lesson?.status !== "done");

  const awaiting = lesson?.status === "awaiting_speakers";
  useEffect(() => {
    if (!awaiting || marked !== undefined) return;
    api.speakers(id).then(
      (f) => setMarked(f ? f.labels : null),
      () => setMarked(null),
    );
  }, [awaiting, marked, id]);

  const back = (
    <a className="back" href={href.home}>
      <Icon name="back" size={16} />
      Все уроки
    </a>
  );

  if (missing) {
    return (
      <>
        {back}
        <PageHead title="Урок не найден" lead="Возможно, его папку удалили или переименовали на диске." />
      </>
    );
  }

  if (!lesson || (awaiting && marked === undefined)) {
    return (
      <>
        {back}
        <p className="loading-line">Загружаем урок…</p>
      </>
    );
  }

  let screen;
  if (lesson.status === "done") {
    screen = <ResultView lesson={lesson} hostDataDir={info?.host_data_dir ?? ""} />;
  } else if (awaiting && (!marked || editing)) {
    screen = (
      <SpeakersForm
        lesson={lesson}
        knownNames={info?.known_names ?? []}
        initial={marked}
        onCancel={marked ? () => setEditing(false) : undefined}
        onSubmitted={(updated, labels) => {
          setMarked(labels);
          setEditing(false);
          setLesson(updated);
          refreshInfo();
          window.scrollTo(0, 0);
        }}
      />
    );
  } else {
    screen = (
      <ProgressView
        lesson={lesson}
        onLesson={setLesson}
        settingsHref={href.settings}
        speakersMarked={awaiting && Boolean(marked)}
        onEditSpeakers={awaiting && marked ? () => setEditing(true) : undefined}
      />
    );
  }

  return (
    <>
      {back}
      {screen}
    </>
  );
}
