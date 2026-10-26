from typing import Optional
from src.rules.base_rule import BaseRule

VALID_SUBTYPES = {
    "Movie": ["Feature Film", "Short Film", "TV Movie", "Direct-to-Video", "Documentary"],
    "Show": ["Series", "Miniseries", "Special", "News", "Talk Show", "Reality", "Documentary", "Anthology"],
    "Sport": ["Live Event", "Highlights", "Magazine", "Documentary"],
}


class SubtypeRequiredRule(BaseRule):
    rule_id = "SUB-001"
    rule_name = "Subtype present when required"
    field = "subtype"
    severity = "high"
    applies_to = ["Movie", "Show", "Sport"]
    standard_reference = "Subtype Official Content Standard"

    def evaluate(self, record: dict) -> Optional[dict]:
        subtype = record.get("subtype")
        if subtype is None or str(subtype).strip() == "":
            return self._make_issue(
                record.get("tmsId", ""),
                "Subtype is required but missing",
                f"Set a valid subtype for this {record.get('recordType', 'record')}"
            )
        return None


class SubtypeValidValueRule(BaseRule):
    rule_id = "SUB-002"
    rule_name = "Subtype is a valid controlled value"
    field = "subtype"
    severity = "high"
    applies_to = ["Movie", "Show", "Sport"]
    standard_reference = "Subtype Official Content Standard"

    def evaluate(self, record: dict) -> Optional[dict]:
        subtype = record.get("subtype")
        if not subtype or str(subtype).strip() == "":
            return None  # Handled by SUB-001

        record_type = record.get("recordType", "")
        valid = VALID_SUBTYPES.get(record_type, [])

        if not valid:
            return None  # No controlled list for this type

        if str(subtype).strip() not in valid:
            return self._make_issue(
                record.get("tmsId", ""),
                f"Subtype '{subtype}' is not valid for {record_type}. Valid values: {', '.join(valid)}",
                f"Use one of: {', '.join(valid)}"
            )
        return None
