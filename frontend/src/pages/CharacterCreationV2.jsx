import React from "react";
import IdentityStep from "../components/CharacterCreationV2/IdentityStep";
import RaceStep from "../components/CharacterCreationV2/RaceStep";
import ClassStep from "../components/CharacterCreationV2/ClassStep";
import AbilityScoresStep from "../components/CharacterCreationV2/AbilityScoresStep";
import BackgroundStep from "../components/CharacterCreationV2/BackgroundStep";
import AppearanceStep from "../components/CharacterCreationV2/AppearanceStep";
import ReviewStep from "../components/CharacterCreationV2/ReviewStep";
import useWizardState, { WIZARD_STEPS } from "../components/CharacterCreationV2/hooks/useWizardState";

const STEP_COMPONENTS = {
  identity: IdentityStep,
  race: RaceStep,
  class: ClassStep,
  abilityScores: AbilityScoresStep,
  background: BackgroundStep,
  appearance: AppearanceStep,
  review: ReviewStep,
};

const CharacterCreationV2 = () => {
  const { state, updateSection, currentStepIndex, steps, nextStep, prevStep, goToStep } = useWizardState();
  const currentStepId = WIZARD_STEPS[currentStepIndex]?.id;
  const StepComponent = STEP_COMPONENTS[currentStepId];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-10 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-amber-400">Character Creation V2</h1>
          <p className="text-sm text-slate-400">Forge your hero through seven guided steps.</p>
          <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/70 px-4 py-2 text-xs text-slate-300">
            <span className="font-semibold text-amber-300">Step {currentStepIndex + 1}</span>
            <span className="text-slate-500">/ {WIZARD_STEPS.length}</span>
            <span className="text-slate-400">·</span>
            <span className="text-slate-200 capitalize">{currentStepId?.replace(/([A-Z])/g, " $1")}</span>
          </div>
        </div>
        {StepComponent ? (
          <StepComponent
            wizardState={state}
            updateSection={updateSection}
            onNext={nextStep}
            onBack={prevStep}
            steps={steps}
            goToStep={goToStep}
            currentStepIndex={currentStepIndex}
          />
        ) : (
          <div>Unknown step</div>
        )}
      </div>
    </div>
  );
};

export default CharacterCreationV2;
