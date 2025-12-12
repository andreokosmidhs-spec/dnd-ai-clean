import { CLASS_SKILLS } from "../../../data/classSkills";
import { CLASS_SUBCLASSES } from "../../../data/classSubclasses";
import { CLASS_EQUIPMENT } from "../../../data/classEquipment";

const isNonEmpty = (value) => typeof value === "string" && value.trim().length > 0;

const SPELL_REQUIREMENTS = {
  Wizard: { cantrips: 3, level1: 6 },
  Sorcerer: { cantrips: 4, level1: 2 },
  Warlock: { cantrips: 2, level1: 2 },
  Bard: { cantrips: 2, level1: 4 },
  Cleric: { cantrips: 3, level1: 0 },
  Druid: { cantrips: 2, level1: 0 },
};

export const getSpellRequirements = (classKey) => {
  if (!classKey) return { cantrips: 0, level1: 0 };
  return SPELL_REQUIREMENTS[classKey] || { cantrips: 0, level1: 0 };
};

export const validateIdentity = (state) => {
  const identity = state.identity || {};
  const { name, sex, age, genderExpression } = identity;
  const hasName = isNonEmpty(name);
  const validSex = sex === "male" || sex === "female";
  const validAge = typeof age === "number" && age > 0;
  const validExpression =
    typeof genderExpression === "number" &&
    genderExpression >= 0 &&
    genderExpression <= 100;
  return hasName && validSex && validAge && validExpression;
};

export const validateRace = (state) => {
  const race = state.race || {};
  return isNonEmpty(race.key);
};

export const validateClass = (state) => {
  const classState = state.class || {};
  if (!isNonEmpty(classState.key)) return false;
  const subclassInfo = CLASS_SUBCLASSES[classState.key];
  if (subclassInfo && (!classState.subclassKey || classState.subclassKey.trim() === "")) {
    return false;
  }
  const skillInfo = CLASS_SKILLS[classState.key];
  if (skillInfo) {
    const required = skillInfo.count || 0;
    const selected = Array.isArray(classState.skillProficiencies)
      ? classState.skillProficiencies.length
      : 0;
    if (required !== selected) return false;
  }

  const equipmentOptions = CLASS_EQUIPMENT[classState.key];
  if (equipmentOptions) {
    const pack = classState.equipment?.pack;
    if (pack !== "A" && pack !== "B") return false;
  }

  const { cantrips, level1 } = getSpellRequirements(classState.key);
  if (cantrips === 0 && level1 === 0) return true;

  const selectedSpells = state.spells?.selected || { cantrips: [], level1: [] };
  const cantripsOk = (selectedSpells.cantrips || []).length === cantrips;
  const level1Ok = (selectedSpells.level1 || []).length === level1;

  return cantripsOk && level1Ok;
};

const abilityKeys = ["str", "dex", "con", "int", "wis", "cha"];

export const validateAbilityScores = (state) => {
  const scores = state.abilityScores || {};
  const { method } = scores;
  const values = abilityKeys.map((key) => scores[key]);
  if (values.some((v) => v == null || Number.isNaN(v))) return false;

  if (method === "standard_array") {
    const STANDARD_ARRAY = [15, 14, 13, 12, 10, 8];
    const set = new Set(values);
    return set.size === STANDARD_ARRAY.length && values.every((val) => STANDARD_ARRAY.includes(val));
  }

  if (method === "point_buy") {
    const POINT_COST = { 8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9 };
    const within = values.every((val) => val >= 8 && val <= 15);
    const total = values.reduce((sum, val) => sum + (POINT_COST[val] ?? 0), 0);
    return within && total <= 27;
  }

  if (method === "manual") {
    return values.every((val) => val >= 1 && val <= 20);
  }

  return false;
};

export const validateBackground = (state) => {
  const background = state.background || {};
  return isNonEmpty(background.key);
};

export const validateAppearance = (state) => {
  const appearance = state.appearance || {};
  const heightOk = typeof appearance.heightCm === "number" && appearance.heightCm >= 100 && appearance.heightCm <= 250;
  return (
    isNonEmpty(appearance.ageCategory) &&
    isNonEmpty(appearance.build) &&
    heightOk &&
    isNonEmpty(appearance.skinTone) &&
    isNonEmpty(appearance.hairColor) &&
    isNonEmpty(appearance.eyeColor)
  );
};

export const validateReview = (state) => {
  return (
    validateIdentity(state) &&
    validateRace(state) &&
    validateClass(state) &&
    validateAbilityScores(state) &&
    validateBackground(state) &&
    validateAppearance(state)
  );
};

export const getValidationMap = (state) => ({
  identity: validateIdentity(state),
  race: validateRace(state),
  class: validateClass(state),
  abilityScores: validateAbilityScores(state),
  background: validateBackground(state),
  appearance: validateAppearance(state),
  review: validateReview(state),
});
