import os
import subprocess
from pathlib import Path

from ..errors import StepError

_BAD_INPUT = "Не удалось прочитать запись: формат не поддерживается или файл повреждён."


def _run(args: list[str], dst: Path, fmt: str) -> None:
    tmp = dst.with_name(dst.name + ".part")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-f", fmt, str(tmp)], capture_output=True, text=True)
    if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size == 0:
        tmp.unlink(missing_ok=True)
        raise StepError(_BAD_INPUT, retry=False)
    os.replace(tmp, dst)


def to_wav16k(src: Path, dst: Path) -> None:
    _run(["-i", str(src), "-vn", "-ac", "1", "-ar", "16000"], dst, "wav")


def to_mp3(src: Path, dst: Path, bitrate: str = "64k") -> None:
    _run(["-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-b:a", bitrate], dst, "mp3")


def to_speech_m4a(src: Path, dst: Path) -> None:
    """Audio for transcription: no video, mono, good enough quality for Scribe."""
    _run(["-i", str(src), "-vn", "-ac", "1", "-ar", "24000", "-c:a", "aac", "-b:a", "64k"], dst, "mp4")


def cut(src: Path, start: float, end: float, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run(["-ss", f"{max(0.0, start):.2f}", "-to", f"{end:.2f}", "-i", str(src), "-ac", "1", "-ar", "16000",
          "-b:a", "64k"], dst, "mp3")


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError as e:
        raise StepError(_BAD_INPUT) from e
