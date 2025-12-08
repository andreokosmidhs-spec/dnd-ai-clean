/**
 * D&D 5e Class Skill Proficiencies
 * Each class gets to choose a certain number of skills from their class list
 */

export const CLASS_SKILLS = {
  "Barbarian": {
    count: 2,
    skills: [
      "Animal Handling",
      "Athletics",
      "Intimidation",
      "Nature",
      "Perception",
      "Survival"
    ]
  },
  "Bard": {
    count: 3,
    skills: [
      "Acrobatics",
      "Animal Handling",
      "Arcana",
      "Athletics",
      "Deception",
      "History",
      "Insight",
      "Intimidation",
      "Investigation",
      "Medicine",
      "Nature",
      "Perception",
      "Performance",
      "Persuasion",
      "Religion",
      "Sleight of Hand",
      "Stealth",
      "Survival"
    ]
  },
  "Cleric": {
    count: 2,
    skills: [
      "History",
      "Insight",
      "Medicine",
      "Persuasion",
      "Religion"
    ]
  },
  "Druid": {
    count: 2,
    skills: [
      "Arcana",
      "Animal Handling",
      "Insight",
      "Medicine",
      "Nature",
      "Perception",
      "Religion",
      "Survival"
    ]
  },
  "Fighter": {
    count: 2,
    skills: [
      "Acrobatics",
      "Animal Handling",
      "Athletics",
      "History",
      "Insight",
      "Intimidation",
      "Perception",
      "Survival"
    ]
  },
  "Monk": {
    count: 2,
    skills: [
      "Acrobatics",
      "Athletics",
      "History",
      "Insight",
      "Religion",
      "Stealth"
    ]
  },
  "Paladin": {
    count: 2,
    skills: [
      "Athletics",
      "Insight",
      "Intimidation",
      "Medicine",
      "Persuasion",
      "Religion"
    ]
  },
  "Ranger": {
    count: 3,
    skills: [
      "Animal Handling",
      "Athletics",
      "Insight",
      "Investigation",
      "Nature",
      "Perception",
      "Stealth",
      "Survival"
    ]
  },
  "Rogue": {
    count: 4,
    skills: [
      "Acrobatics",
      "Athletics",
      "Deception",
      "Insight",
      "Intimidation",
      "Investigation",
      "Perception",
      "Performance",
      "Persuasion",
      "Sleight of Hand",
      "Stealth"
    ]
  },
  "Sorcerer": {
    count: 2,
    skills: [
      "Arcana",
      "Deception",
      "Insight",
      "Intimidation",
      "Persuasion",
      "Religion"
    ]
  },
  "Warlock": {
    count: 2,
    skills: [
      "Arcana",
      "Deception",
      "History",
      "Intimidation",
      "Investigation",
      "Nature",
      "Religion"
    ]
  },
  "Wizard": {
    count: 2,
    skills: [
      "Arcana",
      "History",
      "Insight",
      "Investigation",
      "Medicine",
      "Religion"
    ]
  }
};

// Skill to ability mapping (for reference)
export const SKILL_ABILITIES = {
  "Acrobatics": "DEX",
  "Animal Handling": "WIS",
  "Arcana": "INT",
  "Athletics": "STR",
  "Deception": "CHA",
  "History": "INT",
  "Insight": "WIS",
  "Intimidation": "CHA",
  "Investigation": "INT",
  "Medicine": "WIS",
  "Nature": "INT",
  "Perception": "WIS",
  "Performance": "CHA",
  "Persuasion": "CHA",
  "Religion": "INT",
  "Sleight of Hand": "DEX",
  "Stealth": "DEX",
  "Survival": "WIS"
};
