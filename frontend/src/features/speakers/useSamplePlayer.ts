import { useCallback, useEffect, useRef, useState } from "react";

export interface SamplePlayer {
  playing: string | null;
  /** 0..1 position of the playing sample. */
  position: number;
  failed: string | null;
  toggle: (key: string, url: string) => void;
}

/** One audio element for the whole screen, so only one sample sounds at a time. */
export function useSamplePlayer(): SamplePlayer {
  const audio = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState<string | null>(null);
  const [position, setPosition] = useState(0);
  const [failed, setFailed] = useState<string | null>(null);
  const current = useRef<string | null>(null);

  useEffect(() => {
    const el = new Audio();
    el.preload = "none";
    const stop = () => {
      current.current = null;
      setPlaying(null);
      setPosition(0);
    };
    el.addEventListener("timeupdate", () => {
      if (el.duration > 0) setPosition(el.currentTime / el.duration);
    });
    el.addEventListener("ended", stop);
    el.addEventListener("error", () => {
      if (current.current) setFailed(current.current);
      stop();
    });
    audio.current = el;
    return () => {
      el.pause();
      el.removeAttribute("src");
      audio.current = null;
    };
  }, []);

  const toggle = useCallback((key: string, url: string) => {
    const el = audio.current;
    if (!el) return;
    setFailed(null);
    if (current.current === key) {
      el.pause();
      current.current = null;
      setPlaying(null);
      setPosition(0);
      return;
    }
    el.pause();
    el.src = url;
    current.current = key;
    setPlaying(key);
    setPosition(0);
    el.play().catch(() => {
      if (current.current === key) {
        setFailed(key);
        current.current = null;
        setPlaying(null);
      }
    });
  }, []);

  return { playing, position, failed, toggle };
}
