"""Local-only opt-in telemetry for Prompt Preflight.

Telemetry records aggregate counts and scores only. It never stores prompt text,
suggested rewrites, clarification questions, or reason strings.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
from typing import Any, Iterable

from .analyzer import Analysis


DEFAULT_TELEMETRY_FILE = ".prompt-preflight-telemetry.jsonl"
TELEMETRY_VERSION = 1


def telemetry_event(
    analysis: Analysis,
    *,
    host: str,
    decision: str,
) -> dict[str, Any]:
    """Build a prompt-free telemetry event from an analysis result."""

    return {
        "version": TELEMETRY_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": host,
        "decision": decision,
        "intent": analysis.intent,
        "score": analysis.score,
        "ambiguity": analysis.ambiguity,
        "impact": analysis.impact,
        "reason_count": len(analysis.reasons),
        "question_count": len(analysis.questions),
        "checks": analysis.checks,
        "bypassed": analysis.bypassed,
    }


def decision_for_analysis(analysis: Analysis, *, mode: str) -> str:
    if analysis.bypassed:
        return "bypassed"
    if analysis.should_clarify:
        return "nudged" if mode == "nudge" else "blocked"
    if "conversational follow-up" in analysis.reasons:
        return "followup_accepted"
    return "allowed"


def record_event(
    path: Path, 
    event: dict[str, Any],
    *,
    max_events: int | None = None,
    max_bytes: int | None = None,
    retention_days: int | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if max_events is None and max_bytes is None and retention_days is None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
        return

    events = read_events(path)
    events.append(event)

    if retention_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        pruned_events = []
        for e in events:
            ts_str = e.get("timestamp")
            if not ts_str:
                pruned_events.append(e)
                continue
            
            try:
                if ts_str.endswith('Z'):
                    ts_str = ts_str[:-1] + '+00:00'
                ts = datetime.fromisoformat(ts_str)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= cutoff:
                    pruned_events.append(e)
            except (ValueError, TypeError):
                pruned_events.append(e)
        events = pruned_events

    if max_events is not None:
        if len(events) > max_events:
            events = events[-max_events:]

    lines = [json.dumps(e, sort_keys=True, separators=(",", ":")) + "\n" for e in events]

    if max_bytes is not None:
        total_size = sum(len(line.encode("utf-8")) for line in lines)
        while total_size > max_bytes and lines:
            total_size -= len(lines[0].encode("utf-8"))
            lines.pop(0)

    temp_path = path.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line)
    temp_path.replace(path)


def record_analysis(
    analysis: Analysis,
    *,
    host: str,
    mode: str,
    telemetry_path: Path | None,
    enabled: bool,
    max_events: int | None = None,
    max_bytes: int | None = None,
    retention_days: int | None = None,
) -> None:
    if not enabled or telemetry_path is None:
        return
    record_event(
        telemetry_path,
        telemetry_event(
            analysis,
            host=host,
            decision=decision_for_analysis(analysis, mode=mode),
        ),
        max_events=max_events,
        max_bytes=max_bytes,
        retention_days=retention_days,
    )


def record_analysis_safely(
    analysis: Analysis,
    *,
    host: str,
    mode: str,
    telemetry_path: Path | None,
    enabled: bool,
    max_events: int | None = None,
    max_bytes: int | None = None,
    retention_days: int | None = None,
) -> None:
    try:
        record_analysis(
            analysis,
            host=host,
            mode=mode,
            telemetry_path=telemetry_path,
            enabled=enabled,
            max_events=max_events,
            max_bytes=max_bytes,
            retention_days=retention_days,
        )
    except OSError:
        # Telemetry must never make a host hook unusable.
        return


def read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def summarize_events(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    event_list = list(events)
    decisions = Counter(str(event.get("decision", "unknown")) for event in event_list)
    hosts = Counter(str(event.get("host", "unknown")) for event in event_list)
    intents = Counter(str(event.get("intent", "unknown")) for event in event_list)
    scores = [int(event.get("score", 0)) for event in event_list if isinstance(event.get("score"), int)]

    prompts_checked = len(event_list)
    blocked = decisions.get("blocked", 0)
    nudged = decisions.get("nudged", 0)
    bypassed = decisions.get("bypassed", 0)
    followups = decisions.get("followup_accepted", 0)

    blocked_by_check = Counter()
    for event in event_list:
        if event.get("decision") == "blocked":
            for check in event.get("checks", []):
                blocked_by_check[str(check)] += 1

    return {
        "prompts_checked": prompts_checked,
        "prompts_blocked": blocked,
        "prompts_nudged": nudged,
        "prompts_bypassed": bypassed,
        "followup_accepted": followups,
        "prompts_allowed": decisions.get("allowed", 0),
        "clarification_opportunities": blocked + nudged,
        "estimated_avoided_retry_turns": blocked,
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "blocked_by_check": dict(sorted(blocked_by_check.items())),
        "decisions": dict(sorted(decisions.items())),
        "hosts": dict(sorted(hosts.items())),
        "intents": dict(sorted(intents.items())),
    }


def render_report(summary: dict[str, Any], *, path: Path) -> str:
    lines = [
        "Prompt Preflight telemetry report",
        f"Path: {path}",
        "",
        f"Prompts checked: {summary['prompts_checked']}",
        f"Blocked before model work: {summary['prompts_blocked']}",
    ]
    
    for check, count in summary.get("blocked_by_check", {}).items():
        lines.append(f"  - {check}: {count}")
        
    lines.extend(
        [
            f"Nudged: {summary['prompts_nudged']}",
            f"Allowed: {summary['prompts_allowed']}",
            f"Bypassed: {summary['prompts_bypassed']}",
            f"Follow-up prompts accepted: {summary['followup_accepted']}",
            "",
            f"Clarification opportunities: {summary['clarification_opportunities']}",
            f"Estimated avoided retry turns: {summary['estimated_avoided_retry_turns']}",
            f"Average clarification score: {summary['average_score']}/100",
            "",
            "Privacy: this file stores counts, decisions, hosts, intents, check categories, and scores only.",
            "It does not store prompt text, suggested rewrites, questions, or reason strings.",
        ]
    )
    return "\n".join(lines)
