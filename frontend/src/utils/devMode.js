/**
 * Dev mode utilities
 */

import { mockData } from '../data/mockData';

export const isDevMode = () => {
  // Check if in development environment OR URL has ?dev=1
  const isDev = process.env.NODE_ENV !== 'production';
  const hasDevParam = new URLSearchParams(window.location.search).get('dev') === '1';
  return isDev || hasDevParam;
};

// Helper to pick random item from array
const randomPick = (array) => array[Math.floor(Math.random() * array.length)];

// Generate random stats (standard array method: 15, 14, 13, 12, 10, 8)
const generateRandomStats = () => {
  const standardArray = [15, 14, 13, 12, 10, 8];
  const shuffled = [...standardArray].sort(() => Math.random() - 0.5);
  
  return {
    strength: shuffled[0],
    dexterity: shuffled[1],
    constitution: shuffled[2],
    intelligence: shuffled[3],
    wisdom: shuffled[4],
    charisma: shuffled[5]
  };
};

// Generate random character name
const generateRandomName = () => {
  const firstNames = ['Raven', 'Thorne', 'Aria', 'Kael', 'Luna', 'Drax', 'Selene', 'Finn', 'Nova', 'Rex'];
  const lastNames = ['Shadowstep', 'Ironforge', 'Nightwhisper', 'Stormblade', 'Moonweaver', 'Fireborn', 'Frostwind', 'Swiftarrow', 'Darkbane', 'Brightshield'];
  return `${randomPick(firstNames)} ${randomPick(lastNames)}`;
};

export const generateDevCharacter = () => {
  // Randomly select race, class, and background from actual options
  const race = randomPick(mockData.races);
  const selectedClass = randomPick(mockData.classes);
  const background = randomPick(mockData.backgrounds);
  
  // Get first variant of the background (with safety check)
  const variantKey = background.variants ? Object.keys(background.variants)[0] : 'Base';
  const variant = background.variants ? background.variants[variantKey] : null;
  
  // Random alignments
  const lawfulChaotic = randomPick(['Lawful', 'Neutral', 'Chaotic']);
  const goodEvil = randomPick(['Good', 'Neutral', 'Evil']);
  const alignment = lawfulChaotic === 'Neutral' && goodEvil === 'Neutral' 
    ? 'True Neutral' 
    : `${lawfulChaotic} ${goodEvil}`;
  
  // Generate random stats
  const stats = generateRandomStats();
  
  // Calculate HP based on class
  const hitDie = selectedClass.hitDie || 8;
  const conModifier = Math.floor((stats.constitution - 10) / 2);
  const baseHP = hitDie + conModifier;
  const levelHP = Math.floor(((hitDie / 2) + 1 + conModifier) * 2); // Levels 2-3
  const totalHP = baseHP + levelHP;
  
  // Calculate AC (base 10 + dex modifier + armor bonus estimate)
  const dexModifier = Math.floor((stats.dexterity - 10) / 2);
  const armorBonus = selectedClass.name === 'Wizard' ? 0 : 3; // Light armor estimate
  const ac = 10 + dexModifier + armorBonus;
  
  // Randomly select personality traits from the background
  const personalityTrait = randomPick(background.personalityTraits || ['Determined and focused']);
  const ideal = randomPick(background.ideals || [{ name: 'Freedom', alignment: 'Any', description: 'Freedom is the highest virtue' }]);
  const bond = randomPick(background.bonds || ['I seek to prove myself worthy']);
  const flaw = randomPick(background.flaws || ['I sometimes act without thinking']);
  
  // Random aspiration goal
  const aspirationGoals = [
    'Become the greatest warrior in the realm',
    'Uncover the secrets of ancient magic',
    'Amass a fortune beyond imagination',
    'Bring justice to the corrupt',
    'Find a legendary artifact',
    'Protect the innocent from evil',
    'Master every form of combat',
    'Discover my true heritage'
  ];
  
  return {
    id: `char-dev-${Date.now()}`,
    name: generateRandomName(),
    race: race.name,
    class: selectedClass.name,
    level: 3,
    background: background.name,
    backgroundVariantKey: variantKey,
    alignment: alignment,
    stats: stats,
    hitPoints: totalHP,
    maxHitPoints: totalHP,
    armorClass: ac,
    speed: race.speed || 30,
    experience: 0,
    spellSlots: selectedClass.spellSlots || [],
    // Use actual racial traits
    traits: (race.traits || []).map(trait => ({
      text: trait,
      root_event: `Inherited from ${race.name} heritage`
    })),
    // Use randomly selected personality from background
    ideals: [{
      principle: ideal.name,
      inspiration: ideal.description
    }],
    bonds: [{
      person_or_cause: typeof bond === 'string' ? bond : bond.description || 'Unknown',
      shared_event: 'From my past experiences'
    }],
    flaws_detailed: [{
      habit: typeof flaw === 'string' ? flaw : flaw.description || 'Unknown flaw',
      interference: 'Sometimes causes problems',
      intensity: 0.5 + Math.random() * 0.3 // Random intensity between 0.5-0.8
    }],
    aspiration: {
      goal: randomPick(aspirationGoals),
      motivation: 'To prove myself and make my mark on the world',
      sacrifice_threshold: 5 + Math.floor(Math.random() * 5) // 5-9
    },
    alignment_vector: {
      lawful_chaotic: lawfulChaotic,
      good_evil: goodEvil
    },
    vip_hooks: [],
    proficiencies: selectedClass.proficiencies || []
  };
};
