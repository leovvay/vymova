export type StepName =
  | "ingest"
  | "transcribe"
  | "voices"
  | "await_speakers"
  | "clips"
  | "pass1"
  | "blind"
  | "acoustic"
  | "adjudicate"
  | "language"
  | "summary"
  | "report";

export type StepStatus = "pending" | "running" | "done" | "failed" | "skipped";

export type LessonStatus = "queued" | "running" | "awaiting_speakers" | "failed" | "done";

export interface StepState {
  status: StepStatus;
  error_ru: string | null;
  /** Naive server-local ISO time (no timezone). */
  started_at: string | null;
  finished_at: string | null;
}

export interface Lesson {
  id: string;
  date: string;
  topic: string;
  people: number | null;
  source: string;
  created_at: string;
  steps: Record<StepName, StepState>;
  students: string[];
  status: LessonStatus;
}

export interface Sample {
  start: number;
  end: number;
  text: string;
  /** Path relative to the lesson folder, e.g. "voices/speaker_0_1.mp3". */
  file: string;
}

export type SuggestedRole = "teacher" | "student";

export interface Voice {
  speaker_id: string;
  minutes: number;
  words: number;
  samples: Sample[];
  suggested_name: string | null;
  suggested_role: SuggestedRole | null;
}

export type Role = "teacher" | "student" | "skip";

export interface SpeakerLabel {
  role: Role;
  name: string | null;
}

export type SpeakerLabels = Record<string, SpeakerLabel>;

/** speakers.json, written by PUT /speakers. */
export interface SpeakersFile {
  labels: SpeakerLabels;
  students: Record<string, string[]>;
  teacher: string[];
}

export interface Settings {
  /** Masked like "••••a68e", or "" when not set. */
  elevenlabs_key: string;
  gemini_key: string;
  blind_models: string[] | null;
  acoustic_enabled: boolean;
}

/** null or a masked value = leave unchanged. */
export interface SettingsUpdate {
  elevenlabs_key?: string | null;
  gemini_key?: string | null;
  blind_models?: string[] | null;
  acoustic_enabled?: boolean | null;
}

export interface SettingsSaveResult {
  ok: boolean;
  errors: { elevenlabs?: string; gemini?: string };
  settings: Settings;
}

export interface Info {
  host_data_dir: string;
  known_names: string[];
}

export interface Summary {
  common?: { title_ru: string; students: string[] }[];
  per_student_top3?: Record<string, string[]>;
}

export interface NewLesson {
  file: File;
  date?: string;
  topic?: string;
  people?: number | null;
}
