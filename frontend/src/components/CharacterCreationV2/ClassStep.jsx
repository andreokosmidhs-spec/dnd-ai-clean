import React from "react";
import { CLASS_SKILLS } from "../../data/classSkills";
import { CLASS_PROFICIENCIES } from "../../data/classProficiencies";
import { CLASS_SUBCLASSES } from "../../data/classSubclasses";
import { HIT_DICE } from "../../data/levelingData";
import WizardCard from "./WizardCard";
import { getSpellRequirements, validateClass } from "./utils/validation";

const SPELL_OPTIONS = [
  { name: "Fire Bolt", level: 0, classes: ["Wizard", "Sorcerer"] },
  { name: "Ray of Frost", level: 0, classes: ["Wizard", "Sorcerer"] },
  { name: "Mage Hand", level: 0, classes: ["Wizard", "Sorcerer", "Warlock", "Bard"] },
  { name: "Eldritch Blast", level: 0, classes: ["Warlock"] },
  { name: "Vicious Mockery", level: 0, classes: ["Bard"] },
  { name: "Sacred Flame", level: 0, classes: ["Cleric"] },
  { name: "Guidance", level: 0, classes: ["Cleric", "Druid"] },
  { name: "Produce Flame", level: 0, classes: ["Druid"] },
  { name: "Thorn Whip", level: 0, classes: ["Druid"] },
  { name: "Minor Illusion", level: 0, classes: ["Wizard", "Bard"] },
  { name: "Prestidigitation", level: 0, classes: ["Wizard", "Sorcerer", "Bard"] },
  { name: "Chill Touch", level: 0, classes: ["Wizard", "Warlock", "Sorcerer"] },
  { name: "Light", level: 0, classes: ["Wizard", "Cleric", "Bard", "Sorcerer"] },
  { name: "Shocking Grasp", level: 0, classes: ["Wizard", "Sorcerer"] },
  { name: "Poison Spray", level: 0, classes: ["Wizard", "Sorcerer", "Warlock", "Druid"] },
  { name: "Magic Missile", level: 1, classes: ["Wizard", "Sorcerer"] },
  { name: "Shield", level: 1, classes: ["Wizard", "Sorcerer"] },
  { name: "Burning Hands", level: 1, classes: ["Wizard", "Sorcerer"] },
  { name: "Sleep", level: 1, classes: ["Wizard", "Sorcerer", "Bard"] },
  { name: "Charm Person", level: 1, classes: ["Wizard", "Sorcerer", "Warlock", "Bard"] },
  { name: "Cure Wounds", level: 1, classes: ["Cleric", "Druid", "Bard"] },
  { name: "Healing Word", level: 1, classes: ["Cleric", "Druid", "Bard"] },
  { name: "Bless", level: 1, classes: ["Cleric"] },
  { name: "Command", level: 1, classes: ["Cleric", "Warlock"] },
  { name: "Thunderwave", level: 1, classes: ["Wizard", "Sorcerer", "Bard", "Warlock"] },
  { name: "Hex", level: 1, classes: ["Warlock"] },
  { name: "Witch Bolt", level: 1, classes: ["Warlock", "Sorcerer"] },
  { name: "Faerie Fire", level: 1, classes: ["Bard", "Druid", "Warlock"] },
  { name: "Detect Magic", level: 1, classes: ["Wizard", "Cleric", "Druid", "Bard", "Sorcerer"] },
  { name: "Tasha's Hideous Laughter", level: 1, classes: ["Bard", "Wizard"] },
  { name: "Entangle", level: 1, classes: ["Druid"] },
  { name: "Guiding Bolt", level: 1, classes: ["Cleric"] },
];

