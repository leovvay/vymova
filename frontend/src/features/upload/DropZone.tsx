import { useRef, useState } from "react";
import type { DragEvent } from "react";
import { formatBytes } from "../../shared/format";
import { Icon } from "../../shared/ui";

export const ACCEPTED = [".mp4", ".m4a", ".mp3", ".wav", ".webm"];

export function isAccepted(file: File): boolean {
  const name = file.name.toLowerCase();
  return ACCEPTED.some((ext) => name.endsWith(ext));
}

interface DropZoneProps {
  file: File | null;
  disabled?: boolean;
  invalid?: boolean;
  describedBy?: string;
  onFile: (file: File) => void;
}

export function DropZone({ file, disabled, invalid, describedBy, onFile }: DropZoneProps) {
  const [over, setOver] = useState(false);
  const depth = useRef(0);

  function onDrop(e: DragEvent) {
    e.preventDefault();
    depth.current = 0;
    setOver(false);
    if (disabled) return;
    const f = e.dataTransfer.files?.[0];
    if (f) onFile(f);
  }

  return (
    <label
      className={`drop${over ? " drop--over" : ""}${file ? " drop--filled" : ""}${invalid ? " drop--invalid" : ""}${
        disabled ? " drop--disabled" : ""
      }`}
      onDragEnter={(e) => {
        e.preventDefault();
        depth.current += 1;
        if (!disabled) setOver(true);
      }}
      onDragOver={(e) => e.preventDefault()}
      onDragLeave={() => {
        depth.current = Math.max(0, depth.current - 1);
        if (depth.current === 0) setOver(false);
      }}
      onDrop={onDrop}
    >
      <input
        className="drop__input"
        type="file"
        accept={`${ACCEPTED.join(",")},audio/*,video/mp4,video/webm`}
        disabled={disabled}
        aria-describedby={describedBy}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = "";
        }}
      />
      <span className="drop__mark" aria-hidden="true">
        <Icon name={file ? "file" : "upload"} size={28} />
      </span>
      {file ? (
        <span className="drop__text">
          <span className="drop__title drop__title--file">{file.name}</span>
          <span className="drop__sub">
            <span className="num">{formatBytes(file.size)}</span> · <span className="drop__link">выбрать другой файл</span>
          </span>
        </span>
      ) : (
        <span className="drop__text">
          <span className="drop__title">{over ? "Отпустите файл" : "Перетащите сюда запись урока"}</span>
          <span className="drop__sub">
            или <span className="drop__link">выберите файл на компьютере</span> · mp4, m4a, mp3, wav, webm
          </span>
        </span>
      )}
    </label>
  );
}
