# Optional Hook Templates

This folder contains **opt-in** hook templates.

## Include-order check hook (C/C++)

Template: `include-order-check.json`

Activation:
1. Create directory `.github/hooks/` if it does not exist.
2. Copy `include-order-check.json` into `.github/hooks/`.

Behavior after activation:
- Runs `python3 scripts/check_include_order_changed.py` after tool usage.
- Checks only changed C/C++ files in `src/**`.
- Excludes `src/serial/**` and firmware/platformio-related paths.
- Returns non-zero when include-order issues are found (hook can block further flow).
