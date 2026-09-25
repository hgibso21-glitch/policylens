"""Claude Code PostToolUse hook: format and lint-fix a Python file right after the agent edits it.

Claude Code passes the tool call as JSON on stdin. This script never blocks the agent: if the
file is not Python, or ruff is not installed, it does nothing.
"""

import json
import subprocess
import sys


def main() -> None:
    try:
        path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
    except json.JSONDecodeError:
        return
    if not path.endswith(".py"):
        return
    for args in (["format", path], ["check", "--fix", "--quiet", path]):
        try:
            subprocess.run([sys.executable, "-m", "ruff", *args], check=False, capture_output=True)
        except OSError:
            return


if __name__ == "__main__":
    main()
