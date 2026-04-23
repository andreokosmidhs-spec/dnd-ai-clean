import React, { useEffect, useMemo, useState } from "react";
import { raceData } from "../../data/raceData";
import { CLASS_PROFICIENCIES } from "../../data/classProficiencies";
import { BACKGROUNDS_BY_KEY } from "../../data/backgroundData";
import WizardCard from "./WizardCard";
import { validateReview } from "./utils/validation";
import { buildCharacterPayload } from "./utils/payload";
import { useNavigate } from "react-router-dom";
import { useSessionCore } from "../../store/useSessionCore";

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
  // 'checking' | 'ok' | 'unreachable'
  const [backendStatus, setBackendStatus] = useState("checking");
  const navigate = useNavigate();
  const { setSession } = useSessionCore();

  // Ping the backend as soon as the user lands on the Review step so they
  // know up front if the app was loaded from a stale preview URL or is
  // otherwise unreachable. Tries a cheap existing route.
  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || "";
      // Cheap endpoint that exists, returns 200 quickly.
      const probe = `${backendUrl}/api/characters/v2/`;
      try {
        const res = await fetch(probe, { method: "GET" });
        if (!cancelled) setBackendStatus(res.ok ? "ok" : "unreachable");
      } catch (_e) {
        if (!cancelled) setBackendStatus("unreachable");
      }
    };
    check();
    return () => {
      cancelled = true;
    };
  }, []);

  const raceInfo = useMemo(() => {
    if (!wizardState.race?.key) return null;
    const base = raceData[wizardState.race.key];
    const subrace = wizardState.race.variantKey ? base?.subraces?.[wizardState.race.variantKey] : null;
    return { base, subrace };
  }, [wizardState.race]);

  const classInfo = wizardState.class?.key ? CLASS_PROFICIENCIES[wizardState.class.key] : null;

  const backgroundInfo = wizardState.background?.key ? BACKGROUNDS_BY_KEY[wizardState.background.key] : null;
  const spellSelections = wizardState.spells?.selected || { cantrips: [], level1: [] };

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

    const payload = buildCharacterPayload(wizardState);
    const backendUrl = process.env.REACT_APP_BACKEND_URL || "";
    // Two endpoints serve the same handler. If one is blocked by a stale
    // cache / proxy rule, fall back to the alias so users aren't stuck.
    const endpoints = [
      `${backendUrl}/api/characters/v2/create`,
      `${backendUrl}/api/v2/characters/create`,
    ];

    const parseErrorBody = async (res) => {
      const ctype = (res.headers.get("content-type") || "").toLowerCase();
      try {
        if (ctype.includes("application/json")) {
          const data = await res.json();
          return (
            (typeof data?.detail === "string" && data.detail) ||
            (Array.isArray(data?.detail) && data.detail.map((d) => d?.msg || JSON.stringify(d)).join("; ")) ||
            JSON.stringify(data)
          );
        }
        const raw = await res.text();
        return raw.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim().slice(0, 180);
      } catch (_e) {
        return "";
      }
    };

    try {
      let res = null;
      let lastError = "";
      let lastStatus = 0;
      let triedUrls = [];

      for (const url of endpoints) {
        triedUrls.push(url);
        try {
          const attempt = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          if (attempt.ok) {
            res = attempt;
            break;
          }
          lastStatus = attempt.status;
          lastError = await parseErrorBody(attempt);
          // Only worth trying the alias on 404; any other error is likely a
          // real server/validation problem that the alias won't fix.
          if (attempt.status !== 404) {
            res = attempt;
            break;
          }
        } catch (netErr) {
          lastError = netErr?.message || "Network error";
          lastStatus = 0;
        }
      }

      if (!res || !res.ok) {
        const friendly =
          lastStatus === 404
            ? `The character-creation endpoint wasn't reachable (404). This usually means a stale preview URL or an ad-blocker. Try a hard refresh (Ctrl/Cmd+Shift+R). Tried: ${triedUrls.join(" , ")}`
            : lastStatus === 422 || lastStatus === 400
              ? `We couldn't validate your character (${lastStatus}). ${lastError || "Please re-check the wizard steps."}`
              : lastStatus >= 500
                ? `The server hit an error (${lastStatus}). Please try again in a moment.${lastError ? ` Detail: ${lastError}` : ""}`
                : lastStatus === 0
                  ? `Couldn't reach the backend from your browser. Please check your internet connection or try a hard refresh.${lastError ? ` (${lastError})` : ""}`
                  : `Failed to create character (HTTP ${lastStatus}).${lastError ? ` ${lastError}` : ""}`;
        throw new Error(friendly);
      }

      const data = await res.json();
      console.log("Character V2 created", data);

      if (!data?.id) {
        throw new Error("Character created but id was not returned");
      }

      setSession({
        activeCharacterId: data.id,
        activeCampaignId: null,
        campaignStatus: "none",
      });

      // Kick off portrait generation in the background. Don't block navigation on it.
      fetch(`${backendUrl}/api/characters/v2/${data.id}/generate-portrait`, {
        method: "POST",
      }).catch((err) => {
        console.warn("Portrait generation failed (non-fatal):", err);
      });

      setSubmitSuccess("Character created successfully!");
      navigate("/campaign-setup");
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

        {backendStatus === "unreachable" && (
          <div
            className="rounded-md border border-amber-500/50 bg-amber-900/20 text-amber-100 px-3 py-2 text-sm"
            data-testid="review-backend-unreachable-banner"
            role="alert"
          >
            ⚠️ The backend isn't responding from your browser. If you click
            Create Character now it will probably fail with 404. Try a hard
            refresh (<kbd className="px-1 py-0.5 border border-amber-500/50 rounded text-xs">Ctrl/Cmd+Shift+R</kbd>) first.
          </div>
        )}

        <div className="space-y-4">
          <section className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <h3 className="text-lg font-semibold text-amber-300 mb-2">Identity</h3>
            <p className="text-sm text-slate-200">Name: {identity.name || "—"}</p>
            <p className="text-sm text-slate-200">Age: {identity.age ?? "—"}</p>
            <p className="text-sm text-slate-200">Appearance Expression: {identity.genderExpression ?? "—"}</p>
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

          {(spellSelections.cantrips.length > 0 || spellSelections.level1.length > 0) && (
            <section className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
              <h3 className="text-lg font-semibold text-amber-300 mb-2">Spells</h3>
              {spellSelections.cantrips.length > 0 && (
                <div className="mb-3">
                  <p className="text-sm font-semibold text-amber-200">Cantrips</p>
                  <ul className="list-disc list-inside text-sm text-slate-300">
                    {spellSelections.cantrips.map((spell) => (
                      <li key={`cantrip-${spell}`}>{spell}</li>
                    ))}
                  </ul>
                </div>
              )}
              {spellSelections.level1.length > 0 && (
                <div>
                  <p className="text-sm font-semibold text-amber-200">Level 1 Spells</p>
                  <ul className="list-disc list-inside text-sm text-slate-300">
                    {spellSelections.level1.map((spell) => (
                      <li key={`level1-${spell}`}>{spell}</li>
                    ))}
                  </ul>
                </div>
              )}
            </section>
          )}

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
            <div
              className="rounded-md border border-red-500/60 bg-red-900/30 text-red-100 px-4 py-3 text-sm space-y-2"
              data-testid="review-submit-error"
              role="alert"
            >
              <div className="flex items-start gap-2">
                <span className="font-semibold text-red-200">Couldn't create character.</span>
              </div>
              <p className="text-red-200 leading-relaxed break-words">{submitError}</p>
              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="text-xs px-3 py-1 rounded border border-red-400/60 bg-red-600/30 hover:bg-red-600/50 text-red-50 disabled:opacity-50"
                  data-testid="review-submit-retry-btn"
                >
                  {isSubmitting ? "Retrying…" : "Retry"}
                </button>
                <button
                  type="button"
                  onClick={() => setSubmitError(null)}
                  className="text-xs px-3 py-1 rounded border border-slate-500/50 bg-slate-700/40 hover:bg-slate-700/70 text-slate-200"
                  data-testid="review-submit-dismiss-btn"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}
          {submitSuccess && (
            <div className="rounded border border-green-500 bg-green-900/40 text-green-200 px-4 py-2 text-sm">
              {submitSuccess}
            </div>
          )}
        </div>
      </div>
    </WizardCard>
  );
};

export default ReviewStep;
