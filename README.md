# synthetic-panel

Cursor Agent Skill for synthetic market research: generate N buyer personas,
dispatch isolated parallel subagents (each browses the web in character),
aggregate responses statistically, and deliver an interactive canvas dashboard.

## What it does

1. **Intake** — interactive questions (idea, audience, N, runs, persona models).
2. **Personas** — auto-generated roster with demographics, OCEAN traits, backstory.
3. **Parallel panel** — one subagent per persona, isolated context, web grounding.
4. **Validate & repair** — tolerant JSON parsing, re-dispatch failures.
5. **Aggregate** — distributions, crosstabs, second-order realism diagnostics.
6. **Canvas** — dashboard with charts, themes, and trust panel.

Invoke in Cursor: `/synthetic-panel`

## Repository layout

```
synthetic-panel/
├── SKILL.md              # Orchestrator workflow (read by Cursor)
├── reference.md          # Schemas, persona prompt template
├── scripts/
│   ├── aggregate.py      # Statistics (stdlib only)
│   └── validate.py       # Validate/repair persona responses
├── install.sh            # Symlink into ~/.cursor/skills/
└── README.md
```

Study outputs (`runs/<timestamp>/`, canvases) are written in your **workspace**,
not in this repo. They are gitignored if you clone this repo into a project.

## Install (Cursor)

From this directory:

```bash
./install.sh
```

This replaces `~/.cursor/skills/synthetic-panel` with a symlink to this repo.
Restart or start a new chat so Cursor picks up the skill.

Manual install:

```bash
ln -sfn "$(pwd)" ~/.cursor/skills/synthetic-panel
```

## Scripts (from a workspace with a study run)

```bash
# Validate persona response files (auto-repair fences, list failures)
python /path/to/synthetic-panel/scripts/validate.py runs/<timestamp>

# Aggregate into aggregate.json
python /path/to/synthetic-panel/scripts/aggregate.py runs/<timestamp>
```

When the skill is installed via symlink, the orchestrator resolves paths under
`~/.cursor/skills/synthetic-panel/scripts/`.

## Development

- Edit files in this repo; changes apply immediately if `install.sh` was used.
- No third-party Python dependencies.
- This is a **prototype / bench** for validating prompts and aggregation before
  porting to a production backend — not a SaaS replacement for real panels.

## Limits

- ~8–12 concurrent persona subagents per batch (Cursor practical limit).
- Persona subagents need non-readonly mode for web access.
- Cost runs against your Cursor plan; web-browsing personas are context-heavy.
- Synthetic opinions can be over-constrained; the aggregate script flags this.
