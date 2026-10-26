from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FieldIssue(BaseModel):
    """A single field-level validation failure."""
    tms_id: str = Field(..., alias="tmsId")
    failed_rule: str = Field(..., alias="failedRule")
    correction_suggestion: Optional[str] = Field(None, alias="correctionSuggestion")
    severity: str = "high"
    rule_family: str = Field("", alias="ruleFamily")
    observed_value: Optional[str] = Field(None, alias="observedValue")
    expected_condition: Optional[str] = Field(None, alias="expectedCondition")

    model_config = {"populate_by_name": True}


class ValidationIssues(BaseModel):
    """Field-wise validation issues. Keys are field names (title, genre, duration, etc.)."""
    title: list[FieldIssue] = []
    genre: list[FieldIssue] = []
    subgenre: list[FieldIssue] = []
    duration: list[FieldIssue] = []
    subtype: list[FieldIssue] = []
    original_air_date: list[FieldIssue] = Field(default=[], alias="originalAirDate")
    audio_language: list[FieldIssue] = Field(default=[], alias="audioLanguage")
    required_fields: list[FieldIssue] = Field(default=[], alias="requiredFields")

    model_config = {"populate_by_name": True}

    def has_issues(self) -> bool:
        return any([
            self.title, self.genre, self.subgenre, self.duration,
            self.subtype, self.original_air_date, self.audio_language,
            self.required_fields
        ])

    def total_issue_count(self) -> int:
        return sum([
            len(self.title), len(self.genre), len(self.subgenre),
            len(self.duration), len(self.subtype), len(self.original_air_date),
            len(self.audio_language), len(self.required_fields)
        ])

    def to_flat_dict(self) -> dict:
        """Convert to dict with only non-empty field lists, using camelCase keys."""
        result = {}
        field_map = {
            "title": self.title,
            "genre": self.genre,
            "subgenre": self.subgenre,
            "duration": self.duration,
            "subtype": self.subtype,
            "originalAirDate": self.original_air_date,
            "audioLanguage": self.audio_language,
            "requiredFields": self.required_fields,
        }
        for key, issues in field_map.items():
            if issues:
                result[key] = [i.model_dump(by_alias=True, exclude_none=True) for i in issues]
        return result


class ProgramValidationResult(BaseModel):
    """Validation result for a single program — stored in the program row."""
    tms_id: str = Field(..., alias="tmsId")
    success: bool
    issues: ValidationIssues = ValidationIssues()
    validated_at: Optional[str] = Field(None, alias="validatedAt")

    model_config = {"populate_by_name": True}


class RecordStatusSuccess(BaseModel):
    """Success section of the batch status row."""
    tms_ids: list[str] = Field(default=[], alias="tmsIds")

    model_config = {"populate_by_name": True}


class RecordStatusFailure(BaseModel):
    """Failure section of the batch status row. Contains totalCount + field-wise issues."""
    total_count: int = Field(default=0, alias="totalCount")
    title: list[dict] = []
    genre: list[dict] = []
    subgenre: list[dict] = []
    duration: list[dict] = []
    subtype: list[dict] = []
    original_air_date: list[dict] = Field(default=[], alias="originalAirDate")
    audio_language: list[dict] = Field(default=[], alias="audioLanguage")
    required_fields: list[dict] = Field(default=[], alias="requiredFields")

    model_config = {"populate_by_name": True}


class RecordStatus(BaseModel):
    """The STATUS row for a batch — aggregated validation results."""
    success: RecordStatusSuccess = RecordStatusSuccess()
    failure: RecordStatusFailure = RecordStatusFailure()

    model_config = {"populate_by_name": True}
