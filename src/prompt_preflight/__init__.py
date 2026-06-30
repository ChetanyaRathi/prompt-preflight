"""Prompt Preflight: a local, deterministic prompt clarity gate."""

from .analyzer import (
    Analysis,
    analyze_prompt,
    classify_intent,
    redact_sensitive,
    sensitive_findings,
    suggest_rewrite,
)
from .vague_prompt_library import load_vague_prompts, parse_vague_prompts

__all__ = [
    "Analysis",
    "analyze_prompt",
    "classify_intent",
    "load_vague_prompts",
    "parse_vague_prompts",
    "redact_sensitive",
    "sensitive_findings",
    "suggest_rewrite",
]
__version__ = "0.3.0"
