#!/usr/bin/env python3
"""Benchmark Prompt Preflight against the shared vague prompt library.

The benchmark is intentionally local and deterministic: no model calls, no API
keys, no network. It is meant to catch regressions in Prompt Preflight's ability
to pause prompts that are likely to create expensive clarification loops.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from prompt_preflight.analyzer import analyze_prompt  # noqa: E402
from prompt_preflight.vague_prompt_library import load_vague_prompts  # noqa: E402


BENCHMARK_VERSION = "2026-06-28"

VAGUE_PROMPTS: tuple[str, ...] = load_vague_prompts()


def _rate(part: int, whole: int) -> float:
    return part / whole if whole else 0.0


def _average(values: list[int]) -> float:
    return round(statistics.fmean(values), 2) if values else 0.0


def run_benchmark(
    prompts: tuple[str, ...] = VAGUE_PROMPTS,
    *,
    threshold: int = 45,
    max_questions: int = 3,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    by_intent: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "blocked": 0})

    for index, prompt in enumerate(prompts, start=1):
        analysis = analyze_prompt(
            prompt,
            threshold=max(0, min(100, threshold)),
            max_questions=max(1, min(5, max_questions)),
        )
        by_intent[analysis.intent]["total"] += 1
        if analysis.should_clarify:
            by_intent[analysis.intent]["blocked"] += 1
        rows.append(
            {
                "number": index,
                "prompt": prompt,
                "blocked": analysis.should_clarify,
                "intent": analysis.intent,
                "score": analysis.score,
                "ambiguity": analysis.ambiguity,
                "impact": analysis.impact,
                "reasons": list(analysis.reasons),
                "questions": list(analysis.questions),
                "suggested_prompt": analysis.suggested_prompt,
            }
        )

    total = len(rows)
    blocked = sum(1 for row in rows if row["blocked"])
    missed = [row for row in rows if not row["blocked"]]

    return {
        "benchmark_version": BENCHMARK_VERSION,
        "threshold": max(0, min(100, threshold)),
        "max_questions": max(1, min(5, max_questions)),
        "total_prompts": total,
        "blocked_prompts": blocked,
        "missed_prompts": len(missed),
        "block_rate": round(_rate(blocked, total), 4),
        "average_score": _average([row["score"] for row in rows]),
        "average_ambiguity": _average([row["ambiguity"] for row in rows]),
        "average_impact": _average([row["impact"] for row in rows]),
        "by_intent": {
            intent: {
                **counts,
                "block_rate": round(_rate(counts["blocked"], counts["total"]), 4),
            }
            for intent, counts in sorted(by_intent.items())
        },
        "missed": missed,
        "results": rows,
    }


def print_summary(summary: dict[str, Any], *, show_missed: int = 10) -> None:
    block_rate_percent = summary["block_rate"] * 100
    print("Prompt Preflight vague-prompt benchmark")
    print(f"Version: {summary['benchmark_version']}")
    print(f"Threshold: {summary['threshold']}")
    print(f"Prompts: {summary['total_prompts']}")
    print(f"Blocked: {summary['blocked_prompts']} ({block_rate_percent:.1f}%)")
    print(f"Missed: {summary['missed_prompts']}")
    print(f"Average score: {summary['average_score']}/100")
    print(f"Average ambiguity: {summary['average_ambiguity']}/100")
    print(f"Average impact: {summary['average_impact']}/100")
    print()
    print("By intent:")
    for intent, counts in summary["by_intent"].items():
        rate_percent = counts["block_rate"] * 100
        print(f"- {intent}: {counts['blocked']}/{counts['total']} blocked ({rate_percent:.1f}%)")

    if summary["missed"] and show_missed:
        print()
        print(f"Missed prompts, first {min(show_missed, len(summary['missed']))}:")
        for row in summary["missed"][:show_missed]:
            print(
                f"- #{row['number']} {row['prompt']!r} "
                f"(intent={row['intent']}, score={row['score']}, "
                f"ambiguity={row['ambiguity']}, impact={row['impact']})"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the fixed 150-prompt vague-prompt benchmark.",
    )
    parser.add_argument("--threshold", type=int, default=45, help="Clarification threshold")
    parser.add_argument("--max-questions", type=int, default=3, help="Maximum questions per prompt")
    parser.add_argument(
        "--min-block-rate",
        type=float,
        default=0.90,
        help="Fail when the vague-prompt block rate falls below this value",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path for complete benchmark results as JSON",
    )
    parser.add_argument(
        "--library-path",
        type=Path,
        help="Optional path to a newline-based vague prompt library",
    )
    parser.add_argument(
        "--show-missed",
        type=int,
        default=10,
        help="Number of missed prompts to show in the terminal summary",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    prompts = load_vague_prompts(args.library_path) if args.library_path else VAGUE_PROMPTS
    summary = run_benchmark(
        prompts=prompts,
        threshold=args.threshold,
        max_questions=args.max_questions,
    )
    print_summary(summary, show_missed=max(0, args.show_missed))

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print()
        print(f"Wrote JSON results to {args.json_output}")

    if summary["block_rate"] < args.min_block_rate:
        print()
        print(
            "Benchmark failed: block rate "
            f"{summary['block_rate']:.2%} is below minimum {args.min_block_rate:.2%}."
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
