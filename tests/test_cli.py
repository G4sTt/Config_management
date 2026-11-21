"""Exercise CLI configuration, errors and both output streams."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        """Launch the real entry point from an unrelated directory."""
        return subprocess.run(
            [sys.executable, "-B", str(PROJECT / "src/main.py"),
             *map(str, args)],
            cwd=PROJECT.parent, capture_output=True, text=True, timeout=15,
        )

    def test_dot_and_ascii_are_separate(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "space here" / "graph.dot"
            result = self.run_cli(
                "--config", PROJECT / "configs/simple.ini", "--output", output
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout.startswith("digraph"))
            self.assertIn("+-- B", result.stderr)
            self.assertEqual(output.read_text(), result.stdout)

    def test_config_stage_and_reverse(self):
        result = self.run_cli(
            "--config", PROJECT / "configs/simple.ini", "--stage", "config"
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("max_depth=3", result.stdout)
        result = self.run_cli(
            "--config", PROJECT / "configs/reverse.ini", "--stage", "reverse"
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('"B" -> "A";', result.stdout)

    def test_bad_file_and_config_overwrite(self):
        result = self.run_cli("--config", PROJECT / "configs/missing.ini")
        self.assertEqual(result.returncode, 2)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.ini"
            source = (PROJECT / "configs/itoa.ini").read_text()
            path.write_text(source)
            result = self.run_cli(
                "--config", path, "--stage", "config", "--output", path
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(path.read_text(), source)


if __name__ == "__main__":
    unittest.main()
