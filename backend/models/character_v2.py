from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


class Identity(BaseModel):
    name: str
    sex: Literal["male", "female"]
    genderExpression: int = Field(ge=0, le=100)
    age: int = Field(gt=0)


class RaceInfo(BaseModel):
    key: str
    variantKey: Optional[str] = None


class ClassInfo(BaseModel):
    key: str
    subclassKey: Optional[str] = None
    level: int = Field(default=1, ge=1)
    skillProficiencies: List[str] = Field(default_factory=list)


class AbilityScores(BaseModel):
    str_: int = Field(alias="str", ge=1, le=30)
    dex: int = Field(ge=1, le=30)
    con: int = Field(ge=1, le=30)
    int_: int = Field(alias="int", ge=1, le=30)
    wis: int = Field(ge=1, le=30)
    cha: int = Field(ge=1, le=30)
    method: str = "standard_array"

    # allow using "str"/"int" when constructing from dicts
    model_config = ConfigDict(populate_by_name=True)


class BackgroundInfo(BaseModel):
    key: str
    variantKey: Optional[str] = None


class AppearanceInfo(BaseModel):
    ageCategory: str
    heightCm: int
    build: str
    skinTone: Optional[str] = None
    hairColor: Optional[str] = None
    eyeColor: Optional[str] = None
    notableFeatures: List[str] = Field(default_factory=list)


class MetaInfo(BaseModel):
    version: int = 2
    createdAt: datetime = Field(default_factory=datetime.utcnow)


class CharacterV2Base(BaseModel):
    identity: Identity
    race: RaceInfo
    class_: ClassInfo = Field(alias="class")
    abilityScores: AbilityScores
    background: BackgroundInfo
    appearance: AppearanceInfo
    meta: MetaInfo = Field(default_factory=MetaInfo)

    # allow aliases like "class" and "str" when constructing from dicts
    model_config = ConfigDict(populate_by_name=True)


class CharacterV2Create(CharacterV2Base):
    pass


class CharacterV2Stored(CharacterV2Base):
    id: str
