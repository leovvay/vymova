import type { ReactElement, SVGProps } from "react";

export type IconName =
  | "play"
  | "pause"
  | "upload"
  | "file"
  | "check"
  | "alert"
  | "retry"
  | "copy"
  | "external"
  | "back"
  | "lock"
  | "chevron";

/** One drawn set: 24px grid, 2px square-capped strokes; media glyphs are solid. */
const PATHS: Record<IconName, ReactElement> = {
  play: <path d="M8 5.5v13l10.5-6.5z" fill="currentColor" stroke="none" />,
  pause: (
    <g fill="currentColor" stroke="none">
      <rect x="6.5" y="5.5" width="4" height="13" />
      <rect x="13.5" y="5.5" width="4" height="13" />
    </g>
  ),
  upload: (
    <>
      <path d="M12 15V4" />
      <path d="M7 8.5 12 4l5 4.5" />
      <path d="M4 14v6h16v-6" />
    </>
  ),
  file: (
    <>
      <path d="M6 3h8l4 4v14H6z" />
      <path d="M14 3v4h4" />
      <path d="M9 12h6M9 16h6" />
    </>
  ),
  check: <path d="m5 12.5 4.5 4.5L19 7.5" />,
  alert: (
    <>
      <path d="M12 4.5v10" />
      <path d="M12 18.5v1" />
    </>
  ),
  retry: (
    <>
      <path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3" />
      <path d="M19.5 4v4.5H15" />
    </>
  ),
  copy: (
    <>
      <path d="M9 9h11v11H9z" />
      <path d="M15 9V4H4v11h5" />
    </>
  ),
  external: (
    <>
      <path d="M13 4h7v7" />
      <path d="M20 4 11 13" />
      <path d="M17 14v6H4V7h6" />
    </>
  ),
  back: (
    <>
      <path d="M20 12H5" />
      <path d="m10.5 6.5-5.5 5.5 5.5 5.5" />
    </>
  ),
  chevron: <path d="m9 5.5 6.5 6.5L9 18.5" />,
  lock: (
    <>
      <path d="M5 11h14v10H5z" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </>
  ),
};

interface IconProps extends Omit<SVGProps<SVGSVGElement>, "name"> {
  name: IconName;
  size?: number;
}

export function Icon({ name, size = 20, ...rest }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="square"
      strokeLinejoin="miter"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      {PATHS[name]}
    </svg>
  );
}
