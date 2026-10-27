import { useEffect, useRef, useState } from "react";
import { Icon } from "../../shared/ui";

async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    return ok;
  }
}

export function FolderPath({ path }: { path: string }) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  async function copy() {
    const ok = await copyText(path);
    setState(ok ? "copied" : "failed");
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setState("idle"), 2400);
  }

  return (
    <div className="folder">
      <p className="field__label" id="lesson-folder-label">
        Папка урока
      </p>
      <div className="folder__row">
        <code className="folder__path" aria-labelledby="lesson-folder-label">
          {path}
        </code>
        <button type="button" className="btn folder__copy" onClick={copy}>
          <Icon name={state === "copied" ? "check" : "copy"} />
          {state === "copied" ? "Скопировано" : "Скопировать"}
        </button>
      </div>
      <p className="field__hint" aria-live="polite">
        {state === "failed"
          ? "Не получилось скопировать. Выделите путь и нажмите Ctrl+C."
          : "Вставьте путь в адресную строку Проводника. В папке — PDF, расшифровка и аудиоклипы всех реплик: их можно переслать студентам."}
      </p>
    </div>
  );
}
