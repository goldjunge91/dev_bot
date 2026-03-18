#!/usr/bin/env python3
"""Check cpplint-like include order on changed C/C++ files.

Intended use:
- As optional hook command (PostToolUse)
- As manual report command

Scope:
- src/**
- excludes: src/serial/**, firmware/platformio related paths
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


C_SYSTEM_HEADERS = {
    "assert.h",
    "ctype.h",
    "errno.h",
    "fcntl.h",
    "float.h",
    "inttypes.h",
    "limits.h",
    "locale.h",
    "math.h",
    "setjmp.h",
    "signal.h",
    "stdarg.h",
    "stdbool.h",
    "stddef.h",
    "stdint.h",
    "stdio.h",
    "stdlib.h",
    "string.h",
    "strings.h",
    "time.h",
    "unistd.h",
}

CPP_HEADER_RE = re.compile(r"^\s*#\s*include\s*[<\"]([^>\"]+)[>\"].*$")

CPP_EXTS = {".h", ".hpp", ".hh", ".hxx", ".c", ".cc", ".cpp", ".cxx"}
EXCLUDE_PARTS = {"serial", "firmware", ".pio", "platformio"}

# Tool names that typically modify files.
EDIT_TOOL_HINTS = {
    "apply_patch",
    "create_file",
    "edit_notebook_file",
    "vscode_renamesymbol",
    "mcp_pylance_mcp_s_pylanceinvokerefactoring",
}


def run_git(args: list[str]) -> list[str]:
    proc = subprocess.run(["git", *args], check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def changed_files() -> list[Path]:
    unstaged = run_git(["diff", "--name-only", "--diff-filter=ACMR"])
    staged = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    all_files = sorted(set(unstaged + staged))
    return [Path(p) for p in all_files]


def is_target(path: Path) -> bool:
    if path.suffix.lower() not in CPP_EXTS:
        return False
    parts = {p.lower() for p in path.parts}
    if "src" not in parts:
        return False
    if any(part in parts for part in EXCLUDE_PARTS):
        return False
    if not str(path).startswith("src/"):
        return False
    return True


def find_include_block(lines: list[str]) -> tuple[int, int] | None:
    start = -1
    end = -1

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#include"):
            if start == -1:
                start = i
            end = i
            continue

        if start != -1:
            if stripped == "":
                end = i
                continue
            break

        if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
            return None

    if start == -1:
        return None
    return start, end


def include_category(include_target: str, raw_line: str, self_header: str | None) -> int:
    is_system = "<" in raw_line and ">" in raw_line
    if not is_system:
        if self_header and include_target.endswith(self_header):
            return 0
        return 3
    if include_target in C_SYSTEM_HEADERS:
        return 1
    return 2


def would_reorder(path: Path, text: str) -> bool:
    lines = text.splitlines(keepends=True)
    block = find_include_block(lines)
    if not block:
        return False

    start, end = block
    include_lines = [ln for ln in lines[start : end + 1] if ln.strip().startswith("#include")]
    if len(include_lines) < 2:
        return False

    self_header = None
    if path.suffix in {".cpp", ".cc", ".cxx", ".c"}:
        stem = path.stem
        for ext in (".hpp", ".hh", ".hxx", ".h"):
            candidate = stem + ext
            if any(candidate in ln for ln in include_lines):
                self_header = candidate
                break

    parsed = []
    for ln in include_lines:
        match = CPP_HEADER_RE.match(ln)
        if not match:
            return False
        target = match.group(1)
        parsed.append((include_category(target, ln, self_header), target.lower(), ln.rstrip("\n")))

    sorted_parsed = sorted(parsed, key=lambda x: (x[0], x[1]))
    return parsed != sorted_parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Check include order in changed files.")
    parser.add_argument(
        "--hook-mode",
        action="store_true",
        help="Read hook payload from stdin and skip checks for non-edit tools.",
    )
    parser.add_argument(
        "--non-blocking",
        action="store_true",
        help="Always return 0 even if violations are found.",
    )
    args = parser.parse_args()

    if args.hook_mode:
        payload_raw = sys.stdin.read().strip()
        tool_name = ""
        if payload_raw:
            try:
                payload = json.loads(payload_raw)
                # Try common locations for tool name in hook payloads.
                candidates = [
                    payload.get("toolName"),
                    payload.get("tool_name"),
                    payload.get("name"),
                    payload.get("tool", {}).get("name") if isinstance(payload.get("tool"), dict) else None,
                ]
                tool_name = next((str(c).lower() for c in candidates if c), "")
            except json.JSONDecodeError:
                # Do not block chat if payload is malformed.
                return 0

        if tool_name and not any(hint in tool_name for hint in EDIT_TOOL_HINTS):
            print(f"[include-order-check] Skipped for non-edit tool: {tool_name}")
            return 0

    repo_root = Path.cwd()
    files = [p for p in changed_files() if is_target(p)]

    if not files:
        print("[include-order-check] No changed C/C++ files in src/** (excluding serial/firmware/platformio).")
        return 0

    violations: list[Path] = []
    for rel in files:
        abs_path = repo_root / rel
        if not abs_path.exists() or not abs_path.is_file():
            continue
        try:
            content = abs_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if would_reorder(abs_path, content):
            violations.append(rel)

    if not violations:
        print("[include-order-check] Include order looks good for changed files.")
        return 0

    print("[include-order-check] Include-order issues detected:")
    for path in violations:
        print(f"  - {path}")
    print("[include-order-check] Run: python3 scripts/lint_autofix.py --path src --exclude serial")

    if args.non_blocking:
        return 0

    # Non-zero to block when explicitly desired.
    return 2


if __name__ == "__main__":
    sys.exit(main())
