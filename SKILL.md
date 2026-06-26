---
name: synthetic-panel
description: Runs a synthetic market-research panel. Given an idea, question, or survey plus an audience description, it designs Mom Test-style surveys (hypothesis falsification, past-behavior questions, block structure), generates N buyer personas, dispatches isolated parallel subagents that each browse the web and answer in character, aggregates the responses with a statistics script, and delivers an interactive canvas dashboard. Use when the user wants to test an idea, survey, message, or pricing against simulated personas, or asks to run a synthetic panel / synthetic users / persona study.
disable-model-invocation: true
---

# synthetic-panel

Orchestrate a panel of isolated AI personas to react to an idea/survey, then
aggregate their answers statistically and present a canvas dashboard.

Supporting files (read when needed):
- [survey-design.md](survey-design.md) - **read before designing any survey**; Mom Test
  principles, block structure, bias avoidance, honest interpretation
- [reference.md](reference.md) - persona/response schemas, subagent prompt template
- [scripts/validate.py](scripts/validate.py) - validate/repair persona responses
- [scripts/aggregate.py](scripts/aggregate.py) - deterministic statistics

## Workflow

```
- [ ] Phase 0: Intake (ask the questions, confirm config)
- [ ] Phase 0b: Market context (only if user or research mode)
- [ ] Phase 1: Generate personas.json
- [ ] Phase 2: Dispatch persona subagents in parallel batches
- [ ] Phase 2b: Validate responses, repair/re-dispatch failures
- [ ] Phase 3: Run aggregate.py
- [ ] Phase 4: Cluster qualitative themes
- [ ] Phase 5: Build the canvas dashboard
```

### Phase 0: Intake (interactive)

Do NOT assume parameters. On launch, gather configuration with the `AskQuestion`
tool before doing anything else. Collect:

1. `input` - the idea, question, or list of survey questions to evaluate.
2. `audience` - free-text description of the target audience.
3. `N` - number of personas. Default 10. Warn that larger N means more batches,
   more time, and more cost (each persona browses the web = heavy context use).
4. `runs` - 1 (fast) or >1 (uncertainty bands via repeated runs).
5. `modelo_personas` - model for the persona subagents. Either one model for all,
   or a mix distributed across personas (enables per-model comparison). Choose
   from the Task tool's allowed model slugs in this environment; cheaper/faster
   ones (e.g. `composer-2.5-fast`, `gpt-5.5-medium`, `gemini-3.1-pro`) suit
   personas, leaving a stronger model for orchestration/aggregation. If the user
   does not choose, personas inherit the session model.
