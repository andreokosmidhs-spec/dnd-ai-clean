// HP calculation helpers — D&D 5e
//
// Level 1: hit_die + CON modifier (minimum 1)
// Subsequent levels: +(floor(hit_die/2) + 1 + CON modifier) per level
//   (the standard "fixed average" rule, not rolled HP)
//
// Case-insensitive on the class key because the wizard persists PascalCase
// ("Fighter") while legacy tests/manual payloads sometimes used lowercase.

const HIT_DIE_BY_CLASS = {
  barbarian: 12,
  fighter: 10,
  paladin: 10,
  ranger: 10,
  artificer: 8,
  bard: 8,
  cleric: 8,
  druid: 8,
  monk: 8,
  rogue: 8,
  warlock: 8,
  sorcerer: 6,
  wizard: 6,
};

export const getHitDie = (classKey) => {
  const k = String(classKey || "").trim().toLowerCase();
  return HIT_DIE_BY_CLASS[k] ?? null;
};

export const abilityMod = (score) =>
  Number.isFinite(score) ? Math.floor((Number(score) - 10) / 2) : 0;

/**
 * Compute max HP using the standard 5e fixed-average rule.
 * Returns null when the class is unknown so callers can fall back sensibly.
 */
export const computeMaxHp = (classKey, conScore, level = 1) => {
  const hitDie = getHitDie(classKey);
  if (hitDie == null) return null;
  const lvl = Math.max(1, Number(level) || 1);
  const conMod = abilityMod(conScore);
  const baseLvl1 = hitDie + conMod;
  const perLevel = Math.floor(hitDie / 2) + 1 + conMod;
  const total = baseLvl1 + (lvl - 1) * perLevel;
  return Math.max(1, total);
};
