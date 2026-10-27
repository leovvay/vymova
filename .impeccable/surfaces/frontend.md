---
version: 1
slug: "frontend"
primary_target: "frontend"
related_targets: []
---

# Surface brief: Vymova web UI (all five screens)

Scope: the single-page app in `frontend/` (upload + past lessons, «Кто есть кто» (Who is who), «Обработка» (Processing), «Результат» (Result), «Настройки» (Settings)). Mode: Operate.

Audience and job: one non-technical Ukrainian tutor on a Windows PC, after a lesson. Upload a recording, mark voices, wait ~15–20 min, open one PDF. Russian UI, calm, plain, nothing superfluous. Offline assets only.

Decision note: chosen unattended (subagent run with no answer channel); the roll's assigned direction was built without a decision page. Re-roll is open on request.

## Direction contract

THESIS: Every quantity is a flat, hard-edged slab of exact length, like the stacked type-bars of a 1920s Kharkiv book cover. Refuses the category default: white SaaS cards, dotted drop zone, blue accent, checkmark list.

OWN-WORLD: Grey-white book paper ground, warm black ink, one ochre field colour for "now / your turn", a cinnabar red reserved for errors. Ink-black header band with the wide «ВИМОВА» (VYMOVA) wordmark. Wide geometric display (Unbounded) for titles and figures; Golos Text for everything else. Square corners, hairline rules, no shadows on resting surfaces.

STORY: The tutor sees at once what to do next (drop a file, mark voices, wait, open PDF), trusts that work continues without them, and never meets jargon.

FIRST VIEWPORT: Header band (wordmark left; «Уроки» (Lessons), «Настройки» right). Below, one 880px column: title «Новый урок» (New lesson), a large ink-ruled drop slab, date / topic / people in one row, ochre «Начать» (Start) slab button; past lessons list starts above the fold edge.

FORM: Ukrainian 1920s avant-garde book design (Kharkiv constructivist covers, Yermilov / Narbut era), candidate 7 of 7. Signature move: measure slabs — voice minutes, role colour, step durations and upload progress drawn as solid proportional bars on one shared left edge. Raises: Ikeda (strict four-value palette, no stray greys); Emigre specimen (two families, fixed five-step scale); Labanotation (slab length is the exact quantity, never decoration); J-card (all times tabular, right-aligned tight); Saville catalog (the lesson list is the one map, keyed by date); Botanical folio (one scale per screen, shared baseline). seed:8e7de4769efa4839

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
