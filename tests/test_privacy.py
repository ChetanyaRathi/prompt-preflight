from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from prompt_preflight.analyzer import analyze_prompt, redact_sensitive


class PrivacyTests(unittest.TestCase):
    def test_redacts_private_key(self) -> None:
        prompt = "Here is my key: -----BEGIN RSA PR" + "IVATE KEY-----\nMIICXA" + "IBAAKBgQCqGKukO1\n-----END RSA P" + "RIVATE KEY----- please don't share."
        result = analyze_prompt(prompt)
        self.assertTrue(result.should_clarify)
        self.assertIn("[REDACTED_SECRET]", result.redacted_prompt)
        self.assertNotIn("MIICXA" + "IBAAKBgQCqGKukO1", result.redacted_prompt)

    def test_redacts_stripe_key(self) -> None:
        prompt = "my key is sk_li" + "ve_ABCDEF0123" + "456789ABCDEF01"
        result = analyze_prompt(prompt)
        self.assertTrue(result.should_clarify)
        self.assertIn("my key is [REDACTED_SECRET]", result.redacted_prompt)

    def test_redacts_twilio_token(self) -> None:
        prompt = "Twilio AC12345" + "67890abcdef123" + "4567890abcdef"
        result = analyze_prompt(prompt)
        self.assertTrue(result.should_clarify)
        self.assertIn("Twilio [REDACTED_SECRET]", result.redacted_prompt)

    def test_redacts_azure_token(self) -> None:
        prompt = "AccountName=devstoreaccount1;Account" + "Key=Eby8vdM02xNOcqFl" + "qUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
        result = analyze_prompt(prompt)
        self.assertTrue(result.should_clarify)
        self.assertIn("AccountKey=[REDACTED_SECRET]", result.redacted_prompt)

    def test_redacts_npm_token(self) -> None:
        prompt = "npm" + "_aBcDeFgHiJk" + "LmNoPqRsTuVwXyZ1234567890"
        result = analyze_prompt(prompt)
        self.assertTrue(result.should_clarify)
        self.assertIn("[REDACTED_SECRET]", result.redacted_prompt)

    def test_redacts_docker_hub_pat(self) -> None:
        prompt = "dckr" + "_pat_aBcDeF" + "gHiJkLmNoPqRsTuVwXyZ"
        result = analyze_prompt(prompt)
        self.assertTrue(result.should_clarify)
        self.assertIn("[REDACTED_SECRET]", result.redacted_prompt)

    def test_redacts_vercel_netlify_token(self) -> None:
        prompt = "VERCEL_" + "TOKEN=ABCD" + "EF123456"
        result = analyze_prompt(prompt)
        self.assertTrue(result.should_clarify)
        self.assertIn("VERCEL_TOKEN=[REDACTED_SECRET]", result.redacted_prompt)

    def test_redacts_database_url_password(self) -> None:
        prompt = "postgr" + "es://user:p4ssw0" + "rd123@localhost:5432/db"
        result = analyze_prompt(prompt)
        self.assertTrue(result.should_clarify)
        self.assertEqual("postgr" + "es://user:[REDACTED_SECRET]@localhost:5432/db", result.redacted_prompt)

    def test_redacts_jwt(self) -> None:
        prompt = "eyJhbG" + "ciOiJIUzI1NiIsInR5cCI.eyJz" + "dWIiOiIxMjM0NTY3ODkwIiwibmFtZ.SflKxw" + "RJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = analyze_prompt(prompt)
        self.assertTrue(result.should_clarify)
        self.assertIn("[REDACTED_SECRET]", result.redacted_prompt)

    def test_redacts_pasted_env_block(self) -> None:
        prompt = "SOME_KEY=123\nAPI_SE" + "CRET=my_super_sec" + "ret_value\nOTHER=456"
        result = analyze_prompt(prompt)
        self.assertTrue(result.should_clarify)
        self.assertIn("API_SECRET=[REDACTED_SECRET]", result.redacted_prompt)

    def test_false_positive_aws_example(self) -> None:
        prompt = "Use AKIAIOSFODNN7EXAMPLE for tests"
        result = analyze_prompt(prompt)
        self.assertFalse(result.should_clarify)

    def test_false_positive_placeholder(self) -> None:
        prompt = "my password is changeme"
        result = analyze_prompt(prompt)
        self.assertFalse(result.should_clarify)

    def test_false_positive_db_url_placeholder(self) -> None:
        prompt = "postgres://user:password@localhost/db"
        result = analyze_prompt(prompt)
        self.assertFalse(result.should_clarify)
        self.assertNotIn("[REDACTED_SECRET]", redact_sensitive(prompt))

    def test_false_positive_template_ref(self) -> None:
        prompt = "MY_SECRET=${DB_PASS}"
        result = analyze_prompt(prompt)
        self.assertFalse(result.should_clarify)

    def test_skip_does_not_bypass(self) -> None:
        prompt = "my key is sk_li" + "ve_ABCDEF0123" + "456789ABCDEF01 [preflight:skip]"
        result = analyze_prompt(prompt)
        self.assertTrue(result.should_clarify)
        self.assertFalse(result.bypassed)

if __name__ == "__main__":
    unittest.main()
