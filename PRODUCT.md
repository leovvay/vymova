# Product

<!-- impeccable:product-schema 1 -->

> Written by an unattended agent from the design spec (`docs/superpowers/specs/2026-10-26-vymova-design.md`) and the Task 11 brief; no interview round took place. Facts marked *(inferred)* are not confirmed by Vlad.

## Platform

web

## Users

One Ukrainian tutor, not a native speaker, who teaches small group lessons (2–4 students) in Google Meet and records them. Non-technical: must never need a terminal. Uses the app on their own Windows PC after a lesson, a few times a week *(inferred frequency)*, to get a written analysis of each student's mistakes instead of writing them out by hand.

## Product Purpose

Vymova turns one lesson recording into one combined PDF that lists every student's pronunciation, grammar and vocabulary mistakes. Success: the tutor trusts the report enough to plan the next lesson from it, without re-listening to the recording.

## Positioning

Ordinary transcribers silently "correct" what students say. Vymova keeps the mistakes, and only marks a pronunciation error as confirmed when two independent blind checks heard the same thing. A made-up mistake is worse than a missed one.

## Operating Context

- Runs locally in Docker Desktop on Windows; started from `vymova-start.bat`, opens in the browser at `127.0.0.1:8765`. No accounts, no auth.
- Flow: upload recording → wait ~2 min → mark who is who (teacher / student + name / skip) by listening to two short samples per voice → pipeline runs ~15–20 min in the background (tab may be closed) → open the PDF or the lesson folder on disk.
- Lesson files live on the tutor's disk (`%USERPROFILE%\Documents\Vymova\lessons\<id>`), so they can forward PDFs and audio clips to students.
- The tutor pays for their own ElevenLabs and Gemini keys, entered once in Settings.

## Capabilities and Constraints

- Interface language: Russian only. Report language: Russian.
- Works offline except for the backend's own API calls: no CDN fonts or assets, no analytics, no telemetry.
- Recordings and student names are third-party personal data: never in the repo, never in logs.
- Gemini must be on a paid tier (free tier lets Google use the data, and the data is students' voices).
- Up to 4 students per lesson; 2–8 people on a recording.
- Pipeline steps can fail with a Russian `error_ru`; «Повторить» (Retry) resumes from the failed step.

## Brand Commitments

- Name: Vymova (from Ukrainian «вимова», pronunciation).
- Voice: calm, plain, nothing superfluous. Short sentences, no jargon, no exclamation marks *(inferred from "calm and plain")*.

## Evidence on Hand

- Reference report (visual model for the PDF, not the UI): `~/Downloads/ua-lesson-2026-10-26/razbor-oshibok-2026-10-26.pdf`.
- Agreed screen wireframes (structure only): `/tmp/ua-lesson/.superpowers/brainstorm/84132-1793055072/content/flow.html`, `results-v2.html`.
- No testimonials, pricing, or usage numbers exist; do not invent any.

## Product Principles

1. Trust over volume: show only what the pipeline actually produced; never pad.
2. The tutor never needs a terminal or support for an ordinary lesson.
3. Every wait is explained: what is happening now, that the tab can be closed.
4. Errors say what went wrong and what to do next, in Russian.
5. Students' data stays on the tutor's disk.

## Accessibility & Inclusion

No product-specific requirement established. Default: WCAG AA contrast, full keyboard use, readable at 100–125% Windows display scaling *(inferred)*.
