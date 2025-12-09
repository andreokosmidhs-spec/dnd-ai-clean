import React, { useState } from "react";

const AGE_CATEGORIES = ["Young", "Adult", "Veteran", "Elder"];
const BUILDS = ["Slim", "Average", "Athletic", "Muscular", "Heavy"];

const AppearanceStep = ({ characterData, updateCharacterData, onNext, onBack }) => {
  const appearance = characterData.appearance || {
    ageCategory: null,
    heightCm: null,
    build: null,
    skinTone: "",
    hairColor: "",
    eyeColor: "",
    notableFeatures: [],
  };

  const [newFeature, setNewFeature] = useState("");

  const updateAppearance = (patch) => {
    updateCharacterData({ appearance: { ...appearance, ...patch } });
  };

  const handleAddFeature = () => {
    const trimmed = newFeature.trim();
    if (!trimmed) return;
    updateAppearance({ notableFeatures: [...(appearance.notableFeatures || []), trimmed] });
    setNewFeature("");
  };

  const handleRemoveFeature = (feature) => {
    updateAppearance({
      notableFeatures: (appearance.notableFeatures || []).filter((item) => item !== feature),
    });
  };

  const isValid = Boolean(
    appearance.ageCategory &&
      appearance.build &&
      appearance.heightCm &&
      Number(appearance.heightCm) >= 100 &&
      Number(appearance.heightCm) <= 250
  );

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-lg text-slate-100">
      <h2 className="text-2xl font-bold text-amber-400 mb-4">Step 6 – Define Appearance</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-300 mb-1">Age Category</label>
            <select
              value={appearance.ageCategory || ""}
              onChange={(e) => updateAppearance({ ageCategory: e.target.value || null })}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <option value="" disabled>
                Select age category
              </option>
              {AGE_CATEGORIES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-300 mb-1">Height (cm)</label>
            <input
              type="number"
              min={100}
              max={250}
              value={appearance.heightCm ?? ""}
              onChange={(e) =>
                updateAppearance({ heightCm: e.target.value ? Number(e.target.value) : null })
              }
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
              placeholder="Enter height in cm"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-300 mb-1">Build</label>
            <select
              value={appearance.build || ""}
              onChange={(e) => updateAppearance({ build: e.target.value || null })}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <option value="" disabled>
                Select build
              </option>
              {BUILDS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-300 mb-1">Skin Tone</label>
            <input
              type="text"
              value={appearance.skinTone || ""}
              onChange={(e) => updateAppearance({ skinTone: e.target.value })}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
              placeholder="e.g. Pale, Tan, Deep"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-300 mb-1">Hair Color</label>
              <input
                type="text"
                value={appearance.hairColor || ""}
                onChange={(e) => updateAppearance({ hairColor: e.target.value })}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
                placeholder="e.g. Black, Auburn"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-300 mb-1">Eye Color</label>
              <input
                type="text"
                value={appearance.eyeColor || ""}
                onChange={(e) => updateAppearance({ eyeColor: e.target.value })}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
                placeholder="e.g. Green, Hazel"
              />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <h3 className="text-lg font-semibold text-amber-300 mb-2">Notable Features</h3>
            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={newFeature}
                onChange={(e) => setNewFeature(e.target.value)}
                className="flex-1 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
                placeholder="e.g. Scar across left cheek"
              />
              <button
                type="button"
                onClick={handleAddFeature}
                className="px-3 py-2 rounded-lg bg-amber-500 text-black font-semibold hover:bg-amber-400 transition-colors"
              >
                Add
              </button>
            </div>
            <ul className="space-y-2">
              {(appearance.notableFeatures || []).length === 0 && (
                <li className="text-sm text-slate-400">No notable features added.</li>
              )}
              {(appearance.notableFeatures || []).map((feature) => (
                <li
                  key={feature}
                  className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-800/80 px-3 py-2"
                >
                  <span className="text-slate-100 text-sm">{feature}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveFeature(feature)}
                    className="text-sm text-red-300 hover:text-red-200"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4 space-y-2 text-sm text-slate-200">
            <h3 className="text-lg font-semibold text-amber-300">Summary</h3>
            <p><span className="text-slate-400">Age Category:</span> {appearance.ageCategory || "—"}</p>
            <p><span className="text-slate-400">Height:</span> {appearance.heightCm ? `${appearance.heightCm} cm` : "—"}</p>
            <p><span className="text-slate-400">Build:</span> {appearance.build || "—"}</p>
            <p><span className="text-slate-400">Skin Tone:</span> {appearance.skinTone || "—"}</p>
            <p><span className="text-slate-400">Hair:</span> {appearance.hairColor || "—"}</p>
            <p><span className="text-slate-400">Eyes:</span> {appearance.eyeColor || "—"}</p>
            <p className="text-slate-400">Features:</p>
            <ul className="list-disc list-inside">
              {(appearance.notableFeatures || []).length > 0 ? (
                appearance.notableFeatures.map((f) => <li key={f}>{f}</li>)
              ) : (
                <li className="text-slate-500">None listed</li>
              )}
            </ul>
          </div>
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

export default AppearanceStep;
