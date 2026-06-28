"""Shared vague prompt library loader.

The benchmark reads this packaged library instead of keeping a private prompt
list in source code. Codex, Claude Code, Kiro, and the standalone CLI all ship
the same package, so maintainers have one prompt collection to update.
"""

from __future__ import annotations

from collections import Counter
from importlib import resources
from pathlib import Path


LIBRARY_RESOURCE = "data/vague_prompts.txt"


def parse_vague_prompts(text: str, *, source: str = "<memory>") -> tuple[str, ...]:
    """Parse a newline-based vague prompt library.

    Blank lines and comment lines are ignored. Duplicate prompts are rejected
    because duplicate benchmark rows make coverage numbers misleading.
    """

    prompts: list[str] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "\t" in line:
            raise ValueError(f"{source}:{line_number} contains a tab; use plain prompt text")
        prompts.append(line)

    duplicates = sorted(prompt for prompt, count in Counter(prompts).items() if count > 1)
    if duplicates:
        joined = ", ".join(repr(prompt) for prompt in duplicates[:5])
        raise ValueError(f"{source} contains duplicate vague prompts: {joined}")
    if not prompts:
        raise ValueError(f"{source} does not contain any vague prompts")
    return tuple(prompts)


def load_vague_prompts(path: Path | None = None) -> tuple[str, ...]:
    """Load vague prompts from the packaged library or an explicit file path."""

    if path is not None:
        library_path = path.expanduser()
        return parse_vague_prompts(
            library_path.read_text(encoding="utf-8"),
            source=str(library_path),
        )

    text = resources.files("prompt_preflight").joinpath(LIBRARY_RESOURCE).read_text(
        encoding="utf-8"
    )
    return parse_vague_prompts(text, source=LIBRARY_RESOURCE)
