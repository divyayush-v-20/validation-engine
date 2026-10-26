from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class RecordType(str, Enum):
    MOVIE = "Movie"
    SHOW = "Show"
    SEASON = "Season"
    EPISODE = "Episode"
    SPORT = "Sport"


class ProgramRecord(BaseModel):
    """A single program record as stored in DynamoDB."""
    tms_id: str = Field(..., alias="tmsId")
    record_type: RecordType = Field(..., alias="recordType")
    title: Optional[str] = None
    original_title: Optional[str] = Field(None, alias="originalTitle")
    runtime_minutes: Optional[Any] = Field(None, alias="runtimeMinutes")
    subtype: Optional[str] = None
    original_air_date: Optional[str] = Field(None, alias="originalAirDate")
    original_audio_language: Optional[str] = Field(None, alias="originalAudioLanguage")
    genre: Optional[str] = None
    subgenre: Optional[str] = None
    season_number: Optional[Any] = Field(None, alias="seasonNumber")
    episode_number: Optional[Any] = Field(None, alias="episodeNumber")
    parent_series_id: Optional[str] = Field(None, alias="parentSeriesId")
    parent_season_id: Optional[str] = Field(None, alias="parentSeasonId")
    release_year: Optional[int] = Field(None, alias="releaseYear")
    country_of_origin: Optional[str] = Field(None, alias="countryOfOrigin")
    original_network: Optional[str] = Field(None, alias="originalNetwork")
    market: Optional[str] = None
    description: Optional[str] = None

    model_config = {"populate_by_name": True}
