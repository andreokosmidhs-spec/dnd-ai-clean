import { CLASS_SKILLS } from "../../data/classSkills";
import { CLASS_SUBCLASSES } from "../../data/classSubclasses";

const isNonEmpty = (value) => typeof value === "string" && value.trim().length > 0;

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
  if (!skillInfo) return true;
  const required = skillInfo.count || 0;
  const selected = Array.isArray(classState.skillProficiencies)
    ? classState.skillProficiencies.length
    : 0;
  return required === selected;
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
