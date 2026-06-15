#!/usr/bin/env python3
"""Aggregate synthetic-panel persona responses into statistics.

Usage:
    python aggregate.py <run_dir>

<run_dir> must contain:
    personas.json          study definition + persona roster
    responses/*.json       one file per persona response

Writes <run_dir>/aggregate.json and prints a short summary.
Standard library only (no third-party dependencies).
"""

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Heuristic thresholds for the second-order ("over-constrained") diagnostic.
# Documented so they can be tuned. Lower entropy / higher predictability => opinions
# collapse onto demographics, the failure mode reported in the silicon-sampling literature.
LOW_ENTROPY_THRESHOLD = 0.50          # normalized entropy below this => collapsed
HIGH_PREDICTABILITY_THRESHOLD = 0.60  # demographic predictability above this => over-constrained

SEGMENT_FIELDS = ["age_group", "model", "location", "income", "occupation"]


def age_group(age):
    try:
        age = int(age)
    except (TypeError, ValueError):
        return "unknown"
    if age < 25:
        return "<25"
    if age < 35:
        return "25-34"
    if age < 45:
        return "35-44"
    if age < 55:
        return "45-54"
    return "55+"


def normalized_entropy(values):
    """Shannon entropy of a categorical sample, normalized to [0, 1]."""
    counts = Counter(values)
    n = sum(counts.values())
    k = len(counts)
    if n == 0 or k <= 1:
        return 0.0
    ent = -sum((c / n) * math.log(c / n) for c in counts.values())
    return ent / math.log(k)


def is_numeric(values):
    nums = 0
    for v in values:
        if isinstance(v, bool):
            return False
        if isinstance(v, (int, float)):
            nums += 1
        elif isinstance(v, str):
            try:
                float(v)
                nums += 1
            except ValueError:
                return False
    return nums == len(values) and nums > 0


def as_float(v):
    return float(v)


def load_run(run_dir):
    run_dir = Path(run_dir)
    personas_path = run_dir / "personas.json"
    if not personas_path.exists():
        raise SystemExit(f"Missing {personas_path}")
    personas_doc = json.loads(personas_path.read_text())
    study = personas_doc.get("study", {})
    personas = {p["id"]: p for p in personas_doc.get("personas", [])}

    responses = []
    resp_dir = run_dir / "responses"
    if resp_dir.exists():
        for f in sorted(resp_dir.glob("*.json")):
            try:
                responses.append(json.loads(f.read_text()))
            except json.JSONDecodeError as exc:
                print(f"warn: skipping invalid response {f.name}: {exc}", file=sys.stderr)
    return study, personas, responses


def segments_for(persona):
    seg = {}
    if persona:
        seg["age_group"] = age_group(persona.get("age"))
        seg["model"] = persona.get("model", "unknown")
        for field in ("location", "income", "occupation"):
            if persona.get(field) is not None:
                seg[field] = str(persona[field])
    return seg


def build_question_index(study, responses):
    """Return ordered list of (qid, meta) covering declared + observed questions."""
    declared = {q["id"]: q for q in study.get("questions", []) if "id" in q}
    observed = []
    for r in responses:
        for qid in (r.get("closed_answers") or {}):
            if qid not in declared and qid not in observed:
                observed.append(qid)
    ordered = list(declared.keys()) + observed
    metas = {qid: declared.get(qid, {"id": qid, "type": "unknown"}) for qid in ordered}
    return ordered, metas


def distribution(values):
    counts = Counter(values)
    n = sum(counts.values())
    return {
        "n": n,
        "counts": dict(counts),
        "pct": {k: round(100 * c / n, 1) for k, c in counts.items()} if n else {},
    }


def numeric_summary(values):
    nums = [as_float(v) for v in values]
    if not nums:
        return None
    mx = max(nums)
    top_box = round(100 * sum(1 for v in nums if v == mx) / len(nums), 1)
    summary = {
        "mean": round(statistics.fmean(nums), 3),
        "median": round(statistics.median(nums), 3),
        "min": mx if len(nums) == 1 else min(nums),
        "max": mx,
        "top_box_pct": top_box,
    }
    summary["stdev"] = round(statistics.pstdev(nums), 3) if len(nums) > 1 else 0.0
    return summary


def crosstab(question_values_by_persona, personas, dim):
    """answers grouped by a segment dimension -> distribution per group."""
    grouped = defaultdict(list)
    for pid, answer in question_values_by_persona:
        seg = segments_for(personas.get(pid, {})).get(dim)
        if seg is None:
            continue
        grouped[seg].append(answer)
    return {group: distribution(vals) for group, vals in sorted(grouped.items())}


