import { useEffect, useState } from "react";

export type Route = { name: "home" } | { name: "settings" } | { name: "lesson"; id: string };

export function parseHash(hash: string): Route {
  const path = hash.replace(/^#/, "");
  if (path === "/settings") return { name: "settings" };
  const m = /^\/lesson\/(.+)$/.exec(path);
  if (m) return { name: "lesson", id: decodeURIComponent(m[1]) };
  return { name: "home" };
}

export const href = {
  home: "#/",
  settings: "#/settings",
  lesson: (id: string) => `#/lesson/${encodeURIComponent(id)}`,
};

export function navigate(to: string): void {
  window.location.hash = to.replace(/^#/, "");
}

export function useRoute(): Route {
  const [route, setRoute] = useState(() => parseHash(window.location.hash));
  useEffect(() => {
    const onChange = () => {
      setRoute(parseHash(window.location.hash));
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}
