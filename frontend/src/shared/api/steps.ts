import type { StepName } from "./types";

export const STEPS: readonly StepName[] = [
  "ingest",
  "transcribe",
  "voices",
  "await_speakers",
  "clips",
  "pass1",
  "blind",
  "acoustic",
  "adjudicate",
  "language",
  "summary",
  "report",
];

/** Mirrors STEP_TITLES_RU in backend/vymova/lessons/model.py. */
export const STEP_TITLES: Record<StepName, string> = {
  ingest: "Подготовка записи",
  transcribe: "Расшифровка и голоса",
  voices: "Поиск голосов",
  await_speakers: "Кто есть кто",
  clips: "Нарезка реплик",
  pass1: "Первичный разбор",
  blind: "Слепая проверка реплик",
  acoustic: "Акустическая проверка",
  adjudicate: "Сверка находок",
  language: "Грамматика и лексика",
  summary: "Сводка по группе",
  report: "PDF",
};
