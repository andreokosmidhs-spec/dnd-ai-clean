import React, { useMemo, useState } from "react";
import { raceData } from "../../data/raceData";
import { CLASS_PROFICIENCIES } from "../../data/classProficiencies";
import { BACKGROUNDS_BY_KEY } from "../../data/backgroundData";
import WizardCard from "./WizardCard";
import { validateReview } from "./utils/validation";
import { buildCharacterPayload } from "./utils/payload";
import { useNavigate } from "react-router-dom";

const ABILITIES = [
  { key: "str", label: "STR" },
  { key: "dex", label: "DEX" },
  { key: "con", label: "CON" },
  { key: "int", label: "INT" },
  { key: "wis", label: "WIS" },
  { key: "cha", label: "CHA" },
];

const abilityModifier = (score) => {
  if (score == null || Number.isNaN(score)) return null;
  return Math.floor((score - 10) / 2);
};

const abilityKeys = ["str", "dex", "con", "int", "wis", "cha"];

const getRacialAbilityBonuses = (raceState) => {
  const race = raceState?.key ? raceData[raceState.key] : null;
  const subrace = raceState?.variantKey && race?.subraces ? race.subraces[raceState.variantKey] : null;
  const bonuses = [];

  if (race?.asi) bonuses.push(...race.asi);
  if (subrace?.asi) bonuses.push(...subrace.asi);

  const bonusByAbility = abilityKeys.reduce((acc, key) => ({ ...acc, [key]: 0 }), {});

  bonuses.forEach(({ ability, value }) => {
    if (!ability || value == null) return;
    if (ability === "ALL") {
      abilityKeys.forEach((key) => {
        bonusByAbility[key] += value;
      });
      return;
    }

    const normalizedKey = ability.toLowerCase();
    if (bonusByAbility[normalizedKey] != null) {
      bonusByAbility[normalizedKey] += value;
    }
  });

  return bonusByAbility;
};

const applyAbilityBonuses = (baseAbilities, bonusByAbility) => {
  return abilityKeys.reduce((acc, key) => {
    const base = baseAbilities[key];
    const bonus = bonusByAbility[key] || 0;
    return {
      ...acc,
      [key]: base != null ? base + bonus : null,
    };
  }, {});
};

