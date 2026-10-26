from typing import Optional
from src.rules.base_rule import BaseRule

MIN_DURATION = 1
MAX_DURATION = 600  # 10 hours


class DurationParseableRule(BaseRule):
    rule_id = "DUR-001"
    rule_name = "Duration parseable and positive"
    field = "duration"
    severity = "high"
    applies_to = ["Movie", "Show", "Episode"]
    standard_reference = "NEd Fields catalog - Duration"

    def evaluate(self, record: dict) -> Optional[dict]:
        runtime = record.get("runtimeMinutes")
        if runtime is None:
            # Duration not provided — may be checked by required fields rule
            return None

        # Try to parse as a number
        try:
            val = int(float(str(runtime)))
        except (ValueError, TypeError):
            return self._make_issue(
                record.get("tmsId", ""),
                f"Runtime is not parseable as a number: '{runtime}'",
                "Provide runtime as a positive integer in minutes"
            )

        if val <= 0:
            return self._make_issue(
                record.get("tmsId", ""),
                f"Runtime is not a positive value: {val}",
                "Provide a positive runtime in minutes"
            )

        return None


class DurationPlausibilityRule(BaseRule):
    rule_id = "DUR-003"
    rule_name = "Runtime within plausibility bounds"
    field = "duration"
    severity = "medium"
    applies_to = ["Movie", "Show", "Episode"]
    standard_reference = "NEd Fields catalog - Duration"

    def evaluate(self, record: dict) -> Optional[dict]:
        runtime = record.get("runtimeMinutes")
        if runtime is None:
            return None

        try:
            val = int(float(str(runtime)))
        except (ValueError, TypeError):
            return None  # Handled by DUR-001

        if val <= 0:
            return None  # Handled by DUR-001

        if val < MIN_DURATION or val > MAX_DURATION:
            return self._make_issue(
                record.get("tmsId", ""),
                f"Runtime {val} min is outside plausible range ({MIN_DURATION}-{MAX_DURATION} min)",
                f"Verify the runtime and ensure it falls within {MIN_DURATION}-{MAX_DURATION} minutes"
            )

        return None
