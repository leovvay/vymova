from pydantic import BaseModel


class Settings(BaseModel):
    elevenlabs_key: str = ""
    gemini_key: str = ""
    blind_models: list[str] | None = None
    acoustic_enabled: bool = True


class SettingsUpdate(BaseModel):
    elevenlabs_key: str | None = None
    gemini_key: str | None = None
    blind_models: list[str] | None = None
    acoustic_enabled: bool | None = None


MASK = "••••"


def mask(key: str) -> str:
    return MASK + key[-4:] if key else ""
