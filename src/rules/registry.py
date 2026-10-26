from typing import Optional
from src.rules.base_rule import BaseRule

# Import all rule families
from src.rules.families.titles import TitleRequiredRule, TitleLengthRule, TitleForbiddenCharsRule
from src.rules.families.duration import DurationParseableRule, DurationPlausibilityRule
from src.rules.families.subtype import SubtypeRequiredRule, SubtypeValidValueRule
from src.rules.families.oad import OADFormatRule, OADFutureDateRule
from src.rules.families.audio_language import AudioLanguageControlledRule, AudioLanguageUnknownRule
from src.rules.families.required_fields import ReleaseYearRule, CountryOfOriginRule, OriginalNetworkRule


class RuleRegistry:
    """Registry of all validation rules."""

    def __init__(self):
        self._rules: list[BaseRule] = []
        self._register_all()

    def _register_all(self):
        """Register all P0 rule families."""
        self._rules = [
            # Titles
            TitleRequiredRule(),
            TitleLengthRule(),
            TitleForbiddenCharsRule(),
            # Duration
            DurationParseableRule(),
            DurationPlausibilityRule(),
            # Subtype
            SubtypeRequiredRule(),
            SubtypeValidValueRule(),
            # Original Air Date
            OADFormatRule(),
            OADFutureDateRule(),
            # Audio Language
            AudioLanguageControlledRule(),
            AudioLanguageUnknownRule(),
            # Required Fields
            ReleaseYearRule(),
            CountryOfOriginRule(),
            OriginalNetworkRule(),
        ]

    def get_applicable_rules(self, record: dict) -> list[BaseRule]:
        """Return all rules that apply to the given record."""
        return [r for r in self._rules if r.is_applicable(record)]

    def get_rules_by_field(self, field: str) -> list[BaseRule]:
        return [r for r in self._rules if r.field == field]

    def get_rule_by_id(self, rule_id: str) -> Optional[BaseRule]:
        for r in self._rules:
            if r.rule_id == rule_id:
                return r
        return None

    @property
    def all_rules(self) -> list[BaseRule]:
        return list(self._rules)
