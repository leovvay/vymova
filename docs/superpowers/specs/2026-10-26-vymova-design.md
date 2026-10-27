# Vymova — analyzing student mistakes from a Ukrainian lesson recording

Status: approved by Vlad (2026-10-27). Date: 2026-10-26.
Markers: **[Vlad]** — decided by Vlad, **[mine]** — the design author's decision, open to challenge, **[guess]** — unconfirmed.

## 1. Why

A Ukrainian tutor teaches group lessons in Google Meet and records them. The tutor needs to **collect the students' mistakes**, not get a clean transcript. Ordinary transcribers "correct" mistakes, so right now the tutor writes them down by hand. The tutor is not a native speaker [Vlad].

A prototype of this analysis has already been made by hand for one lesson (55 minutes, 3 voices: the tutor, Vlad and one more student). The result is a 24-page PDF: `~/Downloads/ua-lesson-2026-10-26/razbor-oshibok-2026-10-26.pdf`. Its structure and style are the visual reference for the report. The prototype scripts are in `docs/prototype/`.

## 2. Who uses it and how

The user is the tutor, on their own Windows computer [Vlad]. Technical level: can use Claude Code and Notion [guess, from the lesson recording], but should not have to install Python or deal with a command line.

The flow (screens agreed with Vlad from draft mockups):
1. **Upload.** Double-click `vymova-start.bat` → a page opens in the browser. Drag in the recording (mp4/m4a/mp3/wav), optionally a date and a topic. Past lessons are listed below.
2. **«Кто есть кто» (Who is who).** After ~2 minutes: the voices found, how much each one spoke, two short fragments to listen to. The tutor marks each one: «репетитор» (tutor), «студент: имя» (student: name), «пропустить» (skip). Names are remembered, and next time the program suggests them itself — all that is left is to confirm.
3. **Processing.** Steps with progress. The tab can be closed — the work continues.
4. **Result.** A single lesson card: each student's main mistakes in one line, «Открыть PDF» (Open PDF), «Папка урока» (Lesson folder).

Plus the «Настройки» (Settings) screen: ElevenLabs and Gemini keys, entered once.

## 3. Goals

- A lesson recording in → **one combined PDF per lesson** covering all students [Vlad: "no need for one per student, a combined one is fine"].
- Analysis quality as in the prototype: a mistake goes into «подтверждено» (confirmed) only if it was independently confirmed by different layers of checking.
- Runs on any Windows PC via Docker Desktop and a `.bat`, no command line [Vlad: "let's go with Docker"].
- Everything is stored on the tutor's disk: PDF, transcript, audio clips of utterances.

## 4. Non-goals

- Separate PDFs for each student [Vlad].
- Analysis of the tutor's own speech [Vlad, confirmed on recap].
- A «Как получено и ограничения» (How this was obtained and limitations) page in the PDF [Vlad: "no need for M"].
- A cloud service. The same Docker image could be put on a server, but that is a fallback, not a goal [mine].
- A native Windows program (.exe) [Vlad chose Docker].
- Training a custom model, real-time operation, a mobile version [mine].

## 5. Anti-goals (what would make the product a failure even if it works)

Vlad did not answer directly; this is inferred from the conversation [guess]:
- **Invented mistakes.** A single Gemini pass inflates confidence and makes up mistakes (in the prototype: «наоборот» instead of the real «наугад»). A report that cannot be trusted is worse than doing it by hand.
- **Mistakes "corrected" by the transcript.** The whole point is to catch what transcribers hide.
- **The tutor needing a command line or tech support** for an ordinary lesson.
- **The tutor's keys leaking**: into a log, an image, a repository.

## 6. Constraints

- OS: Windows 10/11 + Docker Desktop (WSL2). CPU only, no GPU assumed.
- Keys: the tutor's own keys — ElevenLabs and Gemini; the tutor pays [Vlad, on recap]. Vlad's keys are not used and do not end up in the code.
- The report language is Russian [Vlad, on recap]. The UI language is Russian [mine].
- Students are native speakers of different languages (for Vlad: Russian, Belarusian, Polish). Interference is detected from the evidence, not hard-coded for one student [mine].
- The tutor is **not a reference** for pronunciation. Their corrections during the lesson are a useful signal («исправлено на уроке» (corrected in the lesson)), but not the truth. In the Gemini prompts the tutor is not called a native speaker.
- The code lives in a new repository on Vlad's personal GitHub `leovvay` [Vlad]. Commits come from the personal identity (`41321050+leovvay@users.noreply.github.com`).
- Vlad's rules for code: split by domain (feature folders, interfaces in separate files, `index.ts`/`__init__` as a facade), a file over ~1500 lines is a signal to decompose, tests are written only if Vlad asks, the UI is designed via `/impeccable` (Opus).
- Lesson recordings contain the voices of third parties (the students). They must not be committed to the repository or used as fixtures anywhere public.

