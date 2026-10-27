import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PORT = 8765


@dataclass(frozen=True)
class Paths:
    data_dir: Path
    host_data_dir: str
    models_dir: Path

    @property
    def lessons_dir(self) -> Path:
        return self.data_dir / "lessons"

    @property
    def settings_file(self) -> Path:
        return self.data_dir / "settings.json"

    @property
    def voices_file(self) -> Path:
        return self.data_dir / "voices.json"

    @property
    def lexicon_cache(self) -> Path:
        return self.data_dir / "lexicon_cache.json"


@lru_cache(maxsize=1)
def paths() -> Paths:
    p = Paths(
        data_dir=Path(os.environ.get("DATA_DIR", "/data")),
        host_data_dir=os.environ.get("HOST_DATA_DIR", ""),
        models_dir=Path(os.environ.get("MODELS_DIR", "/models")),
    )
    p.lessons_dir.mkdir(parents=True, exist_ok=True)
    return p
