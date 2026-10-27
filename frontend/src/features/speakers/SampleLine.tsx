import type { Sample } from "../../shared/api";
import { formatClock } from "../../shared/format";
import { Icon, Slab } from "../../shared/ui";
import type { SamplePlayer } from "./useSamplePlayer";

interface SampleLineProps {
  sample: Sample;
  sampleKey: string;
  url: string;
  voiceLabel: string;
  index: number;
  player: SamplePlayer;
}

export function SampleLine({ sample, sampleKey, url, voiceLabel, index, player }: SampleLineProps) {
  const isPlaying = player.playing === sampleKey;
  const failed = player.failed === sampleKey;
  return (
    <li className={`sample${isPlaying ? " sample--playing" : ""}`}>
      <button
        type="button"
        className="sample__play"
        aria-pressed={isPlaying}
        aria-label={`${isPlaying ? "Остановить" : "Слушать"}: ${voiceLabel}, фрагмент ${index}`}
        onClick={() => player.toggle(sampleKey, url)}
      >
        <Icon name={isPlaying ? "pause" : "play"} size={18} />
      </button>
      <div className="sample__body">
        <p className="sample__text">
          «{sample.text}»
          <span className="sample__at num" title="Момент в записи">
            {formatClock(sample.start)}
          </span>
        </p>
        {isPlaying && <Slab className="sample__progress" tone="ochre" share={player.position} />}
        {failed && <p className="sample__error">Не получилось воспроизвести фрагмент.</p>}
      </div>
    </li>
  );
}
