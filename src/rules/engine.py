from datetime import datetime, timezone
from src.rules.registry import RuleRegistry
import logging

logger = logging.getLogger(__name__)


class ValidationEngine:
    """Runs all applicable rules against a program record."""

    def __init__(self):
        self.registry = RuleRegistry()

    def validate_record(self, record: dict) -> dict:
        """Validate a single program record.

        Returns the per-program validation result:
        {
            "tmsId": "...",
            "success": true/false,
            "issues": {
                "title": [{"tmsId": ..., "failedRule": ..., "correctionSuggestion": ...}],
                "duration": [...],
                ...
            }
        }
        """
        tms_id = record.get("tmsId", "unknown")
        applicable_rules = self.registry.get_applicable_rules(record)

        # Group issues by field
        issues_by_field: dict[str, list[dict]] = {}

        for rule in applicable_rules:
            try:
                issue = rule.evaluate(record)
                if issue is not None:
                    field = rule.field
                    if field not in issues_by_field:
                        issues_by_field[field] = []
                    issues_by_field[field].append(issue)
            except Exception as e:
                logger.error(f"Rule {rule.rule_id} failed on {tms_id}: {e}")

        success = len(issues_by_field) == 0

        return {
            "tmsId": tms_id,
            "success": success,
            "issues": issues_by_field,
            "validatedAt": datetime.now(timezone.utc).isoformat(),
        }

    def validate_batch(self, records: list[dict]) -> list[dict]:
        """Validate a list of records. Returns a list of per-program results."""
        results = []
        for record in records:
            result = self.validate_record(record)
            results.append(result)
        return results
