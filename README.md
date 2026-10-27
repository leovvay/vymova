# Vymova

Pronunciation, grammar and vocabulary error analysis for students of Ukrainian, from a lesson recording.

The tutor uploads a recording of an online group lesson and marks who is who. 15–20 minutes later they get
**one PDF for the whole lesson**. For each student it covers:
- which sounds they get wrong (confirmed by two independent checks);
- grammar mistakes;
- words from other languages;
- what to practise.

It also has a full phonetic transcript of every utterance, with links to the audio.

The app runs on the tutor's own computer. Recordings go only to the speech services the tutor holds keys for
(ElevenLabs and Google Gemini).

> The app's interface and reports are in Russian. They are written for the tutor and students.

## Install (Windows)

1. Install **Docker Desktop**: https://www.docker.com/products/docker-desktop/
   - Keep "Use WSL 2" checked, then restart the PC.
   - You need 8 GB of RAM and about 10 GB of free disk space.
2. Open [Releases](https://github.com/leovvay/vymova/releases/latest) and download `vymova-start.bat`.
3. Double-click it.
   - The first run downloads the app (a few GB) and takes a while. After that it starts in seconds.
   - The browser opens when the app is ready.
4. Open «Настройки» (Settings) and paste the keys:
   - **ElevenLabs** — https://elevenlabs.io → Profile → API Keys (Speech to Text access is required).
   - **Gemini** — https://aistudio.google.com/apikey. Use a **paid** tier. On the free tier Google may use the data it
     receives, and here that data is your students' voices.

Lessons and PDFs are stored in `Documents\Vymova\lessons`. To update the app, run `vymova-start.bat` again. It never
interrupts a lesson that is being processed.

## How it works

1. **Verbatim transcription.** ElevenLabs Scribe keeps the mistakes and separates the speakers.
2. **Who is who.** The tutor confirms which voice is whose. Each student's utterances are cut into clips.
   - Voices are remembered between lessons, so names are suggested next time.
3. **First pass.** Gemini listens to the whole lesson and flags candidate errors.
4. **Blind check.** Two different Gemini models each write a narrow phonetic transcription of every clip. Neither
   knows what to look for.
   - A pattern is **confirmed** only if both models heard it.
   - The adjudicator's quotes from both transcriptions are validated mechanically.
5. **Acoustic layer, no language model.**
   - wav2vec2 phoneme recognisers turn audio into IPA.
   - The IPA is compared with dictionary pronunciation (Wiktionary).
   - Results are corrected for how the recognisers distort native speech; the calibration uses FLEURS.
6. **Report.** Grammar, vocabulary, a group summary — and the PDF.

## Development

```
cd backend && uv venv && uv pip install -e ".[ml]"
DATA_DIR=/tmp/vymova-data MODELS_DIR=/tmp/vymova-models .venv/bin/vymova serve
cd frontend && npm ci && npm run dev          # proxies /api to 127.0.0.1:8766 (VYMOVA_API)
```

- Build the image: `docker build -f docker/Dockerfile -t vymova .`
- Release: push a `v*` tag. GitHub Actions builds `ghcr.io/leovvay/vymova` (linux/amd64) and attaches the launcher to
  the release.
- Rebuild the acoustic calibration: `tools/calibration/build_calibration.py`. It needs `GEMINI_API_KEY`, `DATA_DIR` and
  `MODELS_DIR`.

Design and plan: `docs/superpowers/specs/` and `docs/superpowers/plans/`.

## Attribution

- Acoustic calibration: **FLEURS** (Google, CC-BY-4.0), Ukrainian subset.
- Reference word pronunciation: **Wiktionary** (en.wiktionary.org, CC-BY-SA).
- Models: facebook/wav2vec2-lv-60-espeak-cv-ft and facebook/wav2vec2-xlsr-53-espeak-cv-ft (Apache-2.0),
  microsoft/wavlm-base-plus-sv.
