import type { ReactNode } from "react";
import { Icon } from "./Icon";
import type { IconName } from "./Icon";

type Tone = "error" | "attention" | "plain";

interface NoticeProps {
  tone?: Tone;
  /** Defaults to "alert" for error/attention and to no mark for plain notices. */
  icon?: IconName | null;
  title?: ReactNode;
  children?: ReactNode;
  action?: ReactNode;
  live?: boolean;
}

/** Inline message block. `error` = cinnabar, `attention` = ochre (needs the tutor), `plain` = ink. */
export function Notice({ tone = "plain", icon, title, children, action, live }: NoticeProps) {
  const mark = icon === undefined ? (tone === "plain" ? null : "alert") : icon;
  return (
    <div
      className={`notice notice--${tone}${mark ? "" : " notice--bare"}`}
      role={live ? (tone === "error" ? "alert" : "status") : undefined}
    >
      {mark && (
        <span className="notice__mark" aria-hidden="true">
          <Icon name={mark} size={18} />
        </span>
      )}
      <div className="notice__body">
        {title && <p className="notice__title">{title}</p>}
        {children && <div className="notice__text">{children}</div>}
        {action && <div className="notice__action">{action}</div>}
      </div>
    </div>
  );
}
