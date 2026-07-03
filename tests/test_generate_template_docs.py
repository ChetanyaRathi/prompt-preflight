import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import io

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_template_docs

class TestGenerateTemplateDocs(unittest.TestCase):
    def test_generator_idempotent(self) -> None:
        """Test that generating the docs twice yields identical output."""
        output1 = generate_template_docs.generate_docs()
        output2 = generate_template_docs.generate_docs()
        self.assertEqual(output1, output2)

    def test_all_profiles_documented(self) -> None:
        """Test that all profiles from prompt_templates.json appear in the generated output."""
        output = generate_template_docs.generate_docs()
        profiles = generate_template_docs.load_template_profiles()
        
        for name in profiles.keys():
            self.assertIn(f"- `{name}`", output, f"Profile {name} is missing from the generated list")
            self.assertIn(f"| `{name}` |", output, f"Profile {name} is missing from the generated table")

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_check_mode_passes(self, mock_stdout) -> None:
        """Test that --check exits 0 against the currently committed docs."""
        with patch("sys.argv", ["generate_template_docs.py", "--check"]):
            try:
                exit_code = generate_template_docs.main()
            except SystemExit as e:
                exit_code = e.code
            
            self.assertEqual(exit_code, 0, "TEMPLATES.md is out of sync with prompt_templates.json")

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_check_mode_fails_when_drifted(self, mock_stderr) -> None:
        """Test that --check exits 1 when docs are out of sync."""
        original_read_text = generate_template_docs.DOCS_PATH.read_text()
        
        with patch("pathlib.Path.read_text") as mock_read_text:
            mock_read_text.return_value = original_read_text.replace("| `general` |", "| `general` | modified |")
            with patch("sys.argv", ["generate_template_docs.py", "--check"]):
                try:
                    exit_code = generate_template_docs.main()
                except SystemExit as e:
                    exit_code = e.code
                
                self.assertEqual(exit_code, 1, "Expected --check to fail on mutated docs")
                self.assertIn("out of sync", mock_stderr.getvalue())

if __name__ == "__main__":
    unittest.main()
