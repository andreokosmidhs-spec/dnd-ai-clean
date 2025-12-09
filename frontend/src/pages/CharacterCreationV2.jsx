import React, { useState } from "react";

// Steps
import IdentityStep from "../components/CharacterCreationV2/IdentityStep";

// API
import { createCharacterV2 } from "../api/characterV2Api";

// Steps list
const STEPS = ["identity"]; 
// Later we add: race, class, background, stats, appearance, review

const CharacterCreationV2 = () => {
    // master character state (V2 schema)
    const [character, setCharacter] = useState({
        identity: {
            name: "",
            sex: null,                     // "male" | "female" | "other"
            genderExpression: 50,          // 0 = masculine, 100 = feminine
        },
    });

    const [stepIndex, setStepIndex] = useState(0);
    const currentStep = STEPS[stepIndex];

    // Called by each step to update a specific nested section
    const updateCharacter = (patch) => {
        setCharacter((prev) => ({
            ...prev,
            ...patch,
        }));
    };

    const next = async () => {
        // More steps coming soon
        if (stepIndex < STEPS.length - 1) {
            setStepIndex(stepIndex + 1);
        } else {
            console.log("Submitting character:", character);
            await createCharacterV2(character);
            alert("Character created!");
        }
    };

    // Render the correct step
    let stepContent = null;

    switch (currentStep) {
        case "identity":
        default:
            stepContent = (
                <IdentityStep
                    value={character.identity}
                    onChange={(v) => updateCharacter({ identity: v })}
                    onNext={next}
                />
            );
            break;
    }

    return (
        <div className="p-6 max-w-3xl mx-auto">
            <h1 className="text-3xl font-bold mb-4">Character Creation V2</h1>
            {stepContent}
        </div>
    );
};

export default CharacterCreationV2;
