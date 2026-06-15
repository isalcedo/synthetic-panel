# synthetic-panel reference

Templates and data contracts for the orchestrator. Read this when generating
personas, dispatching persona subagents, or wiring up aggregation.

## 1. Persona generation

From the audience description and `N`, generate a roster that is diverse along
demographics and psychographics. Avoid clones: vary age, location, income,
occupation, and the Big Five (OCEAN) traits. Each persona gets a first-person
backstory (silicon-sampling style) that encodes its context and biases, plus
seed search queries it would plausibly run.

Model assignment:
- Single model: every persona gets the same `model`.
- Mixed: distribute the chosen models across the roster per the requested
  proportion (e.g. 50/50). Record each persona's `model` so aggregation can
  compare answers by model.
- If no model chosen: omit `model` (personas inherit the session model). Write
  `"model": "session-default"` in personas.json for that case so crosstabs stay readable.

OCEAN values are 0-1 floats (O openness, C conscientiousness, E extraversion,
A agreeableness, N neuroticism).

## 2. `personas.json` schema

```json
{
  "study": {
    "input": "One-line description of the idea/question being evaluated",
    "audience": "Free-text audience description",
    "runs": 1,
    "questions": [
      {"id": "q1", "text": "How likely are you to use this?", "type": "scale", "options": [1, 2, 3, 4, 5]},
      {"id": "q2", "text": "Which pricing tier fits you?", "type": "single", "options": ["Free", "Pro", "Team"]},
      {"id": "q3", "text": "What would stop you from buying?", "type": "open"}
    ]
  },
  "personas": [
    {
      "id": "p01",
      "age": 34,
      "location": "Bogotá, CO",
      "income": "middle",
      "occupation": "freelance designer",
      "ocean": {"O": 0.8, "C": 0.5, "E": 0.6, "A": 0.7, "N": 0.4},
      "backstory": "I'm a freelance designer who...",
      "model": "composer-2.5-fast",
      "seed_queries": ["best invoicing tools for freelancers", "..."]
    }
  ]
}
```

Question `type` values: `scale` (numeric), `single` (one option), `multi`
(several options), `open` (free text). Closed types feed the statistics;
`open` feeds the qualitative synthesis.

## 3. Persona subagent prompt template

Send this to each persona subagent. Substitute the bracketed fields. The
subagent receives ONLY this, never the session history.

The two failure modes to design against are (a) the subagent asking for
clarification instead of answering, and (b) returning non-parseable JSON. The
template below makes the agent fully autonomous and has it WRITE its answer to a
file (so there is no chat JSON to parse).

```
You ARE this person. Stay fully in character; never break character or mention being an AI.

PERSONA
- Age: [age], Location: [location], Income: [income], Occupation: [occupation]
- Personality (OCEAN 0-1): [ocean]
- Background: [backstory]

TASK
React, as this person, to the following:
[input]

Answer these questions:
[for each question: id, text, type, options]

AUTONOMY (critical)
- You operate fully autonomously. You CANNOT ask questions or request
  clarification - there is no one to answer you. NEVER reply with a question.
- If anything is ambiguous, make the most reasonable assumption a person like you
  would make, proceed, and record that assumption in "rationale".
- If web browsing fails or returns nothing, still answer from your own knowledge
  and lived experience. NEVER refuse, never return an error, never leave fields blank.

STEPS
1. Browse the web from YOUR perspective. Run searches a person like you would run
   (start from these: [seed_queries]). Read what is relevant to you and form your
   own opinion. Let your background and biases shape what you trust and prefer.
2. Decide your answers honestly as this person, including doubts and dealbreakers.

OUTPUT (critical)
Write your answer as a single JSON object to this exact file path using your file
tools:
  [absolute_response_path]
The file content must be ONLY the JSON object - the first character is { and the
last is }. No markdown, no ``` fences, no text before or after, straight double
quotes only. It must parse with json.loads. Use exactly these keys:

{
  "persona_id": "[id]",
  "closed_answers": { "q1": <answer>, "q2": <answer> },
  "open_answer": "first-person answer to the open question(s)",
  "rationale": "why you answered this way, grounded in who you are and what you read; note any assumptions",
  "sources": ["urls you actually consulted"],
  "self_confidence": 0.0
}

Rules for closed_answers:
- Include EVERY closed question id ([closed_question_ids]).
- For a "scale" question use the number (e.g. 4, not "4. likely").
- For a "single" question use one of the exact option strings.
- For a "multi" question use a JSON array of exact option strings.
self_confidence is a number 0-1.

After writing the file, reply with only one short line: "wrote [persona_id]".
Do not paste the JSON into your reply.
```

Concrete example of a valid file content (for anchoring; do not echo it):

```json
{"persona_id": "p01", "closed_answers": {"q1": 4, "q2": "Pro"}, "open_answer": "I like it but pricing worries me.", "rationale": "As a budget-conscious freelancer I read two comparison pages and the Pro tier felt fair.", "sources": ["https://example.com/pricing"], "self_confidence": 0.7}
```

Dispatch settings: `subagent_type: generalPurpose`, `run_in_background: true`,
`model: <persona.model>` (omit if session-default). Launch in batches of ~8-12.
Substitute `[absolute_response_path]` with the absolute path to
`runs/<timestamp>/responses/<persona_id>.json` and `[closed_question_ids]` with
the list of closed question ids. For multi-run studies, point each run at a
distinct path and set `"run": <n>` inside the JSON.

## 4. Response JSON schema (what each subagent returns)

```json
{
  "persona_id": "p01",
  "closed_answers": {"q1": 4, "q2": "Pro"},
  "open_answer": "...",
  "rationale": "...",
  "sources": ["https://..."],
  "self_confidence": 0.7,
  "run": 1
}
```

`run` is optional (defaults to 1); set it only for multi-run studies.

## 5. Aggregation

Run `python ~/.cursor/skills/synthetic-panel/scripts/aggregate.py <run_dir>`. It reads `personas.json` +
`responses/*.json` and writes `aggregate.json` containing, per closed question:
distribution, numeric summary (for scales), crosstabs by `age_group` (and by
`model` when mixed), and a second-order diagnostic flagging `over_constrained`
opinions (collapsed variance / high demographic predictability). It also reports
confidence and cross-run stability. The orchestrator handles qualitative theme
clustering of `open_answer`/`rationale` separately.
