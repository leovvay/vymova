import type { Role, Voice } from "../../shared/api";
import { lessonFileUrl } from "../../shared/api";
import { formatMinutes } from "../../shared/format";
import { Slab } from "../../shared/ui";
import type { SlabTone } from "../../shared/ui";
import { SampleLine } from "./SampleLine";
import type { SamplePlayer } from "./useSamplePlayer";

export interface RowState {
  role: Role | null;
  name: string;
}

export interface RowProblems {
  role?: string;
  name?: string;
}

interface VoiceRowProps {
  lessonId: string;
  voice: Voice;
  index: number;
  /** Longest voice on this screen, minutes. */
  scale: number;
  state: RowState;
  problems: RowProblems;
  /** Other voices given the same student name. */
  mergedWith: number[];
  namesListId: string;
  player: SamplePlayer;
  onChange: (next: RowState) => void;
}

const ROLES: { value: Role; label: string }[] = [
  { value: "teacher", label: "Репетитор" },
  { value: "student", label: "Студент" },
  { value: "skip", label: "Пропустить" },
];

/** Ochre = still your turn; ink once marked; hatched when the voice is skipped. */
function slabTone(role: Role | null): SlabTone {
  if (!role) return "ochre";
  return role === "skip" ? "hatch" : "ink";
}

export function VoiceRow(props: VoiceRowProps) {
  const { lessonId, voice, index, scale, state, problems, mergedWith, namesListId, player, onChange } = props;
  const label = `Голос ${index}`;
  const base = `voice-${voice.speaker_id}`;
  const roleErrId = `${base}-role-err`;
  const nameErrId = `${base}-name-err`;

  return (
    <section className={`voice voice--${state.role ?? "unset"}`} aria-labelledby={`${base}-title`}>
      <div className="voice__head">
        <h2 className="voice__title" id={`${base}-title`}>
          {label}
        </h2>
        <Slab className="voice__slab" tone={slabTone(state.role)} share={voice.minutes / scale} />
        <p className="voice__minutes">
          <span className="voice__figure num">{formatMinutes(voice.minutes)}</span> мин речи
        </p>
      </div>

      <ul className="voice__samples">
        {voice.samples.map((s, i) => (
          <SampleLine
            key={s.file}
            sample={s}
            sampleKey={s.file}
            url={lessonFileUrl(lessonId, s.file)}
            voiceLabel={label}
            index={i + 1}
            player={player}
          />
        ))}
      </ul>

      <div className="voice__who">
        <fieldset
          className="segmented"
          aria-describedby={problems.role ? roleErrId : undefined}
          aria-invalid={problems.role ? true : undefined}
        >
          <legend className="visually-hidden">Кто это — {label.toLowerCase()}</legend>
          {ROLES.map((r) => (
            <label key={r.value}>
              <input
                type="radio"
                name={`${base}-role`}
                value={r.value}
                checked={state.role === r.value}
                onChange={() => onChange({ ...state, role: r.value })}
              />
              {r.label}
            </label>
          ))}
        </fieldset>

        {state.role === "student" && (
          <div className="voice__name">
            <label className="visually-hidden" htmlFor={`${base}-name`}>
              Имя студента — {label.toLowerCase()}
            </label>
            <input
              id={`${base}-name`}
              className="input"
              list={namesListId}
              placeholder="Имя студента"
              autoComplete="off"
              spellCheck={false}
              value={state.name}
              aria-invalid={problems.name ? true : undefined}
              aria-describedby={problems.name ? nameErrId : undefined}
              onChange={(e) => onChange({ ...state, name: e.target.value })}
            />
          </div>
        )}
      </div>

      {problems.role && (
        <p className="field__error voice__problem" id={roleErrId}>
          {problems.role}
        </p>
      )}
      {problems.name && (
        <p className="field__error voice__problem" id={nameErrId}>
          {problems.name}
        </p>
      )}
      {state.role === "student" && mergedWith.length > 0 && !problems.name && (
        <p className="voice__merged">
          Одно имя с {mergedWith.map((n) => `голосом ${n}`).join(" и ")} — в отчёте это один студент.
        </p>
      )}
    </section>
  );
}
