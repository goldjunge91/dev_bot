import argparse
import re
import os
import sys


def check_logging(content, file_path):
    violations = []
    # Match ad-hoc logging or print statements
    ad_hoc_log_patterns = [
        (r"std::cout\s*<<", "Use RCLCPP_* macros instead of std::cout"),
        (r"printf\(", "Use RCLCPP_* macros instead of printf"),
        (r"print\(", "Use get_logger() instead of print in Python"),
    ]

    # Filter out commented-out lines before searching
    active_lines = [
        line
        for line in content.splitlines()
        if not line.strip().startswith(("//", "#"))
    ]
    active_content = "\n".join(active_lines)

    # Check for ROS 2 logging macros
    patterns = []
    if file_path.endswith((".cpp", ".hpp", ".h")):
        patterns = [r"RCLCPP_[A-Z]+\("]
    elif file_path.endswith(".py"):
        patterns = [r"self\.get_logger\(\)\.\w+\("]

    for pattern in patterns:
        for match in re.finditer(pattern, content):
            start = match.start()
            # Find matching parenthesis
            count = 1
            idx = match.end()
            while idx < len(content) and count > 0:
                if content[idx] == "(":
                    count += 1
                elif content[idx] == ")":
                    count -= 1
                idx += 1
            macro = content[start:idx]
            # Flexible check for mandatory {'id': '...'} payload
            if not re.search(r'\{[\'"]id[\'"]: [\'"].*?[\'"]', macro):
                if file_path.endswith(".py"):
                    violations.append(
                        f"[LOGGING] Missing structured payload. Expected: self.get_logger().info(\"{{'id': '...'}} message\")"
                    )
                else:
                    violations.append(
                        f"[LOGGING] Missing structured payload. Expected: RCLCPP_INFO(logger, \"{{'id': '...'}} message\")"
                    )

    return violations


def check_naming(content, file_path):
    violations = []
    # Strip comments to avoid false positives
    content_no_comments = re.sub(r"//.*|/\*.*?\*/|#.*", "", content, flags=re.DOTALL)
    # Strip strings to avoid false positives (but keep the raw string markers for better parsing)
    content_clean = re.sub(r'["\'].*?["\']', '""', content_no_comments, flags=re.DOTALL)

    # Simplified PascalCase check for classes in C++
    if file_path.endswith((".cpp", ".hpp", ".h")):
        classes = re.findall(r"class\s+(\w+)", content_clean)
        for cls in classes:
            if not re.match(r"^[A-Z][a-zA-Z0-9]*$", cls):
                violations.append(f"[NAMING] Class '{cls}' should be PascalCase")

    # Simplified snake_case check for functions (very basic)
    # This avoids common ROS 2 methods like on_init
    # Matches words followed by whitespace and ( but NOT common keywords or macros
    functions = re.findall(r"\w+\s+(\w+)\s*\(", content_clean)
    for func in functions:
        if func in [
            "main",
            "if",
            "while",
            "for",
            "switch",
            "EXPECT_EQ",
            "EXPECT_TRUE",
            "TEST_F",
            "TEST",
        ]:
            continue
        if func.isupper():
            continue  # Skip macros like RCLCPP_INFO
        if not re.match(r"^[a-z][a-z0-9_]*$", func):
            # Allow some common ROS 2 PascalCase-like names if necessary (e.g. SetUp in GTest)
            if func == "SetUp":
                continue
            violations.append(f"[NAMING] Function '{func}' should be snake_case")

    return violations


def check_retention(content):
    violations = []
    # Very basic check: look for blocks of code where no comments exist
    # A more advanced check would compare diffs, but as a script, we look for
    # the presence of commented-out code blocks if substantial changes are present.
    # For now, we'll just flag a warning if no comments are found in a file > 50 lines.
    lines = content.splitlines()
    if len(lines) > 50:
        comment_count = sum(
            1
            for line in lines
            if line.strip().startswith("//") or line.strip().startswith("#")
        )
        if comment_count < 2:
            violations.append(
                "[RETENTION] No commented-out code found. Ensure original code is retained per policy."
            )
    return violations


def main():
    parser = argparse.ArgumentParser(description="Code Review Helper Script")
    parser.add_argument("--file", required=True, help="File to review")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        sys.exit(1)

    with open(args.file, "r") as f:
        content = f.read()

    all_violations = []
    all_violations.extend(check_logging(content, args.file))
    all_violations.extend(check_naming(content, args.file))
    all_violations.extend(check_retention(content))

    if all_violations:
        print("--- Violations Found ---")
        for v in all_violations:
            print(v)
    else:
        print("No automated violations detected.")


if __name__ == "__main__":
    main()
