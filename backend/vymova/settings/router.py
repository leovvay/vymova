from fastapi import APIRouter

from . import store, validate
from .model import MASK, SettingsUpdate, mask

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _view() -> dict:
    s = store.load()
    d = s.model_dump()
    d["elevenlabs_key"] = mask(s.elevenlabs_key)
    d["gemini_key"] = mask(s.gemini_key)
    return d


@router.get("")
def get_settings() -> dict:
    return _view()


@router.put("")
def put_settings(upd: SettingsUpdate) -> dict:
    s = store.load()
    errors: dict[str, str] = {}
    for field, check, name in (("elevenlabs_key", validate.check_elevenlabs, "elevenlabs"),
                               ("gemini_key", validate.check_gemini, "gemini")):
        value = getattr(upd, field)
        if value is None or value.startswith(MASK):
            continue
        value = value.strip()
        err = check(value) if value else None
        if err:
            errors[name] = err
        else:
            setattr(s, field, value)
    if upd.blind_models is not None:
        s.blind_models = upd.blind_models or None
    if upd.acoustic_enabled is not None:
        s.acoustic_enabled = upd.acoustic_enabled
    store.save(s)
    return {"ok": not errors, "errors": errors, "settings": _view()}
