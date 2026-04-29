/* Lightweight assertions for computeArmorClass — run with `node ac.test.js`
 * (no jest config needed). Validates D&D 5e formulas across class equipment
 * packs and unarmored-defense features. */

import { computeArmorClass } from "../ac";

const cases = [
  {
    name: "Fighter pack A: Chain Mail + Shield (heavy, no DEX, +2 shield)",
    char: { abilityScores: { dex: 14 }, class: { key: "fighter", equipment: { pack: "A" } } },
    expectAc: 18,
  },
  {
    name: "Fighter pack B: Leather Armor (light, full DEX) + Longbow",
    char: { abilityScores: { dex: 16 }, class: { key: "fighter", equipment: { pack: "B" } } },
    expectAc: 11 + 3, // 14
  },
  {
    name: "Cleric pack A: Scale Mail (medium, DEX cap +2) + Shield",
    char: { abilityScores: { dex: 16 }, class: { key: "cleric", equipment: { pack: "A" } } },
    expectAc: 14 + 2 + 2, // 18
  },
  {
    name: "Wizard pack A (no armor): 10 + DEX",
    char: { abilityScores: { dex: 14 }, class: { key: "wizard", equipment: { pack: "A" } } },
    expectAc: 10 + 2, // 12
  },
  {
    name: "Barbarian (no armor) — Unarmored Defense (DEX + CON)",
    char: { abilityScores: { dex: 14, con: 16 }, class: { key: "barbarian", equipment: { pack: "A" } } },
    expectAc: 10 + 2 + 3, // 15
  },
  {
    name: "Monk (no armor, no shield) — Unarmored Defense (DEX + WIS)",
    char: { abilityScores: { dex: 16, wis: 14 }, class: { key: "monk", equipment: { pack: "A" } } },
    expectAc: 10 + 3 + 2, // 15
  },
  {
    name: "Druid pack A: Wooden Shield + Scimitar + Leather (light + shield)",
    char: { abilityScores: { dex: 12 }, class: { key: "druid", equipment: { pack: "A" } } },
    expectAc: 11 + 1 + 2, // 14
  },
];

let passed = 0;
let failed = 0;
for (const c of cases) {
  const result = computeArmorClass(c.char);
  if (result.ac === c.expectAc) {
    console.log(`✓ ${c.name} → AC ${result.ac} (${result.breakdown})`);
    passed += 1;
  } else {
    console.error(
      `✗ ${c.name} → expected ${c.expectAc}, got ${result.ac} (${result.breakdown})`
    );
    failed += 1;
  }
}
console.log(`\n${passed}/${passed + failed} passed`);
if (failed > 0) process.exit(1);
