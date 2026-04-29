import React, { useMemo, useState } from "react";
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
  const navigate = useNavigate();
  const { setSession } = useSessionCore();

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

    // Try a single endpoint with a short timeout. Returns either the success
    // Response or {status, detail} on failure. Larger payloads (e.g. a
    // reference image) get a more generous timeout so slow uplinks don't
    // surface as "All endpoints failed".
    const hasReferenceImage = !!payload?.appearance?.referenceImage;
    const perAttemptTimeoutMs = hasReferenceImage ? 30000 : 12000;
    const tryOnce = async (url) => {
      const ctrl = new AbortController();
      const timeoutId = setTimeout(() => ctrl.abort(), perAttemptTimeoutMs);
      try {
        const attempt = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: ctrl.signal,
        });
        if (attempt.ok) return { ok: true, res: attempt };
        return { ok: false, status: attempt.status, detail: await parseErrorBody(attempt) };
      } catch (netErr) {
        return { ok: false, status: 0, detail: netErr?.message || "Network error" };
      } finally {
        clearTimeout(timeoutId);
      }
    };

    // Run the full submit pass: try each endpoint in order, stop on success
    // or on a non-404 / non-network error (those won't change with retry).
    const runPass = async () => {
      for (const url of endpoints) {
        const result = await tryOnce(url);
        if (result.ok) return { res: result.res };
        // 5xx, 502, 503 + transient network are worth retrying after a beat
        if (result.status === 0 || result.status === 404 || result.status >= 500) {
          // Continue to next endpoint; the FOR loop will exhaust and we'll retry
          continue;
        }
        // 400 / 422 — real validation problem, do NOT retry
        return { fail: result };
      }
      return { fail: { status: 0, detail: "All endpoints failed" } };
    };

    try {
      let triedUrls = [...endpoints];
      let outcome = await runPass();

      // If the first pass failed on transient causes (404/5xx/network), wait
      // 1.2s and try ONCE more before giving up. Catches backend restarts
      // and brief proxy hiccups without surfacing a misleading 404.
      if (!outcome.res) {
        await new Promise((r) => setTimeout(r, 1200));
        outcome = await runPass();
      }

      if (!outcome.res) {
        const lastStatus = outcome.fail?.status ?? 0;
        const lastError = outcome.fail?.detail || "";

        // For status=0 (network failure), do a lightweight reachability
        // probe so we can tell the user WHY the submit failed:
        //   - browser offline?
        //   - preview iframe paused (Emergent "static preview" overlay)?
        //   - real backend outage?
        let reachabilityHint = "";
        if (lastStatus === 0) {
          if (typeof navigator !== "undefined" && navigator.onLine === false) {
            reachabilityHint = "Your browser reports it's OFFLINE. Reconnect to the internet and click Retry.";
          } else {
            const ctrl = new AbortController();
            const timeoutId = setTimeout(() => ctrl.abort(), 5000);
            let probeOk = false;
            try {
              const probe = await fetch(`${backendUrl}/api/characters/v2/`, {
                method: "GET",
                signal: ctrl.signal,
              });
              probeOk = probe.ok;
            } catch (_e) {
              probeOk = false;
            } finally {
              clearTimeout(timeoutId);
            }
            reachabilityHint = probeOk
              // Backend reachable, but the heavy POST failed — most likely a
              // large reference image timed out (slow uplink) or the WAF
              // rejected it. Suggest the precise next step.
              ? "The backend is reachable, but submitting the character timed out. If you uploaded a reference image, try removing it and submit again — then re-upload after the character is created."
              // Backend totally unreachable — paused preview or real outage.
              : "We couldn't reach the backend at all. If you see a black bar at the bottom saying \"You're viewing a static preview\" with a \"Resume Preview\" button, click it and try again. Otherwise hard-refresh the page (Ctrl/Cmd+Shift+R).";
          }
        }

        const friendly =
          lastStatus === 404
            ? `The character-creation endpoint wasn't reachable (404), even after a retry. Try a hard refresh (Ctrl/Cmd+Shift+R). If it persists, the backend may be restarting — wait 10s and click Retry. Tried: ${triedUrls.join(" , ")}`
            : lastStatus === 422 || lastStatus === 400
              ? `We couldn't validate your character (${lastStatus}). ${lastError || "Please re-check the wizard steps."}`
              : lastStatus >= 500
                ? `The server hit an error (${lastStatus}) and the retry also failed. Please wait a few seconds and click Retry.${lastError ? ` Detail: ${lastError}` : ""}`
                : lastStatus === 0
                  ? `Couldn't create character. ${reachabilityHint}`
                  : `Failed to create character (HTTP ${lastStatus}).${lastError ? ` ${lastError}` : ""}`;
        throw new Error(friendly);
      }

      const data = await outcome.res.json();
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
