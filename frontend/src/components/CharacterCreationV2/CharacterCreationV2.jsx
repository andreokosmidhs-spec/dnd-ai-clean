import React, { useState } from "react";
import IdentityStep from "./IdentityStep";

const STEPS = ["identity"]; // We will add race/class later

const CharacterCreationV2 = ({ onCharacterCreated }) => {
  const [stepIndex, setStepIndex] = useState(0);

  // Main state for V2 characters
  const [character, setCharacter] = useState({
    identity: {
      name: "",
      sex: "unspecified",
      genderExpression: 50, // 0 masc — 100 fem
    },
  });

  const currentStepId = STEPS[stepIndex];

  const updateCharacter = (patch) => {
    setCharacter((prev) => ({ ...prev, ...patch }));
  };

  const onNext = () => {
    if (stepIndex < STEPS.length - 1) {
      setStepIndex(stepIndex + 1);
    } else {
      // Last step → send the character to parent (or backend)
      if (onCharacterCreated) {
        onCharacterCreated(character);
      }
    }
  };

  let stepContent = null;
  switch (currentStepId) {
    case "identity":
      stepContent = (
        <IdentityStep
          identity={character.identity}
          onChange={(patch) =>
            updateCharacter({ identity: { ...character.identity, ...patch } })
          }
          onNext={onNext}
        />
      );
      break;
    default:
      stepContent = <div>Unknown step</div>;
  }

  return <div className="p-4">{stepContent}</div>;
};

export default CharacterCreationV2;
