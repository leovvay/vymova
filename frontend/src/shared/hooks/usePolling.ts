import { useEffect, useRef } from "react";

/** Calls `tick` every `ms` while `active`; the next call waits for the previous one. */
export function usePolling(tick: () => Promise<unknown>, ms: number, active: boolean): void {
  const ref = useRef(tick);
  ref.current = tick;

  useEffect(() => {
    if (!active) return;
    let stopped = false;
    let timer: number | undefined;
    const loop = async () => {
      try {
        await ref.current();
      } finally {
        if (!stopped) timer = window.setTimeout(loop, ms);
      }
    };
    timer = window.setTimeout(loop, ms);
    return () => {
      stopped = true;
      window.clearTimeout(timer);
    };
  }, [ms, active]);
}
