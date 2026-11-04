import os
from pathlib import Path
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
PROOF = HERE / "skills" / "prune-drift" / "prose_only.py"
FIXTURES = (
    ("deleted comment", "# a past explanation\nvalue = 1\n", "value = 1\n", True, "prose-only"),
    ("deleted docstrings",
     '"""An explanation."""\nclass Box:\n    """A box."""\n    async def read(self):\n'
     '        """Read a value."""\n        return 1\n',
     'class Box:\n    async def read(self):\n        return 1\n', True, "prose-only"),
    ("docstring-only function becomes pass", 'def read():\n    """An explanation."""\n',
     "def read():\n    pass\n", True, "prose-only"),
    ("changed non-docstring literal", 'value = "one"\n', 'value = "two"\n', False, "AST differs"),
    ("changed statement", "value = 1\n", "raise RuntimeError()\n", False, "AST differs"),
    ("pass outside an emptied body", "def read():\n    return 1\n",
     "def read():\n    pass\n    return 1\n", False, "AST differs"),
    ("file no longer parses", "value = 1\n", "def read(:\n", False, "cannot parse"),
    ("own module docstring reader", '"""An explanation."""\nvalue = __doc__\n',
     "value = __doc__\n", False, "module docstring changed"),
    ("deleted shebang", "#!/usr/bin/env python3\nvalue = 1\n", "value = 1\n", False, "directive comments differ"),
    ("shebang moved from line 1 to line 2", "#!/usr/bin/env python3\nvalue = 1\n",
     "# ordinary prose\n#!/usr/bin/env python3\nvalue = 1\n", False, "directive comments differ", True),
    ("shebang moved from line 2 to line 1", "# ordinary prose\n#!/usr/bin/env python3\nvalue = 1\n",
     "#!/usr/bin/env python3\nvalue = 1\n", False, "directive comments differ", True),
    ("BOM removed before shebang", "\ufeff#!/usr/bin/env python3\nvalue = 1\n",
     "#!/usr/bin/env python3\nvalue = 1\n", False, "directive comments differ", True),
    ("inline type ignore moved to own line", "value = (\n    1  # type: ignore\n)\n",
     "value = (\n    1\n    # type: ignore\n)\n", False, "directive comments differ"),
    ("inline noqa moved to own line", "value = (\n    1  # noqa\n)\n",
     "value = (\n    1\n    # noqa\n)\n", False, "directive comments differ"),
    ("ordinary comment deleted from executable", "#!/usr/bin/env python3\n# ordinary prose\nvalue = 1\n",
     "#!/usr/bin/env python3\nvalue = 1\n", True, "prose-only", True),
    ("active shebang LF changed to CRLF", "#!/usr/bin/env python3\nvalue = 1\n",
     "#!/usr/bin/env python3\r\nvalue = 1\n", False, "directive comments differ", True),
    ("active shebang CRLF changed to LF", "#!/usr/bin/env python3\r\nvalue = 1\n",
     "#!/usr/bin/env python3\nvalue = 1\n", False, "directive comments differ", True),
)


def run_checks(results=None):
    if results is None:
        results = []
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                       GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")
    with tempfile.TemporaryDirectory(prefix="prune-drift-") as temporary:
        for index, fixture in enumerate(FIXTURES):
            label, before, after, expected, diagnostic = fixture[:5]
            executable = len(fixture) > 5 and fixture[5]
            root = Path(temporary) / str(index)
            root.mkdir()

            def git(*args, raw=False):
                output = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args],
                                        cwd=root, env=environment, check=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE).stdout
                return output if raw else output.decode("utf-8").strip()

            git("init", "-q")
            git("config", "core.autocrlf", "false")
            path = root / "sample.py"
            path.write_bytes(before.encode("utf-8"))
            if executable:
                path.chmod(0o755)
            git("add", "sample.py")
            if executable:
                git("update-index", "--chmod=+x", "sample.py")
            git("commit", "-qm", "before")
            old_rev = git("rev-parse", "HEAD")
            path.write_bytes(after.encode("utf-8"))
            git("add", "sample.py")
            if executable:
                git("update-index", "--chmod=+x", "sample.py")
            git("commit", "-qm", "after")
            new_rev = git("rev-parse", "HEAD")
            bytes_match = (git("show", old_rev + ":sample.py", raw=True) == before.encode("utf-8")
                           and git("show", new_rev + ":sample.py", raw=True) == after.encode("utf-8"))
            status = git("status", "--porcelain", "--untracked-files=all")
            result = subprocess.run([sys.executable, "-I", str(PROOF), old_rev, new_rev], cwd=root,
                                    env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    encoding="utf-8", errors="replace")
            output = result.stdout + result.stderr
            ok = bytes_match and result.returncode == (0 if expected else 1) and "sample.py: " + diagnostic in result.stdout
            if label == "own module docstring reader":
                ok = ok and "sample.py:2: own __doc__" in result.stdout
            ok = ok and git("status", "--porcelain", "--untracked-files=all") == status
            results.append((label, bool(ok), "committed bytes match: " + str(bytes_match)
                            + "\nexit " + str(result.returncode) + "\n" + output))
    return results


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    checks = run_checks()
    for label, ok, detail in checks:
        print(("  ok    " if ok else "  FAIL  ") + label)
        if not ok:
            print("        " + detail)
    failures = sum(not ok for _, ok, _ in checks)
    print("\n" + ("FAILED: " + str(failures) if failures else "all green"))
    sys.exit(1 if failures else 0)
