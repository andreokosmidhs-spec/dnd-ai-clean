// Armor Class (AC) calculation — D&D 5e
//
// Derives AC from a V2 character's starting equipment pack, ability scores,
// and class-level "Unarmored Defense" features. Falls back to 10 + DEX mod
// (the standard unarmored AC) when no equipment data is present.
//
// References: PHB Chapter 5 (Armor), Barbarian/Monk class features.

import { abilityMod } from "./hp";
import { CLASS_EQUIPMENT } from "../data/classEquipment";

// armor name (lowercase) -> { base, dexCap, type }
// dexCap === Infinity means full DEX bonus; 0 means no DEX bonus.
const ARMOR_TABLE = {
  // Light — full DEX
  "padded armor": { base: 11, dexCap: Infinity, type: "light" },
  padded: { base: 11, dexCap: Infinity, type: "light" },
  "leather armor": { base: 11, dexCap: Infinity, type: "light" },
  leather: { base: 11, dexCap: Infinity, type: "light" },
  "studded leather": { base: 12, dexCap: Infinity, type: "light" },
  "studded leather armor": { base: 12, dexCap: Infinity, type: "light" },

  // Medium — DEX cap +2
  hide: { base: 12, dexCap: 2, type: "medium" },
  "hide armor": { base: 12, dexCap: 2, type: "medium" },
  "chain shirt": { base: 13, dexCap: 2, type: "medium" },
  "scale mail": { base: 14, dexCap: 2, type: "medium" },
  breastplate: { base: 14, dexCap: 2, type: "medium" },
  "half plate": { base: 15, dexCap: 2, type: "medium" },
  "half plate armor": { base: 15, dexCap: 2, type: "medium" },

  // Heavy — no DEX
  "ring mail": { base: 14, dexCap: 0, type: "heavy" },
  "chain mail": { base: 16, dexCap: 0, type: "heavy" },
  splint: { base: 17, dexCap: 0, type: "heavy" },
  "splint armor": { base: 17, dexCap: 0, type: "heavy" },
  plate: { base: 18, dexCap: 0, type: "heavy" },
  "plate armor": { base: 18, dexCap: 0, type: "heavy" },
};

const SHIELD_NAMES = new Set(["shield", "wooden shield"]);

const findArmor = (items) => {
  for (const raw of items) {
    const name = String(raw || "").toLowerCase().trim();
    if (ARMOR_TABLE[name]) return ARMOR_TABLE[name];
  }
  return null;
};

const hasShield = (items) =>
  items.some((raw) => SHIELD_NAMES.has(String(raw || "").toLowerCase().trim()));

const resolveStartingItems = (classKey, packLetter) => {
  if (!classKey) return [];
  // CLASS_EQUIPMENT is keyed by PascalCase (e.g. "Fighter"); the V2 wizard
  // persists `class.key` as either "Fighter" or "fighter" depending on path.
  const upper = String(classKey).charAt(0).toUpperCase() + String(classKey).slice(1).toLowerCase();
  const entry = CLASS_EQUIPMENT[upper] || CLASS_EQUIPMENT[classKey];
  if (!entry) return [];
  if (packLetter === "B") return entry.packB || [];
  return entry.packA || [];
};

/**
 * Compute AC for a V2 character.
 *
 * @param {object} character - The V2 character (or RPG-shaped legacy object).
 *   Reads `abilityScores.dex|str|con|wis`, `class.key`, `class.equipment.pack`.
 * @returns {{ ac: number, breakdown: string }}
 *   `ac` — final armor class.
 *   `breakdown` — short human label (e.g. "Chain Mail + shield").
 */
export const computeArmorClass = (character) => {
  if (!character) return { ac: 10, breakdown: "no data" };

  // Normalize inputs across V2 and legacy shapes
  const abilities = character.abilityScores || character.stats || {};
  const dex = Number(abilities.dex ?? abilities.dexterity ?? 10);
  const con = Number(abilities.con ?? abilities.constitution ?? 10);
  const wis = Number(abilities.wis ?? abilities.wisdom ?? 10);
  const dexMod = abilityMod(dex);
  const conMod = abilityMod(con);
  const wisMod = abilityMod(wis);

  const cls = character.class || character.class_ || {};
  const classKey = String(cls.key || "").toLowerCase();
  const packLetter = (cls.equipment?.pack || cls.equipment_pack || "A");

  const items = resolveStartingItems(cls.key, packLetter);
  const armor = findArmor(items);
  const shield = hasShield(items);
  const shieldBonus = shield ? 2 : 0;

  // Class-level Unarmored Defense
  // Barbarian: 10 + DEX + CON (shield allowed)
  // Monk:      10 + DEX + WIS (NO shield, NO armor)
  if (!armor && classKey === "barbarian") {
    const ac = 10 + dexMod + conMod + shieldBonus;
    return {
      ac,
      breakdown: `unarmored defense (10 + DEX +${dexMod} + CON +${conMod}${shield ? " + shield" : ""})`,
    };
  }
  if (!armor && !shield && classKey === "monk") {
    return {
      ac: 10 + dexMod + wisMod,
      breakdown: `unarmored defense (10 + DEX +${dexMod} + WIS +${wisMod})`,
    };
  }

  // Standard armor formula
  if (armor) {
    const cappedDex = Math.min(dexMod, armor.dexCap);
    const ac = armor.base + cappedDex + shieldBonus;
    const armorName = items.find((it) => ARMOR_TABLE[String(it || "").toLowerCase().trim()]);
    return {
      ac,
      breakdown: shield ? `${armorName} + shield` : `${armorName}`,
    };
  }

  // Unarmored, no class feature
  const ac = 10 + dexMod + shieldBonus;
  return {
    ac,
    breakdown: shield ? `unarmored + shield` : "unarmored (10 + DEX)",
  };
};
