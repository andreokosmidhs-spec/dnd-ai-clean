export const BACKGROUNDS = [
  {
    key: "acolyte",
    name: "Acolyte",
    description:
      "You have spent your life in the service of a temple, acting as an intermediary between the realm of the holy and the mortal world.",
    skillProficiencies: ["Insight", "Religion"],
    toolProficiencies: [],
    languages: {
      count: 2,
      choices: [],
    },
    equipment: [
      "A holy symbol",
      "A prayer book or prayer wheel",
      "5 sticks of incense",
      "Vestments",
      "Common clothes",
      "15 gp",
    ],
    feature: {
      name: "Shelter of the Faithful",
      description:
        "You and your adventuring companions can expect free healing and care at a temple, shrine, or other established presence of your faith.",
    },
    variants: [],
  },
  {
    key: "criminal",
    name: "Criminal",
    description:
      "You are an experienced criminal with a history of breaking the law and surviving on the wrong side of society.",
    skillProficiencies: ["Deception", "Stealth"],
    toolProficiencies: ["One type of gaming set", "Thieves' tools"],
    languages: {
      count: 0,
      choices: [],
    },
    equipment: [
      "A crowbar",
      "A set of dark common clothes including a hood",
      "15 gp",
    ],
    feature: {
      name: "Criminal Contact",
      description:
        "You have a reliable contact who acts as your liaison to a network of other criminals.",
    },
    variants: [],
  },
  {
    key: "folk_hero",
    name: "Folk Hero",
    description:
      "You come from a humble social rank, but you are destined for so much more after standing up for the helpless.",
    skillProficiencies: ["Animal Handling", "Survival"],
    toolProficiencies: ["One type of artisan's tools", "Vehicles (land)"],
    languages: {
      count: 0,
      choices: [],
    },
    equipment: [
      "A set of artisan's tools (one of your choice)",
      "A shovel",
      "An iron pot",
      "A set of common clothes",
      "10 gp",
    ],
    feature: {
      name: "Rustic Hospitality",
      description:
        "Since you come from the ranks of the common folk, you fit in among them with ease and can find a place to hide or rest.",
    },
    variants: [],
  },
  {
    key: "noble",
    name: "Noble",
    description:
      "You understand wealth, power, and privilege, having been raised in a family with influence and responsibility.",
    skillProficiencies: ["History", "Persuasion"],
    toolProficiencies: ["One type of gaming set"],
    languages: {
      count: 1,
      choices: [],
    },
    equipment: [
      "A set of fine clothes",
      "A signet ring",
      "A scroll of pedigree",
      "25 gp",
    ],
    feature: {
      name: "Position of Privilege",
      description:
        "People are inclined to think the best of you, and you are welcome in high society.",
    },
    variants: [],
  },
  {
    key: "sage",
    name: "Sage",
    description:
      "You spent years learning the lore of the multiverse, seeking knowledge in libraries and through experimentation.",
    skillProficiencies: ["Arcana", "History"],
    toolProficiencies: [],
    languages: {
      count: 2,
      choices: [],
    },
    equipment: [
      "A bottle of black ink",
      "A quill",
      "A small knife",
      "A letter from a dead colleague posing a question you have not yet been able to answer",
      "A set of common clothes",
      "10 gp",
    ],
    feature: {
      name: "Researcher",
      description:
        "When you attempt to learn or recall a piece of lore, if you do not know that information, you often know where and from whom you can obtain it.",
    },
    variants: [],
  },
  {
    key: "soldier",
    name: "Soldier",
    description:
      "You trained in war and served in a military force, gaining discipline and battlefield experience.",
    skillProficiencies: ["Athletics", "Intimidation"],
    toolProficiencies: ["One type of gaming set", "Vehicles (land)"],
    languages: {
      count: 0,
      choices: [],
    },
    equipment: [
      "An insignia of rank",
      "A trophy taken from a fallen enemy",
      "A set of bone dice or deck of cards",
      "A set of common clothes",
      "10 gp",
    ],
    feature: {
      name: "Military Rank",
      description:
        "You have a military rank from your career and soldiers loyal to your former military organization still recognize your authority.",
    },
    variants: [],
  },
];

export const BACKGROUNDS_BY_KEY = BACKGROUNDS.reduce((acc, bg) => {
  acc[bg.key] = bg;
  return acc;
}, {});
