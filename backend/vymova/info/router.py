import json

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from ..config import paths
from ..speakers import TEACHER

router = APIRouter(prefix="/api/info", tags=["info"])


def _known_names() -> list[str]:
    f = paths().voices_file
    if not f.exists():
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    return sorted(name for name in data if name != TEACHER)


@router.get("")
def get_info() -> dict:
    return {"host_data_dir": paths().host_data_dir, "known_names": _known_names()}


@router.get("/busy", response_class=PlainTextResponse)
def busy() -> str:
    """«busy», если какой-то шаг урока выполняется прямо сейчас (лаунчер не перезапускает контейнер)."""
    from ..lessons import store

    return "busy" if any(l.status == "running" for l in store.list()) else "idle"
