"""
Spell and feat card catalog for the D&D AI card system.

Spells are adapted for narrative play:
- Cantrips:         per_day=False, uses_max=0  (unlimited, at-will)
- Leveled spells:   per_day=True,  uses_max=1-2 (simplified slot economy)
- Rarity:           common (cantrip) · rare (1-2) · epic (3-5) · legendary (6+)

Feats grant passive bonuses; those with daily abilities carry per_day/uses_max.
"""

from typing import Dict, List, Any


def _spell_rarity(level: int) -> str:
    if level == 0:
        return "common"
    elif level <= 2:
        return "rare"
    elif level <= 5:
        return "epic"
    return "legendary"


# ---------------------------------------------------------------------------
# Spell catalog — keyed by canonical spell name.
# Shared across all class lists; CANTRIPS_BY_CLASS / STARTER_SPELLS_BY_CLASS
# reference these names.
# ---------------------------------------------------------------------------
SPELL_CATALOG: Dict[str, Dict[str, Any]] = {

    # ── CANTRIPS ──────────────────────────────────────────────────────────────
    "Eldritch Blast": {
        "level": 0, "school": "evocation",
        "description": "A crackling beam of eldritch energy streaks toward a creature. Becomes two beams at 5th level, three at 11th, four at 17th.",
        "mechanical": "Ranged atk: 1d10 force · 120 ft · extra beams at 5/11/17",
    },
    "Fire Bolt": {
        "level": 0, "school": "evocation",
        "description": "A mote of fire hurled at a target. Ignites flammable objects. Grows more powerful at higher levels.",
        "mechanical": "Ranged atk: 1d10 fire · 120 ft · 2d10@5 · 3d10@11 · 4d10@17",
    },
    "Sacred Flame": {
        "level": 0, "school": "evocation",
        "description": "Flame-like radiance descends from the heavens. No cover protects the target.",
        "mechanical": "DEX save: 1d8 radiant · ignores cover · 60 ft · 2d8@5",
    },
    "Vicious Mockery": {
        "level": 0, "school": "enchantment",
        "description": "A string of insults laced with magic leaves the target doubting itself on its next attack.",
        "mechanical": "WIS save: 1d4 psychic · disadv on next attack roll · 60 ft",
    },
    "Guidance": {
        "level": 0, "school": "divination",
        "description": "You touch a willing creature to bolster its next ability check.",
        "mechanical": "Touch: +1d4 to one ability check · concentration 1 min",
    },
    "Shillelagh": {
        "level": 0, "school": "transmutation",
        "description": "The wood of a club or quarterstaff is imbued with nature's power.",
        "mechanical": "Your staff/club: 1d8 magic damage · use WIS to hit · 1 min",
    },
    "Produce Flame": {
        "level": 0, "school": "conjuration",
        "description": "A flickering flame appears in your hand, lighting the area and threatening foes.",
        "mechanical": "Light 10 ft · throw: ranged atk 1d8 fire · 30 ft range",
    },
    "Thorn Whip": {
        "level": 0, "school": "transmutation",
        "description": "A vine-like whip of thorns strikes and pulls a creature toward you.",
        "mechanical": "Melee atk: 1d6 piercing · pull 10 ft toward you · 30 ft",
    },
    "Mage Hand": {
        "level": 0, "school": "conjuration",
        "description": "A spectral floating hand appears and manipulates objects at your command.",
        "mechanical": "Spectral hand: carry ≤10 lbs · open/close · 30 ft · 1 min",
    },
    "Minor Illusion": {
        "level": 0, "school": "illusion",
        "description": "You create a sound or a static image within a 5-foot cube for up to 1 minute.",
        "mechanical": "Sound or static image in 5 ft cube · 30 ft range · 1 min",
    },
    "Prestidigitation": {
        "level": 0, "school": "transmutation",
        "description": "Minor magical tricks conjured in an instant — sparks, scents, small illusions.",
        "mechanical": "Cosmetic effects: spark/clean/soil/mark/warm/chill/flavor",
    },
    "Shocking Grasp": {
        "level": 0, "school": "evocation",
        "description": "Lightning springs from your hand, delivering a shock that prevents the target from reacting.",
        "mechanical": "Melee atk: 1d8 lightning · target loses reaction · adv vs metal armor",
    },
    "Chill Touch": {
        "level": 0, "school": "necromancy",
        "description": "A ghostly skeletal hand disrupts life force and prevents the target from healing.",
        "mechanical": "Ranged atk: 1d8 necrotic · no healing next turn · 120 ft",
    },
    "Ray of Frost": {
        "level": 0, "school": "evocation",
        "description": "A frigid beam of blue-white light slows your target.",
        "mechanical": "Ranged atk: 1d8 cold · −10 ft speed until next turn · 60 ft",
    },
    "Thaumaturgy": {
        "level": 0, "school": "transmutation",
        "description": "You manifest a minor wonder — a sign of supernatural power that impresses onlookers.",
        "mechanical": "Divine tricks: booming voice/tremors/flames/door/eye color · 1 min",
    },
    "Toll the Dead": {
        "level": 0, "school": "necromancy",
        "description": "You point at one creature and the sound of a dolorous bell fills the air around it.",
        "mechanical": "WIS save: 1d8 necrotic · 1d12 if already damaged · 60 ft",
    },
    "Mending": {
        "level": 0, "school": "transmutation",
        "description": "This spell repairs a single break or tear in an object.",
        "mechanical": "Repair 1 ft break/tear in object · 1 min cast",
    },
    "Thunderclap": {
        "level": 0, "school": "evocation",
        "description": "A burst of thunderous sound erupts from you, audible 100 feet away.",
        "mechanical": "CON save: 1d6 thunder · all creatures within 5 ft of you",
    },
    "Spare the Dying": {
        "level": 0, "school": "necromancy",
        "description": "You touch a dying creature and stabilize it instantly.",
        "mechanical": "Touch: creature at 0 HP stabilized (no death saves needed)",
    },

    # ── LEVEL 1 SPELLS ────────────────────────────────────────────────────────
    "Magic Missile": {
        "level": 1, "school": "evocation",
        "description": "Three darts of magical force unerringly seek your targets — they cannot miss.",
        "mechanical": "3 darts: 1d4+1 force each · auto-hit · 120 ft · +1 dart/slot",
        "per_day": True, "uses_max": 2,
    },
    "Shield": {
        "level": 1, "school": "abjuration",
        "description": "An invisible barrier of magical force appears and protects you until your next turn.",
        "mechanical": "React to being hit: +5 AC until start of next turn · blocks Missile",
        "per_day": True, "uses_max": 2,
    },
    "Mage Armor": {
        "level": 1, "school": "abjuration",
        "description": "A protective magical force surrounds an unarmored target.",
        "mechanical": "Touch unarmored creature: AC = 13 + DEX mod · 8 hours",
        "per_day": True, "uses_max": 1,
    },
    "Sleep": {
        "level": 1, "school": "enchantment",
        "description": "A wave of soporific energy sends creatures into magical slumber — lowest HP first.",
        "mechanical": "5d8 HP of creatures sleep · lowest HP first · 90 ft · 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Cure Wounds": {
        "level": 1, "school": "evocation",
        "description": "A creature you touch regains HP as divine or natural magic flows through them.",
        "mechanical": "Touch: heal 1d8+spell mod HP · +1d8/extra slot level",
        "per_day": True, "uses_max": 2,
    },
    "Healing Word": {
        "level": 1, "school": "evocation",
        "description": "A whispered word of power that can restore life even from across the room.",
        "mechanical": "Bonus action: 1d4+spell mod HP · 60 ft range · +1d4/slot",
        "per_day": True, "uses_max": 2,
    },
    "Bless": {
        "level": 1, "school": "enchantment",
        "description": "Divine favor bolsters up to three creatures, adding to their attack rolls and saving throws.",
        "mechanical": "3 creatures: +1d4 to atk rolls and saves · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Guiding Bolt": {
        "level": 1, "school": "evocation",
        "description": "A flash of light streaks toward a creature. The next attack against it has advantage.",
        "mechanical": "Ranged atk: 4d6 radiant · next atk roll vs target has adv · 120 ft",
        "per_day": True, "uses_max": 2,
    },
    "Shield of Faith": {
        "level": 1, "school": "abjuration",
        "description": "A shimmering field of divine force surrounds a creature you can see.",
        "mechanical": "Touch or 60 ft: +2 AC · concentration 10 min",
        "per_day": True, "uses_max": 2,
    },
    "Charm Person": {
        "level": 1, "school": "enchantment",
        "description": "You attempt to charm a humanoid. It regards you as a friendly acquaintance while charmed.",
        "mechanical": "WIS save (adv if in combat): friendly humanoid · 1 hour",
        "per_day": True, "uses_max": 2,
    },
    "Thunderwave": {
        "level": 1, "school": "evocation",
        "description": "A wave of thunderous force sweeps outward, hurling creatures and objects away.",
        "mechanical": "CON save: 2d8 thunder + push 10 ft · 15 ft cube from self",
        "per_day": True, "uses_max": 2,
    },
    "Entangle": {
        "level": 1, "school": "conjuration",
        "description": "Grasping weeds and vines sprout from the ground, restraining those who fail to dodge.",
        "mechanical": "STR save: restrained · 20 ft sq difficult terrain · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Faerie Fire": {
        "level": 1, "school": "evocation",
        "description": "Each object in a 20-foot cube is outlined in light. Attackers have advantage against lit targets.",
        "mechanical": "DEX save: outlined in light · attackers have adv · 60 ft · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Hex": {
        "level": 1, "school": "enchantment",
        "description": "You place a curse on a creature — it takes bonus necrotic damage and suffers on ability checks.",
        "mechanical": "+1d6 necrotic on atks vs target · disadv on chosen ability · conc 1 hr",
        "per_day": True, "uses_max": 2,
    },
    "Armor of Agathys": {
        "level": 1, "school": "abjuration",
        "description": "A protective magical force deals cold damage to any who strike you.",
        "mechanical": "+5 temp HP · attacker takes 5 cold when they hit you · scales +5/slot",
        "per_day": True, "uses_max": 2,
    },
    "Hellish Rebuke": {
        "level": 1, "school": "evocation",
        "description": "You point your finger and the creature that damaged you is momentarily surrounded in hellfire.",
        "mechanical": "React when damaged: DEX save 2d10 fire vs attacker · +1d10/slot",
        "per_day": True, "uses_max": 2,
    },
    "Hunter's Mark": {
        "level": 1, "school": "divination",
        "description": "You choose a creature and mark it as your quarry for the hunt.",
        "mechanical": "+1d6 on atks vs marked · bonus action move mark on kill · conc 1 hr",
        "per_day": True, "uses_max": 2,
    },
    "Divine Favor": {
        "level": 1, "school": "evocation",
        "description": "Your prayer empowers your weapon strikes with divine radiant energy.",
        "mechanical": "Bonus action: +1d4 radiant on weapon hits each turn · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Command": {
        "level": 1, "school": "enchantment",
        "description": "You speak a one-word command to a creature — it must obey if it fails its save.",
        "mechanical": "WIS save: one-word command — approach/drop/flee/grovel/halt",
        "per_day": True, "uses_max": 2,
    },
    "Hideous Laughter": {
        "level": 1, "school": "enchantment",
        "description": "A creature perceives everything as hilariously funny and falls into fits of laughter.",
        "mechanical": "WIS save: prone and incapacitated · conc 1 min · new save each turn",
        "per_day": True, "uses_max": 2,
    },
    "Goodberry": {
        "level": 1, "school": "transmutation",
        "description": "Ten berries appear that restore HP and sustain a creature for a full day each.",
        "mechanical": "10 berries: each restores 1 HP · 1 berry = full day's nourishment",
        "per_day": True, "uses_max": 1,
    },
    "Fog Cloud": {
        "level": 1, "school": "conjuration",
        "description": "A 20-foot radius sphere of thick fog heavily obscures everything within it.",
        "mechanical": "20 ft sphere: heavily obscured · conc 1 hr · 120 ft range",
        "per_day": True, "uses_max": 2,
    },
    "Speak with Animals": {
        "level": 1, "school": "divination",
        "description": "You comprehend and verbally communicate with beasts for the duration.",
        "mechanical": "Communicate with beasts · know their mood/memory · 10 min",
        "per_day": True, "uses_max": 1,
    },
    "Detect Magic": {
        "level": 1, "school": "divination",
        "description": "Sense the presence and school of magic on creatures, objects, or locations within 30 ft.",
        "mechanical": "Sense magic 30 ft · see auras · identify school · conc 10 min",
        "per_day": True, "uses_max": 1,
    },
    "Burning Hands": {
        "level": 1, "school": "evocation",
        "description": "A thin sheet of flames shoots forth from your outstretched fingertips.",
        "mechanical": "DEX save: 3d6 fire · 15 ft cone · ignites flammable objects",
        "per_day": True, "uses_max": 2,
    },
    "Ensnaring Strike": {
        "level": 1, "school": "conjuration",
        "description": "The next time you hit a creature, writhing mass of thorny vines appear, restraining it.",
        "mechanical": "Next hit: STR save or restrained + 1d6 piercing/turn · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Witch Bolt": {
        "level": 1, "school": "evocation",
        "description": "A beam of crackling blue energy lances out toward a creature, forming a sustained arc.",
        "mechanical": "Ranged atk: 1d12 lightning · action each turn: 1d12 more · conc 1 min",
        "per_day": True, "uses_max": 2,
    },

    # ── LEVEL 2 SPELLS ────────────────────────────────────────────────────────
    "Misty Step": {
        "level": 2, "school": "conjuration",
        "description": "Briefly surrounded by silvery mist, you teleport to an unoccupied visible space.",
        "mechanical": "Bonus action: teleport up to 30 ft to visible unoccupied space",
        "per_day": True, "uses_max": 2,
    },
    "Hold Person": {
        "level": 2, "school": "enchantment",
        "description": "Choose a humanoid — paralyzed if it fails its WIS save. Save again each turn.",
        "mechanical": "WIS save: paralyzed humanoid · conc 1 min · new save each turn",
        "per_day": True, "uses_max": 2,
    },
    "Invisibility": {
        "level": 2, "school": "illusion",
        "description": "A creature becomes invisible until the spell ends — or until it attacks or casts.",
        "mechanical": "Touch: invisible until attack/cast · conc 1 hour · +1 creature/slot",
        "per_day": True, "uses_max": 2,
    },
    "Scorching Ray": {
        "level": 2, "school": "evocation",
        "description": "You create three rays of fire and hurl them at targets within range.",
        "mechanical": "3 ranged atk rays: 2d6 fire each · 120 ft · +1 ray/slot",
        "per_day": True, "uses_max": 2,
    },
    "Mirror Image": {
        "level": 2, "school": "illusion",
        "description": "Three illusory duplicates appear around you. Attackers might hit a copy instead.",
        "mechanical": "3 illusory copies: attacker rolls d20 (6+=copy hit) · 1 min no conc",
        "per_day": True, "uses_max": 2,
    },
    "Aid": {
        "level": 2, "school": "abjuration",
        "description": "Your spell bolsters allies with resolve and physical toughness.",
        "mechanical": "3 creatures: +5 max HP and current HP · 8 hours · +5 HP/slot",
        "per_day": True, "uses_max": 2,
    },
    "Spiritual Weapon": {
        "level": 2, "school": "evocation",
        "description": "You create a floating, spectral weapon that attacks at your command.",
        "mechanical": "Bonus action summon: 1d8+spell mod force · move 20 ft · 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Lesser Restoration": {
        "level": 2, "school": "abjuration",
        "description": "You channel positive energy into a creature to cleanse a debilitating condition.",
        "mechanical": "Touch: cure one disease or blinded/deafened/paralyzed/poisoned",
        "per_day": True, "uses_max": 2,
    },
    "Pass Without Trace": {
        "level": 2, "school": "abjuration",
        "description": "A veil of shadows and silence radiates from you, concealing your group.",
        "mechanical": "Group: +10 Stealth · can't be tracked by nonmagical means · conc 1 hr",
        "per_day": True, "uses_max": 2,
    },
    "Shatter": {
        "level": 2, "school": "evocation",
        "description": "A loud ringing noise bursts out painfully from a point — devastating crystalline things.",
        "mechanical": "CON save: 3d8 thunder · 10 ft radius · disadv if inorganic/metal",
        "per_day": True, "uses_max": 2,
    },
    "Silence": {
        "level": 2, "school": "illusion",
        "description": "For the duration, no sound can be created within or pass through a 20-foot sphere.",
        "mechanical": "20 ft sphere: no sound in/out · verbal spells impossible inside · conc 10 min",
        "per_day": True, "uses_max": 2,
    },
    "Moonbeam": {
        "level": 2, "school": "evocation",
        "description": "A silvery beam of pale light rains down. Shapechangers take extra damage.",
        "mechanical": "CON save: 2d10 radiant · 5 ft cyl · +2d10 vs shapechangers · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Barkskin": {
        "level": 2, "school": "transmutation",
        "description": "A creature's skin becomes rough and bark-like, providing natural armor.",
        "mechanical": "Touch: AC can't drop below 16 · conc 1 hour",
        "per_day": True, "uses_max": 2,
    },
    "Darkness": {
        "level": 2, "school": "evocation",
        "description": "Magical darkness spreads from a point, defeating darkvision and mundane lights.",
        "mechanical": "60 ft sphere of magical dark · blocks darkvision · conc 10 min",
        "per_day": True, "uses_max": 2,
    },
    "Phantasmal Force": {
        "level": 2, "school": "illusion",
        "description": "You craft an illusion that takes root in the mind of a creature, seeming utterly real.",
        "mechanical": "INT save: believe illusion real · 1d6 psychic/turn · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Suggestion": {
        "level": 2, "school": "enchantment",
        "description": "You suggest a reasonable course of activity to a creature that can understand you.",
        "mechanical": "WIS save: follow reasonable suggestion · conc 8 hours",
        "per_day": True, "uses_max": 2,
    },
    "Spike Growth": {
        "level": 2, "school": "transmutation",
        "description": "The ground in a 20-foot radius bristles with hard spikes that hinder and injure movement.",
        "mechanical": "20 ft radius: difficult terrain · 2d4 piercing per 5 ft moved · conc 10 min",
        "per_day": True, "uses_max": 2,
    },
    "Zone of Truth": {
        "level": 2, "school": "enchantment",
        "description": "A magical zone guards against deception — creatures within cannot tell deliberate lies.",
        "mechanical": "CHA save: can't lie · know who's affected · 15 ft sphere · 10 min",
        "per_day": True, "uses_max": 1,
    },
    "Blur": {
        "level": 2, "school": "illusion",
        "description": "Your body becomes blurred, shifting and wavering — making you harder to hit.",
        "mechanical": "Attackers have disadv against you (unless they have blindsight) · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Branding Smite": {
        "level": 2, "school": "evocation",
        "description": "The next time you hit with a weapon, the weapon gleams with a brand of divine power.",
        "mechanical": "Next melee hit: +2d6 radiant · target sheds light · visible if invis · conc 1 min",
        "per_day": True, "uses_max": 2,
    },

    # ── LEVEL 3 SPELLS ────────────────────────────────────────────────────────
    "Fireball": {
        "level": 3, "school": "evocation",
        "description": "A bright streak flashes to a point and blossoms with a low roar into a fiery explosion.",
        "mechanical": "DEX save: 8d6 fire · 20 ft radius sphere · 150 ft · +1d6/slot",
        "per_day": True, "uses_max": 2,
    },
    "Lightning Bolt": {
        "level": 3, "school": "evocation",
        "description": "A stroke of lightning forming a 100-foot line blasts out from you.",
        "mechanical": "DEX save: 8d6 lightning · 100 ft line 5 ft wide · +1d6/slot",
        "per_day": True, "uses_max": 2,
    },
    "Counterspell": {
        "level": 3, "school": "abjuration",
        "description": "You attempt to interrupt a creature in the process of casting a spell.",
        "mechanical": "React: auto-counter ≤3rd-level spell · higher level needs Arcana check",
        "per_day": True, "uses_max": 2,
    },
    "Dispel Magic": {
        "level": 3, "school": "abjuration",
        "description": "Choose a creature, object, or magical effect — spell effects on it may end.",
        "mechanical": "Auto-end ≤3rd-level effects · higher level needs Arcana check",
        "per_day": True, "uses_max": 2,
    },
    "Revivify": {
        "level": 3, "school": "necromancy",
        "description": "You touch a creature that has died within the last minute, restoring life at 1 HP.",
        "mechanical": "Dead within 1 min: return at 1 HP · −4 penalty fades · 300gp diamond",
        "per_day": True, "uses_max": 1,
    },
    "Fly": {
        "level": 3, "school": "transmutation",
        "description": "You touch a willing creature — it gains a flying speed of 60 feet.",
        "mechanical": "Touch: fly speed 60 ft · conc 10 min · +1 creature/slot",
        "per_day": True, "uses_max": 2,
    },
    "Haste": {
        "level": 3, "school": "transmutation",
        "description": "A willing creature's speed doubles, its reflexes sharpen, and it gains an extra action.",
        "mechanical": "2× speed · +2 AC · extra Attack action each turn · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Spirit Guardians": {
        "level": 3, "school": "conjuration",
        "description": "You call forth spirits to protect you. They flit around you in a 15-foot aura.",
        "mechanical": "WIS save: 3d8 radiant or necrotic each turn in 15 ft · conc 10 min",
        "per_day": True, "uses_max": 2,
    },
    "Mass Healing Word": {
        "level": 3, "school": "evocation",
        "description": "A flood of healing energy flows into up to six creatures you choose within range.",
        "mechanical": "Bonus action · 6 creatures: 1d4+spell mod HP each · 60 ft",
        "per_day": True, "uses_max": 1,
    },
    "Fear": {
        "level": 3, "school": "illusion",
        "description": "You project a phantasmal image of each creature's deepest fears.",
        "mechanical": "WIS save: frightened + drop items + must flee · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Hypnotic Pattern": {
        "level": 3, "school": "illusion",
        "description": "A twisting pattern of colors weaves through the air, entrancing those who see it.",
        "mechanical": "WIS save: incapacitated (charmed) · 30 ft cube · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Major Image": {
        "level": 3, "school": "illusion",
        "description": "You create a realistic image with sight, sound, smell, and temperature.",
        "mechanical": "20 ft cube illusion · sight/sound/smell/temp · conc 10 min · 120 ft",
        "per_day": True, "uses_max": 2,
    },
    "Hunger of Hadar": {
        "level": 3, "school": "conjuration",
        "description": "You open a gateway to the dark between the stars — a region of malevolent nothingness.",
        "mechanical": "Blinded in 20 ft sphere · 2d6 cold + 2d6 acid each turn · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Bestow Curse": {
        "level": 3, "school": "necromancy",
        "description": "You touch a creature and bestow a terrible curse upon it.",
        "mechanical": "WIS save: disadv on chosen ability · or −1d8 on atks/saves · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Call Lightning": {
        "level": 3, "school": "conjuration",
        "description": "A storm cloud appears 100 feet above you. You call down lightning bolts from it.",
        "mechanical": "Action: DEX save 3d10 lightning from cloud · conc 10 min · 120 ft",
        "per_day": True, "uses_max": 2,
    },
    "Conjure Animals": {
        "level": 3, "school": "conjuration",
        "description": "You summon fey spirits that take the form of beasts to aid you.",
        "mechanical": "Summon beasts: 8×CR¼ · 4×CR½ · 2×CR1 · 1×CR2 · conc 1 hour",
        "per_day": True, "uses_max": 1,
    },
    "Aura of Vitality": {
        "level": 3, "school": "evocation",
        "description": "Healing energy radiates from you in a 30-foot aura.",
        "mechanical": "Bonus action each turn: 2d6 HP to one creature in 30 ft · conc 1 min",
        "per_day": True, "uses_max": 2,
    },
    "Nondetection": {
        "level": 3, "school": "abjuration",
        "description": "For the duration, you hide a target from divination magic.",
        "mechanical": "Touch: immune to divination/scrying/truesight · 8 hours",
        "per_day": True, "uses_max": 1,
    },
    "Lightning Arrow": {
        "level": 3, "school": "transmutation",
        "description": "The next time you make a ranged weapon attack, the missile transforms into a bolt of lightning.",
        "mechanical": "Ranged atk: 4d8 lightning on hit · DEX save 2d8 to adjacent creatures",
        "per_day": True, "uses_max": 2,
    },
    "Plant Growth": {
        "level": 3, "school": "transmutation",
        "description": "You channel vitality into plants within a specific area, causing instant overgrowth.",
        "mechanical": "100 ft radius: difficult terrain through thick overgrowth · or enrich soil",
        "per_day": True, "uses_max": 1,
    },
    "Conjure Barrage": {
        "level": 3, "school": "conjuration",
        "description": "You throw a nonmagical weapon or fire a piece of ammunition into the air.",
        "mechanical": "DEX save: 3d8 of weapon type · 60 ft cone",
        "per_day": True, "uses_max": 1,
    },

    # ── LEVEL 4 SPELLS ────────────────────────────────────────────────────────
    "Greater Invisibility": {
        "level": 4, "school": "illusion",
        "description": "You or a creature you touch becomes invisible — even while attacking or casting.",
        "mechanical": "Touch: invisible even during attacks/spells · conc 1 min",
        "per_day": True, "uses_max": 1,
    },
    "Polymorph": {
        "level": 4, "school": "transmutation",
        "description": "This spell transforms a creature into a new beast form, using that form's HP.",
        "mechanical": "WIS save: transform into beast (CR ≤ level) · conc 1 hour",
        "per_day": True, "uses_max": 1,
    },
    "Banishment": {
        "level": 4, "school": "abjuration",
        "description": "You attempt to send one creature to another plane of existence.",
        "mechanical": "CHA save: native→demiplane or extraplanar→home plane · conc 1 min",
        "per_day": True, "uses_max": 1,
    },
    "Dimension Door": {
        "level": 4, "school": "conjuration",
        "description": "You teleport yourself from your current location to any spot within range.",
        "mechanical": "Teleport self + 1 willing: any known point within 500 ft",
        "per_day": True, "uses_max": 1,
    },
    "Death Ward": {
        "level": 4, "school": "abjuration",
        "description": "You touch a creature and grant it a measure of protection from death.",
        "mechanical": "Touch: survive to 1 HP instead of dying · one time only · 8 hours",
        "per_day": True, "uses_max": 2,
    },
    "Confusion": {
        "level": 4, "school": "enchantment",
        "description": "This spell assaults and twists creatures' minds, spawning delusions and causing them to act randomly.",
        "mechanical": "WIS save: random actions each turn · 10 ft radius · conc 1 min",
        "per_day": True, "uses_max": 1,
    },
    "Guardian of Faith": {
        "level": 4, "school": "conjuration",
        "description": "A spectral guardian appears in an unoccupied space near you and remains there.",
        "mechanical": "Spectral guardian 10 ft: DEX save 20 radiant to enemies · 60 total dmg",
        "per_day": True, "uses_max": 1,
    },
    "Freedom of Movement": {
        "level": 4, "school": "abjuration",
        "description": "You touch a willing creature. It moves freely regardless of conditions.",
        "mechanical": "Touch: ignore difficult terrain · no restraint/paralysis from nonmagical · 1 hr",
        "per_day": True, "uses_max": 2,
    },
    "Conjure Woodland Beings": {
        "level": 4, "school": "conjuration",
        "description": "You summon fey creatures that appear in unoccupied spaces that you can see within range.",
        "mechanical": "Summon fey: 8×CR¼ · 4×CR½ · 2×CR1 · 1×CR2 · conc 1 hour",
        "per_day": True, "uses_max": 1,
    },
    "Aura of Life": {
        "level": 4, "school": "abjuration",
        "description": "Life-preserving energy radiates from you, protecting allies in a 30-foot aura.",
        "mechanical": "30 ft aura: resist necrotic · dropped to 0 regains 1 HP/turn · conc 10 min",
        "per_day": True, "uses_max": 1,
    },
    "Staggering Smite": {
        "level": 4, "school": "evocation",
        "description": "The next time you hit, the strike overwhelms the creature's mind.",
        "mechanical": "Next melee hit: +4d6 psychic · WIS save or disadv + no reactions next turn",
        "per_day": True, "uses_max": 1,
    },

    # ── LEVEL 5 SPELLS ────────────────────────────────────────────────────────
    "Hold Monster": {
        "level": 5, "school": "enchantment",
        "description": "Choose any creature — if it fails its WIS save, it is paralyzed.",
        "mechanical": "WIS save: any creature paralyzed · conc 1 min · new save each turn",
        "per_day": True, "uses_max": 1,
    },
    "Mass Cure Wounds": {
        "level": 5, "school": "evocation",
        "description": "A wave of healing energy washes over up to six creatures of your choice.",
        "mechanical": "6 creatures in 30 ft: 3d8+spell mod HP each · +1d8/slot",
        "per_day": True, "uses_max": 1,
    },
    "Animate Dead": {
        "level": 5, "school": "necromancy",
        "description": "This spell creates undead servants from corpses or piles of bones.",
        "mechanical": "Raise up to 3 skeletons/zombies as servants · obey commands · 24 hr",
        "per_day": True, "uses_max": 1,
    },
    "Dominate Person": {
        "level": 5, "school": "enchantment",
        "description": "You attempt to beguile a humanoid that you can see within range.",
        "mechanical": "WIS save: telepathic control of humanoid · conc 1 min",
        "per_day": True, "uses_max": 1,
    },
    "Animate Objects": {
        "level": 5, "school": "transmutation",
        "description": "Objects come to life at your command, attacking your enemies.",
        "mechanical": "Animate ≤10 Tiny/5 Small/2 Med/1 Large objects as servants · conc 1 min",
        "per_day": True, "uses_max": 1,
    },
    "Raise Dead": {
        "level": 5, "school": "necromancy",
        "description": "You return a dead creature back to life — provided it has been dead no longer than 10 days.",
        "mechanical": "Dead ≤10 days: 1 HP · −4 to checks (fades) · needs 500gp diamond",
        "per_day": True, "uses_max": 1,
    },
    "Destructive Wave": {
        "level": 5, "school": "evocation",
        "description": "You strike the ground, creating a burst of divine energy that ripples outward from you.",
        "mechanical": "CON save: 5d6 thunder + 5d6 radiant or necrotic · 30 ft radius · prone",
        "per_day": True, "uses_max": 1,
    },
    "Scrying": {
        "level": 5, "school": "divination",
        "description": "You can see and hear a creature you choose that is on the same plane of existence.",
        "mechanical": "WIS save (modified by familiarity): observe target · conc 10 min",
        "per_day": True, "uses_max": 1,
    },
    "Cone of Cold": {
        "level": 5, "school": "evocation",
        "description": "A blast of cold air erupts from your hands. Killed creatures become ice statues.",
        "mechanical": "CON save: 8d8 cold · 60 ft cone · killed=ice statue · +1d8/slot",
        "per_day": True, "uses_max": 1,
    },
    "Conjure Elemental": {
        "level": 5, "school": "conjuration",
        "description": "You call forth an elemental servant from one of the four elemental planes.",
        "mechanical": "Summon CR 5 elemental (air/earth/fire/water) · conc 1 hour",
        "per_day": True, "uses_max": 1,
    },
    "Swift Quiver": {
        "level": 5, "school": "transmutation",
        "description": "Your quiver produces an endless supply of nonmagical ammunition.",
        "mechanical": "Bonus action: 2 extra ranged weapon attacks each turn · conc 1 min",
        "per_day": True, "uses_max": 1,
    },
    "Conjure Volley": {
        "level": 5, "school": "conjuration",
        "description": "You fire a piece of ammunition from a ranged weapon that transforms into a volley.",
        "mechanical": "DEX save: 8d8 of ammo type · 40 ft radius · 150 ft range",
        "per_day": True, "uses_max": 1,
    },
    "Wall of Force": {
        "level": 5, "school": "evocation",
        "description": "An invisible wall of force springs into existence — immune to all damage.",
        "mechanical": "Immune to physical and magical damage · conc 10 min · 120 ft",
        "per_day": True, "uses_max": 1,
    },
    "Awaken": {
        "level": 5, "school": "transmutation",
        "description": "After spending the casting time tracing magical pathways within a precious gemstone, you touch a huge or smaller beast or plant. It gains an Intelligence of 10, speaks one language, and is charmed by you for 30 days.",
        "mechanical": "Beast or plant: Intelligence 10 · speaks one language · charmed 30 days",
        "per_day": True, "uses_max": 1,
    },
}


# ---------------------------------------------------------------------------
# Which cantrips each class starts with at character creation.
# ---------------------------------------------------------------------------
CANTRIPS_BY_CLASS: Dict[str, List[str]] = {
    "Wizard":    ["Fire Bolt", "Mage Hand", "Prestidigitation", "Minor Illusion", "Shocking Grasp"],
    "Sorcerer":  ["Fire Bolt", "Mage Hand", "Prestidigitation", "Ray of Frost", "Shocking Grasp"],
    "Warlock":   ["Eldritch Blast", "Chill Touch", "Minor Illusion", "Prestidigitation", "Mage Hand"],
    "Bard":      ["Vicious Mockery", "Minor Illusion", "Prestidigitation", "Mage Hand", "Thunderclap"],
    "Cleric":    ["Sacred Flame", "Guidance", "Toll the Dead", "Thaumaturgy", "Spare the Dying"],
    "Druid":     ["Shillelagh", "Guidance", "Produce Flame", "Thorn Whip", "Mending"],
    "Paladin":   [],  # No cantrips in base class
    "Ranger":    [],  # No cantrips in base class
    "Fighter":   [],
    "Rogue":     [],
    "Barbarian": [],
    "Monk":      [],
}

# ---------------------------------------------------------------------------
# Starting leveled spells per class — iconic picks seeded at character creation.
# ---------------------------------------------------------------------------
STARTER_SPELLS_BY_CLASS: Dict[str, List[str]] = {
    "Wizard":    ["Magic Missile", "Shield", "Mage Armor", "Sleep", "Detect Magic"],
    "Sorcerer":  ["Magic Missile", "Shield", "Sleep", "Charm Person", "Burning Hands"],
    "Warlock":   ["Hex", "Armor of Agathys", "Hellish Rebuke", "Charm Person", "Command"],
    "Bard":      ["Healing Word", "Charm Person", "Hideous Laughter", "Thunderwave", "Sleep"],
    "Cleric":    ["Cure Wounds", "Healing Word", "Bless", "Guiding Bolt", "Shield of Faith"],
    "Druid":     ["Entangle", "Healing Word", "Faerie Fire", "Thunderwave", "Speak with Animals"],
    "Paladin":   ["Bless", "Divine Favor", "Command", "Cure Wounds", "Shield of Faith"],
    "Ranger":    ["Hunter's Mark", "Ensnaring Strike", "Goodberry", "Fog Cloud", "Speak with Animals"],
    "Fighter":   [],
    "Rogue":     [],
    "Barbarian": [],
    "Monk":      [],
}

# ---------------------------------------------------------------------------
# Feat catalog — keyed by feat name.
# Feats with daily abilities carry per_day/uses_max.
# All feats are rarity "rare" unless particularly powerful (epic).
# ---------------------------------------------------------------------------
FEAT_CARDS: Dict[str, Dict[str, Any]] = {
    "Alert": {
        "description": "Always on the lookout for danger. You gain +5 to initiative, can't be surprised while conscious, and hidden attackers gain no advantage against you.",
        "mechanical": "+5 initiative · can't be surprised · hidden attackers: no adv",
        "rarity": "rare",
    },
    "Lucky": {
        "description": "You have inexplicable luck that seems to kick in at just the right moment — three times per day.",
        "mechanical": "3/day: reroll any d20 or force enemy reroll · take the better result",
        "rarity": "epic", "per_day": True, "uses_max": 3,
    },
    "Mobile": {
        "description": "You are exceptionally speedy and agile. You can weave through combat without provoking.",
        "mechanical": "+10 ft speed · Dash ignores OA · no OA from any creature you attacked",
        "rarity": "rare",
    },
    "Tough": {
        "description": "Your hit point maximum increases significantly — retroactively and at every future level.",
        "mechanical": "+2 max HP per level (including past levels)",
        "rarity": "rare",
    },
    "War Caster": {
        "description": "You have practiced casting spells in the midst of combat, learning to maintain focus under pressure.",
        "mechanical": "Adv on Concentration saves · cast as OA reaction · somatic while holding weapons",
        "rarity": "rare",
    },
    "Great Weapon Master": {
        "description": "You've learned to put the full weight of a weapon to your advantage, risking accuracy for raw power.",
        "mechanical": "Opt per atk: −5 to hit for +10 dmg · bonus atk on crit or killing blow",
        "rarity": "epic",
    },
    "Sharpshooter": {
        "description": "You have mastered ranged weapons and can make shots that others find impossible.",
        "mechanical": "Opt per atk: −5 to hit for +10 dmg · ignore 3/4 cover · no disadv at long range",
        "rarity": "epic",
    },
    "Sentinel": {
        "description": "You have mastered techniques to punish every drop in your enemies' guard.",
        "mechanical": "OA reduces speed to 0 · react if adjacent ally attacked · OA even on Disengage",
        "rarity": "rare",
    },
    "Polearm Master": {
        "description": "You can keep your enemies at bay with reach weapons and punish those who enter your space.",
        "mechanical": "Bonus action butt-end atk (1d4) · OA when creatures enter your reach",
        "rarity": "rare",
    },
    "Crossbow Expert": {
        "description": "Thanks to extensive practice with the crossbow, you gain crucial tactical advantages.",
        "mechanical": "No disadv in melee · ignore loading property · bonus hand crossbow atk",
        "rarity": "rare",
    },
    "Resilient": {
        "description": "Choose one ability score. You gain proficiency in saving throws using that ability.",
        "mechanical": "+1 to chosen ability score · proficiency in that ability's saving throws",
        "rarity": "rare",
    },
    "Magic Initiate": {
        "description": "You have dabbled in the magical arts, learning cantrips and a spell from another tradition.",
        "mechanical": "2 cantrips + 1 1st-level spell from chosen class · leveled spell 1/day",
        "rarity": "rare", "per_day": True, "uses_max": 1,
    },
    "Skilled": {
        "description": "You gain proficiency in any combination of three skills or tools of your choice.",
        "mechanical": "Proficiency in 3 skills or tools of your choice",
        "rarity": "common",
    },
    "Athlete": {
        "description": "You have undergone extensive physical training, improving your athleticism.",
        "mechanical": "+1 STR or DEX · stand from prone costs 5 ft · climb/jump at full run speed",
        "rarity": "common",
    },
    "Actor": {
        "description": "Skilled at mimicry and dramatics, you gain advantages when impersonating others.",
        "mechanical": "+1 CHA · mimic voices/mannerisms · adv Deception+Performance while disguised",
        "rarity": "common",
    },
    "Dual Wielder": {
        "description": "You master fighting with two weapons, gaining the following benefits.",
        "mechanical": "+1 AC while holding 2 weapons · dual wield non-light weapons · draw 2 at once",
        "rarity": "rare",
    },
    "Observant": {
        "description": "Quick to notice details of your environment, your passive senses are supernaturally keen.",
        "mechanical": "+1 INT or WIS · read lips · +5 passive Perception and Investigation",
        "rarity": "rare",
    },
    "Inspiring Leader": {
        "description": "You can spend 10 minutes inspiring your companions, shoring up their resolve to fight.",
        "mechanical": "10 min: 6 creatures gain temp HP = your level + CHA mod · 1/short rest",
        "rarity": "rare", "per_day": False, "uses_max": 1,
    },
    "Linguist": {
        "description": "You have studied languages and codes, giving you a facility with all manner of tongues.",
        "mechanical": "+1 INT · learn 3 languages · create/decipher ciphers (INT check)",
        "rarity": "common",
    },
    "Healer": {
        "description": "You are an able physician, allowing you to mend wounds quickly in the field.",
        "mechanical": "Healer's kit: stabilize + 1 HP · spend kit use: restore 1d6+4+HD HP · 1/creature/rest",
        "rarity": "rare",
    },
    "Shield Master": {
        "description": "You use shields not just for protection but also for offense and evasion.",
        "mechanical": "Shove with bonus action · add shield to DEX saves · DEX save success: no damage",
        "rarity": "rare",
    },
    "Tavern Brawler": {
        "description": "Accustomed to rough-and-tumble fighting using whatever happens to be at hand.",
        "mechanical": "+1 STR or CON · unarmed: 1d4 · bonus action grapple on unarmed hit",
        "rarity": "common",
    },
    "Charger": {
        "description": "When you use your action to Dash, you can use a bonus action to make one melee attack.",
        "mechanical": "After Dash (bonus action): +5 dmg on melee hit or push 10 ft",
        "rarity": "common",
    },
    "Dungeon Delver": {
        "description": "Alert to the hidden traps and secret doors found in many dungeons.",
        "mechanical": "Adv Perception+Investigation for traps/secret doors · resist trap dmg · detect traps",
        "rarity": "rare",
    },
    "Grappler": {
        "description": "You've developed the skills necessary to hold your own in close-quarters grappling.",
        "mechanical": "+1 STR · adv atk vs grappled · use action: restrain grappled (STR save)",
        "rarity": "common",
    },
    "Mage Slayer": {
        "description": "You have practiced techniques useful in melee combat against spellcasters.",
        "mechanical": "React: atk adjacent spellcaster · disadv Concentration for adjacent casters",
        "rarity": "rare",
    },
    "Elven Accuracy": {
        "description": "Whenever you have advantage on an attack, you can reroll one die.",
        "mechanical": "+1 DEX/INT/WIS/CHA · advantage atk: reroll one die and use higher",
        "rarity": "rare",
    },
    "Warcaster": {
        "description": "You have practiced casting spells in the midst of combat.",
        "mechanical": "Adv Concentration · cast as opportunity attack reaction · somatic while holding",
        "rarity": "rare",
    },
    "Martial Adept": {
        "description": "You have martial training that allows you to perform special combat maneuvers.",
        "mechanical": "Learn 2 Battle Master maneuvers · 1 superiority die (d6) · refresh on short rest",
        "rarity": "rare", "per_day": False, "uses_max": 1,
    },
    "Savage Attacker": {
        "description": "Once per turn when you roll damage for a melee weapon attack, you can reroll the dice.",
        "mechanical": "Once per turn: reroll melee weapon damage dice · take either result",
        "rarity": "common",
    },
    "Lightly Armored": {
        "description": "You have trained to master the use of light armor.",
        "mechanical": "+1 STR or DEX · proficiency with light armor",
        "rarity": "common",
    },
    "Moderately Armored": {
        "description": "You have trained to master the use of medium armor and shields.",
        "mechanical": "+1 STR or DEX · proficiency with medium armor and shields",
        "rarity": "rare",
    },
    "Heavily Armored": {
        "description": "You have trained to master the use of heavy armor.",
        "mechanical": "+1 STR · proficiency with heavy armor",
        "rarity": "rare",
    },
    "Ritual Caster": {
        "description": "You have learned a number of spells that you can cast as rituals.",
        "mechanical": "Ritual spellbook: 2 1st-level rituals · add more by finding them (INT/WIS/CHA)",
        "rarity": "rare",
    },
}


# ---------------------------------------------------------------------------
# Spell requirements — D&D-style casting constraints for each spell.
# Keys: action_cost, components {V,S,M}, range, duration, concentration, ritual
# Default assumed: action_cost="action", V+S components, concentration inferred
# from "conc" in mechanical text.
# ---------------------------------------------------------------------------
_VS = {"V": True, "S": True, "M": None}
_V  = {"V": True, "S": False, "M": None}
_S  = {"V": False, "S": True, "M": None}

def _M(text: str) -> Dict[str, Any]:
    return {"V": True, "S": True, "M": text}

def _VM(text: str) -> Dict[str, Any]:
    return {"V": True, "S": False, "M": text}

def _SM(text: str) -> Dict[str, Any]:
    return {"V": False, "S": True, "M": text}

SPELL_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    # ── CANTRIPS ────────────────────────────────────────────────────────────
    # save_type / damage_dice / damage_type / half_on_save mark save-based spells
    "Eldritch Blast":  {"components": _VS, "range": "120 ft", "duration": "instantaneous",
                        "damage_type": "force"},
    "Fire Bolt":       {"components": _VS, "range": "120 ft", "duration": "instantaneous",
                        "damage_type": "fire"},
    "Sacred Flame":    {"components": _VS, "range": "60 ft",  "duration": "instantaneous",
                        "save_type": "dex", "half_on_save": False,
                        "damage_dice": "1d8", "damage_type": "radiant"},
    "Vicious Mockery": {"components": _V,  "range": "60 ft",  "duration": "instantaneous",
                        "save_type": "wis", "half_on_save": False,
                        "damage_dice": "1d4", "damage_type": "psychic",
                        "condition_on_fail": "disadvantage on next attack"},
    "Guidance":        {"components": _VS, "range": "touch",  "duration": "1 min", "concentration": True},
    "Shillelagh":      {"action_cost": "bonus_action",
                        "components": _M("mistletoe, shamrock leaf, club or staff"),
                        "range": "touch", "duration": "1 min"},
    "Produce Flame":   {"components": _VS, "range": "self",   "duration": "10 min",
                        "damage_type": "fire"},
    "Thorn Whip":      {"components": _M("plant stem"), "range": "30 ft", "duration": "instantaneous",
                        "damage_type": "piercing"},
    "Mage Hand":       {"components": _VS, "range": "30 ft",  "duration": "1 min"},
    "Minor Illusion":  {"components": _SM("bit of fleece"), "range": "30 ft", "duration": "1 min"},
    "Prestidigitation":{"components": _VS, "range": "10 ft",  "duration": "1 hour"},
    "Shocking Grasp":  {"components": _VS, "range": "touch",  "duration": "instantaneous",
                        "damage_type": "lightning"},
    "Chill Touch":     {"components": _VS, "range": "120 ft", "duration": "1 round",
                        "damage_type": "necrotic"},
    "Ray of Frost":    {"components": _VS, "range": "60 ft",  "duration": "instantaneous",
                        "damage_type": "cold"},
    "Thaumaturgy":     {"components": _V,  "range": "30 ft",  "duration": "1 min"},
    "Toll the Dead":   {"components": _VS, "range": "60 ft",  "duration": "instantaneous",
                        "save_type": "wis", "half_on_save": False,
                        "damage_dice": "1d8", "damage_type": "necrotic"},
    "Mending":         {"components": _M("two lodestones"), "range": "touch", "duration": "instantaneous"},
    "Thunderclap":     {"components": _S,  "range": "5 ft",   "duration": "instantaneous",
                        "save_type": "con", "half_on_save": True,
                        "damage_dice": "1d6", "damage_type": "thunder"},
    "Spare the Dying": {"components": _VS, "range": "touch",  "duration": "instantaneous"},

    # ── LEVEL 1 ──────────────────────────────────────────────────────────────
    "Magic Missile":   {"components": _VS, "range": "120 ft", "duration": "instantaneous"},
    "Shield":          {"action_cost": "reaction",
                        "components": _VS, "range": "self",   "duration": "1 round"},
    "Mage Armor":      {"components": _M("cured leather"), "range": "touch", "duration": "8 hours"},
    "Sleep":           {"components": _M("sand, rose petals, or a cricket"),
                        "range": "90 ft", "duration": "1 min"},
    "Cure Wounds":     {"components": _VS, "range": "touch",  "duration": "instantaneous"},
    "Healing Word":    {"action_cost": "bonus_action",
                        "components": _V,  "range": "60 ft",  "duration": "instantaneous"},
    "Bless":           {"components": _M("holy water"),
                        "range": "30 ft", "duration": "1 min", "concentration": True},
    "Guiding Bolt":    {"components": _VS, "range": "120 ft", "duration": "1 round"},
    "Shield of Faith": {"action_cost": "bonus_action",
                        "components": _M("a small parchment with holy text"),
                        "range": "60 ft", "duration": "10 min", "concentration": True},
    "Charm Person":    {"components": _VS, "range": "30 ft",  "duration": "1 hour",
                        "save_type": "wis", "half_on_save": False,
                        "condition_on_fail": "charmed"},
    "Thunderwave":     {"components": _VS, "range": "self",   "duration": "instantaneous",
                        "save_type": "con", "half_on_save": True,
                        "damage_dice": "2d8", "damage_type": "thunder"},
    "Entangle":        {"components": _VS, "range": "90 ft",  "duration": "1 min", "concentration": True,
                        "save_type": "str", "half_on_save": False,
                        "condition_on_fail": "restrained"},
    "Faerie Fire":     {"components": _V,  "range": "60 ft",  "duration": "1 min", "concentration": True,
                        "save_type": "dex", "half_on_save": False,
                        "condition_on_fail": "outlined (attacks against have advantage)"},
    "Hex":             {"action_cost": "bonus_action",
                        "components": _M("the petrified eye of a newt"),
                        "range": "90 ft", "duration": "1 hour", "concentration": True},
    "Armor of Agathys":{"components": _M("a cup of water"),
                        "range": "self",  "duration": "1 hour"},
    "Hellish Rebuke":  {"action_cost": "reaction",
                        "components": _VS, "range": "60 ft",  "duration": "instantaneous",
                        "save_type": "dex", "half_on_save": True,
                        "damage_dice": "2d10", "damage_type": "fire"},
    "Hunter's Mark":   {"action_cost": "bonus_action",
                        "components": _V,  "range": "90 ft",  "duration": "1 hour", "concentration": True},
    "Divine Favor":    {"action_cost": "bonus_action",
                        "components": _VS, "range": "self",   "duration": "1 min", "concentration": True},
    "Command":         {"components": _V,  "range": "60 ft",  "duration": "1 round",
                        "save_type": "wis", "half_on_save": False,
                        "condition_on_fail": "commanded"},
    "Hideous Laughter":{"components": _M("tiny tarts and a feather"),
                        "range": "30 ft", "duration": "1 min", "concentration": True,
                        "save_type": "wis", "half_on_save": False,
                        "condition_on_fail": "incapacitated (prone laughing)"},
    "Goodberry":       {"components": _M("a sprig of mistletoe"),
                        "range": "touch", "duration": "instantaneous"},
    "Fog Cloud":       {"components": _VS, "range": "120 ft", "duration": "1 hour", "concentration": True},
    "Speak with Animals":{"components": _VS, "range": "self", "duration": "10 min", "ritual": True},
    "Detect Magic":    {"components": _VS, "range": "self",   "duration": "10 min",
                        "concentration": True, "ritual": True},
    "Burning Hands":   {"components": _VS, "range": "self",   "duration": "instantaneous",
                        "save_type": "dex", "half_on_save": True,
                        "damage_dice": "3d6", "damage_type": "fire"},
    "Ensnaring Strike":{"action_cost": "bonus_action",
                        "components": _V,  "range": "self",   "duration": "1 min", "concentration": True},
    "Witch Bolt":      {"components": _M("a twig struck by lightning"),
                        "range": "30 ft", "duration": "1 min", "concentration": True,
                        "damage_type": "lightning"},

    # ── LEVEL 2 ──────────────────────────────────────────────────────────────
    "Misty Step":      {"action_cost": "bonus_action",
                        "components": _V,  "range": "self",   "duration": "instantaneous"},
    "Hold Person":     {"components": _M("a small, straight piece of iron"),
                        "range": "60 ft", "duration": "1 min", "concentration": True,
                        "save_type": "wis", "half_on_save": False,
                        "condition_on_fail": "paralyzed"},
    "Invisibility":    {"components": _M("an eyelash encased in gum arabic"),
                        "range": "touch", "duration": "1 hour", "concentration": True},
    "Scorching Ray":   {"components": _VS, "range": "120 ft", "duration": "instantaneous",
                        "damage_type": "fire"},
    "Mirror Image":    {"components": _VS, "range": "self",   "duration": "1 min"},
    "Aid":             {"components": _M("a tiny strip of white cloth"),
                        "range": "30 ft", "duration": "8 hours"},
    "Spiritual Weapon":{"action_cost": "bonus_action",
                        "components": _VS, "range": "60 ft",  "duration": "1 min"},
    "Lesser Restoration":{"components": _VS, "range": "touch","duration": "instantaneous"},
    "Pass Without Trace":{"components": _M("ashes from a burned leaf of mistletoe and a sprig of spruce"),
                        "range": "self",  "duration": "1 hour", "concentration": True},
    "Shatter":         {"components": _M("a chip of mica"),
                        "range": "60 ft", "duration": "instantaneous",
                        "save_type": "con", "half_on_save": True,
                        "damage_dice": "3d8", "damage_type": "thunder"},
    "Silence":         {"components": _VS, "range": "120 ft", "duration": "10 min",
                        "concentration": True, "ritual": True},
    "Moonbeam":        {"components": _M("several seeds of any moonseed plant and a piece of opalescent feldspar"),
                        "range": "120 ft","duration": "1 min", "concentration": True},
    "Barkskin":        {"components": _M("a handful of oak bark"),
                        "range": "touch", "duration": "1 hour", "concentration": True},
    "Darkness":        {"components": _VM("bat fur and a drop of pitch or piece of coal"),
                        "range": "60 ft", "duration": "10 min", "concentration": True},
    "Phantasmal Force":{"components": _M("a bit of fleece"),
                        "range": "60 ft", "duration": "1 min", "concentration": True},
    "Suggestion":      {"components": _VM("a snake's tongue and either a bit of honeycomb or a drop of sweet oil"),
                        "range": "30 ft", "duration": "8 hours", "concentration": True},
    "Spike Growth":    {"components": _M("seven sharp thorns or seven small twigs, each sharpened to a point"),
                        "range": "150 ft","duration": "10 min", "concentration": True},
    "Zone of Truth":   {"components": _VS, "range": "60 ft",  "duration": "10 min"},
    "Blur":            {"components": _V,  "range": "self",   "duration": "1 min", "concentration": True},
    "Branding Smite":  {"action_cost": "bonus_action",
                        "components": _V,  "range": "self",   "duration": "1 min", "concentration": True},

    # ── LEVEL 3 ──────────────────────────────────────────────────────────────
    "Fireball":        {"components": _M("a tiny ball of bat guano and sulfur"),
                        "range": "150 ft","duration": "instantaneous",
                        "save_type": "dex", "half_on_save": True,
                        "damage_dice": "8d6", "damage_type": "fire"},
    "Lightning Bolt":  {"components": _M("a bit of fur and a rod of amber, crystal, or glass"),
                        "range": "self",  "duration": "instantaneous",
                        "save_type": "dex", "half_on_save": True,
                        "damage_dice": "8d6", "damage_type": "lightning"},
    "Counterspell":    {"action_cost": "reaction",
                        "components": _S,  "range": "60 ft",  "duration": "instantaneous"},
    "Dispel Magic":    {"components": _VS, "range": "120 ft", "duration": "instantaneous"},
    "Revivify":        {"components": _M("diamonds worth at least 300 gp"),
                        "range": "touch", "duration": "instantaneous"},
    "Fly":             {"components": _M("a wing feather from any bird"),
                        "range": "touch", "duration": "10 min", "concentration": True},
    "Haste":           {"components": _M("a shaving of licorice root"),
                        "range": "30 ft", "duration": "1 min", "concentration": True},
    "Spirit Guardians":{"components": _M("a holy symbol"),
                        "range": "self",  "duration": "10 min", "concentration": True,
                        "save_type": "wis", "half_on_save": True,
                        "damage_dice": "3d8", "damage_type": "radiant"},
    "Mass Healing Word":{"action_cost": "bonus_action",
                        "components": _V,  "range": "60 ft",  "duration": "instantaneous"},
    "Fear":            {"components": _M("a white feather or the heart of a hen"),
                        "range": "self",  "duration": "1 min", "concentration": True,
                        "save_type": "wis", "half_on_save": False,
                        "condition_on_fail": "frightened"},
    "Hypnotic Pattern":{"components": _SM("a glowing stick of incense or a crystal vial filled with phosphorescent material"),
                        "range": "120 ft","duration": "1 min", "concentration": True,
                        "save_type": "wis", "half_on_save": False,
                        "condition_on_fail": "incapacitated"},
    "Major Image":     {"components": _M("a bit of fleece"),
                        "range": "120 ft","duration": "10 min", "concentration": True},
    "Hunger of Hadar": {"components": _M("a pickled octopus tentacle"),
                        "range": "150 ft","duration": "1 min", "concentration": True,
                        "save_type": "dex", "half_on_save": True,
                        "damage_dice": "2d6", "damage_type": "cold"},
    "Bestow Curse":    {"components": _VS, "range": "touch",  "duration": "1 min", "concentration": True,
                        "save_type": "wis", "half_on_save": False,
                        "condition_on_fail": "cursed"},
    "Call Lightning":  {"components": _VS, "range": "120 ft", "duration": "10 min", "concentration": True,
                        "save_type": "dex", "half_on_save": True,
                        "damage_dice": "3d10", "damage_type": "lightning"},
    "Conjure Animals": {"components": _VS, "range": "60 ft",  "duration": "1 hour", "concentration": True},
    "Aura of Vitality":{"components": _V,  "range": "self",   "duration": "1 min", "concentration": True},
    "Nondetection":    {"components": _M("a pinch of diamond dust worth 25 gp"),
                        "range": "touch", "duration": "8 hours"},
    "Lightning Arrow": {"action_cost": "bonus_action",
                        "components": _VS, "range": "self",   "duration": "1 min", "concentration": True,
                        "save_type": "dex", "half_on_save": True,
                        "damage_dice": "4d8", "damage_type": "lightning"},
    "Plant Growth":    {"components": _VS, "range": "150 ft", "duration": "instantaneous"},
    "Conjure Barrage": {"components": _M("one piece of ammunition or a thrown weapon"),
                        "range": "self",  "duration": "instantaneous",
                        "save_type": "dex", "half_on_save": True,
                        "damage_dice": "3d8", "damage_type": "piercing"},

    # ── LEVEL 4 ──────────────────────────────────────────────────────────────
    "Greater Invisibility":{"components": _VS, "range": "touch", "duration": "1 min", "concentration": True},
    "Polymorph":       {"components": _M("a caterpillar cocoon"),
                        "range": "60 ft", "duration": "1 hour", "concentration": True,
                        "save_type": "wis", "half_on_save": False,
                        "condition_on_fail": "polymorphed"},
    "Banishment":      {"components": _M("an item distasteful to the target"),
                        "range": "60 ft", "duration": "1 min", "concentration": True,
                        "save_type": "cha", "half_on_save": False,
                        "condition_on_fail": "banished"},
    "Dimension Door":  {"components": _V,  "range": "500 ft", "duration": "instantaneous"},
    "Death Ward":      {"components": _VS, "range": "touch",  "duration": "8 hours"},
    "Confusion":       {"components": _M("three walnut shells"),
                        "range": "90 ft", "duration": "1 min", "concentration": True},
    "Guardian of Faith":{"components": _V, "range": "30 ft",  "duration": "8 hours"},
    "Freedom of Movement":{"components": _M("a leather strap, bound around the arm or a similar appendage"),
                        "range": "touch", "duration": "1 hour"},
    "Conjure Woodland Beings":{"components": _M("one holly berry per creature summoned"),
                        "range": "60 ft", "duration": "1 hour", "concentration": True},
    "Aura of Life":    {"components": _V,  "range": "self",   "duration": "10 min", "concentration": True},
    "Staggering Smite":{"action_cost": "bonus_action",
                        "components": _V,  "range": "self",   "duration": "1 min", "concentration": True},

    # ── LEVEL 5 ──────────────────────────────────────────────────────────────
    "Hold Monster":    {"components": _M("a small, straight piece of iron"),
                        "range": "90 ft", "duration": "1 min", "concentration": True},
    "Mass Cure Wounds":{"components": _VS, "range": "60 ft",  "duration": "instantaneous"},
    "Animate Dead":    {"components": _M("a drop of blood, a piece of flesh, and a pinch of bone dust"),
                        "range": "10 ft", "duration": "instantaneous"},
    "Dominate Person": {"components": _VS, "range": "60 ft",  "duration": "1 min", "concentration": True},
    "Animate Objects": {"components": _VS, "range": "120 ft", "duration": "1 min", "concentration": True},
    "Raise Dead":      {"components": _M("a diamond worth at least 500 gp"),
                        "range": "touch", "duration": "instantaneous"},
    "Destructive Wave":{"components": _V,  "range": "self",   "duration": "instantaneous"},
    "Scrying":         {"components": _M("a focus worth at least 1,000 gp — a silver mirror, a font of holy water, or a crystal ball"),
                        "range": "self",  "duration": "10 min", "concentration": True},
    "Cone of Cold":    {"components": _M("a small crystal or glass cone"),
                        "range": "self",  "duration": "instantaneous"},
    "Conjure Elemental":{"components": _M("burning incense for air, soft clay for earth, sulfur and phosphorus for fire, or water and sand for water"),
                        "range": "90 ft", "duration": "1 hour", "concentration": True},
    "Swift Quiver":    {"action_cost": "bonus_action",
                        "components": _M("a quiver containing at least one piece of ammunition"),
                        "range": "self",  "duration": "1 min", "concentration": True},
    "Conjure Volley":  {"components": _M("one piece of ammunition or a thrown weapon"),
                        "range": "150 ft","duration": "instantaneous"},
    "Wall of Force":   {"components": _M("a pinch of powder made by crushing a clear gemstone"),
                        "range": "120 ft","duration": "10 min", "concentration": True},
    "Awaken":          {"components": _M("an agate worth at least 1,000 gp"),
                        "range": "touch", "duration": "30 days"},
}


def get_spell_card(spell_name: str) -> Dict[str, Any]:
    """Return card-ready dict for a spell from the catalog. Returns None if not found."""
    data = SPELL_CATALOG.get(spell_name)
    if not data:
        return None
    level = data["level"]
    school = data.get("school", "")
    reqs = SPELL_REQUIREMENTS.get(spell_name, {})
    mechanical = data.get("mechanical", "")
    # Infer concentration from mechanical text if not explicitly set
    conc = reqs.get("concentration", "conc" in mechanical.lower())
    return {
        "source": "spell",
        "title": spell_name,
        "description": data["description"],
        "rarity": _spell_rarity(level),
        "mechanical": mechanical,
        "per_day": data.get("per_day", False),
        "uses_max": data.get("uses_max", 0),
        "tags": ["spell", school, f"level-{level}" if level > 0 else "cantrip"],
        "metadata": {"spell_level": level, "school": school},
        "action_cost": reqs.get("action_cost", "action"),
        "components": reqs.get("components", {"V": True, "S": True, "M": None}),
        "range": reqs.get("range", ""),
        "duration": reqs.get("duration", ""),
        "concentration": conc,
        "ritual": reqs.get("ritual", False),
        # Save-spell fields (None = not a save spell)
        "save_type": reqs.get("save_type"),
        "half_on_save": reqs.get("half_on_save"),
        "damage_dice": reqs.get("damage_dice"),
        "damage_type": reqs.get("damage_type"),
        "condition_on_fail": reqs.get("condition_on_fail"),
    }


def get_feat_card(feat_name: str) -> Dict[str, Any]:
    """Return card-ready dict for a feat from the catalog. Returns None if not found."""
    data = FEAT_CARDS.get(feat_name)
    if not data:
        return None
    return {
        "source": "feat",
        "title": feat_name,
        "description": data["description"],
        "rarity": data.get("rarity", "rare"),
        "mechanical": data.get("mechanical", ""),
        "per_day": data.get("per_day", False),
        "uses_max": data.get("uses_max", 0),
        "tags": ["feat"],
        "metadata": {"feat": feat_name},
    }
