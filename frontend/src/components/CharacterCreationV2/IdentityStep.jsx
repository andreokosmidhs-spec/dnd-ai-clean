import React from "react";
import WizardCard from "./WizardCard";

const IdentityStep = ({ identity, onChange, onNext }) => {
  const sexValue =
    identity?.sex === "male" || identity?.sex === "female"
      ? identity.sex
      : "male";
  const nameValue = identity?.name ?? "";
  const genderExpressionValue =
    typeof identity?.genderExpression === "number"
      ? identity.genderExpression
      : 50;
  const ageValue = identity?.age === "" ? "" : identity?.age ?? 25;

  const handleNameChange = (e) => {
    onChange({ name: e.target.value });
  };

  const handleGenderExpression = (e) => {
    onChange({ genderExpression: Number(e.target.value) });
  };

  const canContinue =
    nameValue.trim().length > 0 &&
    (sexValue === "male" || sexValue === "female") &&
    Number(ageValue) > 0;

  // Navigation handlers are passed directly; gating is handled by WizardCard's nextDisabled.
  return (
    <WizardCard
      stepTitle="Step 1 – Identity"
      stepNumber={1}
      totalSteps={7}
      onBack={() => {}}
      backDisabled
      onNext={onNext}
      nextDisabled={!canContinue}
    >
      <div className="space-y-5">
        <div className="space-y-2 flex flex-col items-center">
          <label
            htmlFor="character-name"
            className="block text-center text-sm text-slate-300"
          >
            Character Name
          </label>
          <input
            id="character-name"
            type="text"
            value={nameValue}
            onChange={handleNameChange}
            className="w-full max-w-md rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 text-center capitalize focus:outline-none focus:ring-2 focus:ring-amber-500"
            placeholder="Give your hero a name"
            style={{ textTransform: "capitalize" }}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm text-slate-300">Sex</label>
          <div className="flex gap-3">
            {[
              { key: "female", label: "♀ Female" },
              { key: "male", label: "♂ Male" },
            ].map((option) => {
              const selected = sexValue === option.key;
              return (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => onChange({ sex: option.key })}
                  className={`flex-1 rounded-full border px-3 py-2 text-sm font-semibold transition-colors ${
                    selected
                      ? "border-amber-500 bg-amber-500/20 text-amber-100"
                      : "border-slate-700 bg-slate-800 text-slate-200 hover:border-amber-500/60"
                  }`}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="space-y-2">
          <label
            htmlFor="character-age"
            className="block text-center text-sm text-slate-300"
          >
            Age
          </label>
          <input
            id="character-age"
            type="number"
            min="1"
            value={ageValue}
            onChange={(e) =>
              onChange({ age: e.target.value === "" ? "" : Number(e.target.value) })
            }
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
            placeholder="25"
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm text-slate-300">
            <span>Appearance Expression</span>
            <span className="font-semibold text-slate-200">{genderExpressionValue}</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span>Fem</span>
            <input
              type="range"
              min="0"
              max="100"
              value={genderExpressionValue}
              onChange={handleGenderExpression}
              className="flex-1 accent-slate-500"
            />
            <span>Masc</span>
          </div>
          <p className="text-center text-xs text-slate-500">
            How your character looks, not their gender.
          </p>
        </div>
      </div>
    </WizardCard>
  );
};

export default IdentityStep;
