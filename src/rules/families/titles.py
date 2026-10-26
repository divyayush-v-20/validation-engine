from typing import Optional
from src.rules.base_rule import BaseRule

# Forbidden characters/terms in titles
FORBIDDEN_CHARS = ["™", "®", "©", "\t", "\n"]
FORBIDDEN_TERMS = ["TBD", "TBA", "UNTITLED", "NEW TITLE", "PLACEHOLDER"]
MAX_TITLE_LENGTH = 150  # NEd limit


class TitleRequiredRule(BaseRule):
    rule_id = "TTL-REQ"
    rule_name = "Title must not be blank or missing"
    field = "title"
    severity = "high"
    applies_to = ["Movie", "Show", "Episode"]
    standard_reference = "Titles Official Content Standard"

    def evaluate(self, record: dict) -> Optional[dict]:
        title = record.get("title")
        if title is None or str(title).strip() == "":
            return self._make_issue(
                record.get("tmsId", ""),
                "Title is blank or missing",
                "Provide the official title from the primary source"
            )
        return None


class TitleLengthRule(BaseRule):
    rule_id = "TTL-LEN"
    rule_name = "Title must not exceed NEd length limit"
    field = "title"
    severity = "medium"
    applies_to = ["Movie", "Show", "Episode"]
    standard_reference = "Titles Official Content Standard"

    def evaluate(self, record: dict) -> Optional[dict]:
        title = record.get("title")
        if not title:
            return None  # Handled by TTL-REQ
        if len(str(title)) > MAX_TITLE_LENGTH:
            return self._make_issue(
                record.get("tmsId", ""),
                f"Title exceeds {MAX_TITLE_LENGTH} characters ({len(str(title))} chars)",
                f"Shorten title to {MAX_TITLE_LENGTH} characters or fewer"
            )
        return None


class TitleForbiddenCharsRule(BaseRule):
    rule_id = "TTL-CHR"
    rule_name = "Title contains forbidden characters or terms"
    field = "title"
    severity = "medium"
    applies_to = ["Movie", "Show", "Episode"]
    standard_reference = "Titles Official Content Standard"

    def evaluate(self, record: dict) -> Optional[dict]:
        title = record.get("title")
        if not title:
            return None
        title_str = str(title)

        # Check forbidden characters
        for char in FORBIDDEN_CHARS:
            if char in title_str:
                return self._make_issue(
                    record.get("tmsId", ""),
                    f"Title contains forbidden character: '{char}'",
                    f"Remove '{char}' from the title"
                )

        # Check forbidden terms (case-insensitive)
        upper = title_str.upper().strip()
        for term in FORBIDDEN_TERMS:
            if upper == term or upper.startswith(term + " ") or upper.endswith(" " + term):
                return self._make_issue(
                    record.get("tmsId", ""),
                    f"Title contains placeholder term: '{term}'",
                    "Replace with the official title"
                )

        return None
