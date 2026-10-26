from typing import Optional
from src.rules.base_rule import BaseRule


class ReleaseYearRule(BaseRule):
    rule_id = "REQ-001"
    rule_name = "Release year is present"
    field = "requiredFields"
    severity = "medium"
    applies_to = ["Movie", "Show"]
    standard_reference = "Core Metadata Fields Official Content Standard"

    def evaluate(self, record: dict) -> Optional[dict]:
        year = record.get("releaseYear")
        if year is None or str(year).strip() == "":
            return self._make_issue(
                record.get("tmsId", ""),
                "Release year is missing",
                "Add the release year"
            )

        try:
            y = int(str(year))
            if y < 1888 or y > 2030:
                return self._make_issue(
                    record.get("tmsId", ""),
                    f"Release year {y} is outside plausible range (1888-2030)",
                    "Verify the release year"
                )
        except (ValueError, TypeError):
            return self._make_issue(
                record.get("tmsId", ""),
                f"Release year '{year}' is not a valid integer",
                "Provide release year as a 4-digit number"
            )
        return None


class CountryOfOriginRule(BaseRule):
    rule_id = "REQ-002"
    rule_name = "Country of origin is present"
    field = "requiredFields"
    severity = "medium"
    applies_to = ["Movie", "Show"]
    standard_reference = "Core Metadata Fields Official Content Standard"

    def evaluate(self, record: dict) -> Optional[dict]:
        country = record.get("countryOfOrigin")
        if country is None or str(country).strip() == "":
            return self._make_issue(
                record.get("tmsId", ""),
                "Country of origin is missing",
                "Add the country of origin"
            )
        return None


class OriginalNetworkRule(BaseRule):
    rule_id = "REQ-003"
    rule_name = "Original network is present for Shows"
    field = "requiredFields"
    severity = "medium"
    applies_to = ["Show"]
    standard_reference = "Core Metadata Fields Official Content Standard"

    def evaluate(self, record: dict) -> Optional[dict]:
        network = record.get("originalNetwork")
        if network is None or str(network).strip() == "":
            return self._make_issue(
                record.get("tmsId", ""),
                "Original network is missing for a Show record",
                "Add the original network/platform"
            )
        return None
