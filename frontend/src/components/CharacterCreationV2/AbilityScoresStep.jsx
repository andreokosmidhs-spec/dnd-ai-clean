import React from "react";
import WizardCard from "./WizardCard";

const STANDARD_ARRAY = [15, 14, 13, 12, 10, 8];
const POINT_COST = {
  8: 0,
  9: 1,
  10: 2,
  11: 3,
  12: 4,
  13: 5,
  14: 7,
  15: 9,
};

const abilities = ["str", "dex", "con", "int", "wis", "cha"];
const labels = {
  str: "STR",
  dex: "DEX",
  con: "CON",
  int: "INT",
  wis: "WIS",
  cha: "CHA",
};

const AbilityScoresStep = ({ characterData, updateCharacterData, onNext, onBack }) => {
  const abilityScores = characterData.abilityScores || {
    str: null,
    dex: null,
    con: null,
    int: null,
    wis: null,
    cha: null,
    method: "standard_array",
  };

  const method = abilityScores.method || "standard_array";

  const abilityMod = (score) => {
    if (score == null || Number.isNaN(score)) return null;
    return Math.floor((score - 10) / 2);
  };

  const handleMethodChange = (e) => {
    const nextMethod = e.target.value;

    if (nextMethod === "point_buy") {
      updateCharacterData({
        abilityScores: {
          str: 8,
          dex: 8,
          con: 8,
          int: 8,
          wis: 8,
          cha: 8,
          method: "point_buy",
        },
      });
      return;
    }

    updateCharacterData({
      abilityScores: {
        str: null,
        dex: null,
        con: null,
        int: null,
        wis: null,
        cha: null,
        method: nextMethod,
      },
    });
  };

  const handleStandardSelect = (key, value) => {
    const parsed = value === "" ? null : Number(value);
    updateCharacterData({
      abilityScores: {
        ...abilityScores,
        method: "standard_array",
        [key]: parsed,
      },
    });
  };

  const getStandardOptions = (key) => {
    const selectedValues = abilities
      .filter((a) => a !== key)
      .map((a) => abilityScores[a])
      .filter((v) => v != null);

    return STANDARD_ARRAY.filter((v) => v === abilityScores[key] || !selectedValues.includes(v));
  };

  const pointBuyTotal = () => {
    return abilities.reduce((sum, ability) => {
      const score = abilityScores[ability] ?? 8;
      const cost = POINT_COST[score] ?? 0;
      return sum + cost;
    }, 0);
  };

  const handlePointAdjust = (key, delta) => {
    const current = abilityScores[key] ?? 8;
    const candidate = current + delta;
    if (candidate < 8 || candidate > 15) return;

    const hypotheticalScores = {
      ...abilityScores,
      [key]: candidate,
    };

    const spent = abilities.reduce((sum, ability) => {
      const score = hypotheticalScores[ability] ?? 8;
      return sum + (POINT_COST[score] ?? 0);
    }, 0);

    if (spent > 27) return;

    updateCharacterData({
      abilityScores: {
        ...hypotheticalScores,
        method: "point_buy",
      },
    });
  };

  const handleManualChange = (key, value) => {
    const parsed = value === "" ? null : Number(value);
    if (parsed != null && (parsed < 1 || parsed > 20)) return;

    updateCharacterData({
      abilityScores: {
        ...abilityScores,
        method: "manual",
        [key]: parsed,
      },
    });
  };

  const isValid = () => {
    const scores = abilities.map((a) => abilityScores[a]);
    if (scores.some((s) => s == null || Number.isNaN(s))) return false;

    if (method === "standard_array") {
      const set = new Set(scores);
      return set.size === STANDARD_ARRAY.length && scores.every((s) => STANDARD_ARRAY.includes(s));
    }

    if (method === "point_buy") {
      const withinRange = scores.every((s) => s >= 8 && s <= 15);
      return withinRange && pointBuyTotal() <= 27;
    }

    if (method === "manual") {
      return scores.every((s) => s >= 1 && s <= 20);
    }

    return false;
  };

  const renderAbilityRow = (key) => {
    const score = abilityScores[key];
    const mod = abilityMod(score);

    return (
      <div key={key} className="flex flex-col gap-1 rounded-lg border border-slate-800 bg-slate-900/70 p-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-slate-200">{labels[key]}</span>
          <span className="text-xs text-slate-400">Mod: {mod == null ? "—" : mod >= 0 ? `+${mod}` : mod}</span>
        </div>

        {method === "standard_array" && (
          <select
            value={score ?? ""}
            onChange={(e) => handleStandardSelect(key, e.target.value)}
            className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="" disabled>
              Select score
            </option>
            {getStandardOptions(key).map((val) => (
              <option key={val} value={val}>
                {val}
              </option>
            ))}
          </select>
        )}

        {method === "point_buy" && (
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => handlePointAdjust(key, -1)}
              className="h-8 w-8 rounded border border-slate-700 text-lg leading-none text-slate-200 hover:bg-slate-800"
            >
              −
            </button>
            <div className="min-w-[40px] text-center text-lg font-semibold text-slate-100">{score}</div>
            <button
              type="button"
              onClick={() => handlePointAdjust(key, 1)}
              className="h-8 w-8 rounded border border-slate-700 text-lg leading-none text-slate-200 hover:bg-slate-800"
            >
              +
            </button>
          </div>
        )}

        {method === "manual" && (
          <input
            type="number"
            min={1}
            max={20}
            value={score ?? ""}
            onChange={(e) => handleManualChange(key, e.target.value === "" ? "" : Number(e.target.value))}
            className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        )}
      </div>
    );
  };

  const pointsRemaining = method === "point_buy" ? 27 - pointBuyTotal() : null;
  const canContinue = isValid();

  return (
    <WizardCard
      stepTitle="Step 4 – Assign Ability Scores"
      stepNumber={4}
      totalSteps={7}
      onBack={onBack}
      onNext={() => {
        if (canContinue) onNext();
      }}
      nextDisabled={!canContinue}
    >
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-lg text-slate-100">
        <div className="mb-4">
          <label className="block text-sm text-slate-300 mb-1">Method</label>
          <select
            value={method}
            onChange={handleMethodChange}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="standard_array">Standard Array</option>
            <option value="point_buy">Point Buy</option>
            <option value="manual">Manual Entry</option>
          </select>
        </div>

        {method === "point_buy" && (
          <div className="mb-4 text-sm text-slate-200">Points remaining: {pointsRemaining}</div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {abilities.map((key) => renderAbilityRow(key))}
        </div>
      </div>
    </WizardCard>
  );
};

export default AbilityScoresStep;
