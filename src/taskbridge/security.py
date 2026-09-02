from __future__ import annotations

import re


INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.I),
    re.compile(r"reveal\s+(the\s+)?(system|developer)\s+prompt", re.I),
    re.compile(r"override\s+(the\s+)?(policy|rules?|guardrails?)", re.I),
    re.compile(r"execute\s+(this\s+)?(tool|command|code)", re.I),
    re.compile(r"send\s+.*(secret|credential|password)", re.I),
    re.compile(r"<\s*(system|developer|assistant)\s*>", re.I),
)


class UntrustedInstructionError(ValueError):
    """Raised when supplied workflow text attempts to control the processor."""


def find_untrusted_instruction(text: str) -> str | None:
    normalized = " ".join(text.split())
    for pattern in INJECTION_PATTERNS:
        if match := pattern.search(normalized):
            return match.group(0)
    return None


def assert_safe_text(*values: str) -> None:
    for value in values:
        if match := find_untrusted_instruction(value):
            raise UntrustedInstructionError(
                f"Untrusted instruction detected and quarantined: {match!r}"
            )
