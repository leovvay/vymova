"""Регистрация шагов конвейера: связывает урок с функциями предметных областей."""
from .. import audio, settings, speakers, transcription
from ..analysis import clips, pass1
from . import runner, store
from .model import Lesson


def _ingest(lesson: Lesson) -> None:
    d = store.dir(lesson.id)
    audio.to_wav16k(d / lesson.source, d / "audio16k.wav")
    audio.to_mp3(d / lesson.source, d / "lesson.mp3")


def _transcribe(lesson: Lesson) -> None:
    d = store.dir(lesson.id)
    speech = d / "speech.m4a"
    audio.to_speech_m4a(d / lesson.source, speech)
    try:
        out = transcription.transcribe(speech, settings.load().elevenlabs_key, lesson.people)
    finally:
        speech.unlink(missing_ok=True)
    store.write_json(lesson.id, "transcript.json", out)


def _voices(lesson: Lesson) -> None:
    voices = speakers.build(store.dir(lesson.id), store.read_json(lesson.id, "transcript.json"))
    store.write_json(lesson.id, "voices.json", [v.model_dump() for v in voices])


def _speakers(lesson: Lesson) -> dict:
    return store.read_json(lesson.id, "speakers.json")


def student_folders(lesson: Lesson) -> dict[str, str]:
    """{имя студента: папка} — стабильно, без коллизий."""
    out: dict[str, str] = {}
    for name in _speakers(lesson)["students"]:
        base, n, folder = store.slugify(name), 1, store.slugify(name)
        while folder in out.values():
            n += 1
            folder = f"{base}-{n}"
        out[name] = folder
    return out


def speaker_names(lesson: Lesson) -> dict[str, str]:
    sp = _speakers(lesson)
    names = {spk: speakers.TEACHER for spk in sp["teacher"]}
    names.update({spk: name for name, spks in sp["students"].items() for spk in spks})
    return names


def _clips(lesson: Lesson) -> None:
    sp = _speakers(lesson)
    folders = clips.run(store.dir(lesson.id), store.read_json(lesson.id, "transcript.json"),
                        sp["students"], sp["teacher"], student_folders(lesson))
    store.write_json(lesson.id, "clips/index.json", folders)


def _pass1(lesson: Lesson) -> None:
    out = pass1.run(store.dir(lesson.id), store.read_json(lesson.id, "transcript.json"), speaker_names(lesson),
                    list(_speakers(lesson)["students"]), settings.load().gemini_key)
    store.write_json(lesson.id, "pass1.json", out)


def register_all() -> None:
    def art(name: str):
        return lambda l: store.dir(l.id) / name

    runner.register("ingest", _ingest, art("lesson.mp3"))
    runner.register("transcribe", _transcribe, art("transcript.json"))
    runner.register("voices", _voices, art("voices.json"))
    runner.register("clips", _clips, art("clips/index.json"))
    runner.register("pass1", _pass1, art("pass1.json"))
