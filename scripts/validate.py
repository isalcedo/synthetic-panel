#!/usr/bin/env python3
"""Validate (and lightly repair) synthetic-panel persona responses.

Usage:
    python validate.py <run_dir>

For each persona in <run_dir>/personas.json, checks <run_dir>/responses/<id>.json:
  - missing file
  - non-parseable JSON (tries a tolerant recovery: strips ``` fences and extracts
    the outermost {...}; if recovered, rewrites the file clean)
  - missing required keys
  - closed_answers missing declared closed questions or using out-of-range values

Prints a human summary and a machine line:
    TO_REPAIR: p03,p07
(empty list means everything is valid). Exit code is non-zero if any persona
needs repair, so the orchestrator can branch on it.
Standard library only.
"""

import json
import re
import sys
from pathlib import Path

REQUIRED_KEYS = ["persona_id", "closed_answers", "open_answer", "rationale", "sources", "self_confidence"]
CLOSED_TYPES = {"scale", "single", "multi"}


def tolerant_parse(text):
    """Return (obj, repaired_text) or (None, None)."""
    try:
        return json.loads(text), None
    except (json.JSONDecodeError, TypeError):
        pass
    stripped = text.strip()
    # Strip ```json ... ``` or ``` ... ``` fences.
    fence = re.match(r"^```[a-zA-Z]*\s*(.*?)\s*```$", stripped, re.DOTALL)
    if fence:
        stripped = fence.group(1).strip()
        try:
            return json.loads(stripped), stripped
        except json.JSONDecodeError:
            pass
    # Extract the outermost braces.
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = stripped[start:end + 1]
        try:
            return json.loads(candidate), candidate
        except json.JSONDecodeError:
            pass
    return None, None


def closed_questions(study):
    return [q for q in study.get("questions", []) if q.get("type") in CLOSED_TYPES]


def value_ok(q, value):
    qtype = q.get("type")
    options = q.get("options")
    if qtype == "scale":
        try:
            num = float(value)
        except (TypeError, ValueError):
            return False
        if options:
            return num in {float(o) for o in options}
        return True
    if qtype == "single":
        return options is None or value in options or str(value) in [str(o) for o in options]
    if qtype == "multi":
        if not isinstance(value, list):
            return False
        if options is None:
            return True
        opt = [str(o) for o in options]
        return all(str(v) in opt for v in value)
    return True


def validate_one(persona_id, path, cqs):
    """Return (status, problems). status in {ok, missing, unparseable, incomplete}."""
    if not path.exists():
        return "missing", ["file not found"]

    raw = path.read_text()
    obj, repaired = tolerant_parse(raw)
    if obj is None:
        return "unparseable", ["could not parse JSON even after fence/brace recovery"]
    if repaired is not None:
        # Rewrite a clean, canonical file.
        path.write_text(json.dumps(obj, ensure_ascii=False))

    problems = []
    for key in REQUIRED_KEYS:
        if key not in obj:
            problems.append(f"missing key '{key}'")

    if obj.get("persona_id") not in (persona_id, None):
        problems.append(f"persona_id mismatch (got {obj.get('persona_id')!r})")

    answers = obj.get("closed_answers")
    if not isinstance(answers, dict):
        problems.append("closed_answers is not an object")
    else:
        for q in cqs:
            qid = q["id"]
            if qid not in answers:
                problems.append(f"closed_answers missing '{qid}'")
            elif not value_ok(q, answers[qid]):
                problems.append(f"closed_answers['{qid}']={answers[qid]!r} not a valid option")

    conf = obj.get("self_confidence")
    if not isinstance(conf, (int, float)) or isinstance(conf, bool) or not (0 <= conf <= 1):
        problems.append(f"self_confidence invalid ({conf!r})")

    if problems:
        return "incomplete", problems
    return ("repaired" if repaired is not None else "ok"), []


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    run_dir = Path(sys.argv[1])
    personas_doc = json.loads((run_dir / "personas.json").read_text())
    study = personas_doc.get("study", {})
    personas = personas_doc.get("personas", [])
    cqs = closed_questions(study)
    resp_dir = run_dir / "responses"

    to_repair = []
    repaired = []
    ok = 0
    for p in personas:
        pid = p["id"]
        status, problems = validate_one(pid, resp_dir / f"{pid}.json", cqs)
        if status == "ok":
            ok += 1
        elif status == "repaired":
            ok += 1
            repaired.append(pid)
        else:
            to_repair.append(pid)
            print(f"[{status}] {pid}: {'; '.join(problems)}")

    print(f"\nvalid: {ok}/{len(personas)}", end="")
    if repaired:
        print(f"  (auto-repaired fences/format: {', '.join(repaired)})", end="")
    print()
    print(f"TO_REPAIR: {','.join(to_repair)}")
    sys.exit(1 if to_repair else 0)


if __name__ == "__main__":
    main()