## 7. Analysis pipeline

The steps and what the prototype has already shown (details in `docs/prototype/`).

1. **Transcription — ElevenLabs Scribe v2.** `diarize=true`, `timestamps_granularity=word`, **without** `language_code` (otherwise Russian and Polish insertions get "Ukrainianized"), `tag_audio_events=true`. Known artifacts: it writes numbers as digits; it normalizes some words (sto procent → «стопудово», верно → «вірно», zajęcie → «заняття»); it sometimes stretches a word across a pause for a minute — durations over 3 s must be trimmed.
2. **Who is who.** Voices from diarization → confirmation by the tutor (screen 2). Each student's utterances are cut into clips at word boundaries: adjacent words of one speaker are merged when the pause is under 1.5 s, padding −0.3 / +0.4 s, utterances consisting only of fillers are skipped.
3. **First pass — Gemini, whole lesson + transcript.** It produces candidates for pronunciation mistakes and for places where the transcript diverged from the speech. It is unreliable on its own: it marks everything with high confidence, and timecodes drift by ±1 min. It is used only as a list of candidates. Prompt — `docs/prototype/prompts/pass1.txt`, with these edits: the tutor is not a native speaker, the student's languages are not hard-coded.
4. **Blind check — two Gemini models over the clips.** All of a student's clips go in one request (in the prototype 99 clips, about 7 minutes of audio, inline). The models do not know the hypotheses and write a narrow phonetic transcription in Cyrillic: stress, softness, unstressed vowels, final consonants. **Confirmed = both models heard the same thing.** This is the main filter against invented mistakes. In the prototype — `gemini-4-argon` and `gemini-3.1-pro-preview`.
   - **Model selection [mine].** A ranked list of model pairs is built into the release and can be overridden in settings. At startup the program checks the list against what the key can access. If two different strong models are not available, the «подтверждено» block is not produced: everything goes into «под вопросом» (under question), and the report explicitly warns about this. One model used twice does not count as an independent check.
   - **How a candidate becomes «подтверждено» [mine].** In the prototype a human did this, matching the first-pass candidates against both blind transcriptions. In the program it is a separate adjudicator step: the LLM receives the candidates (first pass), both blind transcriptions and the acoustics, and for each candidate it must cite specific clips and quote fragments from *both* blind transcriptions. Then code mechanically checks that the clips exist and that the quotes appear verbatim in the corresponding transcriptions. A candidate without verified quotes from both transcriptions does not make it into «подтверждено». Acoustics may raise a candidate from «возможно» (possible) to «вероятно» (likely) or mark it «не решено» (unresolved), but by itself never adds a mistake to «подтверждено» — as in the prototype.
5. **Acoustics — no LLM, local.** `facebook/wav2vec2-lv-60-espeak-cv-ft` and `facebook/wav2vec2-xlsr-53-espeak-cv-ft` convert each utterance to IPA. Phones are assigned to words via the Scribe timecodes. Comparison:
   - **Pronunciation reference** — the expected IPA of the word with stress from a language model, checked against a dictionary (Wiktionary), cached per word [Vlad: "the language model already knows the phonetic reference"].
   - **Model calibration [mine].** The recognizer makes systematic errors even on native speakers (it writes [сорак] instead of [сорок]). Once, at development time, it is run over native-speaker recordings (Common Voice uk, CC0), the typical distortions are counted, and the resulting table is shipped in the app. A mistake counts only if it deviates beyond what the model "normally" distorts for native speakers.
   - **Do not use espeak-ng `uk` as the reference.** It makes verifiable mistakes itself: «років» → [рокіф], stress «ме́ні», reduction in «-десят».
   - **Do not use the tutor's speech as the reference.**
