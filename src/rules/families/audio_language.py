from typing import Optional
from src.rules.base_rule import BaseRule

# ISO 639-1/639-2 common language codes
CONTROLLED_LANGUAGES = {
    "en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh", "hi", "ar",
    "ru", "nl", "sv", "no", "da", "fi", "pl", "tr", "th", "vi", "id",
    "ms", "tl", "he", "el", "cs", "hu", "ro", "bg", "uk", "hr", "sk",
    "sl", "sr", "lt", "lv", "et", "ca", "gl", "eu", "cy", "ga", "sq",
    "mk", "bs", "mt", "is", "sw", "af", "zu", "xh", "am", "ta", "te",
    "kn", "ml", "mr", "bn", "gu", "pa", "ur", "ne", "si", "my", "km",
    "lo", "ka", "hy", "az", "uz", "kk", "ky", "tg", "mn",
    # Full names also accepted
    "English", "Spanish", "French", "German", "Italian", "Portuguese",
    "Japanese", "Korean", "Chinese", "Hindi", "Arabic", "Russian",
    "Dutch", "Swedish", "Norwegian", "Danish", "Finnish", "Polish",
    "Turkish", "Thai", "Vietnamese",
}

DISALLOWED_VALUES = {"Unknown", "UNK", "unknown", "unk", "N/A", "n/a", "NA", ""}


class AudioLanguageControlledRule(BaseRule):
    rule_id = "AUD-001"
    rule_name = "Audio language is a controlled value"
    field = "audioLanguage"
    severity = "high"
    applies_to = ["Movie", "Show", "Episode"]
    standard_reference = "Original Audio Language Official Content Standard"

    def evaluate(self, record: dict) -> Optional[dict]:
        lang = record.get("originalAudioLanguage")
        if lang is None:
            return None  # May not be required

        lang_str = str(lang).strip()
        if lang_str == "":
            return None

        if lang_str not in CONTROLLED_LANGUAGES and lang_str.lower() not in {ll.lower() for ll in CONTROLLED_LANGUAGES}:
            return self._make_issue(
                record.get("tmsId", ""),
                f"Audio language '{lang_str}' is not in the controlled language list",
                "Use a valid ISO 639 language code or full language name"
            )
        return None


class AudioLanguageUnknownRule(BaseRule):
    rule_id = "AUD-002"
    rule_name = "Unknown/UNK audio language flagged"
    field = "audioLanguage"
    severity = "medium"
    applies_to = ["Movie", "Show", "Episode"]
    standard_reference = "Original Audio Language Official Content Standard"

    def evaluate(self, record: dict) -> Optional[dict]:
        lang = record.get("originalAudioLanguage")
        if lang is None:
            return None

        if str(lang).strip() in DISALLOWED_VALUES:
            return self._make_issue(
                record.get("tmsId", ""),
                f"Audio language is set to '{lang}' which is not acceptable",
                "Research and provide the actual original audio language"
            )
        return None
