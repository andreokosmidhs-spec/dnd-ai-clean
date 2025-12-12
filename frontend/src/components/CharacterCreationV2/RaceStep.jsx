import React from "react";
import { raceData } from "../../data/raceData";
import WizardCard from "./WizardCard";
import { validateRace } from "./utils/validation";

const RaceStep = ({ wizardState, updateSection, onNext, onBack, steps, goToStep }) => {
  const currentRace = wizardState.race || { key: null, variantKey: null };
  const selectedRace = currentRace.key ? raceData[currentRace.key] : null;
  const subraceOptions = selectedRace?.subraces ? Object.keys(selectedRace.subraces) : [];
  const selectedSubrace =
    selectedRace && currentRace.variantKey ? selectedRace.subraces?.[currentRace.variantKey] : null;

  const combinedTraits = React.useMemo(() => {
    if (!selectedRace) return [];

    const traitMap = new Map();

    (selectedRace.traits || []).forEach((trait) => {
      if (trait?.name) {
        traitMap.set(trait.name, trait);
      }
    });

    (selectedSubrace?.traits || []).forEach((trait) => {
      if (trait?.name && !traitMap.has(trait.name)) {
        traitMap.set(trait.name, trait);
      }
    });

    return Array.from(traitMap.values());
  }, [selectedRace, selectedSubrace]);

  const hasDarkvision = combinedTraits.some((trait) =>
    trait?.name?.toLowerCase().includes("darkvision")
  );
  const hasResistance = combinedTraits.some(
    (trait) =>
      trait?.name?.toLowerCase().includes("resistance") ||
      trait?.mechanical_effect?.toLowerCase().includes("resistance")
  );
  const languageCount = Array.isArray(selectedRace?.languages)
    ? selectedRace.languages.length
    : null;

  const handleRaceChange = (e) => {
    const newKey = e.target.value || "";
    updateSection("race", { key: newKey, variantKey: "" });
  };

  const handleSubraceChange = (e) => {
    const newVariant = e.target.value || "";
    updateSection("race", { ...currentRace, variantKey: newVariant });
  };

  const canContinue = validateRace(wizardState);

  return (
    <WizardCard
      stepTitle="Step 2 – Choose Your Race"
      stepNumber={2}
      totalSteps={steps.length}
      steps={steps}
      onSelectStep={goToStep}
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
            <div className="space-y-3 text-sm text-slate-200">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                {selectedRace.asi?.length ? (
                  <span className="rounded-full bg-slate-800 px-3 py-1 text-amber-200 border border-slate-700">
                    Ability Increases: {selectedRace.asi.map((a) => `${a.ability}+${a.value}`).join(", ")}
                  </span>
                ) : null}
                {hasDarkvision && (
                  <span className="rounded-full bg-slate-800 px-2 py-1 text-blue-200 border border-slate-700">Darkvision</span>
                )}
                {hasResistance && (
                  <span className="rounded-full bg-slate-800 px-2 py-1 text-green-200 border border-slate-700">Resistance</span>
                )}
                {languageCount !== null && (
                  <span className="rounded-full bg-slate-800 px-2 py-1 text-purple-200 border border-slate-700">
                    Languages: {languageCount}
                  </span>
                )}
              </div>

              {selectedSubrace && (
                <p className="text-xs text-slate-400">
                  Subrace: <span className="text-slate-200">{selectedSubrace.name || currentRace.variantKey}</span>
                </p>
              )}

              <div className="space-y-2">
                {combinedTraits.length > 0 ? (
                  combinedTraits.map((trait) => (
                    <details
                      key={trait.name}
                      className="group rounded-lg border border-slate-800 bg-slate-800/50 px-3 py-2"
                    >
                      <summary className="flex cursor-pointer items-center justify-between text-slate-100">
                        <span className="font-semibold">{trait.name}</span>
                        <span className="text-xs text-slate-500 group-open:hidden">Show</span>
                        <span className="text-xs text-slate-500 hidden group-open:inline">Hide</span>
                      </summary>
                      <div className="mt-2 space-y-1 text-slate-300">
                        {trait.summary && <p>{trait.summary}</p>}
                        {trait.mechanical_effect && (
                          <p className="text-slate-200">{trait.mechanical_effect}</p>
                        )}
                      </div>
                    </details>
                  ))
                ) : (
                  <p className="text-slate-500">Traits not listed.</p>
                )}
              </div>

              {selectedRace.flavor && <p className="text-slate-400 text-xs">{selectedRace.flavor}</p>}
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
