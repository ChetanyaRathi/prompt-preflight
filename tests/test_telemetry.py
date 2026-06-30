from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from prompt_preflight.analyzer import analyze_prompt
from prompt_preflight.cli import main
from prompt_preflight.config import load_config, resolve_telemetry_report_path
from prompt_preflight.telemetry import (
    read_events,
    record_analysis,
    render_report,
    summarize_events,
    telemetry_event,
)


class TelemetryTests(unittest.TestCase):
    def test_telemetry_event_does_not_store_prompt_text(self) -> None:
        analysis = analyze_prompt("Create a car image")
        event = telemetry_event(analysis, host="test", decision="blocked")
        encoded = json.dumps(event)

        self.assertNotIn("Create a car image", encoded)
        self.assertNotIn("photorealistic", encoded)
        self.assertNotIn("What should the car look like", encoded)
        self.assertEqual(event["decision"], "blocked")
        self.assertEqual(event["intent"], "image_generation")
        self.assertEqual(event["question_count"], 3)

    def test_record_and_summarize_counts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "telemetry.jsonl"
            record_analysis(
                analyze_prompt("Create a car image"),
                host="codex",
                mode="block",
                telemetry_path=path,
                enabled=True,
            )
            record_analysis(
                analyze_prompt("Create a car image [preflight:skip]"),
                host="codex",
                mode="block",
                telemetry_path=path,
                enabled=True,
            )
            record_analysis(
                analyze_prompt("go ahead"),
                host="codex",
                mode="block",
                telemetry_path=path,
                enabled=True,
            )

            events = read_events(path)
            summary = summarize_events(events)

        self.assertEqual(len(events), 3)
        self.assertEqual(summary["prompts_checked"], 3)
        self.assertEqual(summary["prompts_blocked"], 1)
        self.assertEqual(summary["prompts_bypassed"], 1)
        self.assertEqual(summary["followup_accepted"], 1)
        self.assertEqual(summary["estimated_avoided_retry_turns"], 1)

    def test_render_report_explains_privacy(self) -> None:
        summary = summarize_events(
            [
                {
                    "decision": "blocked",
                    "host": "codex",
                    "intent": "software_build",
                    "score": 60,
                }
            ]
        )
        report = render_report(summary, path=Path("telemetry.jsonl"))
        self.assertIn("Prompts checked: 1", report)
        self.assertIn("Estimated avoided retry turns: 1", report)
        self.assertIn("does not store prompt text", report)

    def test_config_telemetry_is_disabled_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = load_config(directory)
        self.assertFalse(config.telemetry_enabled)
        self.assertIsNone(config.telemetry_path)

    def test_config_telemetry_path_is_relative_to_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Path(root, ".prompt-preflight.json").write_text(
                json.dumps({"telemetry": {"enabled": True, "path": "local-telemetry.jsonl"}}),
                encoding="utf-8",
            )
            config = load_config(root)
        self.assertTrue(config.telemetry_enabled)
        self.assertEqual(config.telemetry_path, root.resolve() / "local-telemetry.jsonl")

    def test_resolve_telemetry_report_path_uses_configured_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Path(root, ".prompt-preflight.json").write_text(
                json.dumps({"telemetry": {"enabled": True, "path": "local-telemetry.jsonl"}}),
                encoding="utf-8",
            )
            self.assertEqual(
                resolve_telemetry_report_path(root),
                root.resolve() / "local-telemetry.jsonl",
            )

    def test_resolve_telemetry_report_path_when_telemetry_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Path(root, ".prompt-preflight.json").write_text(
                json.dumps(
                    {
                        "telemetry": {
                            "enabled": False,
                            "path": "archived-telemetry.jsonl",
                        }
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                resolve_telemetry_report_path(root),
                root.resolve() / "archived-telemetry.jsonl",
            )

    def test_resolve_telemetry_report_path_falls_back_to_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(
                resolve_telemetry_report_path(root),
                root.resolve() / ".prompt-preflight-telemetry.jsonl",
            )


class TelemetryReportCliTests(unittest.TestCase):
    def _write_event(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "decision": "blocked",
                    "host": "codex",
                    "intent": "software_build",
                    "score": 60,
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def test_telemetry_report_default_path_without_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            telemetry_path = root / ".prompt-preflight-telemetry.jsonl"
            self._write_event(telemetry_path)
            stdout = StringIO()
            with patch("sys.stdout", stdout):
                code = main(["--cwd", str(root), "--telemetry-report"])
            self.assertEqual(code, 0)
            self.assertIn("Prompts checked: 1", stdout.getvalue())
            self.assertIn(str(telemetry_path.resolve()), stdout.getvalue())

    def test_telemetry_report_discovers_path_from_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            telemetry_path = root / "project-telemetry.jsonl"
            Path(root, ".prompt-preflight.json").write_text(
                json.dumps({"telemetry": {"enabled": True, "path": "project-telemetry.jsonl"}}),
                encoding="utf-8",
            )
            self._write_event(telemetry_path)
            stdout = StringIO()
            with patch("sys.stdout", stdout):
                code = main(["--cwd", str(root), "--telemetry-report"])
            self.assertEqual(code, 0)
            self.assertIn("Prompts checked: 1", stdout.getvalue())
            self.assertIn(str(telemetry_path.resolve()), stdout.getvalue())

    def test_telemetry_report_uses_explicit_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            configured_path = root / "configured.jsonl"
            explicit_path = root / "explicit.jsonl"
            Path(root, ".prompt-preflight.json").write_text(
                json.dumps({"telemetry": {"enabled": True, "path": "configured.jsonl"}}),
                encoding="utf-8",
            )
            self._write_event(configured_path)
            self._write_event(explicit_path)
            stdout = StringIO()
            with patch("sys.stdout", stdout):
                code = main(["--cwd", str(root), "--telemetry-report", str(explicit_path)])
            self.assertEqual(code, 0)
            report = stdout.getvalue()
            self.assertIn("Prompts checked: 1", report)
            self.assertIn(explicit_path.name, report)
            self.assertNotIn(configured_path.name, report)

    def test_telemetry_report_resolves_config_with_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "my-project"
            project.mkdir()
            telemetry_path = project / "project-telemetry.jsonl"
            Path(project, ".prompt-preflight.json").write_text(
                json.dumps({"telemetry": {"enabled": True, "path": "project-telemetry.jsonl"}}),
                encoding="utf-8",
            )
            self._write_event(telemetry_path)
            stdout = StringIO()
            with patch("sys.stdout", stdout):
                code = main(["--cwd", str(project), "--telemetry-report"])
            self.assertEqual(code, 0)
            self.assertIn(str(telemetry_path.resolve()), stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
