from typing import List, Optional
from pydantic import BaseModel


# -----------------------
#  Ability Scores
# -----------------------
class AbilityScores(BaseModel):
    STR: int
    DEX: int
    CON: int
    INT: int
    WIS: int
    CHA: int


# -----------------------
#  Race Model
# -----------------------
class AppearanceOptions(BaseModel):
    skin_colors: List[str]
    hair_colors: List[str]
    eye_colors: List[str]
    height_range: List[int]     # e.g. [150, 190]
    age_range: List[int]        # adjusted per-race
    can_have_tail: bool = False
    can_have_horns: bool = False
    can_have_wings: bool = False


class RaceModel(BaseModel):
    name: str
    traits: List[str]
    ability_bonuses: dict       # {"DEX": 2, "WIS": 1}
    languages: List[str]
    appearance: AppearanceOptions


# -----------------------
#  Class Model
# -----------------------
class ClassFeature(BaseModel):
    level: int
    name: str
    description: str


class SubclassModel(BaseModel):
    name: str
    level_unlock: int
    features: List[ClassFeature]


class ClassModel(BaseModel):
    name: str
    hit_die: str
    primary_ability: str
    saving_throws: List[str]
    proficiencies: List[str]
    starting_equipment: List[str]
    spells_known: Optional[List[str]] = None
    features: List[ClassFeature]
    subclasses: Optional[List[SubclassModel]] = None


# -----------------------
#  Background Model
# -----------------------
class BackgroundModel(BaseModel):
    name: str
    skill_proficiencies: List[str]
    tool_proficiencies: List[str]
    languages: List[str]
    equipment: List[str]
    personality_traits: List[str]
    ideals: List[str]
    bonds: List[str]
    flaws: List[str]


# -----------------------
#  Appearance Model (final chosen values)
# -----------------------
class Appearance(BaseModel):
    sex: str                    # "male", "female", "other"
    masc_fem_balance: int       # slider 0–100
    skin_color: str
    hair_color: str
    eye_color: str
    height_cm: int
    age: int
    has_tail: bool = False
    has_horns: bool = False
    has_wings: bool = False
    scars: Optional[List[str]] = None
    tattoos: Optional[List[str]] = None


# -----------------------
#  Final Character V2 Model
# -----------------------
class CharacterV2(BaseModel):
    name: str
    race: RaceModel
    char_class: ClassModel
    subclass: Optional[SubclassModel] = None
    background: BackgroundModel
    level: int = 1

    abilities: AbilityScores
    appearance: Appearance

    # For DM + portrait generation
    appearance_tags: List[str] = []
