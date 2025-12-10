import React from "react";
import { raceData } from "../../data/raceData";
import WizardCard from "./WizardCard";

const RaceStep = ({ characterData, updateCharacterData, onNext, onBack }) => {
  const currentRace = characterData.race || { key: null, variantKey: null };
  const selectedRace = currentRace.key ? raceData[currentRace.key] : null;
  const subraceOptions = selectedRace?.subraces
    ? Object.keys(selectedRace.subraces)
    : [];

  const handleRaceChange = (e) => {
    const newKey = e.target.value || null;
    updateCharacterData({ race: { key: newKey, variantKey: null } });
  };

  const handleSubraceChange = (e) => {
    const newVariant = e.target.value || null;
    updateCharacterData({ race: { ...currentRace, variantKey: newVariant } });
  };

  const canContinue = Boolean(currentRace.key);

  return (
    <WizardCard
      stepTitle="Step 2 – Choose Your Race"
      stepNumber={2}
      totalSteps={7}
      onBack={onBack}
      onNext={onNext}
      nextDisabled={!canContinue}
    >
      <div className="space-y-5">
        <div className="space-y-2">
          <label className="block text-sm text-slate-300">Race</label>
          <select
            value={currentRace.key || ""}
            onChange={handleRaceChange}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="" disabled>
              Select a race
            </option>
            {Object.keys(raceData).map((raceKey) => (
              <option key={raceKey} value={raceKey}>
                {raceData[raceKey].name || raceKey}
              </option>
            ))}
          </select>
        </div>

        {subraceOptions.length > 0 && (
          <div className="space-y-2">
            <label className="block text-sm text-slate-300">Subrace</label>
            <select
              value={currentRace.variantKey || ""}
              onChange={handleSubraceChange}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <option value="">Select a subrace (optional)</option>
              {subraceOptions.map((variant) => (
                <option key={variant} value={variant}>
                  {selectedRace.subraces[variant].name || variant}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
          <h3 className="text-lg font-semibold text-amber-300 mb-1">
            {selectedRace ? selectedRace.name : "Race Details"}
          </h3>
          {selectedRace ? (
            <div className="space-y-2 text-sm text-slate-200">
              {selectedRace.asi?.length ? (
                <p className="text-slate-300">
                  <span className="text-slate-400">Ability Increases:</span> {" "}
                  {selectedRace.asi.map((a) => `${a.ability}+${a.value}`).join(", ")}
                </p>
              ) : null}
              <ul className="list-disc list-inside space-y-1">
                {(selectedRace.traits || []).slice(0, 3).map((trait) => (
                  <li key={trait.name}>
                    <span className="font-semibold text-slate-100">{trait.name}:</span>{" "}
                    <span className="text-slate-300">{trait.summary}</span>
                  </li>
                ))}
                {(!selectedRace.traits || selectedRace.traits.length === 0) && (
                  <li className="text-slate-500">Traits not listed.</li>
                )}
              </ul>
              {selectedRace.flavor && (
                <p className="text-slate-400 text-xs">{selectedRace.flavor}</p>
              )}
            </div>
          ) : (
            <p className="text-sm text-slate-400">Select a race to view its traits and bonuses.</p>
          )}
        </div>
      </div>
    </WizardCard>
  );
};

export default RaceStep;
