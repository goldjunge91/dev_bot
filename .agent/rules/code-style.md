---
trigger: always_on
---

# Development Standards & Behavioral Rules
**Description**: Core constraints for TDD, code modification, and architectural integrity.
**Activation**: Always On

## 1. Test-Driven Development (TDD)
- **Validation First**: Always use a TDD approach. Do not assume solutions are correct.
- **Verification Loop**: Before implementing a fix or feature, create a test case that fails (proving the bug/gap) and run it. 
- **Proof of Work**: Only consider a task complete once the test case passes and proves the solution works as intended.

## 2. Knowledge & Research
- **Fresh Context**: Assume internal world knowledge is outdated. 
- **Tool Usage**: Use the `web_search` tool to find the most recent documentation, API changes, and industry best practices before proceeding with implementation.

## 3. Code Modification & Lifecycle
- **No Implicit Backwards Compatibility**: Do not maintain backwards compatibility unless specifically requested; update all downstream consumers immediately when breaking changes occur.
- **Retention Policy**: Commented-out code must never be removed without express approval from the user.
- **Change Workflow**: 
    1. Comment out the existing code block.
    2. Insert the new code block directly below it.
    3. The commented-out code remains until explicit approval for removal is given.

## 4. Coding Guidelines & ROS 2 Standards
- **Naming Conventions**:
    - **Classes/Types**: `PascalCase` (e.g., `NerfSystem`).
    - **Functions/Variables**: `snake_case` (e.g., `on_init`, `baud_rate_`).
    - **Constants/Macros**: `SCREAMING_SNAKE_CASE` (e.g., `BAUD_RATE_DEFAULT`).
    - **Files**: `snake_case` (e.g., `nerf_system.cpp`).
- **SOLID Principles**: Adhere to Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion.
- **DRY & KISS**: Avoid logic duplication and over-engineering. Maintain simplicity in design.
- **Modern C++ (ROS 2 Humble)**:
    - Use **RAII** (Resource Acquisition Is Initialization).
    - Use smart pointers (`std::shared_ptr`, `std::unique_ptr`) instead of raw pointers.
    - Prefer C++ standard library containers over C-style arrays.
- **Error Handling & Logging**:
    - Implement robust error handling (exceptions or `CallbackReturn`).
    - Use **ROS 2 Logging Macros** (`RCLCPP_INFO`, `RCLCPP_ERROR`, etc.) for system integration.
    - **Payload Format**: Embed structured data (JSON-like) within the message for observability.
    - **Example**: `RCLCPP_INFO(logger, "{'id': 'status_check', 'attribute': 'ok'} Message text")`.

## 5. Verification & Testing
- **Functional Validation**: Every feature or fix MUST have a corresponding functional test.
    - **C++**: Use `gtest` (Google Test) integrated via `ament_cmake_gtest`.
    - **Python**: Use `pytest` integrated via `ament_add_pytest_test`.
- **Linters**: Adhere to `ament_lint_common` (flake8, cppcheck, cpplint, pep257).

## 5. References & Context
- Use `@filename` to reference specific project documentation or context files within this rule if necessary.