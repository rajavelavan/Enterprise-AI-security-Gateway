"""Aho-Corasick based DLP keyword scanner.

Builds a Deterministic Finite Automaton (DFA) resembling a prefix tree
with failure links for safe state-machine transitions. Guarantees
O(n + m + z) search time complexity for multi-pattern keyword matching.
"""

from __future__ import annotations

from typing import Optional

import ahocorasick

from app.core.config import settings


class DLPScanner:
    """Aho-Corasick based DLP keyword scanner.

    Builds a Deterministic Finite Automaton (DFA) resembling a prefix tree
    with failure links for safe state-machine transitions. Guarantees
    O(n + m + z) search time complexity where:
        n = length of input text
        m = total length of all keywords
        z = number of matches found
    """

    def __init__(self) -> None:
        self.automaton = ahocorasick.Automaton()
        self._build_automaton()

    def _build_automaton(
        self, keywords: Optional[list[str]] = None
    ) -> None:
        """Construct the Aho-Corasick automaton from the keyword list.

        Keywords are normalized to lowercase for case-insensitive matching.
        Calling ``make_automaton()`` internally builds failure links to allow
        the state machine to transition safely without backtracking.

        Args:
            keywords: Optional override list; defaults to configured keywords.
        """
        keywords = keywords or settings.SENSITIVE_KEYWORDS
        self.automaton = ahocorasick.Automaton()
        for idx, keyword in enumerate(keywords):
            self.automaton.add_word(keyword.lower(), (idx, keyword))

        # Build the automaton — this constructs the DFA with failure links
        # enabling O(n + m + z) multi-pattern search in a single pass
        self.automaton.make_automaton()

    def scan(self, text: str) -> list[tuple[int, str]]:
        """Scan the input text for sensitive keywords (case-insensitive).

        Args:
            text: The input text to scan.

        Returns:
            A list of tuples containing ``(end_index, keyword)`` found.
        """
        results = []
        for end_index, (_idx, original_value) in self.automaton.iter(text.lower()):
            results.append((end_index, original_value))
        return results

    def is_safe(self, text: str) -> bool:
        """Return True if no sensitive keywords are found, False otherwise.

        Args:
            text: The input text to check.
        """
        for _ in self.automaton.iter(text.lower()):
            return False
        return True

    def redact(
        self, text: str, mask: str = "[REDACTED]"
    ) -> tuple[str, list[dict]]:
        """Scan the input text and replace every matched keyword with *mask*.

        Search against lowered text but replace in the original text.
        Positions are identical because ``.lower()`` preserves string length
        for ASCII characters. Matches are processed in reverse order so
        that replacements do not shift the indices of earlier matches.

        Args:
            text: The input text to scan and redact.
            mask: The replacement string for matched keywords.

        Returns:
            A tuple of ``(redacted_text, list_of_findings)``.
        """
        findings: list[dict] = []
        matches: list[tuple[int, int, str]] = []

        for end_index, (_idx, keyword) in self.automaton.iter(text.lower()):
            start_index = end_index - len(keyword) + 1
            matches.append((start_index, end_index, keyword))
            findings.append({
                "type": "KEYWORD",
                "keyword": keyword,
                "start": start_index,
                "end": end_index + 1,  # exclusive end for consistency
                "original_snippet": text[max(0, start_index - 10):end_index + 11],
            })

        # Sort by start index descending so replacements don't shift positions
        matches.sort(key=lambda m: m[0], reverse=True)

        redacted = text
        for start, end, _keyword in matches:
            redacted = redacted[:start] + mask + redacted[end + 1:]

        return redacted, findings

    def reload_keywords(self, keywords: list[str]) -> None:
        """Hot-reload the keyword dictionary without server restart.

        Args:
            keywords: New list of sensitive keywords.
        """
        self._build_automaton(keywords)


dlp_scanner = DLPScanner()
