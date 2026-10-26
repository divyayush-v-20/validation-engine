from typing import Optional
from datetime import datetime, timedelta
from src.rules.base_rule import BaseRule


class OADFormatRule(BaseRule):
    rule_id = "OAD-001"
    rule_name = "Original Air Date has valid format"
    field = "originalAirDate"
    severity = "high"
    applies_to = ["Show", "Episode"]
    standard_reference = "Original Air Date Official Content Standard"

    def evaluate(self, record: dict) -> Optional[dict]:
        oad = record.get("originalAirDate")
        if oad is None or str(oad).strip() == "":
            return None  # OAD may not be required for all records

        oad_str = str(oad).strip()
        # Try common date formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"]:
            try:
                datetime.strptime(oad_str, fmt)
                return None  # Valid
            except ValueError:
                continue

        return self._make_issue(
            record.get("tmsId", ""),
            f"Original Air Date '{oad_str}' is not a valid date format",
            "Use YYYY-MM-DD format"
        )


class OADFutureDateRule(BaseRule):
    rule_id = "OAD-002"
    rule_name = "Original Air Date is not suspiciously in the future"
    field = "originalAirDate"
    severity = "medium"
    applies_to = ["Show", "Episode"]
    standard_reference = "Original Air Date Official Content Standard"

    def evaluate(self, record: dict) -> Optional[dict]:
        oad = record.get("originalAirDate")
        if not oad:
            return None

        oad_str = str(oad).strip()
        parsed = None
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"]:
            try:
                parsed = datetime.strptime(oad_str, fmt)
                break
            except ValueError:
                continue

        if parsed is None:
            return None  # Format issue handled by OAD-001

        one_year_out = datetime.now() + timedelta(days=365)
        if parsed > one_year_out:
            return self._make_issue(
                record.get("tmsId", ""),
                f"Original Air Date '{oad_str}' is more than 1 year in the future",
                "Verify the date — it may be a data entry error"
            )
        return None