def second_order_diagnostic(question_values_by_persona, personas):
    """Measure how much opinion collapses / is predictable from demographics."""
    all_vals = [a for _, a in question_values_by_persona]
    overall = normalized_entropy(all_vals)
    predictability = {}
    for dim in ("age_group", "model"):
        grouped = defaultdict(list)
        for pid, answer in question_values_by_persona:
            seg = segments_for(personas.get(pid, {})).get(dim)
            if seg is not None:
                grouped[seg].append(answer)
        if not grouped:
            continue
        total = sum(len(v) for v in grouped.values())
        weighted = sum(len(v) / total * normalized_entropy(v) for v in grouped.values())
        # 1 means knowing the segment fully determines the answer relative to overall spread.
        predictability[dim] = round(1 - (weighted / overall), 3) if overall > 0 else 0.0
    max_pred = max(predictability.values()) if predictability else 0.0
    over_constrained = overall < LOW_ENTROPY_THRESHOLD or max_pred > HIGH_PREDICTABILITY_THRESHOLD
    return {
        "overall_entropy_norm": round(overall, 3),
        "demographic_predictability": predictability,
        "over_constrained": over_constrained,
    }


def confidence_summary(responses):
    confs = [r["self_confidence"] for r in responses if isinstance(r.get("self_confidence"), (int, float))]
    if not confs:
        return {"n": 0}
    return {
        "n": len(confs),
        "mean": round(statistics.fmean(confs), 3),
        "median": round(statistics.median(confs), 3),
        "stdev": round(statistics.pstdev(confs), 3) if len(confs) > 1 else 0.0,
        "low_confidence_pct": round(100 * sum(1 for c in confs if c < 0.5) / len(confs), 1),
    }


def stability_across_runs(per_question_run_dists):
    """Max swing in answer proportions across runs (only if >1 run)."""
    out = {}
    for qid, run_dists in per_question_run_dists.items():
        if len(run_dists) < 2:
            continue
        keys = set()
        for d in run_dists.values():
            keys.update(d["pct"].keys())
        max_swing = 0.0
        for k in keys:
            vals = [d["pct"].get(k, 0.0) for d in run_dists.values()]
            max_swing = max(max_swing, max(vals) - min(vals))
        out[qid] = {"runs": len(run_dists), "max_proportion_swing_pct": round(max_swing, 1)}
    return out


def aggregate(run_dir):
    study, personas, responses = load_run(run_dir)
    question_ids, metas = build_question_index(study, responses)

    models_used = Counter(p.get("model", "unknown") for p in personas.values())
    mixed_models = len(models_used) > 1

    responded_ids = {r.get("persona_id") for r in responses}
    missing = [pid for pid in personas if pid not in responded_ids]

    questions_out = {}
    per_question_run_dists = defaultdict(dict)

    for qid in question_ids:
        pairs = []  # (persona_id, answer)
        run_pairs = defaultdict(list)
        for r in responses:
            ans = (r.get("closed_answers") or {}).get(qid)
            if ans is None:
                continue
            pid = r.get("persona_id")
            pairs.append((pid, ans))
            run_pairs[r.get("run", 1)].append(ans)
        if not pairs:
            continue

        values = [a for _, a in pairs]
        block = {
            "type": metas[qid].get("type", "unknown"),
            "text": metas[qid].get("text"),
            "distribution": distribution(values),
        }
        if is_numeric(values):
            block["numeric"] = numeric_summary(values)

        crosstabs = {}
        present_dims = ["age_group", "model"] if mixed_models else ["age_group"]
        for dim in present_dims:
            ct = crosstab(pairs, personas, dim)
            if ct:
                crosstabs[dim] = ct
        if crosstabs:
            block["crosstabs"] = crosstabs

        block["second_order"] = second_order_diagnostic(pairs, personas)
        questions_out[qid] = block

        for run_id, vals in run_pairs.items():
            per_question_run_dists[qid][run_id] = distribution(vals)

    result = {
        "study": {
            "input": study.get("input"),
            "audience": study.get("audience"),
            "runs": study.get("runs", 1),
        },
        "summary": {
            "n_personas": len(personas),
            "n_responses": len(responses),
            "missing_responses": missing,
            "models_used": dict(models_used),
            "mixed_models": mixed_models,
        },
        "confidence": confidence_summary(responses),
        "questions": questions_out,
        "stability_across_runs": stability_across_runs(per_question_run_dists),
        "diagnostics_thresholds": {
            "low_entropy_threshold": LOW_ENTROPY_THRESHOLD,
            "high_predictability_threshold": HIGH_PREDICTABILITY_THRESHOLD,
        },
    }
    return result


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    run_dir = Path(sys.argv[1])
    result = aggregate(run_dir)
    out_path = run_dir / "aggregate.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    s = result["summary"]
    print(f"Aggregated {s['n_responses']}/{s['n_personas']} responses -> {out_path}")
    if s["missing_responses"]:
        print(f"  missing: {', '.join(s['missing_responses'])}")
    if s["mixed_models"]:
        print(f"  models: {s['models_used']}")
    flagged = [q for q, b in result["questions"].items() if b["second_order"]["over_constrained"]]
    if flagged:
        print(f"  over-constrained questions (low realism signal): {', '.join(flagged)}")


if __name__ == "__main__":
    main()
