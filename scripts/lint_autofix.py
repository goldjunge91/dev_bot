#!/usr/bin/env python3
"""Apply safe, repeatable lint autofixes for this ROS2 workspace.

Targets:
- cpplint header guards / #endif comments
- cpplint include order (self header, C system, C++ system, other)
- pep257 first-line punctuation and blank line after summary

Scope:
- Only scans under a selected root (default: src/)
- Excludes path fragments by default: serial, firmware, .pio, platformio
"""

from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


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
IFNDEF_RE = re.compile(r"^\s*#\s*ifndef\s+([A-Za-z0-9_]+)\s*$")
DEFINE_RE = re.compile(r"^\s*#\s*define\s+([A-Za-z0-9_]+)\s*$")
ENDIF_RE = re.compile(r"^\s*#\s*endif\b.*$")


@dataclass
class FixStats:
    files_changed: int = 0
    header_guard_fixes: int = 0
    include_order_fixes: int = 0
    python_docstring_fixes: int = 0


def sanitize_macro_part(part: str) -> str:
    part = re.sub(r"[^A-Za-z0-9]", "_", part)
    part = re.sub(r"_+", "_", part).strip("_")
    return part.upper()


def expected_header_guard(path: Path, src_root: Path) -> str:
    rel = path.resolve().relative_to(src_root.resolve())
    parts = list(rel.parts)

    if "include" in parts:
        include_idx = parts.index("include")
        if include_idx + 1 < len(parts):
            parts = parts[include_idx + 1 :]
        else:
            parts = [path.name]
    else:
        parts = [path.name]

    macro_parts = [sanitize_macro_part(p) for p in parts if sanitize_macro_part(p)]
    return "__".join(macro_parts) + "_"


def find_include_block(lines: list[str]) -> tuple[int, int] | None:
    start = -1
    end = -1
    seen_include = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#include"):
            if start == -1:
                start = i
            end = i
            seen_include = True
            continue

        if start != -1:
            if stripped == "":
                end = i
                continue
            break

        if seen_include:
            break

        if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
            # Stop scanning if real code appears before include block.
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


def reorder_include_block(path: Path, original: str) -> tuple[str, bool]:
    lines = original.splitlines(keepends=True)
    block = find_include_block(lines)
    if not block:
        return original, False

    start, end = block
    include_lines: list[str] = []
    for i in range(start, end + 1):
        if lines[i].strip().startswith("#include"):
            include_lines.append(lines[i])

    if len(include_lines) < 2:
        return original, False

    self_header = None
    if path.suffix in {".cpp", ".cc", ".cxx"}:
        stem = path.stem
        for ext in (".hpp", ".hh", ".hxx", ".h"):
            self_header = stem + ext
            if any(self_header in ln for ln in include_lines):
                break

    parsed: list[tuple[int, str, str]] = []
    for ln in include_lines:
        match = CPP_HEADER_RE.match(ln)
        if not match:
            continue
        target = match.group(1)
        category = include_category(target, ln, self_header)
        parsed.append((category, target.lower(), ln.rstrip("\n")))

    if len(parsed) != len(include_lines):
        return original, False

    parsed.sort(key=lambda x: (x[0], x[1]))

    rebuilt: list[str] = []
    previous_category = None
    for category, _, raw in parsed:
        if previous_category is not None and category != previous_category:
            rebuilt.append("")
        rebuilt.append(raw)
        previous_category = category

    new_block = "\n".join(rebuilt) + "\n"
    old_block = "".join(lines[start : end + 1])
    if new_block == old_block:
        return original, False

    new_lines = lines[:start] + [new_block] + lines[end + 1 :]
    return "".join(new_lines), True


def fix_header_guard(path: Path, src_root: Path, original: str) -> tuple[str, bool]:
    if path.suffix not in {".h", ".hpp", ".hh", ".hxx"}:
        return original, False

    lines = original.splitlines(keepends=True)
    if not lines:
        return original, False

    expected = expected_header_guard(path, src_root)

    ifndef_idx = define_idx = None
    for i in range(min(60, len(lines))):
        if ifndef_idx is None and IFNDEF_RE.match(lines[i]):
            ifndef_idx = i
            continue
        if ifndef_idx is not None and define_idx is None and DEFINE_RE.match(lines[i]):
            define_idx = i
            break

    endif_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if ENDIF_RE.match(lines[i]):
            endif_idx = i
            break

    if ifndef_idx is None or define_idx is None or endif_idx is None:
        return original, False

    changed = False
    if lines[ifndef_idx].strip() != f"#ifndef {expected}":
        lines[ifndef_idx] = f"#ifndef {expected}\n"
        changed = True

    if lines[define_idx].strip() != f"#define {expected}":
        lines[define_idx] = f"#define {expected}\n"
        changed = True

    desired_endif = f"#endif  // {expected}"
    if lines[endif_idx].strip() != desired_endif:
        lines[endif_idx] = desired_endif + "\n"
        changed = True

    if not changed:
        return original, False
    return "".join(lines), True


