from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Identity(BaseModel):
    name: str
    sex: Literal["male", "female"]
    genderExpression: int = Field(ge=0, le=100)
    age: int = Field(gt=0)


class RaceInfo(BaseModel):
    key: Optional[str] = None
    variantKey: Optional[str] = None


class ClassInfo(BaseModel):
    key: Optional[str] = None
    subclassKey: Optional[str] = None
    level: int = Field(default=1, ge=1)


class AbilityScores(BaseModel):
    str: Optional[int] = None
    dex: Optional[int] = None
    con: Optional[int] = None
    int: Optional[int] = None
    wis: Optional[int] = None
    cha: Optional[int] = None
    method: str = "standard_array"


class BackgroundInfo(BaseModel):
    key: Optional[str] = None
    variantKey: Optional[str] = None


class AppearanceInfo(BaseModel):
    ageCategory: Optional[str] = None
    heightCm: Optional[int] = None
    build: Optional[str] = None
    skinTone: Optional[str] = None
    hairColor: Optional[str] = None
    eyeColor: Optional[str] = None
    notableFeatures: List[str] = Field(default_factory=list)


class MetaInfo(BaseModel):
    version: int = 2
    createdAt: Optional[datetime]


class CharacterV2Base(BaseModel):
    identity: Identity
    race: RaceInfo
    class_: ClassInfo = Field(alias="class")
    abilityScores: AbilityScores
    background: BackgroundInfo
    appearance: AppearanceInfo
    meta: MetaInfo

    class Config:
        allow_population_by_field_name = True


class CharacterV2Create(CharacterV2Base):
    pass


class CharacterV2Stored(CharacterV2Base):
    id: str

