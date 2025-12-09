import React from "react";
import { raceData } from "../../data/raceData";

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
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-lg text-slate-100">
      <h2 className="text-2xl font-bold text-amber-400 mb-4">Step 2 – Choose Your Race</h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm text-slate-300 mb-1">Race</label>
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
                {raceKey}
              </option>
            ))}
          </select>
        </div>

        {subraceOptions.length > 0 && (
          <div>
            <label className="block text-sm text-slate-300 mb-1">Subrace</label>
            <select
              value={currentRace.variantKey || ""}
              onChange={handleSubraceChange}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <option value="">Select a subrace (optional)</option>
              {subraceOptions.map((variant) => (
                <option key={variant} value={variant}>
                  {variant}
                </option>
              ))}
            </select>
          </div>
        )}

        {selectedRace && (
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <h3 className="text-lg font-semibold text-amber-300 mb-2">
              {selectedRace.name}
            </h3>
            <ul className="list-disc list-inside text-sm text-slate-300 space-y-1">
              {(selectedRace.traits || []).slice(0, 3).map((trait) => (
                <li key={trait.name}>
                  <span className="font-semibold text-slate-100">{trait.name}:</span>{" "}
                  <span className="text-slate-300">{trait.summary}</span>
                </li>
              ))}
              {!selectedRace.traits && (
                <li className="text-slate-400">No traits listed.</li>
              )}
            </ul>
          </div>
        )}
      </div>

      <div className="mt-6 flex items-center justify-between">
        <button
          type="button"
          onClick={onBack}
          className="px-4 py-2 rounded-lg border border-slate-700 text-slate-200 hover:bg-slate-800"
        >
          Back
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!canContinue}
          className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
            canContinue
              ? "bg-amber-500 text-black hover:bg-amber-400"
              : "bg-slate-700 text-slate-400 cursor-not-allowed"
          }`}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default RaceStep;