def build_docstring_block(indent: str, text: str) -> str:
    """Build a minimally changed docstring block (safe-only behavior)."""

    lines = text.splitlines()
    if not lines:
        return f'{indent}"""."""'

    summary = lines[0].rstrip()
    if summary and summary[-1] not in ".?!":
        summary += "."

    body = lines[1:]
    has_body = any(ln.strip() for ln in body)

    if not has_body:
        return f'{indent}"""{summary}"""'

    # Keep body text and indentation semantics intact as much as possible.
    # Only enforce one blank line between summary and description.
    normalized_body = body[:]
    while normalized_body and normalized_body[0].strip() == "":
        normalized_body.pop(0)

    output = [f'{indent}"""{summary}', ""]
    output.extend(normalized_body)
    output.append(f'{indent}"""')
    return "\n".join(output)


def fix_python_docstrings(path: Path, original: str) -> tuple[str, bool]:
    try:
        tree = ast.parse(original)
    except SyntaxError:
        return original, False

    lines = original.splitlines()
    edits: list[tuple[int, int, str]] = []

    def process_docstring_node(node: ast.AST) -> None:
        body = getattr(node, "body", None)
        if not body:
            return
        first = body[0]
        if not isinstance(first, ast.Expr):
            return
        value = first.value
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            return
        if first.lineno is None or first.end_lineno is None:
            return

        start = first.lineno - 1
        end = first.end_lineno - 1
        if start < 0 or end >= len(lines):
            return

        doc_text = value.value
        indent_match = re.match(r"^(\s*)", lines[start])
        indent = indent_match.group(1) if indent_match else ""

        replacement = build_docstring_block(indent, doc_text)
        original_block = "\n".join(lines[start : end + 1])
        if replacement != original_block:
            edits.append((start, end, replacement))

    process_docstring_node(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            process_docstring_node(node)

    if not edits:
        return original, False

    edits.sort(key=lambda x: x[0], reverse=True)
    mutable = lines[:]
    for start, end, replacement in edits:
        mutable[start : end + 1] = replacement.split("\n")

    new_text = "\n".join(mutable)
    if original.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, True


def is_excluded(path: Path, excludes: set[str]) -> bool:
    normalized_parts = {p.lower() for p in path.parts}
    for token in excludes:
        token = token.strip().lower()
        if not token:
            continue
        if token in normalized_parts:
            return True
    return False


def iter_files(root: Path, excludes: set[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {"build", "install", "log", ".git", "__pycache__"} for part in path.parts):
            continue
        if is_excluded(path, excludes):
            continue
        yield path


def apply_fixes(src_root: Path, apply: bool, excludes: set[str]) -> FixStats:
    stats = FixStats()

    for path in iter_files(src_root, excludes):
        if path.suffix not in {".h", ".hpp", ".hh", ".hxx", ".cpp", ".cc", ".cxx", ".py"}:
            continue

        original = path.read_text(encoding="utf-8")
        updated = original
        changed_file = False

        if path.suffix in {".h", ".hpp", ".hh", ".hxx"}:
            updated2, changed = fix_header_guard(path, src_root, updated)
            if changed:
                stats.header_guard_fixes += 1
                updated = updated2
                changed_file = True

        if path.suffix in {".h", ".hpp", ".hh", ".hxx", ".cpp", ".cc", ".cxx"}:
            updated2, changed = reorder_include_block(path, updated)
            if changed:
                stats.include_order_fixes += 1
                updated = updated2
                changed_file = True

        if path.suffix == ".py":
            updated2, changed = fix_python_docstrings(path, updated)
            if changed:
                stats.python_docstring_fixes += 1
                updated = updated2
                changed_file = True

        if changed_file:
            stats.files_changed += 1
            if apply:
                path.write_text(updated, encoding="utf-8")
            print(f"[lint_autofix] {'updated' if apply else 'would update'}: {path}")

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply deterministic lint autofixes.")
    parser.add_argument("--path", default="src", help="Root path to scan (default: src)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Dry run. Report files that would change without writing.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=["serial", "firmware", ".pio", "platformio"],
        help="Path fragment to exclude (can be provided multiple times).",
    )
    args = parser.parse_args()

    src_root = Path(args.path).resolve()
    if not src_root.exists() or not src_root.is_dir():
        print(f"[lint_autofix] ERROR: path does not exist or is not a directory: {src_root}")
        return 2

    excludes = {item.strip() for item in args.exclude if item.strip()}
    stats = apply_fixes(src_root, apply=not args.check, excludes=excludes)

    print("\n[lint_autofix] Summary")
    print(f"  files changed:          {stats.files_changed}")
    print(f"  header guard fixes:     {stats.header_guard_fixes}")
    print(f"  include order fixes:    {stats.include_order_fixes}")
    print(f"  python docstring fixes: {stats.python_docstring_fixes}")
    print(f"  excluded fragments:     {', '.join(sorted(excludes)) if excludes else '-'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
