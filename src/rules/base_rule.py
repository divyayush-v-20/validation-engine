from abc import ABC, abstractmethod
from typing import Optional


class BaseRule(ABC):
    """Base class for all validation rules."""

    rule_id: str = ""
    rule_name: str = ""
    field: str = ""  # Which field category this rule checks (title, duration, etc.)
    severity: str = "high"
    applies_to: list[str] = []  # Record types: Movie, Show, Episode, Season, Sport
    standard_reference: str = ""

    def is_applicable(self, record: dict) -> bool:
        """Check if this rule applies to the given record type."""
        if not self.applies_to:
            return True
        record_type = record.get("recordType", "")
        return record_type in self.applies_to

    @abstractmethod
    def evaluate(self, record: dict) -> Optional[dict]:
        """Evaluate the rule against a record.

        Returns None if the record passes.
        Returns a dict with {tmsId, failedRule, correctionSuggestion} if it fails.
        """
        ...

    def _make_issue(self, tms_id: str, message: str, suggestion: str = "") -> dict:
        """Helper to build a standard issue dict."""
        return {
            "tmsId": tms_id,
            "failedRule": f"[{self.rule_id}] {message}",
            "correctionSuggestion": suggestion or "",
        }
