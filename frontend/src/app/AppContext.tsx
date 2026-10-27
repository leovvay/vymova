import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api } from "../shared/api";
import type { Info, Settings } from "../shared/api";

interface AppState {
  info: Info | null;
  settings: Settings | null;
  /** True when both keys are saved. null while unknown. */
  keysReady: boolean | null;
  offline: boolean;
  setOffline: (v: boolean) => void;
  refreshInfo: () => void;
  setSettings: (s: Settings) => void;
}

const Ctx = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [info, setInfo] = useState<Info | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [offline, setOffline] = useState(false);

  const refreshInfo = useCallback(() => {
    api.info().then(setInfo, () => setOffline(true));
  }, []);

  useEffect(() => {
    refreshInfo();
    api.settings().then(setSettings, () => setOffline(true));
  }, [refreshInfo]);

  const value = useMemo<AppState>(
    () => ({
      info,
      settings,
      keysReady: settings ? Boolean(settings.elevenlabs_key && settings.gemini_key) : null,
      offline,
      setOffline,
      refreshInfo,
      setSettings,
    }),
    [info, settings, offline, refreshInfo],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useApp(): AppState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useApp outside AppProvider");
  return v;
}