const ReviewStep = ({ wizardState, onBack, steps, goToStep }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(null);
  const navigate = useNavigate();

  const raceInfo = useMemo(() => {
    if (!wizardState.race?.key) return null;
    const base = raceData[wizardState.race.key];
    const subrace = wizardState.race.variantKey ? base?.subraces?.[wizardState.race.variantKey] : null;
    return { base, subrace };
  }, [wizardState.race]);

  const classInfo = wizardState.class?.key ? CLASS_PROFICIENCIES[wizardState.class.key] : null;

  const backgroundInfo = wizardState.background?.key ? BACKGROUNDS_BY_KEY[wizardState.background.key] : null;

  const abilities = wizardState.abilityScores || {};
  const racialBonuses = useMemo(() => getRacialAbilityBonuses(wizardState.race), [wizardState.race]);
  const totalAbilities = useMemo(
    () => applyAbilityBonuses(abilities, racialBonuses),
    [abilities, racialBonuses]
  );
  const appearance = wizardState.appearance || {};
  const identity = wizardState.identity || {};
  const languagesText = backgroundInfo
    ? backgroundInfo.languages?.count
      ? `Choose ${backgroundInfo.languages.count} language${backgroundInfo.languages.count > 1 ? "s" : ""}`
      : "—"
    : "—";

  const canSubmit = validateReview(wizardState);

  const handleSubmit = async () => {
    if (!canSubmit || isSubmitting) return;
    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(null);

    try {
      const payload = buildCharacterPayload(wizardState);
      const res = await fetch("/api/characters/v2/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Failed to create character");
      }

      const data = await res.json();
      console.log("Character V2 created", data);
      setSubmitSuccess("Character created successfully!");
      navigate("/adventure");
    } catch (err) {
      setSubmitError(err.message || "Failed to create character");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <WizardCard
      stepTitle="Step 7 – Review & Submit"
      stepNumber={7}
      totalSteps={steps.length}
      steps={steps}
      onSelectStep={goToStep}
      onBack={onBack}
      onNext={handleSubmit}
      backDisabled={isSubmitting}
      nextDisabled={!canSubmit || isSubmitting}
      nextLabel={isSubmitting ? "Creating..." : "Create Character"}
    >
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-lg text-slate-100 space-y-6">
        <h2 className="text-2xl font-bold text-amber-400">Step 7 – Review & Submit</h2>

        <div className="space-y-4">
          <section className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <h3 className="text-lg font-semibold text-amber-300 mb-2">Identity</h3>
            <p className="text-sm text-slate-200">Name: {identity.name || "—"}</p>
            <p className="text-sm text-slate-200">Age: {identity.age ?? "—"}</p>
            <p className="text-sm text-slate-200">Appearance Expression: {identity.appearanceExpression ?? "—"}</p>
            <p className="text-sm text-slate-200">Sex: {identity.sex || "—"}</p>
          </section>

          <section className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <h3 className="text-lg font-semibold text-amber-300 mb-2">Race</h3>
            <p className="text-sm text-slate-200">Race: {raceInfo?.base?.name || "—"}</p>
            {raceInfo?.subrace && <p className="text-sm text-slate-200">Subrace: {raceInfo.subrace.name}</p>}
            <p className="text-sm text-slate-200">
              ASI: {raceInfo?.base?.asi?.map((asi) => `${asi.ability}+${asi.value}`).join(", ") || "—"}
            </p>
            <div className="text-sm text-slate-200">
              <p className="text-slate-300">Traits:</p>
              <ul className="list-disc list-inside text-slate-300">
                {(raceInfo?.base?.traits || []).slice(0, 3).map((trait) => (
                  <li key={trait.name}>
                    {trait.name}: {trait.summary}
                  </li>
                ))}
                {!raceInfo?.base?.traits?.length && <li className="text-slate-500">—</li>}
              </ul>
            </div>
          </section>

          <section className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <h3 className="text-lg font-semibold text-amber-300 mb-2">Class</h3>
            <p className="text-sm text-slate-200">Class: {wizardState.class?.key || "—"}</p>
            <p className="text-sm text-slate-200">Saving Throws: {classInfo?.savingThrows?.join(", ") || "—"}</p>
            <p className="text-sm text-slate-200">
              Proficiencies: {classInfo
                ? [...(classInfo.armor || []), ...(classInfo.weapons || []), ...(classInfo.tools || [])]
                    .filter(Boolean)
                    .join(", ") || "—"
                : "—"}
            </p>
          </section>

          <section className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <h3 className="text-lg font-semibold text-amber-300 mb-2">Ability Scores</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {ABILITIES.map(({ key, label }) => {
                const baseScore = abilities[key];
                const bonus = racialBonuses[key] || 0;
                const score = totalAbilities[key];
                const mod = abilityModifier(score);
                return (
                  <div
                    key={key}
                    className="rounded border border-slate-800 bg-slate-800/70 p-3 text-sm text-slate-200"
                  >
                    <p className="font-semibold text-amber-200">{label}</p>
                    <p>Base: {baseScore ?? "—"}</p>
                    {bonus !== 0 && <p>Racial Bonus: +{bonus}</p>}
                    <p>Total: {score ?? "—"}</p>
                    <p>Mod: {mod != null ? (mod >= 0 ? `+${mod}` : mod) : "—"}</p>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-lg font-semibold text-amber-300">Background</h3>
            </div>
            <p className="text-sm text-slate-200">Background: {backgroundInfo?.name || "—"}</p>
            <p className="text-sm text-slate-200">Skills: {backgroundInfo?.skillProficiencies?.join(", ") || "—"}</p>
            <p className="text-sm text-slate-200">Tools: {backgroundInfo?.toolProficiencies?.join(", ") || "—"}</p>
            <p className="text-sm text-slate-200">Languages: {languagesText}</p>
            {backgroundInfo?.feature && (
              <p className="text-sm text-slate-200">
                Feature: {backgroundInfo.feature.name} — {backgroundInfo.feature.description}
              </p>
            )}
          </section>

          <section className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-lg font-semibold text-amber-300">Appearance</h3>
            </div>
            <p className="text-sm text-slate-200">Age Category: {appearance.ageCategory || "—"}</p>
            <p className="text-sm text-slate-200">Height: {appearance.heightCm ? `${appearance.heightCm} cm` : ""}</p>
            <p className="text-sm text-slate-200">Build: {appearance.build || "—"}</p>
            <p className="text-sm text-slate-200">Skin Tone: {appearance.skinTone || "—"}</p>
            <p className="text-sm text-slate-200">Hair Color: {appearance.hairColor || "—"}</p>
            <p className="text-sm text-slate-200">Eye Color: {appearance.eyeColor || "—"}</p>
            <div className="text-sm text-slate-200">
              <p className="text-slate-300">Notable Features:</p>
              <ul className="list-disc list-inside text-slate-300">
                {(appearance.notableFeatures || []).length > 0 ? (
                  appearance.notableFeatures.map((feature) => <li key={feature}>{feature}</li>)
                ) : (
                  <li className="text-slate-500">—</li>
                )}
              </ul>
            </div>
          </section>

          {submitError && (
            <div className="rounded border border-red-500 bg-red-900/40 text-red-200 px-4 py-2 text-sm">{submitError}</div>
          )}
          {submitSuccess && (
            <div className="rounded border border-green-500 bg-green-900/40 text-green-200 px-4 py-2 text-sm">{submitSuccess}</div>
          )}
        </div>
      </div>
    </WizardCard>
  );
};

export default ReviewStep;
