import type { ReactNode } from "react";
import type { StepName, StepState, StepStatus } from "../../shared/api";
import { STEP_TITLES } from "../../shared/api";
import { formatClock } from "../../shared/format";
import { Icon, Slab } from "../../shared/ui";
import type { SlabTone } from "../../shared/ui";

const STATUS_WORD: Record<StepStatus, string> = {
  pending: "ещё впереди",
  running: "идёт сейчас",
  done: "готово",
  failed: "ошибка",
  skipped: "пропущено",
};

interface StepRowProps {
  name: StepName;
  state: StepState;
  /** Exact seconds: finished duration, or elapsed so far for the running step. */
  seconds: number | null;
  /** Share of the longest time on this screen. */
  share: number;
  /** Replaces the right-hand time text. */
  note?: string;
  children?: ReactNode;
}

const TONE: Record<StepStatus, SlabTone> = {
  pending: "empty",
  skipped: "empty",
  running: "ochre",
  done: "ink",
  failed: "cinnabar",
};

export function StepRow({ name, state, seconds, share, note, children }: StepRowProps) {
  const { status } = state;
  let time = note ?? "";
  if (!note) {
    if (status === "skipped") time = "пропущено";
    else if (seconds != null && status !== "pending") time = formatClock(seconds);
    else if (status === "running") time = "идёт";
  }

  return (
    <li className={`step step--${status}`} aria-current={status === "running" ? "step" : undefined}>
      <span className="step__mark" aria-hidden="true">
        {status === "failed" && <Icon name="alert" size={14} />}
      </span>
      <span className="step__title">
        {STEP_TITLES[name]}
        <span className="visually-hidden">, {STATUS_WORD[status]}</span>
      </span>
      <Slab
        className="step__slab"
        tone={seconds == null ? "empty" : TONE[status]}
        share={share}
      />
      <span className="step__time num">{time}</span>
      {children && <div className="step__detail">{children}</div>}
    </li>
  );
}
