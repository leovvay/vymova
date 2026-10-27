import { ApiError, OFFLINE_MESSAGE, detailMessage } from "./errors";
import type {
  Info,
  Lesson,
  NewLesson,
  Settings,
  SettingsSaveResult,
  SettingsUpdate,
  SpeakerLabels,
  SpeakersFile,
  Summary,
  Voice,
} from "./types";

export * from "./types";
export { STEPS, STEP_TITLES } from "./steps";
export { ApiError, OFFLINE_MESSAGE } from "./errors";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, { ...init, headers: { Accept: "application/json", ...init?.headers } });
  } catch {
    throw new ApiError(0, OFFLINE_MESSAGE);
  }
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, detailMessage(body, res.status));
  return body as T;
}

function json(method: string, data: unknown): RequestInit {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) };
}

const enc = encodeURIComponent;

/** URL of a file inside the lesson folder; each path segment is escaped. */
export function lessonFileUrl(lessonId: string, path: string): string {
  return `/api/lessons/${enc(lessonId)}/files/${path.split("/").map(enc).join("/")}`;
}

/** Returns null when the file does not exist yet. */
async function lessonFile<T>(lessonId: string, path: string): Promise<T | null> {
  try {
    return await request<T>(lessonFileUrl(lessonId, path));
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}

export const api = {
  info: () => request<Info>("/api/info"),

  settings: () => request<Settings>("/api/settings"),
  saveSettings: (upd: SettingsUpdate) => request<SettingsSaveResult>("/api/settings", json("PUT", upd)),

  lessons: () => request<Lesson[]>("/api/lessons"),
  lesson: (id: string) => request<Lesson>(`/api/lessons/${enc(id)}`),
  retry: (id: string) => request<Lesson>(`/api/lessons/${enc(id)}/retry`, { method: "POST" }),
  labelSpeakers: (id: string, labels: SpeakerLabels) =>
    request<Lesson>(`/api/lessons/${enc(id)}/speakers`, json("PUT", labels)),

  voices: (id: string) => lessonFile<Voice[]>(id, "voices.json"),
  speakers: (id: string) => lessonFile<SpeakersFile>(id, "speakers.json"),
  summary: (id: string) => lessonFile<Summary>(id, "summary.json"),
  reportUrl: (id: string) => lessonFileUrl(id, "report.pdf"),

  /** Multipart upload through XHR so the page can show real upload progress (0..1). */
  createLesson(input: NewLesson, onProgress: (share: number) => void, signal?: AbortSignal): Promise<Lesson> {
    const form = new FormData();
    form.append("file", input.file);
    if (input.date) form.append("date", input.date);
    if (input.topic?.trim()) form.append("topic", input.topic.trim());
    if (input.people) form.append("people", String(input.people));

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/api/lessons");
      xhr.responseType = "json";
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress(e.loaded / e.total);
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) resolve(xhr.response as Lesson);
        else reject(new ApiError(xhr.status, detailMessage(xhr.response, xhr.status)));
      };
      xhr.onerror = () => reject(new ApiError(0, OFFLINE_MESSAGE));
      xhr.onabort = () => reject(new ApiError(-1, "Загрузка отменена."));
      signal?.addEventListener("abort", () => xhr.abort());
      xhr.send(form);
    });
  },
};
