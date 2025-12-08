export const mockData = {
  // Available languages for character selection
  availableLanguages: [
    "Common", "Elvish", "Dwarvish", "Halfling", "Draconic",
    "Orc", "Giant", "Gnomish", "Goblin", "Abyssal",
    "Celestial", "Deep Speech", "Infernal", "Primordial", "Sylvan",
    "Undercommon", "Druidic" // Druidic is secret, only from Druid class
  ],
  
  races: [
    {
      name: "Human",
      description: "Versatile and ambitious, humans are the most adaptable of all races. They gain a +1 bonus to all ability scores and an extra language choice.",
      size: "Medium",
      speed: 30,
      traits: ["Versatile"],
      languages: {
        automatic: ["Common"],
        choices: 1 // Gets one additional language of choice
      }
    },
    {
      name: "Elf",
      description: "Graceful and long-lived, elves possess keen senses and a natural affinity for magic. They have darkvision and are immune to sleep magic.",
      size: "Medium",
      speed: 30,
      traits: ["Darkvision", "Keen Senses", "Fey Ancestry", "Trance"],
      languages: {
        automatic: ["Common", "Elvish"],
        choices: 0
      }
    },
    {
      name: "Dwarf",
      description: "Stout and resilient, dwarves are known for their craftsmanship and martial prowess. They have resistance to poison and proficiency with certain weapons.",
      size: "Medium",
      speed: 25,
      traits: ["Darkvision", "Dwarven Resilience", "Stonecunning", "Tool Proficiency"],
      languages: {
        automatic: ["Common", "Dwarvish"],
        choices: 0
      }
    },
    {
      name: "Halfling",
      description: "Small but brave, halflings are naturally lucky and nimble. They can reroll natural 1s on attack rolls, ability checks, and saving throws.",
      size: "Small",
      speed: 25,
      traits: ["Lucky", "Brave", "Halfling Nimbleness"],
      languages: {
        automatic: ["Common", "Halfling"],
        choices: 0
      }
    },
    {
      name: "Dragonborn",
      description: "Descended from dragons, dragonborn possess draconic heritage including breath weapons and natural armor. They command respect and fear.",
      size: "Medium",
      speed: 30,
      traits: ["Draconic Ancestry", "Breath Weapon", "Damage Resistance"],
      languages: {
        automatic: ["Common", "Draconic"],
        choices: 0
      }
    }
  ],

  classes: [
    {
      name: "Fighter",
      description: "Masters of martial combat, skilled with a variety of weapons and armor. They gain extra attacks and Action Surge.",
      hitDie: 10,
      spellcaster: false,
      proficiencies: ["All Armor", "Shields", "Simple Weapons", "Martial Weapons"],
      languages: {
        automatic: [],
        choices: 0
      }
    },
    {
      name: "Wizard",
      description: "Scholarly magic-users capable of manipulating the structures of reality. They learn spells from a spellbook and have the largest spell selection.",
      hitDie: 6,
      spellcaster: true,
      spellSlots: {
        1: [1, 1, 1] // Level 1: 3 first-level spell slots
      },
      proficiencies: ["Daggers", "Darts", "Slings", "Quarterstaffs", "Light Crossbows"],
      languages: {
        automatic: [],
        choices: 0
      }
    },
    {
      name: "Rogue",
      description: "Skilled in stealth and precision, rogues excel at dealing massive damage from the shadows. They gain Sneak Attack and various expertise.",
      hitDie: 8,
      spellcaster: false,
      proficiencies: ["Light Armor", "Simple Weapons", "Hand Crossbows", "Longswords", "Rapiers", "Shortswords", "Thieves' Tools"],
      languages: {
        automatic: [],
        choices: 0
      }
    },
    {
      name: "Cleric",
      description: "Divine spellcasters who serve the gods and protect their allies. They can heal wounds, turn undead, and cast powerful divine magic.",
      hitDie: 8,
      spellcaster: true,
      spellSlots: {
        1: [1, 1] // Level 1: 2 first-level spell slots
      },
      proficiencies: ["Light Armor", "Medium Armor", "Shields", "Simple Weapons"],
      languages: {
        automatic: [],
        choices: 0 // Knowledge domain may grant 2 additional languages, but that's domain-specific
      }
    },
    {
      name: "Ranger",
      description: "Warriors of the wilderness, skilled in tracking, survival, and combat. They have favored enemies and can cast nature magic.",
      hitDie: 10,
      spellcaster: true,
      spellSlots: {
        1: [] // No spells at level 1
      },
      proficiencies: ["Light Armor", "Medium Armor", "Shields", "Simple Weapons", "Martial Weapons"],
      languages: {
        automatic: [],
        choices: 0
      }
    },
    {
      name: "Monk",
      description: "Masters of martial arts who channel ki energy. They gain supernatural speed and can strike with devastating precision.",
      hitDie: 8,
      spellcaster: false,
      proficiencies: ["Simple Weapons", "Shortswords"],
      languages: {
        automatic: [],
        choices: 1 // PHB: Monks get one additional language of choice at level 1
      }
    },
    {
      name: "Druid",
      description: "Guardians of nature who can shapeshift and command the elements. They cast primal magic and commune with beasts.",
      hitDie: 8,
      spellcaster: true,
      proficiencies: ["Light Armor (non-metal)", "Medium Armor (non-metal)", "Shields (non-metal)", "Simple Weapons"],
      languages: {
        automatic: ["Druidic"], // Secret language of druids
        choices: 0
      }
    }
  ],

  backgrounds: [
    {
      name: "Acolyte",
      theme: "A servant of a temple or religious figure.",
      description: "You have spent your life in service to a temple or faith.",
      variants: {
        Base: {
          label: "Acolyte",
          inheritsPersonality: true,
          skills: ["Insight", "Religion"],
          toolProficiencies: [],
          languages: 2,
          equipment: "Holy symbol, prayer book or wheel, 5 sticks of incense, vestments, common clothes, pouch (15 gp)",
          feature: {
            name: "Shelter of the Faithful",
            description: "You command respect within your faith. You can receive free healing and care at a temple, and gain lodging/support from fellow worshippers."
          }
        },
        Hermit: {
          label: "Hermit",
          inheritsPersonality: true,
          skills: ["Medicine", "Religion"],
          toolProficiencies: ["Herbalism kit"],
          languages: 0,
          equipment: "Scroll case of notes from isolation, winter blanket, common clothes, herbalism kit, 5 gp",
          feature: {
            name: "Discovery",
            description: "During isolation, you uncovered a great truth—this secret can shape the campaign (e.g., knowledge of a forgotten god, a prophecy, or hidden corruption)."
          }
        }
      },
      personalityTraits: [
        "I idolize a particular hero of my faith.",
        "I can find common ground with almost anyone.",
        "I see omens in every event.",
        "Nothing can shake my optimistic faith.",
        "I quote or misquote sacred texts constantly.",
        "I'm tolerant of others' beliefs … except the faiths I despise.",
        "I've enjoyed fine temple life and expect special treatment.",
        "I've spent too long in temples; I speak awkwardly with commoners."
      ],
      ideals: [
        { name: "Tradition", alignment: "Lawful", description: "Uphold ancient practices." },
        { name: "Charity", alignment: "Good", description: "Always aid those in need." },
        { name: "Change", alignment: "Chaotic", description: "We must bring our faith to others." },
        { name: "Power", alignment: "Lawful Evil", description: "Faith is the path to power." },
        { name: "Faith", alignment: "Lawful Good", description: "My god's teachings guide all I do." },
        { name: "Aspiration", alignment: "Any", description: "I seek to become worthy of my deity." }
      ],
      bonds: [
        "I owe everything to the temple that took me in.",
        "I'll protect the ancient texts.",
        "I'd die for my faith.",
        "I wish to find my god's chosen one.",
        "I owe a debt to the priest who raised me.",
        "I seek to preserve my temple's relics."
      ],
      flaws: [
        "I judge others harshly.",
        "My piety hides greed.",
        "I'm inflexible in my thinking.",
        "I'll do anything to protect my faith's secrets.",
        "I'm distrustful of other religions.",
        "Once I choose a path, I never deviate."
      ]
    },
    {
      name: "Criminal",
      theme: "An experienced lawbreaker or operative.",
      description: "You are an experienced criminal with a history of breaking the law.",
      variants: {
        Base: {
          label: "Criminal",
          inheritsPersonality: true,
          skills: ["Deception", "Stealth"],
          toolProficiencies: ["One type of gaming set", "Thieves' tools"],
          languages: 0,
          equipment: "Crowbar, dark common clothes with hood, pouch (15 gp)",
          feature: {
            name: "Criminal Contact",
            description: "You have a reliable contact in the criminal network who can get messages to and from other criminals."
          }
        },
        Spy: {
          label: "Spy",
          inheritsPersonality: true,
          skills: ["Deception", "Stealth"],
          toolProficiencies: ["One type of gaming set", "Thieves' tools"],
          languages: 0,
          equipment: "Crowbar, dark common clothes with hood, pouch (15 gp)",
          feature: {
            name: "Spy Contact",
            description: "Your contact is tied to a secret organization, political faction, or intelligence network."
          }
        }
      },
      personalityTraits: [
        "I always have a plan for when things go wrong.",
        "I prefer to let others take the blame.",
        "I never raise my voice or show anger.",
        "I always look over my shoulder.",
        "I blow everything out of proportion.",
        "I never trust anyone but my crew.",
        "I hate to see others suffer.",
        "I'm slow to trust but loyal once proven."
      ],
      ideals: [
        { name: "Honor", alignment: "Lawful", description: "Never betray my word." },
        { name: "Freedom", alignment: "Chaotic", description: "Chains are for others, not me." },
        { name: "Charity", alignment: "Good", description: "Steal from the rich, aid the poor." },
        { name: "Greed", alignment: "Evil", description: "Everything's for sale." },
        { name: "People", alignment: "Neutral", description: "The crew is family." },
        { name: "Redemption", alignment: "Good", description: "There's a better life for me." }
      ],
      bonds: [
        "I'm loyal to my first boss.",
        "Someone I love was killed because of me.",
        "I owe debts I must repay.",
        "I'd do anything for my crew.",
        "A rival ruined me—I'll get revenge.",
        "I'm still hunted by the law."
      ],
      flaws: [
        "I can't resist a shiny thing.",
        "I'm too greedy to walk away.",
        "I'll betray a friend for the right price.",
        "I get violent when mocked.",
        "I'm paranoid everyone's out to get me.",
        "I can't resist taking risks."
      ]
    },
    {
      name: "Folk Hero",
      theme: "A commoner who rose to prominence.",
      description: "You come from humble social rank, but you are destined for so much more.",
      variants: {
        Base: {
          label: "Folk Hero",
          inheritsPersonality: true,
          skills: ["Animal Handling", "Survival"],
          toolProficiencies: ["One type of artisan's tools", "Land vehicles"],
          languages: 0,
          equipment: "Artisan's tools, shovel, iron pot, common clothes, pouch (10 gp)",
          feature: {
            name: "Rustic Hospitality",
            description: "You can find shelter and support among common folk who admire your deeds."
          }
        },
        RuralDefender: {
          label: "Rural Defender",
          inheritsPersonality: true,
          skills: ["Animal Handling", "Survival"],
          toolProficiencies: ["One type of artisan's tools", "Land vehicles"],
          languages: 0,
          equipment: "Artisan's tools, shovel, iron pot, common clothes, pouch (10 gp)",
          feature: {
            name: "Guardian's Reputation",
            description: "The people of your homeland trust you implicitly. You can request help from locals — food, shelter, or militia support — when defending their lands."
          }
        }
      },
      personalityTraits: [
        "I judge people by actions, not words.",
        "If someone's in trouble, I help.",
        "I respect the law but not rulers.",
        "I protect those who cannot protect themselves.",
        "I'd rather eat plain food than rich fare.",
        "I don't back down from a challenge.",
        "I'm eager to prove my worth.",
        "I misuse big words to sound smarter."
      ],
      ideals: [
        { name: "Respect", alignment: "Good", description: "All deserve dignity." },
        { name: "Fairness", alignment: "Lawful", description: "No one should get special treatment." },
        { name: "Freedom", alignment: "Chaotic", description: "Tyrants must fall." },
        { name: "Might", alignment: "Evil", description: "The strong rule the weak." },
        { name: "Sincerity", alignment: "Neutral", description: "Be true to yourself." },
        { name: "Destiny", alignment: "Any", description: "I'm chosen for greatness." }
      ],
      bonds: [
        "I'll protect my village.",
        "I owe my life to the people who helped me.",
        "I pursue the monster that destroyed my home.",
        "I fight for those who can't.",
        "I must prove myself a true hero.",
        "My tools are a family heirloom."
      ],
      flaws: [
        "I'm naive about city ways.",
        "I believe I'm always right.",
        "I'm obsessed with proving my heroism.",
        "I underestimate my foes.",
        "I overcommit to causes.",
        "I'm blunt and tactless."
      ]
    },
    {
      name: "Noble",
      theme: "A person of wealth and status.",
      description: "You understand wealth, power, and privilege.",
      variants: {
        Base: {
          label: "Noble",
          inheritsPersonality: true,
          skills: ["History", "Persuasion"],
          toolProficiencies: ["One gaming set"],
          languages: 1,
          equipment: "Fine clothes, signet ring, scroll of pedigree, purse (25 gp)",
          feature: {
            name: "Position of Privilege",
            description: "You're welcome in high society. Commoners defer to you; nobles treat you as an equal."
          }
        },
        Knight: {
          label: "Knight",
          inheritsPersonality: true,
          skills: ["History", "Persuasion"],
          toolProficiencies: ["One gaming set"],
          languages: 0,
          equipment: "Fine clothes, signet ring, scroll of pedigree, purse (25 gp)",
          feature: {
            name: "Knightly Order",
            description: "You belong to a knightly order and can gain limited hospitality or recognition among allies of that order."
          }
        },
        Courtier: {
          label: "Courtier",
          inheritsPersonality: true,
          skills: ["Insight", "Persuasion"],
          toolProficiencies: [],
          languages: 2,
          equipment: "Fine clothes, writing kit, 10 gp",
          feature: {
            name: "Court Functionary",
            description: "You have easy access to government or noble bureaucracies."
          }
        }
      },
      personalityTraits: [
        "My manners are flawless.",
        "I flaunt my wealth when possible.",
        "I always act above my station.",
        "I show respect to other nobles.",
        "I take offense easily.",
        "I help those beneath me.",
        "I secretly hate my status.",
        "I measure people by lineage."
      ],
      ideals: [
        { name: "Respect", alignment: "Good", description: "Duty to protect the weak." },
        { name: "Responsibility", alignment: "Lawful", description: "Nobility requires service." },
        { name: "Independence", alignment: "Chaotic", description: "I'll carve my own legacy." },
        { name: "Power", alignment: "Evil", description: "I crave control." },
        { name: "Family", alignment: "Any", description: "Blood comes first." },
        { name: "Noblesse Oblige", alignment: "Good", description: "I must lead by example." }
      ],
      bonds: [
        "My family is everything.",
        "I'll reclaim my family's honor.",
        "My loyalty lies with my house.",
        "I love someone beneath my station.",
        "The commoners must learn their place.",
        "I owe my house's survival to a powerful ally."
      ],
      flaws: [
        "I secretly despise commoners.",
        "I can't resist gossip.",
        "I'm a terrible gambler.",
        "I hold grudges.",
        "I crave luxury.",
        "I'm vain and arrogant."
      ]
    },
    {
      name: "Soldier",
      theme: "A veteran trained in warfare.",
      description: "War has been your life for as long as you can remember.",
      variants: {
        Base: {
          label: "Soldier",
          inheritsPersonality: true,
          skills: ["Athletics", "Intimidation"],
          toolProficiencies: ["One gaming set", "Land vehicles"],
          languages: 0,
          equipment: "Insignia of rank, trophy from a fallen foe, bone dice or deck, common clothes, pouch (10 gp)",
          feature: {
            name: "Military Rank",
            description: "You retain authority among soldiers of your former organization and can requisition simple aid or horses."
          }
        },
        MercenaryVeteran: {
          label: "Mercenary Veteran",
          inheritsPersonality: true,
          skills: ["Athletics", "Persuasion"],
          toolProficiencies: ["One gaming set", "Land vehicles"],
          languages: 0,
          equipment: "Insignia of rank, trophy from a fallen foe, bone dice or deck, common clothes, pouch (10 gp)",
          feature: {
            name: "Mercenary Life",
            description: "You can find mercenary work anywhere. You know the reputation of major companies and can leverage them for contracts or contacts."
          }
        },
        CityWatch: {
          label: "City Watch",
          inheritsPersonality: true,
          skills: ["Athletics", "Insight"],
          toolProficiencies: [],
          languages: 2,
          equipment: "Uniform, insignia of rank, horn, manacles, pouch (10 gp)",
          feature: {
            name: "Watcher's Eye",
            description: "You can recognize the patterns of crime and find local law enforcement to gather information."
          }
        },
        Investigator: {
          label: "Investigator",
          inheritsPersonality: true,
          skills: ["Investigation", "Insight"],
          toolProficiencies: [],
          languages: 2,
          equipment: "Uniform, insignia of rank, horn, manacles, pouch (10 gp)",
          feature: {
            name: "Watcher's Eye",
            description: "You can recognize the patterns of crime and find local law enforcement to gather information."
          }
        }
      },
      personalityTraits: [
        "I obey orders without question.",
        "I'm haunted by war memories.",
        "I've lost comrades and hide the pain.",
        "I take pride in discipline.",
        "I joke to mask fear.",
        "I respect competence above rank.",
        "I'm slow to trust civilians.",
        "I'd rather face danger than boredom."
      ],
      ideals: [
        { name: "Greater Good", alignment: "Good", description: "We fight for others." },
        { name: "Responsibility", alignment: "Lawful", description: "Duty above all." },
        { name: "Independence", alignment: "Chaotic", description: "I fight for myself." },
        { name: "Might", alignment: "Evil", description: "The strong rule." },
        { name: "Live and Let Live", alignment: "Neutral", description: "All wars end someday." },
        { name: "Nation", alignment: "Any", description: "My homeland first." }
      ],
      bonds: [
        "I would die for my unit.",
        "My honor is my life.",
        "I'll never forget a fallen comrade.",
        "My weapon belonged to a mentor.",
        "I seek glory.",
        "I'm loyal to my commander."
      ],
      flaws: [
        "I follow orders even when wrong.",
        "I drink to forget.",
        "I'm reckless in battle.",
        "I despise the enemy.",
        "I'm too blunt for politics.",
        "I secretly fear cowardice."
      ]
    },
    {
      name: "Sage",
      theme: "A lifelong student or researcher obsessed with uncovering truth.",
      description: "A lifelong student or researcher obsessed with uncovering truth and knowledge.",
      variants: {
        Base: {
          label: "Sage",
          inheritsPersonality: true,
          skills: ["Arcana", "History"],
          toolProficiencies: [],
          languages: 2,
          equipment: "Bottle of black ink, quill, small knife, letter from a dead colleague with a question you cannot yet answer, common clothes, pouch (10 gp)",
          feature: {
            name: "Researcher",
            description: "When you attempt to learn or recall information, if you don't know it, you usually know where or from whom it can be obtained. You have a network of scholars, libraries, and archives across regions."
          }
        },
        CloisteredScholar: {
          label: "Cloistered Scholar",
          inheritsPersonality: true,
          skills: ["History", "Arcana"],
          toolProficiencies: [],
          languages: 2,
          equipment: "Bottle of black ink, quill, small knife, letter from a dead colleague, common clothes, pouch (10 gp)",
          feature: {
            name: "Library Access",
            description: "You have credentials allowing access to restricted stacks and scholarly circles; you can request assistance from learned contacts."
          }
        }
      },
      personalityTraits: [
        "I use polysyllabic words that confuse people.",
        "I've read every book in the world's greatest libraries—or I like to think so.",
        "I'm used to helping others but secretly long for recognition.",
        "I'm willing to listen to every side of an argument before making a judgment.",
        "I… get lost in thought and forget what I was doing.",
        "I speak without thinking through my words' implications.",
        "I love a good mystery.",
        "I will lecture on anything at length."
      ],
      ideals: [
        { name: "Knowledge", alignment: "Neutral", description: "The path to power and self-improvement is through knowledge." },
        { name: "Beauty", alignment: "Good", description: "What is beautiful must be preserved." },
        { name: "Logic", alignment: "Lawful", description: "Emotions must not cloud reason." },
        { name: "No Limits", alignment: "Chaotic", description: "Nothing should fetter the endless quest for knowledge." },
        { name: "Power", alignment: "Evil", description: "Knowledge is the key to domination." },
        { name: "Self-Improvement", alignment: "Any", description: "Study makes one better." }
      ],
      bonds: [
        "My mentor is the most important person in my life.",
        "I must protect a library, university, or archive.",
        "I own an ancient text that holds terrible secrets.",
        "I work to prove a theory that could rewrite history.",
        "I've been wronged by another scholar and seek revenge.",
        "My life's work is nearly complete; I must see it through."
      ],
      flaws: [
        "I am easily distracted by promising information.",
        "I speak condescendingly to the uneducated.",
        "I can't keep a secret to save my life.",
        "I'm obsessed with my studies.",
        "I disregard practical matters for theoretical ones.",
        "I'll risk anything for a big discovery."
      ]
    },
    {
      name: "Outlander",
      theme: "You grew up in the wilds, far from civilization.",
      description: "You grew up in the wilds, far from civilization, living by your instincts and survival skills.",
      variants: {
        Base: {
          label: "Outlander",
          inheritsPersonality: true,
          skills: ["Athletics", "Survival"],
          toolProficiencies: ["One type of musical instrument"],
          languages: 1,
          equipment: "Staff, hunting trap, trophy from an animal you killed, traveler's clothes, pouch (10 gp)",
          feature: {
            name: "Wanderer",
            description: "You have an excellent memory for geography and maps. You can always recall the layout of terrain, settlements, and features, and you can find food and fresh water for up to five people each day."
          }
        },
        TribalNomad: {
          label: "Tribal Nomad",
          inheritsPersonality: true,
          skills: ["Survival", "Perception"],
          toolProficiencies: ["One type of musical instrument"],
          languages: 1,
          equipment: "Staff, hunting trap, trophy from an animal, traveler's clothes, pouch (10 gp)",
          feature: {
            name: "Pathfinder's Instinct",
            description: "You can identify safe campsites and detect natural hazards. Gain advantage on navigation or tracking checks while outdoors."
          }
        },
        ExileTracker: {
          label: "Exile Tracker",
          inheritsPersonality: true,
          skills: ["Survival", "Perception"],
          toolProficiencies: ["One type of musical instrument"],
          languages: 1,
          equipment: "Staff, hunting trap, trophy from an animal, traveler's clothes, pouch (10 gp)",
          feature: {
            name: "Mark the Trail",
            description: "Expert at tracking people/beasts. Advantage to follow signs and tracks."
          }
        }
      },
      personalityTraits: [
        "I'm driven by wanderlust; no home will ever hold me.",
        "I watch over my friends as if they were younglings.",
        "I place no stock in wealthy or well-dressed folk.",
        "I'm quick to anger but quick to forgive.",
        "I feel more comfortable among animals than people.",
        "I'm always picking things up, fiddling with them, and sometimes breaking them.",
        "I'm a survivalist who distrusts most authority.",
        "I'm blunt to a fault."
      ],
      ideals: [
        { name: "Change", alignment: "Chaotic", description: "Life is like the seasons; we must change with it." },
        { name: "Greater Good", alignment: "Good", description: "Nature must be protected." },
        { name: "Honor", alignment: "Lawful", description: "My word is my bond." },
        { name: "Might", alignment: "Evil", description: "The strong survive and the weak perish." },
        { name: "Nature", alignment: "Neutral", description: "The natural world is more important than all civilization." },
        { name: "Glory", alignment: "Any", description: "I must prove myself through great deeds." }
      ],
      bonds: [
        "My family, clan, or tribe is my life.",
        "An injury to the wilderness is an injury to me.",
        "I will bring terrible wrath down on those who despoil nature.",
        "I was once saved by a great beast; I owe it a debt.",
        "I seek vengeance on those who destroyed my home.",
        "I want to see the world beyond the wilds."
      ],
      flaws: [
        "I am too quick to judge city folk.",
        "There's no room for mercy in the wild.",
        "I struggle to adapt to civilized life.",
        "I can't resist a good challenge.",
        "I hoard trophies of my kills.",
        "I believe every problem can be solved with survival skill."
      ]
    },
    {
      name: "Charlatan",
      theme: "A skilled deceiver and con artist.",
      description: "You have always had a way with people. You excel at telling people what they want to hear.",
      variants: null,
      skills: ["Deception", "Sleight of Hand"],
      toolProficiencies: ["Disguise kit", "Forgery kit"],
      languages: 0,
      equipment: "Fine clothes, disguise kit, tools of the con, pouch (15 gp)",
      feature: {
        name: "False Identity",
        description: "You have created a second identity that includes documentation, established acquaintances, and disguises."
      },
      personalityTraits: [
        "I fall in and out of love easily, and am always pursuing someone.",
        "I have a joke for every occasion, especially ones where humor is inappropriate.",
        "Flattery is my preferred trick for getting what I want.",
        "I'm a born gambler who can't resist taking a risk.",
        "I lie about almost everything, even when there's no good reason to.",
        "Sarcasm and insults are my weapons of choice.",
        "I keep multiple holy symbols on me and invoke whatever deity might come in useful.",
        "I pocket anything I see that might have some value."
      ],
      ideals: [
        { name: "Independence", alignment: "Chaotic", description: "I am a free spirit—no one tells me what to do." },
        { name: "Fairness", alignment: "Lawful", description: "I never target people who can't afford to lose a few coins." },
        { name: "Charity", alignment: "Good", description: "I distribute the money I acquire to the people who really need it." },
        { name: "Creativity", alignment: "Chaotic", description: "I never run the same con twice." },
        { name: "Friendship", alignment: "Good", description: "Material goods come and go. Bonds of friendship last forever." },
        { name: "Aspiration", alignment: "Any", description: "I'm determined to make something of myself." }
      ],
      bonds: [
        "I fleeced the wrong person and must work to ensure that this individual never crosses paths with me or those I care about.",
        "I owe everything to my mentor—a horrible person who's probably rotting in jail somewhere.",
        "Somewhere out there, I have a child who doesn't know me. I'm making the world better for him or her.",
        "I come from a noble family, and one day I'll reclaim my lands and title from those who stole them from me.",
        "A powerful person killed someone I love. Some day soon, I'll have my revenge.",
        "I swindled and ruined a person who didn't deserve it. I seek to atone for my misdeeds but might never be able to forgive myself."
      ],
      flaws: [
        "I can't resist a pretty face.",
        "I'm always in debt. I spend my ill-gotten gains on decadent luxuries faster than I bring them in.",
        "I'm convinced that no one could ever fool me the way I fool others.",
        "I'm too greedy for my own good. I can't resist taking a risk if there's money involved.",
        "I can't resist swindling people who are more powerful than me.",
        "I hate to admit it and will hate myself for it, but I'll run and preserve my own hide if the going gets tough."
      ]
    },
    {
      name: "Entertainer",
      theme: "A performer who thrives in the spotlight.",
      description: "You thrive in front of an audience. You know how to entrance them, entertain them, and even inspire them.",
      variants: {
        Base: {
          label: "Entertainer",
          inheritsPersonality: true,
          skills: ["Acrobatics", "Performance"],
          toolProficiencies: ["Disguise kit", "One type of musical instrument"],
          languages: 0,
          equipment: "Musical instrument, favor of an admirer, costume, pouch (15 gp)",
          feature: {
            name: "By Popular Demand",
            description: "You can always find a place to perform. You receive free lodging and food at inns and taverns in exchange for performances."
          }
        },
        Gladiator: {
          label: "Gladiator",
          inheritsPersonality: true,
          skills: ["Acrobatics", "Performance"],
          toolProficiencies: ["Disguise kit", "One unusual weapon"],
          languages: 0,
          equipment: "Unusual weapon, favor of an admirer, costume, pouch (15 gp)",
          feature: {
            name: "By Popular Demand",
            description: "You can always find a place to perform fighting in arenas / pits instead of stages. You receive free lodging and food."
          }
        }
      },
      personalityTraits: [
        "I know a story relevant to almost every situation.",
        "Whenever I come to a new place, I collect local rumors and spread gossip.",
        "I'm a hopeless romantic, always searching for that 'special someone.'",
        "Nobody stays angry at me or around me for long, since I can defuse any amount of tension.",
        "I love a good insult, even one directed at me.",
        "I get bitter if I'm not the center of attention.",
        "I'll settle for nothing less than perfection.",
        "I change my mood or my mind as quickly as I change key in a song."
      ],
      ideals: [
        { name: "Beauty", alignment: "Good", description: "When I perform, I make the world better than it was." },
        { name: "Tradition", alignment: "Lawful", description: "The stories, legends, and songs of the past must never be forgotten." },
        { name: "Creativity", alignment: "Chaotic", description: "The world is in need of new ideas and bold action." },
        { name: "Greed", alignment: "Evil", description: "I'm only in it for the money and fame." },
        { name: "People", alignment: "Neutral", description: "I like seeing the smiles on people's faces when I perform." },
        { name: "Honesty", alignment: "Any", description: "Art should reflect the soul; it should come from within and reveal who we really are." }
      ],
      bonds: [
        "My instrument is my most treasured possession, and it reminds me of someone I love.",
        "Someone stole my precious instrument, and someday I'll get it back.",
        "I want to be famous, whatever it takes.",
        "I idolize a hero of the old tales and measure my deeds against that person's.",
        "I will do anything to prove myself superior to my hated rival.",
        "I would do anything for the other members of my old troupe."
      ],
      flaws: [
        "I'll do anything to win fame and renown.",
        "I'm a sucker for a pretty face.",
        "A scandal prevents me from ever going home again. That kind of trouble seems to follow me around.",
        "I once satirized a noble who still wants my head. It was a mistake that I will likely repeat.",
        "I have trouble keeping my true feelings hidden. My sharp tongue lands me in trouble.",
        "Despite my best efforts, I am unreliable to my friends."
      ]
    },
    {
      name: "Guild Artisan",
      theme: "A skilled tradesperson and guild member.",
      description: "You are a member of an artisan's guild, skilled in a particular field and closely associated with other artisans.",
      variants: {
        Base: {
          label: "Guild Artisan",
          inheritsPersonality: true,
          skills: ["Insight", "Persuasion"],
          toolProficiencies: ["One type of artisan's tools"],
          languages: 1,
          equipment: "Artisan's tools, letter of introduction from guild, traveler's clothes, pouch (15 gp)",
          feature: {
            name: "Guild Membership",
            description: "As an established and respected member of a guild, you can rely on certain benefits that membership provides."
          }
        },
        GuildMerchant: {
          label: "Guild Merchant",
          inheritsPersonality: true,
          skills: ["Insight", "Persuasion"],
          toolProficiencies: ["Navigator's tools or one vehicle"],
          languages: 1,
          equipment: "Artisan's tools or vehicle, letter of introduction, traveler's clothes, pouch (15 gp)",
          feature: {
            name: "Guild Membership",
            description: "Guild membership leaned into trade routes, caravans, and contacts."
          }
        }
      },
      personalityTraits: [
        "I believe that anything worth doing is worth doing right. I can't help it—I'm a perfectionist.",
        "I'm a snob who looks down on those who can't appreciate fine art.",
        "I always want to know how things work and what makes people tick.",
        "I'm full of witty aphorisms and have a proverb for every occasion.",
        "I'm rude to people who lack my commitment to hard work and fair play.",
        "I like to talk at length about my profession.",
        "I don't part with my money easily and will haggle tirelessly to get the best deal possible.",
        "I'm well known for my work, and I want to make sure everyone appreciates it. I'm always taken aback when people haven't heard of me."
      ],
      ideals: [
        { name: "Community", alignment: "Lawful", description: "It is the duty of all civilized people to strengthen the bonds of community and the security of civilization." },
        { name: "Generosity", alignment: "Good", description: "My talents were given to me so that I could use them to benefit the world." },
        { name: "Freedom", alignment: "Chaotic", description: "Everyone should be free to pursue his or her own livelihood." },
        { name: "Greed", alignment: "Evil", description: "I'm only in it for the money." },
        { name: "People", alignment: "Neutral", description: "I'm committed to the people I care about, not to ideals." },
        { name: "Aspiration", alignment: "Any", description: "I work hard to be the best there is at my craft." }
      ],
      bonds: [
        "The workshop where I learned my trade is the most important place in the world to me.",
        "I created a great work for someone, and then found them unworthy to receive it. I'm still looking for someone worthy.",
        "I owe my guild a great debt for forging me into the person I am today.",
        "I pursue wealth to secure someone's love.",
        "One day I will return to my guild and prove that I am the greatest artisan of them all.",
        "I will get revenge on the evil forces that destroyed my place of business and ruined my livelihood."
      ],
      flaws: [
        "I'll do anything to get my hands on something rare or priceless.",
        "I'm quick to assume that someone is trying to cheat me.",
        "No one must ever learn that I once stole money from guild coffers.",
        "I'm never satisfied with what I have—I always want more.",
        "I would kill to acquire a noble title.",
        "I'm horribly jealous of anyone who can outshine my handiwork. Everywhere I go, I'm surrounded by rivals."
      ]
    },
    {
      name: "Sailor",
      theme: "An experienced mariner of the seas.",
      description: "You sailed on a seagoing vessel for years. In that time, you faced storms, monsters, and those who wanted to sink your craft.",
      variants: {
        Base: {
          label: "Sailor",
          inheritsPersonality: true,
          skills: ["Athletics", "Perception"],
          toolProficiencies: ["Navigator's tools", "Water vehicles"],
          languages: 0,
          equipment: "Belaying pin (club), 50 feet of silk rope, lucky charm, common clothes, pouch (10 gp)",
          feature: {
            name: "Ship's Passage",
            description: "When you need to, you can secure free passage on a sailing ship for yourself and your adventuring companions."
          }
        },
        Pirate: {
          label: "Pirate",
          inheritsPersonality: true,
          skills: ["Athletics", "Perception"],
          toolProficiencies: ["Navigator's tools", "Water vehicles"],
          languages: 0,
          equipment: "Belaying pin (club), 50 feet of silk rope, lucky charm, common clothes, pouch (10 gp)",
          feature: {
            name: "Bad Reputation",
            description: "You have a fearsome reputation; most people are scared to cross you. You can get away with minor criminal offenses."
          }
        }
      },
      personalityTraits: [
        "My friends know they can rely on me, no matter what.",
        "I work hard so that I can play hard when the work is done.",
        "I enjoy sailing into new ports and making new friends over a flagon of ale.",
        "I stretch the truth for the sake of a good story.",
        "To me, a tavern brawl is a nice way to get to know a new city.",
        "I never pass up a friendly wager.",
        "My language is as foul as an otyugh nest.",
        "I like a job well done, especially if I can convince someone else to do it."
      ],
      ideals: [
        { name: "Respect", alignment: "Good", description: "The thing that keeps a ship together is mutual respect between captain and crew." },
        { name: "Fairness", alignment: "Lawful", description: "We all do the work, so we all share in the rewards." },
        { name: "Freedom", alignment: "Chaotic", description: "The sea is freedom—the freedom to go anywhere and do anything." },
        { name: "Mastery", alignment: "Evil", description: "I'm a predator, and the other ships on the sea are my prey." },
        { name: "People", alignment: "Neutral", description: "I'm committed to my crewmates, not to ideals." },
        { name: "Aspiration", alignment: "Any", description: "Someday I'll own my own ship and chart my own destiny." }
      ],
      bonds: [
        "I'm loyal to my captain first, everything else second.",
        "The ship is most important—crewmates and captains come and go.",
        "I'll always remember my first ship.",
        "In a harbor town, I have a paramour whose eyes nearly stole me from the sea.",
        "I was cheated out of my fair share of the profits, and I want to get my due.",
        "Ruthless pirates murdered my captain and crewmates, plundered our ship, and left me to die. Vengeance will be mine."
      ],
      flaws: [
        "I follow orders, even if I think they're wrong.",
        "I'll say anything to avoid having to do extra work.",
        "Once someone questions my courage, I never back down no matter how dangerous the situation.",
        "Once I start drinking, it's hard for me to stop.",
        "I can't help but pocket loose coins and other trinkets I come across.",
        "My pride will probably lead to my destruction."
      ]
    },
    {
      name: "Urchin",
      theme: "A street kid who grew up in poverty.",
      description: "You grew up on the streets alone, orphaned, and poor. You had no one to watch over you or to provide for you.",
      variants: null,
      skills: ["Sleight of Hand", "Stealth"],
      toolProficiencies: ["Disguise kit", "Thieves' tools"],
      languages: 0,
      equipment: "Small knife, map of your city, pet mouse, token to remember parents, common clothes, pouch (10 gp)",
      feature: {
        name: "City Secrets",
        description: "You know the secret patterns and flow of cities and can find passages through the urban sprawl that others would miss."
      },
      personalityTraits: [
        "I hide scraps of food and trinkets away in my pockets.",
        "I ask a lot of questions.",
        "I like to squeeze into small places where no one else can get to me.",
        "I sleep with my back to a wall or tree, with everything I own wrapped in a bundle in my arms.",
        "I eat like a pig and have bad manners.",
        "I think anyone who's nice to me is hiding evil intent.",
        "I don't like to bathe.",
        "I bluntly say what other people are hinting at or hiding."
      ],
      ideals: [
        { name: "Respect", alignment: "Good", description: "All people, rich or poor, deserve respect." },
        { name: "Community", alignment: "Lawful", description: "We have to take care of each other, because no one else is going to do it." },
        { name: "Change", alignment: "Chaotic", description: "The low are lifted up, and the high and mighty are brought down. Change is the nature of things." },
        { name: "Retribution", alignment: "Evil", description: "The rich need to be shown what life and death are like in the gutters." },
        { name: "People", alignment: "Neutral", description: "I help the people who help me—that's what keeps us alive." },
        { name: "Aspiration", alignment: "Any", description: "I'm going to prove that I'm worthy of a better life." }
      ],
      bonds: [
        "My town or city is my home, and I'll fight to defend it.",
        "I sponsor an orphanage to keep others from enduring what I was forced to endure.",
        "I owe my survival to another urchin who taught me to live on the streets.",
        "I owe a debt I can never repay to the person who took pity on me.",
        "I escaped my life of poverty by robbing an important person, and I'm wanted for it.",
        "No one else should have to endure the hardships I've been through."
      ],
      flaws: [
        "If I'm outnumbered, I will run away from a fight.",
        "Gold seems like a lot of money to me, and I'll do just about anything for more of it.",
        "I will never fully trust anyone other than myself.",
        "I'd rather kill someone in their sleep than fight fair.",
        "It's not stealing if I need it more than someone else.",
        "People who can't take care of themselves get what they deserve."
      ]
    }
  ],

  locations: [
    {
      id: "ravens-hollow",
      name: "Raven's Hollow",
      region: "temperate-forest",
      description: "A small trading town nestled in a valley surrounded by dense, ancient forests. The town is known for its lumber trade and the mysterious ravens that seem to watch everything.",
      features: ["Inn", "Market", "Blacksmith", "Temple", "Mayor's Hall"],
      npcs: [
        {
          name: "Gareth Ironwood",
          class: "Blacksmith",
          description: "A gruff dwarf who runs the town's forge. He's always looking for rare metals and has connections to mining operations.",
          status: "common",
          traits: ["Hardworking", "Honest", "Suspicious of Outsiders"]
        },
        {
          name: "Elara Moonwhisper",
          class: "Innkeeper",
          description: "An elegant elf who owns The Silver Stag Inn. She knows all the town gossip and has a mysterious past.",
          status: "rare",
          traits: ["Charming", "Secretive", "Well-Connected"]
        },
        {
          name: "Brother Marcus",
          class: "Cleric",
          description: "The town's priest who tends to the Temple of Light. He's concerned about strange omens and dark portents.",
          status: "common",
          traits: ["Devout", "Worried", "Protective"]
        }
      ],
      resources: ["Timber", "Game", "Iron Ore"],
      architecture: "Wood and stone buildings with thatched roofs"
    },
    {
      id: "sunspear-oasis",
      name: "Sunspear Oasis",
      region: "desert",
      description: "A vital watering hole in the vast desert, surrounded by date palms and defended by nomadic tribes. Trade caravans often stop here.",
      features: ["Oasis", "Caravanserai", "Tribal Council", "Market Bazaar"],
      npcs: [
        {
          name: "Khalil al-Rashid",
          class: "Merchant Prince",
          description: "A wealthy trader who controls much of the caravan trade through the oasis. He has information about distant lands.",
          status: "legendary",
          traits: ["Wealthy", "Influential", "Ambitious"]
        }
      ],
      resources: ["Water", "Dates", "Spices", "Gems"],
      architecture: "Adobe buildings and colorful tents"
    }
  ],

  world: {
    name: "Aethermoor",
    regions: [
      {
        name: "The Verdant Reaches",
        type: "temperate-forest",
        climate: "Temperate",
        resources: ["Timber", "Game", "Iron", "Coal"],
        description: "Rolling hills covered in ancient forests, dotted with small farming communities and mining settlements."
      },
      {
        name: "The Sundered Wastes",
        type: "desert",
        climate: "Arid",
        resources: ["Gems", "Rare Metals", "Spices"],
        description: "Vast desert wastes broken by occasional oases and ancient ruins of a fallen civilization."
      },
      {
        name: "The Frostpeak Mountains",
        type: "arctic",
        climate: "Arctic",
        resources: ["Precious Metals", "Magical Ice", "Rare Stones"],
        description: "Towering snow-capped peaks where ancient dragons once made their lairs."
      }
    ]
  },

  events: [
    {
      title: "The Missing Caravan",
      description: "A trading caravan bound for Sunspear Oasis has gone missing. Local merchants are worried about the trade route.",
      priority: "high",
      type: "mystery",
      npcsInvolved: ["Khalil al-Rashid"],
      locations: ["ravens-hollow", "sunspear-oasis"]
    },
    {
      title: "Strange Omens",
      description: "The ravens in Raven's Hollow have been acting strangely, and the local priest speaks of dark portents.",
      priority: "medium",
      type: "supernatural",
      npcsInvolved: ["Brother Marcus"],
      locations: ["ravens-hollow"]
    },
    {
      title: "The Blacksmith's Request",
      description: "Gareth needs someone to retrieve rare iron ore from the abandoned mine north of town.",
      priority: "low",
      type: "quest",
      npcsInvolved: ["Gareth Ironwood"],
      locations: ["ravens-hollow"]
    }
  ],

  startingInventory: [
    {
      name: "Worn Leather Armor",
      type: "armor",
      description: "Simple leather armor that has seen better days. Provides basic protection.",
      equipped: true,
      armorClass: 11
    },
    {
      name: "Iron Sword",
      type: "weapon",
      description: "A reliable iron sword with a well-worn grip. Nothing fancy, but it gets the job done.",
      equipped: true,
      damage: "1d8 slashing"
    },
    {
      name: "Traveler's Pack",
      type: "equipment",
      description: "A sturdy backpack containing basic adventuring gear.",
      contents: ["Rope (50 feet)", "Rations (3 days)", "Waterskin", "Tinderbox", "Blanket"]
    },
    {
      name: "Gold Pieces",
      type: "currency",
      quantity: 25,
      description: "Starting coin for equipment and supplies."
    }
  ],

  gameActions: [
    {
      command: "look",
      description: "Examine your surroundings or a specific object",
      examples: ["look", "look at the inn", "examine the strange runes"]
    },
    {
      command: "talk",
      description: "Speak with NPCs or other characters",
      examples: ["talk to Gareth", "speak with the innkeeper", "question the guard"]
    },
    {
      command: "go",
      description: "Move to a different location",
      examples: ["go north", "enter the inn", "travel to the market"]
    },
    {
      command: "attack",
      description: "Engage in combat with enemies",
      examples: ["attack the bandit", "strike with sword", "cast fireball"]
    },
    {
      command: "use",
      description: "Use an item from your inventory",
      examples: ["use healing potion", "use rope", "use lockpicks"]
    },
    {
      command: "search",
      description: "Look for hidden items or secrets",
      examples: ["search the room", "look for traps", "check for secret doors"]
    }
  ]
};