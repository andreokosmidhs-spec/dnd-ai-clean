import React from "react";
import { BACKGROUNDS, BACKGROUNDS_BY_KEY } from "../../data/backgroundData";
import WizardCard from "./WizardCard";
import { validateBackground } from "./utils/validation";

const BackgroundStep = ({ wizardState, updateSection, onNext, onBack, steps, goToStep }) => {
  const currentBackground = wizardState.background || { key: null, variantKey: null, toolChoices: [] };
  const defaultPersonality = { ideal: "", bond: "", flaw: "" };
  const currentBackground = wizardState.background || { key: null, variantKey: null, personality: defaultPersonality };
  const selectedBackground = currentBackground.key ? BACKGROUNDS_BY_KEY[currentBackground.key] : null;
  const variants = selectedBackground?.variants || [];
  const toolProficiencies = selectedBackground?.toolProficiencies;
  const fixedTools = toolProficiencies?.fixed || [];
  const toolChoices = currentBackground.toolChoices || [];
  const toolChoiceData = toolProficiencies?.choices;

  const handleBackgroundChange = (e) => {
    const newKey = e.target.value || "";
    updateSection("background", { key: newKey, variantKey: "", toolChoices: [] });
    updateSection("background", { key: newKey, variantKey: "", personality: defaultPersonality });
  };

  const handleVariantChange = (e) => {
    const variantKey = e.target.value || "";
    updateSection("background", { ...currentBackground, variantKey });
  };

  const handleToolChoiceToggle = (option) => {
    if (!toolChoiceData) return;
    const isSelected = toolChoices.includes(option);
    const maxChoices = toolChoiceData.count || 0;

    if (!isSelected && toolChoices.length >= maxChoices) return;

    const nextChoices = isSelected
      ? toolChoices.filter((choice) => choice !== option)
      : [...toolChoices, option];

    updateSection("background", { ...currentBackground, toolChoices: nextChoices });
  const handlePersonalityChange = (field) => (e) => {
    const value = e.target.value || "";
    updateSection("background", {
      ...currentBackground,
      personality: {
        ...(currentBackground.personality || defaultPersonality),
        [field]: value,
      },
    });
  };

  const isValid = validateBackground(wizardState);

  const renderDetails = () => {
    if (!selectedBackground) {
      return <p className="text-sm text-slate-400">Select a background to see details.</p>;
    }

    return (
      <div className="space-y-3 text-sm text-slate-200">
        <p className="text-slate-300">{selectedBackground.description}</p>

        <div>
          <h4 className="text-amber-300 font-semibold">Skill Proficiencies</h4>
          <p className="text-slate-200">{selectedBackground.skillProficiencies?.join(", ") || "None"}</p>
        </div>

        <div>
          <h4 className="text-amber-300 font-semibold">Tool Proficiencies</h4>
          <p className="text-slate-200">
            {fixedTools.length ? fixedTools.join(", ") : "None"}
            {toolChoiceData && (
              <>
                {fixedTools.length ? "; " : ""}
                Choose {toolChoiceData.count}: {toolChoiceData.options.join(", ")}
              </>
            )}
          </p>
        </div>

        <div>
          <h4 className="text-amber-300 font-semibold">Languages</h4>
          <p className="text-slate-200">
            {selectedBackground.languages?.count
              ? `Choose ${selectedBackground.languages.count} language${selectedBackground.languages.count === 1 ? "" : "s"}`
              : "No additional languages"}
          </p>
        </div>

        <div>
          <h4 className="text-amber-300 font-semibold">Feature: {selectedBackground.feature?.name}</h4>
          <p className="text-slate-200">{selectedBackground.feature?.description}</p>
        </div>

        <div>
          <h4 className="text-amber-300 font-semibold">Starting Equipment</h4>
          <ul className="list-disc list-inside text-slate-200 space-y-1">
            {(selectedBackground.equipment || []).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  return (
    <WizardCard
      stepTitle="Step 5 – Choose Your Background"
      stepNumber={5}
      totalSteps={steps.length}
      steps={steps}
      onSelectStep={goToStep}
      onBack={onBack}
      onNext={() => {
        if (isValid) onNext();
      }}
      nextDisabled={!isValid}
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 text-slate-100">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="block text-sm text-slate-300">Background</label>
            <select
              value={currentBackground.key || ""}
              onChange={handleBackgroundChange}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <option value="" disabled>
                Select a background
              </option>
              {BACKGROUNDS.map((bg) => (
                <option key={bg.key} value={bg.key}>
                  {bg.name}
                </option>
              ))}
            </select>
          </div>

          {variants.length > 0 && (
            <div className="space-y-2">
              <label className="block text-sm text-slate-300">Variant</label>
              <select
                value={currentBackground.variantKey || ""}
                onChange={handleVariantChange}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                <option value="">Select a variant (optional)</option>
                {variants.map((variant) => (
                  <option key={variant.key || variant.name} value={variant.key || variant.name}>
                    {variant.name || variant.key}
                  </option>
                ))}
              </select>
            </div>
          )}

          {selectedBackground && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="space-y-2">
                <label className="block text-sm text-slate-300">Ideal</label>
                <select
                  value={currentBackground.personality?.ideal || ""}
                  onChange={handlePersonalityChange("ideal")}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <option value="" disabled>
                    Select an ideal
                  </option>
                  {(selectedBackground.personality?.ideals || []).map((ideal) => (
                    <option key={ideal} value={ideal}>
                      {ideal}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="block text-sm text-slate-300">Bond</label>
                <select
                  value={currentBackground.personality?.bond || ""}
                  onChange={handlePersonalityChange("bond")}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <option value="" disabled>
                    Select a bond
                  </option>
                  {(selectedBackground.personality?.bonds || []).map((bond) => (
                    <option key={bond} value={bond}>
                      {bond}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="block text-sm text-slate-300">Flaw</label>
                <select
                  value={currentBackground.personality?.flaw || ""}
                  onChange={handlePersonalityChange("flaw")}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <option value="" disabled>
                    Select a flaw
                  </option>
                  {(selectedBackground.personality?.flaws || []).map((flaw) => (
                    <option key={flaw} value={flaw}>
                      {flaw}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
          <h3 className="text-lg font-semibold text-amber-300 mb-2">
            {selectedBackground ? selectedBackground.name : "Background Details"}
          </h3>
          {renderDetails()}
        </div>
      </div>

      {selectedBackground && (
        <div className="mt-6 rounded-lg border border-slate-800 bg-slate-900/80 p-4 space-y-4">
          <div>
            <h4 className="text-amber-300 font-semibold mb-2">Tool Proficiencies</h4>
            <div className="flex flex-wrap gap-2">
              {fixedTools.length > 0 ? (
                fixedTools.map((tool) => (
                  <span
                    key={tool}
                    className="rounded-full bg-slate-800 border border-slate-700 px-3 py-1 text-xs text-slate-200"
                  >
                    {tool}
                  </span>
                ))
              ) : (
                <span className="text-sm text-slate-400">No fixed tool proficiencies.</span>
              )}
            </div>
          </div>

          {toolChoiceData && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-amber-300 font-semibold">Select Tool Proficiencies</h4>
                  <p className="text-xs text-slate-400">
                    Choose {toolChoiceData.count} option{toolChoiceData.count === 1 ? "" : "s"}.
                  </p>
                </div>
                <span className="text-xs text-slate-400">
                  {toolChoices.length}/{toolChoiceData.count} selected
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {toolChoiceData.options.map((option) => {
                  const isSelected = toolChoices.includes(option);
                  const selectionFull = !isSelected && toolChoices.length >= toolChoiceData.count;

                  return (
                    <label
                      key={option}
                      className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm cursor-pointer transition ${
                        isSelected
                          ? "border-amber-500 bg-amber-500/10 text-amber-100"
                          : "border-slate-700 bg-slate-800/70 text-slate-200"
                      }`}
                    >
                      <input
                        type="checkbox"
                        className="mt-1 h-4 w-4 rounded border-slate-600 bg-slate-900 text-amber-500"
                        checked={isSelected}
                        disabled={selectionFull}
                        onChange={() => handleToolChoiceToggle(option)}
                      />
                      <span className="flex-1">{option}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </WizardCard>
  );
};

export default BackgroundStep;
