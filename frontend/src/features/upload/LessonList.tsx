import type { Lesson, LessonStatus } from "../../shared/api";
import { formatDateNumeric } from "../../shared/format";
import { href } from "../../app/router";

const STATUS: Record<LessonStatus, string> = {
  done: "Готово",
  running: "Идёт разбор",
  queued: "В очереди",
  awaiting_speakers: "Отметьте голоса",
  failed: "Ошибка",
};

export function LessonList({ lessons }: { lessons: Lesson[] | null }) {
  return (
    <section className="past" aria-labelledby="past-title">
      <h2 className="section-title" id="past-title">
        Прошлые уроки
      </h2>

      {lessons === null && <p className="past__empty">Загружаем…</p>}
      {lessons?.length === 0 && (
        <p className="past__empty">Пока пусто. Здесь появятся загруженные уроки — их можно открыть в любой момент.</p>
      )}

      {lessons && lessons.length > 0 && (
        <ul className="past__list">
          {lessons.map((l) => (
            <li key={l.id}>
              <a className={`past__row past__row--${l.status}`} href={href.lesson(l.id)}>
                <span className="past__date num">{formatDateNumeric(l.date)}</span>
                <span className="past__topic">{l.topic || "Без темы"}</span>
                <span className="past__students">{l.students.length ? l.students.join(", ") : "—"}</span>
                <span className="past__status">
                  <span className="past__dot" aria-hidden="true" />
                  {STATUS[l.status]}
                </span>
              </a>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
