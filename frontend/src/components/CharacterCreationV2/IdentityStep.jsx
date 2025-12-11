import React from "react";
import WizardCard from "./WizardCard";
import { validateIdentity } from "./utils/validation";

const IdentityStep = ({
  wizardState,
  updateSection,
  onNext,
  steps,
  goToStep,
  currentStepIndex,
}) => {
  const identity = wizardState.identity || {};
  const sexValue = identity?.sex === "male" || identity?.sex === "female" ? identity.sex : "";
  const nameValue = identity?.name ?? "";
  const appearanceExpressionValue =
    typeof identity?.genderExpression === "number" ? identity.genderExpression : 50;
  const ageValue = identity?.age === "" ? "" : identity?.age ?? "";

  const handleNameChange = (e) => {
    updateSection("identity", { name: e.target.value });
  };

  const handleAppearanceExpression = (e) => {
    updateSection("identity", { genderExpression: Number(e.target.value) });
  };

  const canContinue = validateIdentity({ ...wizardState, identity: { ...identity, age: ageValue === "" ? null : ageValue } });

  return (
    <WizardCard
      stepTitle="Step 1 – Identity"
      stepNumber={1}
      totalSteps={steps.length}
      steps={steps}
      onSelectStep={goToStep}
      onBack={() => {}}
      backDisabled
      onNext={onNext}
      nextDisabled={!canContinue}
    >
      <div className="space-y-5">
        <div className="space-y-2 flex flex-col items-center">
          <label htmlFor="character-name" className="block text-center text-sm text-slate-300">
            Character Name
          </label>
          <input
            id="character-name"
            type="text"
            value={nameValue}
            onChange={handleNameChange}
            autoCapitalize="words"
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 text-center [text-transform:capitalize] focus:outline-none focus:ring-2 focus:ring-slate-400"
            placeholder="Give your hero a name"
            style={{ textTransform: "capitalize" }}
          />
        </div>

        <div className="space-y-2">
          <label className="block text-center text-sm text-slate-300">Sex</label>
          <div className="flex gap-3">
            {[{ key: "female", label: "♀ Female" }, { key: "male", label: "♂ Male" }].map((option) => {
              const selected = sexValue === option.key;
              return (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => updateSection("identity", { sex: option.key })}
                  className={`flex-1 rounded-full border px-3 py-2 text-sm font-semibold transition-colors ${
                    selected
                      ? "border-slate-400 bg-slate-700 text-slate-100"
                      : "border-slate-700 bg-slate-800 text-slate-200 hover:border-slate-500"
                  }`}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="space-y-2">
          <label htmlFor="character-age" className="block text-center text-sm text-slate-300">
            Age
          </label>
          <input
            id="character-age"
            type="number"
            min="1"
            value={ageValue}
            onChange={(e) => updateSection("identity", { age: e.target.value === "" ? "" : Number(e.target.value) })}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-400"
            placeholder="25"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-center text-sm text-slate-300">Appearance Expression</label>
          <div className="flex items-center justify-center text-sm text-slate-300">
            <span className="font-semibold text-slate-200">{appearanceExpressionValue}</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span>Fem</span>
            <input
              type="range"
              min="0"
              max="100"
              value={appearanceExpressionValue}
              onChange={handleAppearanceExpression}
              className="flex-1 accent-slate-500"
            />
            <span>Masc</span>
          </div>
          <p className="text-center text-xs text-slate-500">How your character looks, not their gender.</p>
        </div>
      </div>
    </WizardCard>
  );
};

export default IdentityStep;
