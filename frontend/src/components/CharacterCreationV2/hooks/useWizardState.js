import { useMemo, useState } from "react";
import {
  validateAppearance,
  validateAbilityScores,
  validateBackground,
  validateClass,
  validateIdentity,
  validateRace,
} from "../utils/validation";

export const WIZARD_STEPS = [
  { id: "identity", label: "Identity", title: "Step 1 – Identity" },
  { id: "race", label: "Race", title: "Step 2 – Choose Your Race" },
  { id: "class", label: "Class", title: "Step 3 – Choose Your Class" },
  { id: "abilityScores", label: "Ability Scores", title: "Step 4 – Assign Ability Scores" },
  { id: "background", label: "Background", title: "Step 5 – Choose Your Background" },
  { id: "appearance", label: "Appearance", title: "Step 6 – Define Appearance" },
  { id: "review", label: "Review", title: "Step 7 – Review & Submit" },
];

export const initialWizardState = {
  identity: {
    name: "",
    sex: "",
    age: null,
    appearanceExpression: 50,
  },
  race: {
    key: "",
    variantKey: "",
  },
  class: {
    key: "",
    subclassKey: "",
    level: 1,
    skillProficiencies: [],
  },
  abilityScores: {
    str: null,
    dex: null,
    con: null,
    int: null,
    wis: null,
    cha: null,
    method: "standard_array",
  },
  background: {
    key: "",
    variantKey: "",
  },
  appearance: {
    ageCategory: "",
    heightCm: null,
    build: "",
    skinTone: "",
    hairColor: "",
    eyeColor: "",
    notableFeatures: [],
  },
  review: {},
};

const validationByStep = {
  identity: validateIdentity,
  race: validateRace,
  class: validateClass,
  abilityScores: validateAbilityScores,
  background: validateBackground,
  appearance: validateAppearance,
  review: () => true,
};

const mergePatch = (prevSection, patch) => ({
  ...prevSection,
  ...(typeof patch === "function" ? patch(prevSection) : patch),
});

const maxCompletedIndex = (steps, validations) => {
  let furthest = -1;
  steps.forEach((step, index) => {
    if (validations[step.id]) {
      furthest = index;
    }
  });
  return furthest;
};

const useWizardState = () => {
  const [state, setState] = useState(initialWizardState);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const validations = useMemo(() => {
    const result = {};
    WIZARD_STEPS.forEach((step) => {
      const validator = validationByStep[step.id];
      result[step.id] = validator ? validator(state) : true;
    });
    return result;
  }, [state]);

  const updateState = (patch) => {
    setState((prev) => ({
      ...prev,
      ...(typeof patch === "function" ? patch(prev) : patch),
    }));
  };

  const updateSection = (section, patch) => {
    setState((prev) => ({
      ...prev,
      [section]: mergePatch(prev[section] || {}, patch),
    }));
  };

  const goToStep = (targetIndex) => {
    const safeIndex = Math.max(0, Math.min(WIZARD_STEPS.length - 1, targetIndex));
    const furthestComplete = maxCompletedIndex(WIZARD_STEPS, validations);
    if (safeIndex <= furthestComplete || safeIndex === currentStepIndex) {
      setCurrentStepIndex(safeIndex);
      return;
    }

    if (safeIndex === currentStepIndex + 1 && validations[WIZARD_STEPS[currentStepIndex].id]) {
      setCurrentStepIndex(safeIndex);
    }
  };

  const nextStep = () => {
    const isValid = validations[WIZARD_STEPS[currentStepIndex].id];
    if (!isValid) return;
    setCurrentStepIndex((prev) => Math.min(prev + 1, WIZARD_STEPS.length - 1));
  };

  const prevStep = () => {
    setCurrentStepIndex((prev) => Math.max(prev - 1, 0));
  };

  const stepsWithStatus = WIZARD_STEPS.map((step, index) => {
    const isActive = index === currentStepIndex;
    const isComplete = validations[step.id];
    const furthestComplete = maxCompletedIndex(WIZARD_STEPS, validations);
    const isLocked = index > furthestComplete + 1;
    return {
      ...step,
      isActive,
      isComplete,
      isLocked,
    };
  });

  return {
    state,
    updateState,
    updateSection,
    currentStepIndex,
    currentStep: WIZARD_STEPS[currentStepIndex],
    validations,
    steps: stepsWithStatus,
    nextStep,
    prevStep,
    goToStep,
  };
};

export default useWizardState;
