---
name: code_review
description: A skill for performing rigorous code reviews of ROS2, C++, and Python code, ensuring adherence to project standards, SOLID principles, TDD, and specific architectural rules.
---

# Code Review Skill

This skill allows the Antigravity agent to perform standardized, high-quality code reviews. It enforces the project's unique development standards, including the mandatory retention policy for modified code.

## Triggers
- When the user asks for a code review of a file or directory.
- When the user asks to "check" or "audit" their code for quality.
- When a task involves complex code modifications that require a pre-commit review.

## Review Guidelines

### 1. Mandatory Retention Policy
**CRITICAL**: Modified code must NEVER be deleted.
- **Rule**: Comment out the existing code block.
- **Rule**: Insert the new code block directly below it.
- **Verification**: Ensure the original code remains as comments.

### 2. Test-Driven Development (TDD) & Testing
- **GTest/Pytest**: Verify if functional tests exist for the feature or fix. Standard linters are NOT enough.
- **Coverage**: Ensure tests cover logic (e.g., coordinate transforms, mapping math).
- **Verification**: If no functional tests exist, require them before approval.

### 3. Coding Standards (SOLID & ROS 2 Humble)
- **Naming Conventions**:
    - Classes: `PascalCase`.
    - Functions/Variables: `snake_case`.
    - Constants: `SCREAMING_SNAKE_CASE`.
- **Modern C++**: Check for RAII, smart pointers (`std::shared_ptr`, `std::unique_ptr`), and `std::vector` instead of C-arrays.
- **SOLID**: Ensure single responsibility and modularity.

### 4. Logging Standards
- **Standard**: Must use ROS 2 macros (`RCLCPP_INFO`, `RCLCPP_ERROR`, etc.).
- **Payload**: Must embed a JSON-like payload for observability.
- **Format**: `RCLCPP_INFO(logger, "{'id': '...', 'attribute': '...'} Message")`.
- **Rejection**: Reject `std::cout`, `printf`, or ad-hoc strings without structured data.

### 5. ROS2 & Simulation Integrity
- **Compatibility**: Ensure code is compatible with ROS 2 Humble.
- **Middleware**: Check for proper usage of `rclcpp` or `rclpy` interfaces.
- **Simulation**: Verify OGRE1/WSL2 compatibility (avoid heavy GUI operations in real-time loops).

## Automation
The agent should utilize the helper scripts in the `scripts/` folder to automate checks:
- `python3 .agent/skills/code_review/scripts/review_helpers.py --file <path_to_file>`

## Steps for the Agent
1. **Research**: Call `view_file` on the target file(s).
2. **Automated Check**: Run `review_helpers.py` on the file.
3. **Manual Audit**: Read the code carefully against the checklists above.
4. **Report**: Provide a structured markdown report with:
    - ✅ Passes
    - ❌ Violations (Critical/Minor)
    - 💡 Suggestions