const ClassStep = ({ wizardState, updateSection, onNext, onBack, steps, goToStep }) => {
  const currentClass =
    wizardState.class || {
      key: null,
      subclassKey: null,
      level: 1,
      skillProficiencies: [],
    };

  const classKey = currentClass.key;
  const skillInfo = classKey ? CLASS_SKILLS[classKey] : null;
  const profInfo = classKey ? CLASS_PROFICIENCIES[classKey] : null;
  const subclassInfo = classKey ? CLASS_SUBCLASSES[classKey] : null;

  const spellRequirements = getSpellRequirements(classKey);
  const availableCantrips = SPELL_OPTIONS.filter(
    (spell) => spell.level === 0 && spell.classes.includes(classKey)
  );
  const availableLevel1 = SPELL_OPTIONS.filter(
    (spell) => spell.level === 1 && spell.classes.includes(classKey)
  );
  const selectedSpells = wizardState.spells?.selected || { cantrips: [], level1: [] };

  const conScore = wizardState.abilityScores?.con ?? null;
  const conMod = conScore != null ? Math.floor((conScore - 10) / 2) : 0;
  const hitDie = classKey ? HIT_DICE[classKey] : null;
  const startingHp = hitDie != null ? hitDie + conMod : null;

  const requiredSkills = skillInfo?.count ?? 0;
  const selectedSkills = currentClass.skillProficiencies || [];
  const selectedSubclass = currentClass.subclassKey || "";

  const handleClassChange = (e) => {
    const newKey = e.target.value || "";
    const nextRequirements = getSpellRequirements(newKey);
    const nextAvailableCantrips = SPELL_OPTIONS.filter(
      (spell) => spell.level === 0 && spell.classes.includes(newKey)
    ).map((spell) => spell.name);
    const nextAvailableLevel1 = SPELL_OPTIONS.filter(
      (spell) => spell.level === 1 && spell.classes.includes(newKey)
    ).map((spell) => spell.name);
    const safeSelected = wizardState.spells?.selected || { cantrips: [], level1: [] };
    const filteredCantrips = nextRequirements.cantrips
      ? safeSelected.cantrips.filter((spell) => nextAvailableCantrips.includes(spell)).slice(0, nextRequirements.cantrips)
      : [];
    const filteredLevel1 = nextRequirements.level1
      ? safeSelected.level1.filter((spell) => nextAvailableLevel1.includes(spell)).slice(0, nextRequirements.level1)
      : [];

    updateSection("class", {
      key: newKey,
      subclassKey: "",
      level: 1,
      skillProficiencies: [],
    });

    updateSection("spells", {
      selected: {
        cantrips: filteredCantrips,
        level1: filteredLevel1,
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

    updateSection("class", {
      ...currentClass,
      skillProficiencies: nextSkills,
    });
  };

  const handleSubclassChange = (e) => {
    const newSubclass = e.target.value;
    updateSection("class", {
      ...currentClass,
      subclassKey: newSubclass,
    });
  };

  const handleSpellToggle = (spellName, levelKey, requiredCount) => {
    const currentSelection = selectedSpells[levelKey] || [];
    const isSelected = currentSelection.includes(spellName);
    if (!isSelected && currentSelection.length >= requiredCount) return;

    const nextSelection = isSelected
      ? currentSelection.filter((name) => name !== spellName)
      : [...currentSelection, spellName];

    updateSection("spells", {
      selected: {
        ...selectedSpells,
        [levelKey]: nextSelection,
      },
    });
  };

  const canContinue = validateClass(wizardState);

  return (
    <WizardCard
      stepTitle="Step 3 – Choose Your Class"
      stepNumber={3}
      totalSteps={steps.length}
      steps={steps}
      onSelectStep={goToStep}
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
              <p className="text-sm text-slate-200">Hit Die: 1d{hitDie} — Level 1 HP: {startingHp}</p>
            ) : (
              <p className="text-sm text-slate-400">Select a class to see hit points.</p>
            )}
            <p className="text-xs text-slate-500 mt-1">Calculated as maximum hit die + CON modifier.</p>
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

        {subclassInfo && (
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold text-amber-300">Subclass</h3>
              <p className="text-sm text-slate-400">Required at level {subclassInfo.requiredLevel}</p>
            </div>
            <div className="space-y-2">
              {subclassInfo.options.map((subclass) => {
                const isSelected = selectedSubclass === subclass.key;
                return (
                  <label
                    key={subclass.key}
                    className={`flex items-center justify-between gap-3 rounded border px-3 py-2 text-sm transition ${
                      isSelected
                        ? "border-amber-500 bg-amber-500/10 text-amber-100"
                        : "border-slate-800 bg-slate-900/80 text-slate-200"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <input
                        type="radio"
                        name="subclass"
                        value={subclass.key}
                        checked={isSelected}
                        onChange={handleSubclassChange}
                        className="mt-1 h-4 w-4 accent-amber-500"
                      />
                      <div>
                        <p className="font-semibold">{subclass.name}</p>
                        <p className="text-slate-400">{subclass.summary}</p>
                      </div>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>
        )}

        <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-semibold text-amber-300">Skill Proficiencies</h3>
            <p className="text-sm text-slate-400">Choose {requiredSkills} {requiredSkills === 1 ? "skill" : "skills"}</p>
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

        {spellRequirements.cantrips > 0 && (
          <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-amber-300">Spell Selection</h3>
              <div className="text-sm text-slate-400 space-x-3">
                <span>
                  Cantrips: {selectedSpells.cantrips.length}/{spellRequirements.cantrips}
                </span>
                {spellRequirements.level1 > 0 && (
                  <span>
                    Level 1 Spells: {selectedSpells.level1.length}/{spellRequirements.level1}
                  </span>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-md font-semibold text-amber-200">Cantrips</h4>
                  <p className="text-xs text-slate-400">
                    Select exactly {spellRequirements.cantrips}
                  </p>
                </div>
                {availableCantrips.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {availableCantrips.map((spell) => {
                      const selected = selectedSpells.cantrips.includes(spell.name);
                      const disableCheckbox =
                        !selected && selectedSpells.cantrips.length >= spellRequirements.cantrips;
                      return (
                        <label
                          key={spell.name}
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
                            onChange={() => handleSpellToggle(spell.name, "cantrips", spellRequirements.cantrips)}
                            className="h-4 w-4 accent-amber-500"
                          />
                          {spell.name}
                        </label>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">No cantrips available for this class.</p>
                )}
                {selectedSpells.cantrips.length !== spellRequirements.cantrips && (
                  <p className="text-sm text-rose-400">Select exactly {spellRequirements.cantrips} cantrips.</p>
                )}
              </div>

              {spellRequirements.level1 > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-md font-semibold text-amber-200">Level 1 Spells</h4>
                    <p className="text-xs text-slate-400">
                      Select exactly {spellRequirements.level1}
                    </p>
                  </div>
                  {availableLevel1.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {availableLevel1.map((spell) => {
                        const selected = selectedSpells.level1.includes(spell.name);
                        const disableCheckbox =
                          !selected && selectedSpells.level1.length >= spellRequirements.level1;
                        return (
                          <label
                            key={spell.name}
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
                              onChange={() => handleSpellToggle(spell.name, "level1", spellRequirements.level1)}
                              className="h-4 w-4 accent-amber-500"
                            />
                            {spell.name}
                          </label>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-400">No level 1 spells available for this class.</p>
                  )}
                  {selectedSpells.level1.length !== spellRequirements.level1 && (
                    <p className="text-sm text-rose-400">Select exactly {spellRequirements.level1} level 1 spells.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </WizardCard>
  );
};

export default ClassStep;
