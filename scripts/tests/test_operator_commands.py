from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]


class OperatorCommandTests(unittest.TestCase):
    def test_operator_script_has_valid_shell_syntax_and_complete_help(self) -> None:
        subprocess.run(
            ["bash", "-n", "scripts/poc.sh"], cwd=ROOT, check=True
        )
        result = subprocess.run(
            ["bash", "scripts/poc.sh", "help"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        for command in (
            "prerequisites",
            "start",
            "stop",
            "migrate",
            "seed",
            "reset",
            "api",
            "worker",
            "web",
            "health",
            "certify-headless",
            "record-headed",
        ):
            self.assertIn(command, result.stdout)

    def test_make_and_npm_commands_delegate_to_the_operator_contract(self) -> None:
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        package = (ROOT / "package.json").read_text(encoding="utf-8")
        for command in ("start", "stop", "migrate", "seed", "reset", "health"):
            self.assertIn(f"bash scripts/poc.sh {command}", makefile)
        self.assertIn("bash scripts/poc.sh certify-headless", makefile)
        self.assertIn("bash scripts/poc.sh record-headed", makefile)
        self.assertIn("bash scripts/poc.sh start", package)
        self.assertIn("bash scripts/poc.sh reset", package)
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn("${API_PORT:-8000}:8000", compose)
        self.assertIn("${WEB_PORT:-4173}:80", compose)

    def test_reset_orders_worker_quiescence_before_schema_replacement(self) -> None:
        script = (ROOT / "scripts/poc.sh").read_text(encoding="utf-8")
        stop_worker = script.index('"${compose[@]}" stop worker')
        reset_state = script.index("python -m app.manage reset")
        restart_worker = script.index(
            '"${compose[@]}" up --build -d --wait worker', reset_state
        )
        self.assertLess(stop_worker, reset_state)
        self.assertLess(reset_state, restart_worker)
        self.assertIn('api_port="${API_PORT:-8000}"', script)
        self.assertIn('web_port="${WEB_PORT:-4173}"', script)

    def test_runbook_records_the_supported_reset_and_evidence_contract(self) -> None:
        runbook = (ROOT / "docs/operations/poc-runbook.md").read_text(
            encoding="utf-8"
        )
        for evidence in (
            "synthetic",
            "state fingerprint",
            "numbered migrations",
            "make journey11-headless",
            "make journey11-headed",
            "video",
            "trace",
            "screenshots",
            "runtime logs",
        ):
            self.assertIn(evidence, runbook)


if __name__ == "__main__":
    unittest.main()