6. `market_context_mode` - use `AskQuestion` to ask whether to incorporate
   market externalities (politics, economy, regulation, recent news) that shape
   how personas decide. Options:
   - `none` — no extra market context (current default behavior).
   - `user` — the user provides context (e.g. political landscape of a country
     over the last two months, rate hikes, elections).
   - `research` — the orchestrator researches via web search before generating
     personas and builds a canonical brief.

   **Follow-ups when `user`:** ask for free-text context with a short prompt
   (e.g. "Describe the external factors you want all personas to share — political
   climate, economy, regulation, social mood, etc."). Reject empty input.

   **Follow-ups when `research`:** use `AskQuestion` (no fixed default — ask every
   time):
   - `market_scope` — country/region/market. Infer from `audience` when obvious;
     otherwise ask explicitly. For global/multi-country audiences, default to one
     shared scope unless the user requests per-persona scope by location.
   - `market_window` — time window (e.g. 1 month, 2 months, 3 months, 6 months,
     custom).
   - `market_focus` (optional, multi-select) — `political`, `economic`,
     `regulatory`, `social`, `all`.

   Include `market_context_mode` and derived fields in the final config summary.

#### Survey design (mandatory when deriving or reviewing questions)

Read [survey-design.md](survey-design.md) before writing or approving any
questionnaire. The goal is to **falsify** business hypotheses, not to confirm
what the user already believes.

**When `input` is an idea (not explicit questions):**

1. Derive 3–5 falsifiable hypotheses from the idea (problem exists, people pay
   today, willingness to switch, channel, etc.).
2. Design a questionnaire following the block structure (max 10–12 questions):
   - Block 0 — profile filter (2–3)
   - Block 1 — the problem, no solution mention (3–4)
   - Block 2 — current behavior / past spend (2–3)
   - Block 3 — willingness to change / past search (2–3)
   - Block 4 — concept reaction (optional; only after blocks 1–3)
   - Block 5 — pricing (1–2; concrete ranges or Van Westendorp)
3. Map every question to a `hypothesis` id and `block` (see [reference.md](reference.md)).
4. Apply Mom Test rules: past behavior over future intent; no leading or
   double-barrel questions; balanced scales; descriptive over evaluative wording.
5. Run the pre-publish checklist in survey-design.md and show the user:
   hypotheses, full question list with mappings, and any trade-offs (e.g. skipping
   Block 4 if the idea is too early). Confirm before proceeding.

**When `input` is already a question list:** audit it against survey-design.md.
If it violates the principles (hypothetical intent questions, solution revealed
too early, leading wording, >12 questions), propose a revised version and explain
why — do not run a biased survey silently.

**Never use as primary questions:** "Would you use/buy this?", likelihood-to-buy
scales, or open-ended "how much would you pay?" without past-spend anchors.

Then summarize the final config (including hypotheses) and proceed.

Validate any requested model against the allowed slugs. If invalid, do not
silently substitute - tell the user and ask for a valid one.

### Phase 0b: Market context (when `market_context_mode` is `user` or `research`)

Skip this phase when `market_context_mode` is `none`.

1. Create the run directory `runs/<timestamp>/` in the workspace (before personas).
2. **If `research`:** use web search (Tavily / web search available in the
   environment) with queries derived from `market_scope`, `market_window`, and
   `market_focus`. Synthesize a factual, neutral brief with dates and source URLs.
   Do not tailor facts to the user's business hypothesis.
3. **If `user`:** save the user's text as the brief. You may normalize formatting
   (headings, bullets) but do not rewrite or dilute their content.
4. Write artifacts:
   - `runs/<timestamp>/market_context.md` — readable brief; sources listed at the end.
   - Structured `study.market_context` object in `personas.json` (see
     [reference.md](reference.md)).
5. If the brief is long or ambiguous, show a short summary and confirm with the
   user before Phase 1.

**Canonical brief rules:**
- Shared facts for **all** personas (same macro reality).
- No business recommendations or bias toward the study hypothesis.
- Each persona will weight these facts differently in their backstory (Phase 1).

### Phase 1: Generate personas

If Phase 0b did not run, create `runs/<timestamp>/` now. Generate
`runs/<timestamp>/personas.json` following the schema in
[reference.md](reference.md): `study.hypotheses`, block-tagged `questions` (per
[survey-design.md](survey-design.md)), `study.market_context` (when applicable),
diverse demographics + OCEAN traits + first-person backstory + assigned `model` +
seed queries. Keep personas distinct (no clones).

When `study.market_context.mode` is not `none`:
- Weave the shared brief into each `backstory` with **different salience** per
  persona (e.g. a retiree notices inflation; a founder notices fintech regulation).
- Add `seed_queries` for the study topic **and** for how that persona would
  double-check macro factors relevant to them — subagents receive the brief
  directly; they should not re-research the full macro landscape from scratch.

### Phase 2: Dispatch persona subagents (parallel, isolated)

For each persona, launch a subagent with the `Task` tool:
- `subagent_type: generalPurpose` (has web search; `readonly` agents have NO
  internet, so do not use readonly here).
- `run_in_background: true` and launch in batches of ~8-12 concurrently (Cursor's
  practical concurrency limit; large N = several batches).
- `model: <persona.model>` (omit when session-default).
- Prompt = the persona subagent template in [reference.md](reference.md). Pass
  ONLY the persona + input + questions + `study.market_context.summary` (when
  mode is not `none`) + output contract. Never pass session history — isolation
  is what prevents groupthink. Subagents browse the web for the **product/survey**
  topic, not to rebuild the shared macro brief from scratch.

Reliability is critical here: persona subagents commonly (a) ask for
clarification instead of answering, or (b) return non-parseable JSON. The
template counters both - it forbids asking back (they must assume and proceed)
and has each subagent WRITE its answer directly to
`runs/<timestamp>/responses/<persona_id>.json` (absolute path), replying with
only a one-line confirmation. Do not parse JSON out of the chat reply; read the
files.

### Phase 2b: Validate and repair (do not skip)

After a batch finishes, validate before aggregating (use the skill's scripts path):

```bash
python ~/.cursor/skills/synthetic-panel/scripts/validate.py runs/<timestamp>
```

It auto-repairs trivial format issues (strips ``` fences, extracts the JSON
object, rewrites a clean file) and prints `TO_REPAIR: <ids>` for personas whose
file is missing, unparseable, or incomplete (missing keys / invalid closed
answers). For each id in `TO_REPAIR`, re-dispatch ONLY that persona with the same
prompt plus a strict reminder: "Write ONLY the JSON object to <path>, every
closed question id present, no prose, no fences." Re-run the validator. Repeat at
most twice; if some still fail, proceed and note the reduced N (and which
personas dropped) in the dashboard rather than blocking. Only continue to
aggregation once `TO_REPAIR` is empty or retries are exhausted.

### Phase 3: Aggregate

Run the statistics script:

```bash
python ~/.cursor/skills/synthetic-panel/scripts/aggregate.py runs/<timestamp>
```

It writes `runs/<timestamp>/aggregate.json` with, per closed question:
distribution, numeric summary (scales), crosstabs by `age_group` (and by `model`
when mixed), and the second-order diagnostic (`over_constrained` flag for
collapsed variance / high demographic predictability). It also reports confidence
and cross-run stability. Note any over-constrained questions - they signal low
realism and must be surfaced honestly in the dashboard.

### Phase 4: Qualitative synthesis

Follow **Principle 8** in [survey-design.md](survey-design.md): interpret to
falsify, not to confirm.

Cluster the `open_answer` and `rationale` fields across responses into a handful
of themes. For each theme, keep **verbatim quotes** (customer language for
marketing) and the `sources` personas cited (traceability).

Per hypothesis in `study.hypotheses`, state: **confirmed**, **refuted**, or
**inconclusive**, with evidence from closed + open answers.

Segment analysis when Block 0 filter questions exist: compare distributions for
personas who qualify vs. those who do not (qualification criteria from filter
answers, not from demographics alone).

Flag contradictions: high enthusiasm in Block 4 but no past search/spend in
Blocks 1–3 is a weak demand signal — say so explicitly.

When `study.market_context.mode` is not `none`, note in the synthesis how the
shared external environment may have shaped answers (e.g. austerity mood vs.
spending questions). Cite whether rationales reference macro factors from the brief.

Do this yourself; the script only handles quantitative data.

### Phase 5: Canvas dashboard

Read the canvas skill at `~/.cursor/skills-cursor/canvas/SKILL.md` before writing
the `.canvas.tsx`. Build one canvas embedding the aggregate.json data inline (no
fetch). Sections:

1. Header - study input, audience, N, models used, runs, hypotheses list. When
   `study.market_context` exists, show mode, scope, window, and 1–2 bullets from
   the summary.
2. Executive summary - 3-5 takeaways; include at least one falsification signal
   or honest limitation, not only positive findings.
3. Hypothesis verdicts - one row per hypothesis (confirmed / refuted / inconclusive).
4. Per-question distributions - grouped by survey block; labeled bar chart per closed
   question (title = the question, axis labels with units, % on the value axis).
5. Crosstabs - answer by `age_group`, and by `model` when models were mixed
   (this is the model-bias comparison); add filter-qualified vs. not when Block 0 exists.
6. Qualitative themes - theme name, verbatim quotes, cited sources.
7. Trust panel - mean self-confidence, low-confidence share, the
   `over_constrained` alert per question, enthusiasm-vs-behavior contradictions,
   cross-run stability if runs > 1, and when market context was used: a note that
   responses are conditioned on that external scenario (not a live news feed).

Only render sections that have data. Surface the over-constrained alert plainly:
it tells the user when NOT to trust the result.

## Output contract

- Market context (optional): `runs/<timestamp>/market_context.md`
- Persona responses: `runs/<timestamp>/responses/*.json`
- Statistics: `runs/<timestamp>/aggregate.json`
- Deliverable: a `.canvas.tsx` in the workspace `canvases/` directory

## Limits (state these to the user when relevant)

- Practical concurrency is ~8-12 subagents per batch; this is a prototype/bench,
  not a production backend. Large N runs in several batches.
- Persona subagents must run non-readonly to have web access.
- Cost/quota runs against the Cursor plan; web-browsing personas use heavy
  context. Mixed/cheaper models for personas is the main cost lever.
- Synthetic panels are a discovery co-pilot, not a replacement for real research
  (see survey-design.md Principle 7: real validation needs 50–500 responses).
  Persona opinions can be over-constrained (collapsed onto demographics) - the
  second-order diagnostic exists to flag exactly this.
- Market context (`research` mode) adds orchestrator web searches once per run;
  the brief is a point-in-time simulation, not a live feed. `none` preserves
  prior behavior with no extra cost.
