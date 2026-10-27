import os
import subprocess
from pathlib import Path

from ..errors import StepError


def print_pdf(html: Path, out: Path) -> None:
    """HTML → PDF через headless Chromium (в контейнере — пакет chromium)."""
    binary = os.environ.get("CHROMIUM_BIN", "chromium")
    tmp = out.with_name(out.name + ".part")
    try:
        r = subprocess.run([binary, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--no-pdf-header-footer",
                            f"--print-to-pdf={tmp}", html.resolve().as_uri()],
                           capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise StepError("Не удалось напечатать PDF.") from e
    if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size == 0:
        tmp.unlink(missing_ok=True)
        raise StepError("Не удалось напечатать PDF.")
    os.replace(tmp, out)
