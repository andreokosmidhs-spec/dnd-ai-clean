import React, { useState } from "react";

import IdentityStep from "../components/CharacterCreationV2/IdentityStep";
import RaceStep from "../components/CharacterCreationV2/RaceStep";
import ClassStep from "../components/CharacterCreationV2/ClassStep";
import AbilityScoresStep from "../components/CharacterCreationV2/AbilityScoresStep";
import BackgroundStep from "../components/CharacterCreationV2/BackgroundStep";
import AppearanceStep from "../components/CharacterCreationV2/AppearanceStep";
import ReviewStep from "../components/CharacterCreationV2/ReviewStep";

const STEPS = [
  "identity",
  "race",
  "class",
  "abilityScores",
  "background",
  "appearance",
  "review",
];

const CharacterCreationV2 = () => {
  const [character, setCharacter] = useState({
    identity: {
      name: "",
      sex: null,
      genderExpression: 50,
    },
    race: {
      key: null,
      variantKey: null,
    },
    class: {
      key: null,
      subclassKey: null,
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
      key: null,
      variantKey: null,
    },
    appearance: {
      ageCategory: null,
      heightCm: null,
      build: null,
      skinTone: "",
      hairColor: "",
      eyeColor: "",
      notableFeatures: [],
    },
  });

  const [stepIndex, setStepIndex] = useState(0);
  const currentStep = STEPS[stepIndex];

  const updateCharacter = (patch) => {
    setCharacter((prev) => ({
      ...prev,
      ...patch,
    }));
  };

  const prev = () => {
    if (stepIndex > 0) {
      setStepIndex(stepIndex - 1);
    }
  };

  const next = () => {
    if (stepIndex < STEPS.length - 1) {
      setStepIndex(stepIndex + 1);
    }
  };

  let stepContent = null;

  switch (currentStep) {
    case "identity":
      stepContent = (
        <IdentityStep
          identity={character.identity}
          onChange={(v) => updateCharacter({ identity: v })}
          onNext={next}
        />
      );
      break;
    case "race":
      stepContent = (
        <RaceStep
          characterData={character}
          updateCharacterData={updateCharacter}
          onBack={prev}
          onNext={next}
        />
      );
      break;
    case "class":
      stepContent = (
        <ClassStep
          characterData={character}
          updateCharacterData={updateCharacter}
          onBack={prev}
          onNext={next}
        />
      );
      break;
    case "abilityScores":
      stepContent = (
        <AbilityScoresStep
          characterData={character}
          updateCharacterData={updateCharacter}
          onBack={prev}
          onNext={next}
        />
      );
      break;
    case "background":
      stepContent = (
        <BackgroundStep
          characterData={character}
          updateCharacterData={updateCharacter}
          onBack={prev}
          onNext={next}
        />
      );
      break;
    case "appearance":
      stepContent = (
        <AppearanceStep
          characterData={character}
          updateCharacterData={updateCharacter}
          onBack={prev}
          onNext={next}
        />
      );
      break;
    case "review":
      stepContent = (
        <ReviewStep
          characterData={character}
          onBack={prev}
        />
      );
      break;
    default:
      stepContent = <div>Unknown step</div>;
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Character Creation V2</h1>
      {stepContent}
    </div>
  );
};

export default CharacterCreationV2;
