---
name: synthetic-panel
description: Runs a synthetic market-research panel. Given an idea, question, or survey plus an audience description, it generates N buyer personas, dispatches isolated parallel subagents that each browse the web and answer in character, aggregates the responses with a statistics script, and delivers an interactive canvas dashboard. Use when the user wants to test an idea, survey, message, or pricing against simulated personas, or asks to run a synthetic panel / synthetic users / persona study.
disable-model-invocation: true
---

# synthetic-panel

Orchestrate a panel of isolated AI personas to react to an idea/survey, then
aggregate their answers statistically and present a canvas dashboard.

Supporting files (read when needed):
- [reference.md](reference.md) - persona/response schemas, subagent prompt template
- [scripts/validate.py](scripts/validate.py) - validate/repair persona responses
- [scripts/aggregate.py](scripts/aggregate.py) - deterministic statistics

## Workflow

```
- [ ] Phase 0: Intake (ask the questions, confirm config)
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

If `input` is just an idea (not explicit questions), propose a small default
question set (e.g. likelihood-to-use scale, pricing-tier choice, dealbreaker
open question) and confirm. Then summarize the final config and proceed.

Validate any requested model against the allowed slugs. If invalid, do not
silently substitute - tell the user and ask for a valid one.

### Phase 1: Generate personas

Create a run directory `runs/<timestamp>/` in the workspace. Generate
`runs/<timestamp>/personas.json` following the schema in
[reference.md](reference.md): diverse demographics + OCEAN traits + first-person
backstory + assigned `model` + seed queries. Keep personas distinct (no clones).

### Phase 2: Dispatch persona subagents (parallel, isolated)

For each persona, launch a subagent with the `Task` tool:
- `subagent_type: generalPurpose` (has web search; `readonly` agents have NO
  internet, so do not use readonly here).
- `run_in_background: true` and launch in batches of ~8-12 concurrently (Cursor's
  practical concurrency limit; large N = several batches).
- `model: <persona.model>` (omit when session-default).
- Prompt = the persona subagent template in [reference.md](reference.md). Pass
  ONLY the persona + input + questions + output contract. Never pass session
  history - isolation is what prevents groupthink.

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

Cluster the `open_answer` and `rationale` fields across responses into a handful
of themes. For each theme, keep representative quotes and the `sources` personas
cited (traceability). Do this yourself; the script only handles quantitative data.

### Phase 5: Canvas dashboard

Read the canvas skill at `~/.cursor/skills-cursor/canvas/SKILL.md` before writing
the `.canvas.tsx`. Build one canvas embedding the aggregate.json data inline (no
fetch). Sections:

1. Header - study input, audience, N, models used, runs.
2. Executive summary - 3-5 takeaways you write from the data.
3. Per-question distributions - a labeled bar chart per closed question (title =
   the question, axis labels with units, % on the value axis).
4. Crosstabs - answer by `age_group`, and by `model` when models were mixed
   (this is the model-bias comparison).
5. Qualitative themes - theme name, representative quotes, cited sources.
6. Trust panel - mean self-confidence, low-confidence share, the
   `over_constrained` alert per question, and cross-run stability if runs > 1.

Only render sections that have data. Surface the over-constrained alert plainly:
it tells the user when NOT to trust the result.

## Output contract

- Persona responses: `runs/<timestamp>/responses/*.json`
- Statistics: `runs/<timestamp>/aggregate.json`
- Deliverable: a `.canvas.tsx` in the workspace `canvases/` directory

## Limits (state these to the user when relevant)

- Practical concurrency is ~8-12 subagents per batch; this is a prototype/bench,
  not a production backend. Large N runs in several batches.
- Persona subagents must run non-readonly to have web access.
- Cost/quota runs against the Cursor plan; web-browsing personas use heavy
  context. Mixed/cheaper models for personas is the main cost lever.
- Synthetic panels are a discovery co-pilot, not a replacement for real research.
  Persona opinions can be over-constrained (collapsed onto demographics) - the
  second-order diagnostic exists to flag exactly this.
