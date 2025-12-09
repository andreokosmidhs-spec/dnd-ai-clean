import React from "react";
import { BACKGROUNDS, BACKGROUNDS_BY_KEY } from "../../data/backgroundData";

const BackgroundStep = ({ characterData, updateCharacterData, onNext, onBack }) => {
  const currentBackground = characterData.background || { key: null, variantKey: null };
  const selectedBackground = currentBackground.key
    ? BACKGROUNDS_BY_KEY[currentBackground.key]
    : null;
  const variants = selectedBackground?.variants || [];

  const handleBackgroundChange = (e) => {
    const newKey = e.target.value || null;
    updateCharacterData({ background: { key: newKey, variantKey: null } });
  };

  const handleVariantChange = (e) => {
    const variantKey = e.target.value || null;
    updateCharacterData({ background: { ...currentBackground, variantKey } });
  };

  const isValid = Boolean(currentBackground.key && selectedBackground);

  const renderDetails = () => {
    if (!selectedBackground) {
      return <p className="text-sm text-slate-400">Select a background to see details.</p>;
    }

    return (
      <div className="space-y-3 text-sm text-slate-200">
        <p className="text-slate-300">{selectedBackground.description}</p>

        <div>
          <h4 className="text-amber-300 font-semibold">Skill Proficiencies</h4>
          <p className="text-slate-200">
            {selectedBackground.skillProficiencies?.join(", ") || "None"}
          </p>
        </div>

        <div>
          <h4 className="text-amber-300 font-semibold">Tool Proficiencies</h4>
          <p className="text-slate-200">
            {selectedBackground.toolProficiencies?.length
              ? selectedBackground.toolProficiencies.join(", ")
              : "None"}
          </p>
        </div>

        <div>
          <h4 className="text-amber-300 font-semibold">Languages</h4>
          <p className="text-slate-200">
            {selectedBackground.languages?.count
              ? `Choose ${selectedBackground.languages.count} language${
                  selectedBackground.languages.count === 1 ? "" : "s"
                }`
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
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-lg text-slate-100">
      <h2 className="text-2xl font-bold text-amber-400 mb-4">Step 5 – Choose Your Background</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-300 mb-1">Background</label>
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
            <div>
              <label className="block text-sm text-slate-300 mb-1">Variant</label>
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
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
          <h3 className="text-lg font-semibold text-amber-300 mb-2">
            {selectedBackground ? selectedBackground.name : "Background Details"}
          </h3>
          {renderDetails()}
        </div>
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
          onClick={() => {
            if (isValid) onNext();
          }}
          disabled={!isValid}
          className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
            isValid
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

export default BackgroundStep;
