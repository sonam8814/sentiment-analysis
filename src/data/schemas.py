"""Pydantic models for NPS response data validation."""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class NPSResponseRaw(BaseModel):
    """Schema for a raw NPS response as fetched from Supabase."""

    id: str
    created_at: datetime
    response_date: date
    nps_score: int = Field(ge=0, le=10)
    comment: Optional[str] = None
    customer_id: Optional[str] = None
    segment: Optional[str] = None

    @field_validator("comment", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Optional[str]) -> Optional[str]:
        """Treat empty strings as None."""
        if v is not None and v.strip() == "":
            return None
        return v


class AspectSentiment(BaseModel):
    """A single aspect–sentiment pair from ABSA."""

    aspect: Literal[
        "ui_ux", "pricing", "features", "support", "performance", "onboarding", "other"
    ]
    sentiment: Literal["positive", "neutral", "negative"]
    confidence: float = Field(ge=0.0, le=1.0)


class NPSResponseProcessed(BaseModel):
    """Schema for a fully processed NPS response with derived columns."""

    id: str
    created_at: datetime
    response_date: date
    nps_score: int = Field(ge=0, le=10)
    comment: Optional[str] = None
    customer_id: Optional[str] = None
    segment: Optional[str] = None
    comment_redacted: str = ""
    category: Literal["promoter", "passive", "detractor"]
    aspects: list[AspectSentiment] = Field(default_factory=list)
    overall_sentiment: Literal["positive", "neutral", "negative"] = "neutral"
    is_toxic_promoter: bool = False
    analyzed_at: Optional[datetime] = None
