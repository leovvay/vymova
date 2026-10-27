import type { CSSProperties } from "react";

export type SlabTone = "ink" | "ochre" | "cinnabar" | "hatch" | "empty";

interface SlabProps {
  /** 0..1 share of the track; ignored for `empty`. */
  share?: number;
  tone: SlabTone;
  label?: string;
  className?: string;
}

/**
 * The measure slab: a flat bar whose length is the exact quantity, on a hairline track.
 * Every slab on one screen shares a scale and a left edge.
 */
export function Slab({ share = 0, tone, label, className }: SlabProps) {
  const clamped = Math.max(0, Math.min(1, share));
  const style = { "--share": clamped } as CSSProperties;
  return (
    <span
      className={`slab slab--${tone}${className ? ` ${className}` : ""}`}
      style={style}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      <span className="slab__fill" />
    </span>
  );
}
