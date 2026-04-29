import React, { useRef, useState } from "react";
import WizardCard from "./WizardCard";
import { validateAppearance } from "./utils/validation";
import { fileToCompressedDataUrl } from "../../utils/imageUpload";

const AGE_CATEGORIES = ["Young", "Adult", "Veteran", "Elder"];
const BUILDS = ["Slim", "Average", "Athletic", "Muscular", "Heavy"];
const HAIR_STYLE_SUGGESTIONS = [
  "Buzz cut",
  "Short cropped",
  "Shoulder-length",
  "Long flowing",
  "Topknot",
  "Ponytail",
  "Braided",
  "Twin braids",
  "Dreadlocks",
  "Wavy",
  "Curly",
  "Mohawk",
  "Undercut",
  "Shaved",
  "Bald",
];
const FACIAL_HAIR_SUGGESTIONS = [
  "Clean-shaven",
  "Stubble",
  "Light goatee",
  "Goatee",
  "Mustache",
  "Short beard",
  "Full beard",
  "Long beard",
  "Braided beard",
  "Mutton chops",
  "Van Dyke",
  "Forked beard",
];

const AppearanceStep = ({ wizardState, updateSection, onNext, onBack, steps, goToStep }) => {
  const appearance = wizardState.appearance || {
    ageCategory: null,
    heightCm: null,
    build: null,
    skinTone: "",
    hairColor: "",
    hairStyle: "",
    facialHair: "",
    eyeColor: "",
    notableFeatures: [],
  };

  const [newFeature, setNewFeature] = useState("");
  const [referenceError, setReferenceError] = useState(null);
  const fileInputRef = useRef(null);

  const handleReferenceUpload = async (e) => {
    setReferenceError(null);
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const dataUrl = await fileToCompressedDataUrl(file);
      updateAppearance({ referenceImage: dataUrl });
    } catch (err) {
      setReferenceError(err.message || "Could not load image");
    } finally {
      // Reset so the same file can be selected again after removing
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleRemoveReference = () => {
    updateAppearance({ referenceImage: "" });
    setReferenceError(null);
  };

  const updateAppearance = (patch) => {
    updateSection("appearance", { ...appearance, ...patch });
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

  const isValid = validateAppearance({ ...wizardState, appearance });

  return (
    <WizardCard
      stepTitle="Step 6 – Define Appearance"
      stepNumber={6}
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
              onChange={(e) => updateAppearance({ heightCm: e.target.value ? Number(e.target.value) : null })}
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

          <div>
            <label className="block text-sm text-slate-300 mb-1">Hair Style</label>
            <input
              type="text"
              list="hair-style-suggestions"
              value={appearance.hairStyle || ""}
              onChange={(e) => updateAppearance({ hairStyle: e.target.value })}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
              placeholder="e.g. Long braided, Topknot, Shaved"
              data-testid="appearance-hair-style-input"
            />
            <datalist id="hair-style-suggestions">
              {HAIR_STYLE_SUGGESTIONS.map((opt) => (
                <option key={opt} value={opt} />
              ))}
            </datalist>
            <p className="text-xs text-slate-500 mt-1">
              Used by the portrait artist and DM. Pick a suggestion or write your own.
            </p>
          </div>

          <div>
            <label className="block text-sm text-slate-300 mb-1">Facial Hair</label>
            <input
              type="text"
              list="facial-hair-suggestions"
              value={appearance.facialHair || ""}
              onChange={(e) => updateAppearance({ facialHair: e.target.value })}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
              placeholder="e.g. Full beard, Stubble, Clean-shaven"
              data-testid="appearance-facial-hair-input"
            />
            <datalist id="facial-hair-suggestions">
              {FACIAL_HAIR_SUGGESTIONS.map((opt) => (
                <option key={opt} value={opt} />
              ))}
            </datalist>
            <p className="text-xs text-slate-500 mt-1">
              Leave blank for clean-shaven. Free-text for things like "auburn moustache, neatly trimmed".
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-amber-700/40 bg-amber-950/20 p-4">
            <h3 className="text-lg font-semibold text-amber-300 mb-1">Portrait Reference (optional)</h3>
            <p className="text-xs text-slate-400 mb-3">
              Upload a reference image (face, art, mood board) and the AI portrait artist will use it as visual inspiration alongside your written description. PNG, JPG, or WEBP. Resized client-side; nothing is uploaded until you submit.
            </p>

            {appearance.referenceImage ? (
              <div className="space-y-3">
                <div className="rounded-md overflow-hidden border border-slate-800 bg-slate-900 max-w-[240px]">
                  <img
                    src={appearance.referenceImage}
                    alt="Portrait reference"
                    className="w-full h-auto block"
                    data-testid="appearance-reference-preview"
                  />
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="px-3 py-2 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-100 text-sm"
                    data-testid="appearance-reference-replace-btn"
                  >
                    Replace image
                  </button>
                  <button
                    type="button"
                    onClick={handleRemoveReference}
                    className="px-3 py-2 rounded-lg border border-red-700/50 bg-transparent hover:bg-red-600/10 text-red-300 text-sm"
                    data-testid="appearance-reference-remove-btn"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 rounded-lg bg-amber-500 text-black font-semibold hover:bg-amber-400 transition-colors"
                data-testid="appearance-reference-upload-btn"
              >
                Upload reference image
              </button>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={handleReferenceUpload}
              className="hidden"
              data-testid="appearance-reference-file-input"
            />

            {referenceError && (
              <p className="text-xs text-red-300 mt-2" data-testid="appearance-reference-error">
                {referenceError}
              </p>
            )}
          </div>

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
            <p>
              <span className="text-slate-400">Age Category:</span> {appearance.ageCategory || "—"}
            </p>
            <p>
              <span className="text-slate-400">Height:</span> {appearance.heightCm ? `${appearance.heightCm} cm` : "—"}
            </p>
            <p>
              <span className="text-slate-400">Build:</span> {appearance.build || "—"}
            </p>
            <p>
              <span className="text-slate-400">Skin Tone:</span> {appearance.skinTone || "—"}
            </p>
            <p>
              <span className="text-slate-400">Hair:</span> {[appearance.hairStyle, appearance.hairColor].filter(Boolean).join(" ") || "—"}
            </p>
            <p>
              <span className="text-slate-400">Facial Hair:</span> {appearance.facialHair || "—"}
            </p>
            <p>
              <span className="text-slate-400">Eyes:</span> {appearance.eyeColor || "—"}
            </p>
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
    </WizardCard>
  );
};

export default AppearanceStep;
