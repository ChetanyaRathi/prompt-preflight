#!/usr/bin/env python3
"""Install Prompt Preflight into the default personal Codex plugin marketplace.

The installer performs the manual setup steps documented in docs/SETUP.md:

1. Copy this plugin to ~/plugins/prompt-preflight.
2. Create or update ~/.agents/plugins/marketplace.json.
3. Attempt to run `codex plugin add prompt-preflight@<marketplace-name>`.

It makes no network requests and does not call any model.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any
from urllib.parse import quote


PLUGIN_NAME = "prompt-preflight"
DEFAULT_MARKETPLACE_NAME = "personal"
DEFAULT_SOURCE_PATH = f"./plugins/{PLUGIN_NAME}"
IGNORE_PATTERNS = (
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "build",
    "dist",
    "*.egg-info",
    "benchmark-results*.json",
)


class InstallerError(RuntimeError):
    """Raised for expected installer failures."""


def default_plugins_dir(home: Path | None = None) -> Path:
    home = home or Path.home()
    return home / "plugins"


def default_marketplace_path(home: Path | None = None) -> Path:
    home = home or Path.home()
    return home / ".agents" / "plugins" / "marketplace.json"


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InstallerError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise InstallerError(f"{path} must contain a JSON object")
    return data


def validate_source_plugin(root: Path) -> dict[str, Any]:
    manifest_path = root / ".codex-plugin" / "plugin.json"
    required_paths = (
        manifest_path,
        root / "hooks" / "hooks.json",
        root / "scripts" / "prompt_preflight_hook.py",
        root / "src" / "prompt_preflight" / "analyzer.py",
        root / "src" / "prompt_preflight" / "data" / "vague_prompts.txt",
    )
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise InstallerError("Source plugin is incomplete. Missing: " + ", ".join(missing))

    manifest = read_json(manifest_path)
    if manifest.get("name") != PLUGIN_NAME:
        raise InstallerError(
            f"Expected plugin manifest name {PLUGIN_NAME!r}, found {manifest.get('name')!r}"
        )
    return manifest


def marketplace_entry(source_path: str = DEFAULT_SOURCE_PATH) -> dict[str, Any]:
    return {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": source_path,
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }


def plugin_ref(marketplace_name: str) -> str:
    return f"{PLUGIN_NAME}@{marketplace_name}"


def codex_plugin_deeplink(marketplace_path: Path, *, share: bool = False) -> str:
    query = f"marketplacePath={quote(str(marketplace_path.expanduser().resolve()), safe='')}"
    if share:
        query += "&mode=share"
    return f"codex://plugins/{quote(PLUGIN_NAME, safe='')}?{query}"


def load_or_create_marketplace(path: Path, marketplace_name: str) -> dict[str, Any]:
    if not path.exists():
        return {
            "name": marketplace_name,
            "interface": {
                "displayName": marketplace_name[:1].upper() + marketplace_name[1:],
            },
            "plugins": [],
        }

    marketplace = read_json(path)
    if not isinstance(marketplace.get("plugins", []), list):
        raise InstallerError(f"{path} has a non-list 'plugins' field")
    marketplace.setdefault("name", marketplace_name)
    marketplace.setdefault("interface", {"displayName": marketplace["name"]})
    marketplace.setdefault("plugins", [])
    return marketplace


def upsert_marketplace_entry(
    marketplace: dict[str, Any],
    *,
    source_path: str = DEFAULT_SOURCE_PATH,
) -> str:
    """Add or update the Prompt Preflight marketplace entry.

    Returns one of: "created", "updated", or "unchanged".
    """

    plugins = marketplace.setdefault("plugins", [])
    if not isinstance(plugins, list):
        raise InstallerError("Marketplace 'plugins' field must be a list")

    desired = marketplace_entry(source_path)
    for index, existing in enumerate(plugins):
        if isinstance(existing, dict) and existing.get("name") == PLUGIN_NAME:
            updated = dict(existing)
            updated.update(desired)
            if updated == existing:
                return "unchanged"
            plugins[index] = updated
            return "updated"

    plugins.append(desired)
    return "created"


def write_marketplace(path: Path, marketplace: dict[str, Any], *, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(marketplace, indent=2) + "\n", encoding="utf-8")


def destination_is_safe_to_clean(destination: Path) -> bool:
    if not destination.exists():
        return True
    manifest_path = destination / ".codex-plugin" / "plugin.json"
    if not manifest_path.exists():
        return False
    try:
        manifest = read_json(manifest_path)
    except InstallerError:
        return False
    return manifest.get("name") == PLUGIN_NAME


def copy_plugin(source_root: Path, destination: Path, *, clean: bool, dry_run: bool) -> None:
    source_root = source_root.resolve()
    destination = destination.expanduser().resolve()

    if source_root == destination:
        raise InstallerError("Source and destination are the same directory")
    if source_root in destination.parents:
        raise InstallerError("Destination cannot be inside the source plugin directory")

    if clean and destination.exists():
        if not destination_is_safe_to_clean(destination):
            raise InstallerError(
                f"Refusing to clean {destination}; it does not look like a {PLUGIN_NAME} install"
            )
        if not dry_run:
            shutil.rmtree(destination)

    if dry_run:
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source_root,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(*IGNORE_PATTERNS),
    )


def run_codex_install(
    marketplace_name: str,
    *,
    codex_bin: str,
    reinstall: bool,
    dry_run: bool,
) -> str:
    reference = plugin_ref(marketplace_name)
    commands: list[list[str]] = []
    if reinstall:
        commands.append([codex_bin, "plugin", "remove", reference])
    commands.append([codex_bin, "plugin", "add", reference])

    if dry_run:
        for command in commands:
            print("$ " + " ".join(command))
        return "dry-run"

    if shutil.which(codex_bin) is None:
        return "cli-unavailable"

    for command in commands:
        result = subprocess.run(command, check=False)
        if command[2] == "remove" and result.returncode != 0:
            print(f"Note: {' '.join(command)} exited {result.returncode}; continuing.")
            continue
        if result.returncode != 0:
            raise InstallerError(f"Command failed with exit code {result.returncode}: {' '.join(command)}")
    return "installed"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install or update Prompt Preflight in the personal Codex plugin marketplace.",
    )
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=default_plugins_dir(),
        help="Directory that should contain the installed prompt-preflight plugin",
    )
    parser.add_argument(
        "--marketplace-path",
        type=Path,
        default=default_marketplace_path(),
        help="Path to the personal marketplace.json file",
    )
    parser.add_argument(
        "--marketplace-name",
        default=DEFAULT_MARKETPLACE_NAME,
        help="Marketplace name to use when creating a new marketplace file",
    )
    parser.add_argument(
        "--source-path",
        default=DEFAULT_SOURCE_PATH,
        help="Marketplace source.path value for this plugin",
    )
    parser.add_argument("--codex-bin", default="codex", help="Codex CLI executable name or path")
    parser.add_argument(
        "--skip-codex-add",
        action="store_true",
        help="Copy files and update marketplace.json, but do not run codex plugin add",
    )
    parser.add_argument(
        "--require-codex-cli",
        action="store_true",
        help="Fail when the Codex CLI is not available on PATH",
    )
    parser.add_argument(
        "--no-reinstall",
        action="store_true",
        help="Do not run codex plugin remove before codex plugin add",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove the existing installed prompt-preflight directory before copying",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print intended actions without writing files or running Codex commands",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        source_root = plugin_root()
        destination = args.plugins_dir.expanduser() / PLUGIN_NAME
        marketplace_path = args.marketplace_path.expanduser()

        validate_source_plugin(source_root)
        marketplace = load_or_create_marketplace(marketplace_path, args.marketplace_name)
        marketplace_before = copy.deepcopy(marketplace)
        entry_status = upsert_marketplace_entry(marketplace, source_path=args.source_path)
        marketplace_name = str(marketplace.get("name") or args.marketplace_name)

        print("Prompt Preflight installer")
        print(f"Source: {source_root}")
        print(f"Destination: {destination.expanduser()}")
        print(f"Marketplace: {marketplace_path}")
        print(f"Marketplace name: {marketplace_name}")
        print()

        copy_plugin(source_root, destination, clean=args.clean, dry_run=args.dry_run)
        print(("Would copy" if args.dry_run else "Copied") + " plugin files.")

        if marketplace != marketplace_before:
            write_marketplace(marketplace_path, marketplace, dry_run=args.dry_run)
            print(
                ("Would write" if args.dry_run else "Wrote")
                + f" marketplace entry ({entry_status})."
            )
        else:
            print("Marketplace entry already up to date.")

        if args.skip_codex_add:
            print("Skipped Codex plugin add.")
        else:
            install_status = run_codex_install(
                marketplace_name,
                codex_bin=args.codex_bin,
                reinstall=not args.no_reinstall,
                dry_run=args.dry_run,
            )
            reference = plugin_ref(marketplace_name)
            if install_status == "cli-unavailable":
                if args.require_codex_cli:
                    raise InstallerError(
                        f"Could not find {args.codex_bin!r} on PATH. "
                        f"Run `codex plugin add {reference}` manually."
                    )
                print()
                print(f"Codex CLI not found on PATH, so `{args.codex_bin} plugin add` was skipped.")
                print("Plugin files and the marketplace entry are installed.")
                print(f"If you have the Codex CLI elsewhere, run: codex plugin add {reference}")
                print("Or open this in the Codex app:")
                print(codex_plugin_deeplink(marketplace_path))
            else:
                print(
                    ("Would install" if args.dry_run else "Installed")
                    + f" {PLUGIN_NAME}@{marketplace_name}."
                )

        print()
        print("Next steps:")
        print("1. Restart Codex.")
        print("2. Open a new thread.")
        print("3. Run /hooks and trust the Prompt Preflight hook.")
        print('4. Test with: "Create a car image"')
        return 0
    except InstallerError as exc:
        print(f"Install failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
