import { useEffect, useState } from "react";
import { api } from "../../shared/api";
import type { Lesson, Summary } from "../../shared/api";
import { capitalize, formatDate, plural } from "../../shared/format";
import { Icon, PageHead } from "../../shared/ui";
import { FolderPath } from "./FolderPath";
import "./results.css";

interface ResultViewProps {
  lesson: Lesson;
  hostDataDir: string;
}

function folderPath(hostDataDir: string, id: string): string {
  const root = hostDataDir.replace(/[\\/]+$/, "");
  if (!root) return `lessons\\${id}`;
  const sep = root.includes("\\") || !root.includes("/") ? "\\" : "/";
  return `${root}${sep}lessons${sep}${id}`;
}

export function ResultView({ lesson, hostDataDir }: ResultViewProps) {
  const [summary, setSummary] = useState<Summary | null | undefined>(undefined);

  useEffect(() => {
    let alive = true;
    api.summary(lesson.id).then(
      (s) => alive && setSummary(s),
      () => alive && setSummary(null),
    );
    return () => {
      alive = false;
    };
  }, [lesson.id]);

  const students = lesson.students.length
    ? lesson.students
    : Object.keys(summary?.per_student_top3 ?? {});
  const n = students.length;
  const title = lesson.topic ? capitalize(lesson.topic) : `Урок ${formatDate(lesson.date, { short: true })}`;

  return (
    <>
      <PageHead title="Разбор готов" />

      <article className="result" aria-labelledby="result-title">
        <header className="result__cover">
          <h2 className="result__title" id="result-title">
            {title}
          </h2>
          <p className="result__meta">
            {lesson.topic ? `${formatDate(lesson.date)} · ` : ""}
            {n} {plural(n, ["студент", "студента", "студентов"])} · один PDF на урок
          </p>
        </header>

        <div className="result__body">
          <h3 className="result__label">Главное по каждому</h3>
          <ul className="result__students">
            {students.map((name) => {
              const line = summary?.per_student_top3?.[name]?.[0];
              return (
                <li key={name} className="result__student">
                  <span className="result__name">{name}</span>
                  <span className="result__line">
                    {line ?? (summary === undefined ? "…" : "Подробности — в PDF.")}
                  </span>
                </li>
              );
            })}
          </ul>

          <div className="result__actions">
            <a className="btn btn--primary" href={api.reportUrl(lesson.id)} target="_blank" rel="noopener">
              <Icon name="file" />
              Открыть PDF
            </a>
            <span className="result__pdf-hint">Откроется в новой вкладке</span>
          </div>

          <FolderPath path={folderPath(hostDataDir, lesson.id)} />
        </div>
      </article>
    </>
  );
}