6. **Grammar and vocabulary — an LLM over each student's text.** It relies on the words confirmed by the blind check. It produces three tables: grammar (time, said, should be, rule), Russianisms, Polonisms. In essence this is "interference" broken down by source language. Words that the transcript normalized but the blind check showed were actually pronounced are marked ✓. In the prototype this step was done by hand.
7. **Group summary.** Mistakes shared by several students are the topic of the next lesson. Plus the 3 main mistakes for each student [the author's guess, Vlad did not strike it].
8. **PDF.** HTML → PDF via headless Chromium inside the container.

## 8. The report — one PDF per lesson

1. Cover: date, topic, duration, students.
2. Group summary.
3. A section for each student, as in the prototype:
   - top 5 for the next lesson;
   - pronunciation, confirmed: cards with the pattern, examples, timecodes, «исправлено на уроке» where applicable;
   - acoustic check: a table «что проверяли / студент / эталон / итог» (what was checked / student / reference / result);
   - still under question;
   - grammar;
   - vocabulary: Russianisms and Polonisms;
   - what went well;
   - what to practice.
4. Appendices, per student:
   - full phonetic transcript of all utterances: the word, IPA from the two acoustic models, the two blind Gemini transcriptions, highlighting of the checked words, the utterance number — a link to its audio clip;
   - every checked word against the reference.

No methodology page. The visual reference is the prototype PDF (see §1). Its source HTML with all the CSS: `~/Downloads/ua-lesson-2026-10-26/report.html`.

**Quality criterion [mine].** The reference run is the lesson of 2026-10-26 (`~/Downloads/6576c256-edf0-4ca8-be0d-a50e0ded3eca.mp4`). On it the program must:
- find the confirmed patterns from `~/Downloads/ua-lesson-2026-10-26/errors.md`;
- **not** raise to «подтверждено» the three candidates rejected in the prototype.

The recording is used only locally as a fixture and is not committed to the repository.

## 9. Packaging and launch

- A Docker image on GHCR under `leovvay`, public (see §12).
- `vymova-start.bat` [mine]: checks that Docker Desktop is running, otherwise gives a clear message in Russian → `docker pull` (updates arrive on their own) → `docker run` with the port bound to `127.0.0.1` only → opens the browser.
- A data folder on the Windows disk is mounted into the container, for example `%USERPROFILE%\Documents\Vymova\`. It holds the lessons (`<date>_<topic>/`: PDF, transcript, clips), settings, keys, and voice memory [mine].
- Keys are stored only in the data folder, not in the image. They are not written to logs.
- Processing runs in the background on the server. Closing the tab does not interrupt it.

## 10. At the implementer's discretion

- The web stack: backend and frontend frameworks, task queue. The backend is most likely Python, because the whole pipeline is in Python.
- Acoustic model weights: bake into the image or download on first run; PyTorch CPU or ONNX Runtime (lv-60 has a ready-made ONNX).
- How the program "recognizes" voices between lessons: speaker embeddings or something simpler.
- The specific prompts for layers 4 and 6, caching, API retries, resuming after a container restart.
- Exactly how to calibrate the acoustics and compute the deviation threshold.
- The visual design of the interface — via `/impeccable`.

## 11. Expected numbers (from the prototype, need verification)

- Time for a 55-minute lesson: Scribe about 1 min, Gemini first pass about 3 min, blind check 1–3 min per student, acoustics about 1 min on a Mac with MPS (several times longer on Windows CPU), PDF seconds. Total 15–20 minutes [guess].
- Cost: ElevenLabs about 22 credits per minute of audio plus Gemini (first pass about 130k tokens, blind check 20–40k per model and student). On the order of $1–2 per lesson [guess, to be calculated at real rates].
- A student's speech volume per lesson — 4–6 minutes, about 100 utterances.

## 12. Decisions after the document review

- **Visibility [Vlad]:** the repository is public. The Docker image on GHCR is public, and `docker pull` works without a login. `vymova-start.bat` is distributed through GitHub Releases. Lesson recordings, student names and keys do not go into the repository.
- **The tutor's computer [mine, Vlad did not specify]:** we assume a Windows PC with 8 GB RAM, CPU only. The acoustic models are loaded one at a time, not both at once. The acoustic layer can be turned off in settings. If it is off, the report is built from the blind check, and the acoustics table is marked «не запускалась» (not run).
- **Keys [mine]:** settings show a warning that a paid Gemini tier is required. On the free tier Google may use the data, and that data is the students' voices. Keys are validated on save with a test request.
- **Group size [mine]:** up to 4 students per lesson. The Gemini first pass is one per lesson, the blind check is separate for each student.
