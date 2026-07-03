import argparse
import sys
from pathlib import Path

# Add src to sys.path so we can import prompt_preflight
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from prompt_preflight.templates import load_template_profiles, SUPPORTED_TEMPLATE_FORMATS

DOCS_PATH = ROOT / "docs" / "TEMPLATES.md"
START_MARKER = "<!-- BEGIN GENERATED TEMPLATE DOCS - do not edit by hand -->"
END_MARKER = "<!-- END GENERATED TEMPLATE DOCS -->"

def generate_docs() -> str:
    profiles = load_template_profiles()
    
    lines = []
    
    # Supported profiles
    lines.append("Supported profiles:")
    lines.append("")
    for name in profiles.keys():
        lines.append(f"- `{name}`")
    lines.append("")
    
    # Supported formats
    lines.append("Supported formats:")
    lines.append("")
    for fmt in SUPPORTED_TEMPLATE_FORMATS:
        lines.append(f"- `{fmt}`")
    lines.append("")
    
    # Required fields by profile
    lines.append("## Required fields by profile")
    lines.append("")
    lines.append("| Profile | Required fields | Useful optional fields |")
    lines.append("| --- | --- | --- |")
    
    for name, profile in profiles.items():
        req_labels = []
        for req in profile.required:
            label = req.label
            if label == "scope or context":
                label = "scope/context"
            elif label == "style or mood":
                label = "style/mood"
            elif label == "context or source material":
                label = "context/source material"
            req_labels.append(label)
        
        req_str = ", ".join(req_labels) if req_labels else ""
        
        opt_str = ", ".join(profile.optional).replace("_", "-") if profile.optional else ""
        # The existing docs show `plan-first`, `non-goals` instead of `plan_first`, `non_goals`.
        # Wait, I should format the optional fields exactly as they are in the current markdown.
        # Let's write a function to format optional fields like in the existing table.
        
        # Existing options in table:
        # constraints, examples, non-goals, privacy notes
        # platform/stack, plan-first
        # avoid, tone, length, exclusions, date range, geography, citation style, uncertainty rule
        # segments, filters, assumptions
        # source material, visual style, speaker notes
        # Let's map underscores to spaces, except for specific known ones like `platform_stack` -> `platform/stack`, `non_goals` -> `non-goals`, `plan_first` -> `plan-first`.
        
        opts = []
        for opt in profile.optional:
            if opt == "platform_stack":
                opts.append("platform/stack")
            elif opt == "non_goals":
                opts.append("non-goals")
            elif opt == "plan_first":
                opts.append("plan-first")
            else:
                opts.append(opt.replace("_", " "))
        opt_str = ", ".join(opts) if opts else ""
        
        lines.append(f"| `{name}` | {req_str} | {opt_str} |")
        
    return "\n".join(lines) + "\n"

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate template documentation.")
    parser.add_argument("--write", action="store_true", help="Write the generated documentation to TEMPLATES.md")
    parser.add_argument("--check", action="store_true", help="Check if the documentation is up-to-date")
    args = parser.parse_args()

    if not args.write and not args.check:
        parser.print_help()
        return 1

    generated = generate_docs()
    
    try:
        content = DOCS_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: {DOCS_PATH} not found.", file=sys.stderr)
        return 1

    start_idx = content.find(START_MARKER)
    end_idx = content.find(END_MARKER)

    if start_idx == -1 or end_idx == -1:
        print(f"Error: Markers not found in {DOCS_PATH}.", file=sys.stderr)
        return 1

    new_content = content[:start_idx + len(START_MARKER)] + "\n" + generated + content[end_idx:]

    if args.check:
        if content != new_content:
            print("Error: TEMPLATES.md is out of sync with prompt_templates.json.", file=sys.stderr)
            print("Run `python3 scripts/generate_template_docs.py --write` to update it.", file=sys.stderr)
            # Find a way to show a diff if needed, or just exit 1
            return 1
        else:
            print("TEMPLATES.md is up-to-date.")
            return 0

    if args.write:
        DOCS_PATH.write_text(new_content, encoding="utf-8")
        print(f"Updated {DOCS_PATH}")
        return 0

    return 0

if __name__ == "__main__":
    sys.exit(main())
