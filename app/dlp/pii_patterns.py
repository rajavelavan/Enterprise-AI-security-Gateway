"""Regex-based PII pattern scanner for structured sensitive data.

Complements the Aho-Corasick keyword scanner by detecting structured
PII formats (SSNs, credit card numbers, emails, API keys, etc.) that
cannot be matched with fixed strings.
"""

from __future__ import annotations

import re
from typing import Optional


# Compiled regex patterns for real-world PII detection.
# Each pattern is designed to catch actual sensitive data formats,
# not just keyword strings.
PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "SSN": re.compile(
        r"\b\d{3}-\d{2}-\d{4}\b"
    ),
    "CREDIT_CARD": re.compile(
        r"\b(?:"
        r"4[0-9]{12}(?:[0-9]{3})?"       # Visa
        r"|5[1-5][0-9]{14}"               # MasterCard
        r"|3[47][0-9]{13}"                # American Express
        r"|6(?:011|5[0-9]{2})[0-9]{12}"   # Discover
        r")\b"
    ),
    "EMAIL": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    "AWS_ACCESS_KEY": re.compile(
        r"\bAKIA[0-9A-Z]{16}\b"
    ),
    "OPENAI_API_KEY": re.compile(
        r"\bsk-[A-Za-z0-9]{20,}\b"
    ),
    "PHONE_US": re.compile(
        r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    ),
    "IP_ADDRESS": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
    ),
    "PRIVATE_KEY_HEADER": re.compile(
        r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----"
    ),
}


class PIIScanner:
    """Regex-based PII pattern scanner.

    Complements the Aho-Corasick keyword scanner by detecting
    structured PII formats (SSNs, credit card numbers, emails,
    API keys, etc.) that cannot be matched with fixed strings.
    """

    def __init__(
        self, patterns: Optional[dict[str, re.Pattern[str]]] = None
    ) -> None:
        self.patterns = patterns or PII_PATTERNS

    def scan(self, text: str) -> list[dict]:
        """Scan text against all PII regex patterns.

        Args:
            text: The input text to scan.

        Returns:
            A list of finding dicts with type, value, start, end.
        """
        findings: list[dict] = []
        for label, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                findings.append({
                    "type": label,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })
        return findings

    def redact(
        self, text: str, mask: str = "[REDACTED]"
    ) -> tuple[str, list[dict]]:
        """Scan and redact all PII patterns from text.

        Args:
            text: The input text to scan and redact.
            mask: The replacement string for matched patterns.

        Returns:
            A tuple of ``(redacted_text, list_of_findings)``.
        """
        findings = self.scan(text)
        # Sort by start position descending to avoid index shifting
        findings.sort(key=lambda f: f["start"], reverse=True)
        redacted = text
        for finding in findings:
            redacted = (
                redacted[:finding["start"]]
                + mask
                + redacted[finding["end"]:]
            )
        return redacted, findings

    def is_safe(self, text: str) -> bool:
        """Return True if no PII patterns are found.

        Args:
            text: The input text to check.
        """
        for _label, pattern in self.patterns.items():
            if pattern.search(text):
                return False
        return True


pii_scanner = PIIScanner()
