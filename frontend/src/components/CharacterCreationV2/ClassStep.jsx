import React from "react";
import { CLASS_SKILLS } from "../../data/classSkills";
import { CLASS_PROFICIENCIES } from "../../data/classProficiencies";
import { HIT_DICE } from "../../data/levelingData";
import WizardCard from "./WizardCard";

const ClassStep = ({ characterData, updateCharacterData, onNext, onBack }) => {
  const currentClass =
    characterData.class ||
    {
      key: null,
      subclassKey: null,
      level: 1,
      skillProficiencies: [],
    };

  const classKey = currentClass.key;
  const skillInfo = classKey ? CLASS_SKILLS[classKey] : null;
  const profInfo = classKey ? CLASS_PROFICIENCIES[classKey] : null;

  const conScore = characterData.abilityScores?.con ?? null;
  const conMod = conScore != null ? Math.floor((conScore - 10) / 2) : 0;
  const hitDie = classKey ? HIT_DICE[classKey] : null;
  const startingHp = hitDie != null ? hitDie + conMod : null;

  const requiredSkills = skillInfo?.count ?? 0;
  const selectedSkills = currentClass.skillProficiencies || [];

  const handleClassChange = (e) => {
    const newKey = e.target.value || null;
    updateCharacterData({
      class: {
        key: newKey,
        subclassKey: null,
        level: 1,
        skillProficiencies: [],
      },
    });
  };

  const handleSkillToggle = (skill) => {
    const alreadySelected = selectedSkills.includes(skill);

    if (!alreadySelected && selectedSkills.length >= requiredSkills) {
      return;
    }

    const nextSkills = alreadySelected
      ? selectedSkills.filter((s) => s !== skill)
      : [...selectedSkills, skill];

    updateCharacterData({
      class: {
        ...currentClass,
        skillProficiencies: nextSkills,
      },
    });
  };

  const canContinue = Boolean(classKey) && selectedSkills.length === requiredSkills;

  return (
    <WizardCard
      stepTitle="Step 3 – Choose Your Class"
      stepNumber={3}
      totalSteps={7}
      onBack={onBack}
      onNext={onNext}
      nextDisabled={!canContinue}
    >
      <div className="space-y-6 text-slate-100">
        <div className="space-y-2">
          <label className="block text-sm text-slate-300">Class</label>
          <select
            value={classKey || ""}
            onChange={handleClassChange}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="" disabled>
              Select a class
            </option>
            {Object.keys(CLASS_SKILLS).map((key) => (
              <option key={key} value={key}>
                {key}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <h3 className="text-lg font-semibold text-amber-300 mb-2">Starting Hit Points</h3>
            {hitDie ? (
              <p className="text-sm text-slate-200">
                Hit Die: 1d{hitDie} — Level 1 HP: {startingHp}
              </p>
            ) : (
              <p className="text-sm text-slate-400">Select a class to see hit points.</p>
            )}
            <p className="text-xs text-slate-500 mt-1">
              Calculated as maximum hit die + CON modifier.
            </p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <h3 className="text-lg font-semibold text-amber-300 mb-2">Proficiencies</h3>
            {profInfo ? (
              <div className="text-sm text-slate-200 space-y-1">
                <p>
                  <span className="text-slate-400">Armor:</span> {profInfo.armor?.join(", ") || "None"}
                </p>
                <p>
                  <span className="text-slate-400">Weapons:</span> {profInfo.weapons?.join(", ") || "None"}
                </p>
                <p>
                  <span className="text-slate-400">Tools:</span> {profInfo.tools?.join(", ") || "None"}
                </p>
                <p>
                  <span className="text-slate-400">Saving Throws:</span> {profInfo.savingThrows?.join(", ") || "None"}
                </p>
              </div>
            ) : (
              <p className="text-sm text-slate-400">Select a class to see proficiencies.</p>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-semibold text-amber-300">Skill Proficiencies</h3>
            <p className="text-sm text-slate-400">
              Choose {requiredSkills} {requiredSkills === 1 ? "skill" : "skills"}
            </p>
          </div>

          {skillInfo ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {skillInfo.skills.map((skill) => {
                const selected = selectedSkills.includes(skill);
                const disableCheckbox = !selected && selectedSkills.length >= requiredSkills;
                return (
                  <label
                    key={skill}
                    className={`flex items-center gap-2 rounded border px-3 py-2 text-sm transition ${
                      selected
                        ? "border-amber-500 bg-amber-500/10 text-amber-100"
                        : "border-slate-800 bg-slate-900/80 text-slate-200"
                    } ${disableCheckbox ? "opacity-60" : ""}`}
                  >
                    <input
                      type="checkbox"
                      checked={selected}
                      disabled={disableCheckbox}
                      onChange={() => handleSkillToggle(skill)}
                      className="h-4 w-4 accent-amber-500"
                    />
                    {skill}
                  </label>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-400">Select a class to choose skills.</p>
          )}
        </div>
      </div>
    </WizardCard>
  );
};

export default ClassStep;
