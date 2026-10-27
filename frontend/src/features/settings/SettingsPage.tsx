import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useApp } from "../../app/AppContext";
import { api, ApiError } from "../../shared/api";
import type { Settings, SettingsUpdate } from "../../shared/api";
import { useDocumentTitle } from "../../shared/hooks";
import { Icon, Notice, PageHead, Switch } from "../../shared/ui";
import { KeyField } from "./KeyField";
import "./settings.css";

type Status = { kind: "idle" } | { kind: "saving"; checking: boolean } | { kind: "saved" } | { kind: "partial" } | { kind: "error"; message: string };

export function SettingsPage() {
  useDocumentTitle("Настройки");
  const app = useApp();
  const [saved, setSaved] = useState<Settings | null>(app.settings);
  const [eleven, setEleven] = useState("");
  const [gemini, setGemini] = useState("");
  const [acoustic, setAcoustic] = useState(true);
  const [modelA, setModelA] = useState("");
  const [modelB, setModelB] = useState("");
  const [errors, setErrors] = useState<{ elevenlabs?: string; gemini?: string; models?: string }>({});
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  function adopt(s: Settings) {
    setSaved(s);
    setAcoustic(s.acoustic_enabled);
    setModelA(s.blind_models?.[0] ?? "");
    setModelB(s.blind_models?.[1] ?? "");
  }

  useEffect(() => {
    api.settings().then(adopt, (e) =>
      setStatus({ kind: "error", message: e instanceof ApiError ? e.message : "Не удалось загрузить настройки." }),
    );
  }, []);

  const busy = status.kind === "saving";
  const modelsOpen = Boolean(saved?.blind_models?.length);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const a = modelA.trim();
    const b = modelB.trim();
    if (!a && b) {
      setErrors({ models: "Сначала укажите основную модель — вторая необязательна." });
      return;
    }
    if (a && a === b) {
      setErrors({ models: "Вторая модель должна отличаться от первой: одна модель дважды не считается независимой проверкой." });
      return;
    }
    const upd: SettingsUpdate = {
      acoustic_enabled: acoustic,
      blind_models: a ? (b ? [a, b] : [a]) : [],
      elevenlabs_key: eleven.trim() ? eleven.trim() : null,
      gemini_key: gemini.trim() ? gemini.trim() : null,
    };
    setErrors({});
    setStatus({ kind: "saving", checking: Boolean(upd.elevenlabs_key || upd.gemini_key) });
    try {
      const res = await api.saveSettings(upd);
      adopt(res.settings);
      app.setSettings(res.settings);
      setErrors(res.errors);
      if (!res.errors.elevenlabs) setEleven("");
      if (!res.errors.gemini) setGemini("");
      setStatus(res.ok ? { kind: "saved" } : { kind: "partial" });
    } catch (err) {
      setStatus({ kind: "error", message: err instanceof ApiError ? err.message : "Не получилось сохранить." });
    }
  }

  return (
    <>
      <PageHead
        title="Настройки"
        lead="Ключи вводятся один раз и хранятся только в папке Vymova на этом компьютере."
      />

      <form className="settings" onSubmit={submit} noValidate>
        <section className="settings__section" aria-labelledby="keys-title">
          <h2 className="section-title" id="keys-title">
            Ключи
          </h2>
          <p className="settings__text">
            ElevenLabs расшифровывает запись и разделяет голоса. Gemini проверяет произношение, грамматику и лексику.
            Оплата идёт с ваших аккаунтов.
          </p>

          <KeyField
            id="key-elevenlabs"
            label="Ключ ElevenLabs"
            saved={saved?.elevenlabs_key ?? ""}
            value={eleven}
            error={errors.elevenlabs}
            helpUrl="https://elevenlabs.io/app/settings/api-keys"
            helpText="Где взять ключ ElevenLabs"
            disabled={busy}
            onChange={setEleven}
          />

          <KeyField
            id="key-gemini"
            label="Ключ Gemini"
            saved={saved?.gemini_key ?? ""}
            value={gemini}
            error={errors.gemini}
            helpUrl="https://aistudio.google.com/apikey"
            helpText="Где взять ключ Gemini"
            disabled={busy}
            onChange={setGemini}
          />

          <Notice tone="attention" title="Нужен платный тариф Gemini">
            На бесплатном тарифе Google может использовать отправленные данные, а здесь это голоса ваших студентов.
            Включите оплату в Google AI Studio для проекта, к которому относится ключ.
          </Notice>
        </section>

        <section className="settings__section" aria-labelledby="acoustic-title">
          <div className="settings__switch-row">
            <div>
              <h2 className="section-title" id="acoustic-title">
                Акустическая проверка
              </h2>
              <p className="settings__text" id="acoustic-desc">
                Ещё одна проверка произношения, прямо на этом компьютере. На слабом компьютере заметно удлиняет
                обработку. Если выключить, отчёт опирается на слепую проверку Gemini.
              </p>
            </div>
            <Switch
              checked={acoustic}
              onChange={setAcoustic}
              labelledBy="acoustic-title"
              describedBy="acoustic-desc"
              disabled={busy}
            />
          </div>
        </section>

        <details className="settings__more" open={modelsOpen || Boolean(errors.models)}>
          <summary>
            <Icon name="chevron" size={16} className="settings__chev" />
            Дополнительно: модели для слепой проверки
          </summary>
          <div className="settings__more-body">
            <p className="settings__text">
              По умолчанию реплики вслепую слушает одна модель — Gemini 4 Argon. Можно указать другую или добавить
              вторую: тогда ошибка подтверждается, только если её услышали обе. Так точнее, но заметно дороже.
            </p>
            <div className="settings__models">
              <div className="field">
                <label className="field__label" htmlFor="model-a">
                  Модель
                </label>
                <input
                  id="model-a"
                  className="input input--path"
                  placeholder="например, gemini-4-argon"
                  spellCheck={false}
                  autoComplete="off"
                  value={modelA}
                  disabled={busy}
                  aria-invalid={errors.models ? true : undefined}
                  onChange={(e) => setModelA(e.target.value)}
                />
              </div>
              <div className="field">
                <label className="field__label" htmlFor="model-b">
                  Вторая модель — необязательно
                </label>
                <input
                  id="model-b"
                  className="input input--path"
                  placeholder="например, gemini-3.1-pro-preview"
                  spellCheck={false}
                  autoComplete="off"
                  value={modelB}
                  disabled={busy}
                  aria-invalid={errors.models ? true : undefined}
                  onChange={(e) => setModelB(e.target.value)}
                />
              </div>
            </div>
            {errors.models && <p className="field__error">{errors.models}</p>}
          </div>
        </details>

        <div className="settings__save">
          <button type="submit" className="btn btn--primary" disabled={busy || !saved}>
            {busy && <span className="btn__spinner" aria-hidden="true" />}
            {busy ? (status.checking ? "Проверяем ключи…" : "Сохраняем…") : "Сохранить"}
          </button>
          <p className={`settings__status settings__status--${status.kind}`} role="status">
            {status.kind === "saved" && "Сохранено."}
            {status.kind === "partial" && "Остальное сохранено, но ключ не принят — подробности у поля выше."}
            {status.kind === "error" && status.message}
            {status.kind === "saving" && status.checking && "Это может занять до полуминуты."}
          </p>
        </div>
      </form>
    </>
  );
}
