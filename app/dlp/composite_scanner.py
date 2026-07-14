"""Composite DLP scanner combining keyword and PII pattern detection.

Runs both the Aho-Corasick DFA keyword matcher and the regex-based PII
scanner, merging overlapping matches to produce a unified set of findings.
"""

from __future__ import annotations

from app.dlp.pii_patterns import pii_scanner
from app.dlp.scanner import dlp_scanner


class CompositeDLPScanner:
    """Composite DLP scanner that combines two detection engines.

    1. Aho-Corasick DFA keyword matching  (O(n+m+z) fixed-string scan)
    2. Regex-based PII pattern detection   (SSN, CC, email, API keys, etc.)

    This ensures both policy-violating keywords AND structured PII formats
    are detected and redacted in a single pass through the scanning pipeline.
    """

    def scan(self, text: str) -> list[dict]:
        """Run both scanners and return a unified list of findings.

        Each finding is a dict with: type, value/keyword, start, end.

        Args:
            text: The input text to scan.

        Returns:
            Combined list of findings from both engines.
        """
        # Aho-Corasick keyword hits
        keyword_hits = dlp_scanner.scan(text)
        normalized_keywords = [
            {
                "type": "KEYWORD",
                "value": kw,
                "start": end_idx - len(kw) + 1,
                "end": end_idx + 1,  # exclusive end
            }
            for end_idx, kw in keyword_hits
        ]

        # Regex PII hits
        pii_hits = pii_scanner.scan(text)

        return normalized_keywords + pii_hits

    def redact(
        self, text: str, mask: str = "[REDACTED]"
    ) -> tuple[str, list[dict]]:
        """Scan text with both engines, merge overlapping matches, and redact.

        Args:
            text: The input text to scan and redact.
            mask: The replacement string for matched content.

        Returns:
            A tuple of ``(redacted_text, all_findings)``.
        """
        all_findings = self.scan(text)

        # Sort by start position, then by longest match first for merging
        all_findings.sort(
            key=lambda f: (f["start"], -(f["end"] - f["start"]))
        )

        # Merge overlapping intervals to avoid double-redacting
        merged: list[dict] = []
        for finding in all_findings:
            if merged and finding["start"] < merged[-1]["end"]:
                # Overlapping — extend the previous interval
                merged[-1]["end"] = max(merged[-1]["end"], finding["end"])
                merged[-1]["type"] = (
                    f"{merged[-1]['type']}+{finding['type']}"
                )
            else:
                merged.append({
                    "type": finding["type"],
                    "start": finding["start"],
                    "end": finding["end"],
                })

        # Replace in reverse order to preserve positions
        redacted = text
        for interval in reversed(merged):
            redacted = (
                redacted[:interval["start"]]
                + mask
                + redacted[interval["end"]:]
            )

        return redacted, all_findings

    def is_safe(self, text: str) -> bool:
        """Return True if no keywords or PII patterns are found.

        Args:
            text: The input text to check.
        """
        return not self.scan(text)

    def reload_keywords(self, keywords: list[str]) -> None:
        """Delegate keyword reload to the underlying Aho-Corasick scanner.

        Args:
            keywords: New list of sensitive keywords to load.
        """
        dlp_scanner.reload_keywords(keywords)


composite_scanner = CompositeDLPScanner()
