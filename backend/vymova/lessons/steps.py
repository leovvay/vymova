"""Pipeline step registration: connects the lesson to the domain functions."""
from .. import audio, settings, speakers, transcription
from .. import gemini, report
from ..config import paths
from ..analysis import acoustic, adjudication, blind, clips, language, pass1, summary
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
    """{student name: folder} — stable, no collisions."""
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


def _blind(lesson: Lesson) -> None:
    st = settings.load()
    pair = gemini.pick_blind_pair(st.gemini_key, st.blind_models)
    folders = store.read_json(lesson.id, "clips/index.json")
    out = blind.run(store.dir(lesson.id), folders, pair, st.gemini_key)
    store.write_json(lesson.id, "blind/index.json", {**out, "students": folders})


def _acoustic(lesson: Lesson) -> None:
    st = settings.load()
    folders = store.read_json(lesson.id, "clips/index.json")
    acoustic.run(store.dir(lesson.id), store.read_json(lesson.id, "transcript.json"), folders, st.gemini_key,
                 st.acoustic_enabled)
    store.write_json(lesson.id, "acoustic/index.json", folders)


def _adjudicate(lesson: Lesson) -> None:
    key = settings.load().gemini_key
    folders = store.read_json(lesson.id, "clips/index.json")
    for name, folder in folders.items():
        if not (store.dir(lesson.id) / "adjudication" / f"{folder}.json").exists():
            store.write_json(lesson.id, f"adjudication/{folder}.json",
                             adjudication.run(store.dir(lesson.id), name, folder, key))
    store.write_json(lesson.id, "adjudication/index.json", folders)


def _language(lesson: Lesson) -> None:
    key = settings.load().gemini_key
    folders = store.read_json(lesson.id, "clips/index.json")
    for name, folder in folders.items():
        if not (store.dir(lesson.id) / "language" / f"{folder}.json").exists():
            store.write_json(lesson.id, f"language/{folder}.json", language.run(store.dir(lesson.id), name, folder, key))
    store.write_json(lesson.id, "language/index.json", folders)


def _summary(lesson: Lesson) -> None:
    folders = store.read_json(lesson.id, "clips/index.json")
    store.write_json(lesson.id, "summary.json", summary.run(store.dir(lesson.id), folders, settings.load().gemini_key))


def _report(lesson: Lesson) -> None:
    d = store.dir(lesson.id)
    html = report.build(d, lesson.id, lesson.date, lesson.topic, paths().host_data_dir)
    report.print_pdf(html, d / "report.pdf")


def register_all() -> None:
    def art(name: str):
        return lambda l: store.dir(l.id) / name

    runner.register("ingest", _ingest, art("lesson.mp3"))
    runner.register("transcribe", _transcribe, art("transcript.json"))
    runner.register("voices", _voices, art("voices.json"))
    runner.register("clips", _clips, art("clips/index.json"))
    runner.register("pass1", _pass1, art("pass1.json"))
    runner.register("blind", _blind, art("blind/index.json"))
    runner.register("acoustic", _acoustic, art("acoustic/index.json"))
    runner.register("adjudicate", _adjudicate, art("adjudication/index.json"))
    runner.register("language", _language, art("language/index.json"))
    runner.register("summary", _summary, art("summary.json"))
    runner.register("report", _report, art("report.pdf"))
