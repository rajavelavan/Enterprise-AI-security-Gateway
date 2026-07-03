import ahocorasick
from app.core.config import settings
from typing import List, Tuple

class DLPScanner:
    def __init__(self):
        self.automaton = ahocorasick.Automaton()
        self._build_automaton()

    def _build_automaton(self):
        # Add keywords to the automaton
        for idx, keyword in enumerate(settings.SENSITIVE_KEYWORDS):
            self.automaton.add_word(keyword, (idx, keyword))
        
        # Build the Aho-Corasick automaton
        # This allows for O(n+m+z) search time complexity
        self.automaton.make_automaton()

    def scan(self, text: str) -> List[Tuple[int, str]]:
        """
        Scans the input text for sensitive keywords.
        Returns a list of tuples containing (end_index, keyword) found.
        """
        results = []
        for end_index, (idx, original_value) in self.automaton.iter(text):
            results.append((end_index, original_value))
        return results

    def is_safe(self, text: str) -> bool:
        """
        Returns True if no sensitive keywords are found, False otherwise.
        """
        for _ in self.automaton.iter(text):
            return False
        return True

dlp_scanner = DLPScanner()
