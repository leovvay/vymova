import { Icon } from "../../shared/ui";

interface KeyFieldProps {
  id: string;
  label: string;
  /** Masked saved value ("••••a68e") or "". */
  saved: string;
  value: string;
  error?: string;
  helpUrl: string;
  helpText: string;
  disabled?: boolean;
  onChange: (v: string) => void;
}

export function KeyField({ id, label, saved, value, error, helpUrl, helpText, disabled, onChange }: KeyFieldProps) {
  const statusId = `${id}-status`;
  const errId = `${id}-err`;
  return (
    <div className="field key-field">
      <div className="key-field__top">
        <label className="field__label" htmlFor={id}>
          {label}
        </label>
        <span id={statusId} className={`key-field__status${saved ? " key-field__status--set" : ""}`}>
          {saved ? (
            <>
              <Icon name="check" size={16} />
              Сохранён <span className="key-field__mask">{saved}</span>
            </>
          ) : (
            "Не задан"
          )}
        </span>
      </div>
      <input
        id={id}
        className="input input--path"
        type="password"
        autoComplete="new-password"
        spellCheck={false}
        placeholder={saved ? "Вставьте новый ключ, чтобы заменить" : "Вставьте ключ"}
        value={value}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        aria-describedby={`${statusId}${error ? ` ${errId}` : ""}`}
        onChange={(e) => onChange(e.target.value)}
      />
      {error && (
        <p className="field__error" id={errId}>
          <Icon name="alert" size={16} />
          {error}
        </p>
      )}
      <a className="key-field__help" href={helpUrl} target="_blank" rel="noopener noreferrer">
        {helpText}
        <Icon name="external" size={14} />
      </a>
    </div>
  );
}
