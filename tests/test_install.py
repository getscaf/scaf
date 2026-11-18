"""Run the isolated installer tests with: python3 -m unittest discover -s tests -v."""

import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELLS = list(dict.fromkeys(["/bin/bash", "/bin/sh", shutil.which("dash")]))


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="scaf-install-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        (self.root / "tmp").mkdir()
        self.download_log = self.root / "downloads"
        self.env = {
            "HOME": str(self.root),
            "PATH": str(self.bin),
            "PREFERRED_BIN_FOLDER": str(self.bin),
            "TMPDIR": str(self.root / "tmp"),
            "GIT_CONFIG_GLOBAL": str(self.root / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "SCAF_TEST_DOWNLOAD_LOG": str(self.download_log),
            "SCAF_TEST_SOURCE": str(ROOT / "scaf"),
        }
        for command in (
            "chmod",
            "cp",
            "cut",
            "dirname",
            "grep",
            "head",
            "mkdir",
            "mktemp",
            "mv",
            "tr",
            "uname",
        ):
            self.bin.joinpath(command).symlink_to(shutil.which(command))
        for command, version in {
            "bash": "3.2.57",
            "curl": "8.0.0",
            "make": "4.0",
            "python3": "3.6.0",
            "docker": "20.0.0",
            "git": "2.40.0",
            "rsync": "3.2.0",
        }.items():
            self.version(command, version)
        self.command(
            "curl",
            'if [ "$1" = "--version" ]; then\n'
            "    printf '%s\\n' 'curl 8.0.0'\n"
            "    exit 0\n"
            "fi\n"
            'printf \'%s\\n\' "$*" >> "$SCAF_TEST_DOWNLOAD_LOG"\n'
            'while [ "$#" -gt 0 ]; do\n'
            '    if [ "$1" = "-o" ]; then\n'
            '        cp "$SCAF_TEST_SOURCE" "$2"\n'
            "        exit $?\n"
            "    fi\n"
            "    shift\n"
            "done\n"
            "exit 1\n",
        )
        for command in ("kubectl", "kind", "tilt", "uv"):
            self.command(command, "exit 0\n")

    def command(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + body)
        path.chmod(0o755)

    def version(self, name, version):
        self.command(name, "printf '%s\\n' " + shlex.quote(name + " " + version) + "\n")

    def run_installer(self, shell):
        return subprocess.run(
            [shell, str(ROOT / "install.sh")],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def assert_dependency_failure(self, result, records, instructions):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertNotIn("\\n", result.stdout)
        summary = result.stdout.split("Please install", 1)[0].splitlines()
        for record in records:
            self.assertEqual(summary.count(record), 1, result.stdout)
        for instruction in instructions:
            self.assertIn(instruction, result.stdout)
        self.assertFalse(self.download_log.exists(), result.stdout)
        self.assertFalse((self.bin / "scaf").exists())

    def test_accepts_bash_3_2(self):
        for shell in filter(None, SHELLS):
            with self.subTest(shell=shell):
                result = self.run_installer(shell)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertIn("All top-level dependencies are installed", result.stdout)
                self.assertTrue(self.download_log.exists())
                installed = self.bin / "scaf"
                self.assertEqual(installed.read_bytes(), (ROOT / "scaf").read_bytes())
                self.assertTrue(os.access(installed, os.X_OK))
                installed.unlink()
                self.download_log.unlink()

    def test_multiple_missing_commands(self):
        for command in ("bash", "python3"):
            (self.bin / command).unlink()
        for shell in filter(None, SHELLS):
            with self.subTest(shell=shell):
                self.assert_dependency_failure(
                    self.run_installer(shell),
                    ["bash", "python3"],
                    ["brew install bash", "brew install python"],
                )

    def test_multiple_outdated_commands(self):
        self.version("make", "3.7")
        self.version("rsync", "2.6.9")
        for shell in filter(None, SHELLS):
            with self.subTest(shell=shell):
                self.assert_dependency_failure(
                    self.run_installer(shell),
                    ["make>=3.8 but found 3.7", "rsync>=3.2.0 but found 2.6.9"],
                    ["brew install make", "brew install rsync"],
                )

    def test_missing_and_outdated_commands(self):
        (self.bin / "python3").unlink()
        self.version("rsync", "2.6.9")
        for shell in filter(None, SHELLS):
            with self.subTest(shell=shell):
                self.assert_dependency_failure(
                    self.run_installer(shell),
                    ["python3", "rsync>=3.2.0 but found 2.6.9"],
                    ["brew install python", "brew install rsync"],
                )


if __name__ == "__main__":
    unittest.main()
