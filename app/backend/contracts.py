"""Request and response models for the API. Pydantic validates the bounds and returns a 422 with the field name."""
from pydantic import BaseModel, ConfigDict, Field, field_validator

from schema import BOOLEANS, CATEGORICAL


class Importance(BaseModel):
    """How important each job factor is to the person: 1-4 where 4 = very important."""
    model_config = ConfigDict(extra="forbid")

    advancement: int | None = Field(None, ge=1, le=4)
    benefits: int | None = Field(None, ge=1, le=4)
    challenge: int | None = Field(None, ge=1, le=4)
    independence: int | None = Field(None, ge=1, le=4)
    location: int | None = Field(None, ge=1, le=4)
    responsibility: int | None = Field(None, ge=1, le=4)
    salary: int | None = Field(None, ge=1, le=4)
    security: int | None = Field(None, ge=1, le=4)
    society: int | None = Field(None, ge=1, le=4)


class PredictRequest(BaseModel):
    """Only occupation_code is required; anything left out (null) is imputed by the pipeline."""
    model_config = ConfigDict(extra="forbid")

    occupation_code: str
    salary: float | None = Field(None, ge=0, le=100_000_000)
    hours_per_week: float | None = Field(None, ge=1, le=96)
    weeks_per_year: float | None = Field(None, ge=1, le=52)
    tenure_years: float | None = Field(None, ge=0, le=60)
    age: float | None = Field(None, ge=16, le=100)
    employer_size: int | None = Field(None, ge=1, le=8)
    degree_relatedness: int | None = Field(None, ge=1, le=3)
    telework_days: int | None = Field(None, ge=0, le=4)
    sex: str | None = None
    race_ethnicity: str | None = None
    citizenship: str | None = None
    marital_status: str | None = None
    highest_degree: str | None = None
    degree_field: str | None = None
    employer_type: str | None = None
    telework: str | None = None
    offers_health_insurance: bool | None = None
    offers_pension: bool | None = None
    offers_profit_sharing: bool | None = None
    offers_paid_leave: bool | None = None
    expertise_natural_sci_eng: bool | None = None
    expertise_other: bool | None = None
    expertise_social_sci: bool | None = None
    importance: Importance = Field(default_factory=Importance)

    @field_validator(*CATEGORICAL)
    @classmethod
    def _allowed_option(cls, value, info):
        if value is None:
            return value
        allowed = [o["value"] for o in CATEGORICAL[info.field_name][2]]
        if value not in allowed:
            raise ValueError(f"must be one of: {allowed}")
        return value


assert all(name in PredictRequest.model_fields for name in [*CATEGORICAL, *BOOLEANS])


class ModelPrediction(BaseModel):
    probability: float
    threshold: float
    predicted_very_satisfied: bool


class FitPair(BaseModel):
    work_value: str
    person_items: list[str]  # importance ratings averaged into P
    P: float | None  # person importance composite, 1-4 (4 = very important)
    J: float | None  # O*NET Work Value of the occupation
    P_z: float | None  # P and J standardized against the training data
    J_z: float | None
    fit_prod: float | None  # P_z * J_z: high when the person cares and the job delivers
    fit_gap: float | None  # |P_z - J_z|: large when they mismatch


class FitDetail(BaseModel):
    available: bool
    reason: str | None = None
    pairs: list[FitPair]
    unpaired: dict[str, float | None]  # location rating and the Support work value have no counterpart


class PredictResponse(BaseModel):
    occupation: dict
    A1: ModelPrediction
    A2: ModelPrediction
    fit: FitDetail
    notes: list[str]
