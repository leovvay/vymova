import { AppProvider, useApp } from "./AppContext";
import { href, useRoute } from "./router";
import type { Route } from "./router";
import { LessonPage } from "./LessonPage";
import { UploadPage } from "../features/upload";
import { SettingsPage } from "../features/settings";
import { OFFLINE_MESSAGE } from "../shared/api";

function Band({ route }: { route: Route }) {
  const lessonsActive = route.name !== "settings";
  return (
    <div className="band">
      <div className="band__inner">
        <a className="wordmark" href={href.home} aria-label="Vymova — на главную">
          <span className="wordmark__bars" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          ВИМОВА
        </a>
        <nav className="nav" aria-label="Разделы">
          <a href={href.home} aria-current={lessonsActive ? "page" : undefined}>
            Уроки
          </a>
          <a href={href.settings} aria-current={route.name === "settings" ? "page" : undefined}>
            Настройки
          </a>
        </nav>
      </div>
    </div>
  );
}

function Screen({ route }: { route: Route }) {
  switch (route.name) {
    case "settings":
      return <SettingsPage />;
    case "lesson":
      return <LessonPage key={route.id} id={route.id} />;
    default:
      return <UploadPage />;
  }
}

function Shell() {
  const route = useRoute();
  const { offline } = useApp();
  return (
    <>
      <Band route={route} />
      {offline && (
        <div className="offline" role="alert">
          <p>{OFFLINE_MESSAGE}</p>
        </div>
      )}
      <main className="main">
        <Screen route={route} />
      </main>
    </>
  );
}

export function App() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  );
}
