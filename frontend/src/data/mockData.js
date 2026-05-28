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
        { name: "Tradition", alignment: "Lawful", description: "The rituals and hierarchies of your faith exist because generations before you built them to hold something real together. You perform them with precision because imprecision is what lets chaos in. Deviation is not reform — it is rot.", chaosNote: "Chaos cools when you uphold sacred duties even at personal cost. Chaos spikes when you enforce tradition to control others rather than serve the divine." },
        { name: "Charity", alignment: "Good", description: "You see the face of your god in the poor, the sick, and the outcast. The temple's resources exist to flow outward, and you are the channel — whether or not it's convenient, and whether or not the recipient is deserving by your standards.", chaosNote: "Chaos cools when you give without expectation of return. Chaos spikes when you withhold aid because someone offended your faith or your pride." },
        { name: "Change", alignment: "Chaotic", description: "Your faith is a living thing, and living things grow — sometimes away from what their elders intended. You push the boundaries of doctrine because the divine demands relevance, not repetition. The gods are not fossils.", chaosNote: "Chaos cools when you challenge doctrine to better serve the people it claims to protect. Chaos spikes when you upend faith structures for personal glory or just to provoke." },
        { name: "Power", alignment: "Lawful Evil", description: "Faith is architecture. Whoever controls the architecture controls what people believe — what they fear, what they'll sacrifice, what they'll obey. You understand this, and you are building deliberately.", chaosNote: "Chaos rises when you exploit others' faith for control. It only cools when you use that power to protect rather than dominate." },
        { name: "Faith", alignment: "Lawful Good", description: "Doubt is the enemy. Your deity's will is not a menu — you follow all of it, not the comfortable parts. That certainty is your armor and your compass, and sometimes the hardest thing to carry in a room full of compromise.", chaosNote: "Chaos cools when your faith holds you steady in moral crisis. Chaos spikes when you weaponize it to dismiss suffering happening right in front of you." },
        { name: "Aspiration", alignment: "Any", description: "You have seen what devotion can build. You want to become worthy of the highest callings in your faith — not for status, but because the work at that level is where you can do the most genuine good.", chaosNote: "Chaos cools when you grow through service and real effort. Chaos spikes when ambition within the temple makes you step on those you were meant to serve." }
      ],
      bonds: [
        { text: "I owe everything to the temple that took me in.", description: "Before the temple, there was nothing — or worse. Every good thing you have, you have because they opened the doors. That debt shapes how you see every question of loyalty and obligation.", chaosNote: "Chaos cools when you act to protect or honor the temple. Chaos spikes when that debt becomes a leash that silences your conscience." },
        { text: "I'll protect the ancient texts.", description: "The texts predate the current church, the current politics, possibly the current gods. What's written in them matters — and what gets lost cannot be recovered. You are their last reliable guardian.", chaosNote: "Chaos cools when you preserve knowledge at personal risk. Chaos spikes when you use the texts as a source of power over others rather than a trust to keep." },
        { text: "I'd die for my faith.", description: "Not for the institution. Not for the politics. For what the faith actually means — the thing underneath the doctrine. You have drawn a line and you know which side of it you stand on.", chaosNote: "Chaos cools when that conviction holds you to a genuinely moral choice. Chaos spikes when it becomes an excuse to stop thinking." },
        { text: "I wish to find my god's chosen one.", description: "There are signs — there are always signs. You've read them your whole life and you believe they point to someone alive now. Whether you're right or wrong, the search gives you purpose and direction.", chaosNote: "Chaos cools when the quest serves your faith honestly. Chaos spikes when obsession overrides the reality of the person in front of you." },
        { text: "I owe a debt to the priest who raised me.", description: "Not just teachings — that person gave you a life when you had nothing. They are probably flawed and complicated. The debt doesn't expire because of that.", chaosNote: "Chaos cools when you honor that relationship through sacrifice. Chaos spikes when loyalty to them makes you cover for genuine harm." },
        { text: "I seek to preserve my temple's relics.", description: "Sacred objects are the faith made physical — and they're targets. Losing them would break something in your community that cannot be rebuilt with stone and timber alone.", chaosNote: "Chaos cools when preservation requires you to sacrifice something. Chaos spikes when you hoard them from the people who need to be inspired by them." }
      ],
      flaws: [
        { text: "I judge others harshly.", description: "You have a clear picture of how people ought to live, and watching them fall short is genuinely painful — but you mistake that pain for moral authority. The result: you read every stranger as a verdict before they've spoken.", chaosNote: "Chaos spikes when your contempt for others becomes a reason to abandon them or publicly expose them." },
        { text: "My piety hides greed.", description: "The robes are real. The prayers are real. But underneath, you track the temple's finances with a hunger that has nothing to do with the divine. You are very good at not noticing the contradiction.", chaosNote: "Quiet self-interest that harms no one is neutral. Chaos spikes when you redirect faith's resources — tithes, offerings — toward your own comfort or ambition." },
        { text: "I'm inflexible in my thinking.", description: "You arrived at your convictions through hard experience and they are load-bearing. When someone challenges them, you don't argue — you shut down. This feels like certainty. It mostly looks like a wall.", chaosNote: "Chaos spikes when you refuse to update even when staying rigid causes harm to fall on someone else." },
        { text: "I'll do anything to protect my faith's secrets.", description: "Every institution has what it cannot afford to have known. You know what those things are and you have decided that their concealment matters more than your honesty — and possibly more than someone's safety.", chaosNote: "Chaos spikes when protecting the secret means actively deceiving or harming people who deserve the truth." },
        { text: "I'm distrustful of other religions.", description: "You grew up inside one truth, and the existence of other truths is, to you, competition. You don't persecute — you observe, you wait, and you do not give your back to clerics of other faiths.", chaosNote: "Wariness is neutral. Chaos spikes when distrust becomes sabotage or you let someone suffer because their faith differs from yours." },
        { text: "Once I choose a path, I never deviate.", description: "You gave your word once, and that word is still operating. This is admirable in matters of discipline. It is a liability when you need to recognize you were wrong.", chaosNote: "Chaos spikes when you follow a chosen path into territory that is clearly wrong, using commitment as a reason not to choose again." }
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
        { name: "Honor", alignment: "Lawful", description: "There is no law that applies to you — but there is a code. You made a promise once and it held. You made another and it held. The chain of kept words is the only thing that makes you different from the people who'd kill you in your sleep.", chaosNote: "Chaos cools when you honor commitments even when breaking them would be safe. Chaos spikes when you invoke 'honor' selectively to justify what you already wanted to do." },
        { name: "Freedom", alignment: "Chaotic", description: "Every rule was written by someone who benefits from you following it, and you stopped following other people's rules a long time ago. You resist constraint on principle — legal, social, economic. You move when you choose and stay when you choose.", chaosNote: "Chaos cools when you break unjust constraints and help others do the same. Chaos spikes when 'freedom' covers abandoning people who were counting on you." },
        { name: "Charity", alignment: "Good", description: "The coin moves upward naturally — always. You redirect some of it. You know what hunger looks like, you know where the excess is, and the math is simple.", chaosNote: "Chaos cools when you genuinely redistribute at cost to yourself. Chaos spikes when 'steal from the rich' becomes cover for stealing from anyone convenient." },
        { name: "Greed", alignment: "Evil", description: "Nothing is sacred. Everything has a price, including the people around you. You're not proud of this — you've just stopped pretending otherwise, which is its own kind of honesty.", chaosNote: "Neutral at low stakes. Chaos spikes sharply when you sell out people who trusted you, especially those who have less than you." },
        { name: "People", alignment: "Neutral", description: "Abstract principles are for people who've never needed to trust someone with their life. What keeps you alive is the crew — specific people, specific trust, specific history. That's where your loyalty lives.", chaosNote: "Chaos cools when you sacrifice for the crew without expectation. Chaos spikes when crew loyalty becomes a reason to harm those outside it." },
        { name: "Redemption", alignment: "Good", description: "You know what you've done. You're not going to apologize for surviving, but you would like to leave less wreckage behind you. You're testing whether that's actually possible.", chaosNote: "Chaos cools when you make a hard choice that serves someone else instead of yourself. Chaos spikes when 'redemption' is a story you tell without changing your actual behavior." }
      ],
      bonds: [
        { text: "I'm loyal to my first boss.", description: "The person who gave you your first real job and your first real trust — whatever they've done since, that debt doesn't expire. You think about them when things get hard.", chaosNote: "Chaos cools when you honor that loyalty at real cost. Chaos spikes when you sell them out for convenience or pretend the debt is settled." },
        { text: "Someone I love was killed because of me.", description: "You made a call, or failed to make one, and someone died for it. You don't explain this to people. You carry it alone and let it shape your choices in ways you don't always acknowledge.", chaosNote: "Chaos cools when grief pushes you toward protecting others. Chaos spikes when it justifies recklessness or revenge that harms the innocent." },
        { text: "I owe debts I must repay.", description: "Real debts — the kind where someone finds you if you don't pay. And a few debts of the other kind, where the person who helped you will never ask. Both matter.", chaosNote: "Chaos cools when you honor a debt at personal cost. Chaos spikes when you prioritize dangerous creditors while ignoring people you've actually wronged." },
        { text: "I'd do anything for my crew.", description: "They've seen you at your worst and kept their mouths shut. You've done the same. The crew is not sentiment — it's an operational reality you don't compromise.", chaosNote: "Chaos cools when you protect crew at personal risk. Chaos spikes when crew loyalty becomes a reason to harm people outside it who didn't deserve it." },
        { text: "A rival ruined me — I'll get revenge.", description: "They took something — a job, a reputation, a relationship — and they did it deliberately. You're not emotional about it. You're patient, you're specific, and you're waiting for the right moment.", chaosNote: "Neutral for a legitimate wrong. Chaos spikes when revenge spreads to people adjacent to your target who had nothing to do with it." },
        { text: "I'm still hunted by the law.", description: "There's a warrant or a grudge somewhere with your face on it. This is a constant overhead cost on every plan you make and every relationship you form.", chaosNote: "Neutral to manage pragmatically. Chaos spikes when you burn someone else's cover or put allies at risk to protect your own anonymity." }
      ],
      flaws: [
        { text: "I can't resist a shiny thing.", description: "Your hands move toward valuable objects before your mind catches up — acquisition is a reflex you built over years, and it activates whether or not it's a good idea right now.", chaosNote: "Neutral in everyday operation. Chaos spikes when you steal from the people protecting you or from those who are already desperate." },
        { text: "I'm too greedy to walk away.", description: "The sensible exit point keeps moving. There's always one more score between you and enough, and you know this, and you stay anyway.", chaosNote: "Ambition is neutral. Chaos spikes when your inability to leave pulls others into danger they didn't sign up for." },
        { text: "I'll betray a friend for the right price.", description: "You've done it before. You've thought it through since. You haven't arrived at a different answer — you've just gotten more careful about who you call a friend.", chaosNote: "Almost always a chaos spike. The only neutral ground is when the 'friend' was themselves a threat to someone more vulnerable." },
        { text: "I get violent when mocked.", description: "Pride is armor in your world. Let someone crack it in public and you respond in the only language that reestablishes respect. The logic is circular and you know it.", chaosNote: "Chaos spikes when you escalate a social slight into physical harm against someone who wasn't actually a danger." },
        { text: "I'm paranoid everyone's out to get me.", description: "Some of the time this is accurate. The problem is your calibration: the paranoia is constant whether or not the threat is real, which means it leaks into relationships that were safe.", chaosNote: "Skepticism in genuine danger is neutral. Chaos spikes when paranoia makes you act against someone who was trying to help you." },
        { text: "I can't resist taking risks.", description: "Risk is the medium you operate in, and after years in it, safe feels wrong. You escalate when you should consolidate. You gamble when the position is already good.", chaosNote: "Taking calculated risks with your own skin is neutral. Chaos spikes when the risk you chase pulls others into jeopardy they didn't choose." }
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
        { name: "Respect", alignment: "Good", description: "You came from nothing, and you remember what it felt like to be talked past and dismissed. That experience didn't make you bitter — it made you careful to never do it to someone else. Every person in front of you gets treated like they matter, because they do.", chaosNote: "Chaos cools when you stand up for someone being disrespected at personal cost. Chaos spikes when you demand respect for yourself while denying it to those who haven't 'earned' it in your eyes." },
        { name: "Fairness", alignment: "Lawful", description: "You've seen what happens when the rules bend for people with gold. You hold to a standard that doesn't move — not because you're naive, but because someone has to be the fixed point in a world that bends.", chaosNote: "Chaos cools when fairness applies equally to people you like and people you don't. Chaos spikes when you enforce fairness selectively based on who you've already decided is wrong." },
        { name: "Freedom", alignment: "Chaotic", description: "Tyrants don't call themselves tyrants. They call themselves lords, or order, or tradition. You've seen the shape of a boot on a neck and you recognize it regardless of what it's wearing. You pull boots off.", chaosNote: "Chaos cools when you resist or dismantle genuine oppression. Chaos spikes when you define 'tyrant' so broadly that any leader who disagrees with you qualifies." },
        { name: "Might", alignment: "Evil", description: "The strong rule and the weak serve — not because it's right, but because it's true. You used to pretend otherwise. You don't anymore. The question now is whether you intend to be among the strong.", chaosNote: "Power in situations of genuine threat is neutral. Chaos spikes sharply when you use 'might makes right' to harm people who are simply weaker, not wrong." },
        { name: "Sincerity", alignment: "Neutral", description: "Flattery is a lie wrapped in a compliment. You say what you mean, you mean what you say, and you expect the same — not because you're naive, but because you've seen what happens when everyone plays a role instead.", chaosNote: "Direct speech is neutral. Chaos spikes when sincerity becomes a weapon — brutal honesty deployed to wound rather than to clarify." },
        { name: "Destiny", alignment: "Any", description: "You didn't ask to become the person people turn to. But the things that happened to you, the choices you made, the fact that you're still standing — it points somewhere. You feel the pull even when you can't name the destination.", chaosNote: "Pursuing purpose is neutral. Chaos spikes when belief in destiny makes you discount the choices and suffering of the people who got caught in your story." }
      ],
      bonds: [
        { text: "I'll protect my village.", description: "Not an abstract concept — the actual people: the miller's family, the kids who played in the square, the elder who sat outside in summer. They're the reason everything started.", chaosNote: "Chaos cools when you sacrifice for them even when they can't repay it. Chaos spikes when you use 'protecting the village' to justify violence against people who haven't actually threatened it." },
        { text: "I owe my life to the people who helped me.", description: "There was a moment when you were finished, and someone stepped in. The debt doesn't go away with time — it just changes shape. You're still paying it.", chaosNote: "Chaos cools when you extend that same help to others. Chaos spikes when honoring this debt means abandoning an obligation that matters just as much." },
        { text: "I pursue the monster that destroyed my home.", description: "There's a specific target to this — not 'monsters in general' but this one, what it did, to people with names. The pursuit is what got you here.", chaosNote: "Focused pursuit of a genuine wrong is neutral. Chaos spikes when the hunt consumes you enough to ignore harm you could prevent along the way." },
        { text: "I fight for those who can't.", description: "The people who need protection are never the ones with resources to get it. You fill that gap — not because you expect anything back, but because if not you, then nobody.", chaosNote: "Chaos cools when you intervene at personal risk. Chaos spikes when you decide who deserves protection based on your own judgments rather than their need." },
        { text: "I must prove myself a true hero.", description: "Other people started calling you a hero and you've never been sure they were right. The stories got bigger than the reality. You keep looking for the act that proves the title fits.", chaosNote: "Chaos cools when you act heroically without an audience. Chaos spikes when the need for proof pushes you to take risks that endanger the people you're supposed to be protecting." },
        { text: "My tools are a family heirloom.", description: "They came down through hands that worked harder than yours, in conditions worse than yours. Using them is an act of connection to people who are gone.", chaosNote: "Caring for inherited objects is neutral. Chaos spikes when protecting the tools makes you hesitate to use them for the exact purpose those people would have wanted." }
      ],
      flaws: [
        { text: "I'm naive about city ways.", description: "You can read weather and land, but not a merchant's parlor full of people with competing agendas. The gap between what you know and what cities require is real and has costs.", chaosNote: "Neutral to be out of your element. Chaos spikes when your naivety gets used against the people who trusted you to navigate on their behalf." },
        { text: "I believe I'm always right.", description: "Your instincts have saved lives. Your gut has been reliable enough that you've stopped distinguishing between 'I think' and 'I know.' This is the gap that will eventually cause problems.", chaosNote: "Confidence in genuine expertise is neutral. Chaos spikes when certainty makes you override better judgment from someone who actually knows more than you." },
        { text: "I'm obsessed with proving my heroism.", description: "The fear underneath every decision is: what if you're not what the stories say? What if you stumbled into the right place at the right time? The obsession is the fear in disguise.", chaosNote: "Chaos cools when you help without needing recognition. Chaos spikes when the need to be seen as heroic pushes you into unnecessary danger or recklessness." },
        { text: "I underestimate my foes.", description: "You've beaten bigger. You've walked out of worse. The pattern has taught you that things tend to work out — which means you stop taking enemies seriously until they've already surprised you.", chaosNote: "Confidence is neutral. Chaos spikes when underestimating an enemy gets a companion killed or a situation out of hand." },
        { text: "I overcommit to causes.", description: "Every problem you hear about is a call you feel personally responsible to answer. You haven't figured out yet that saying yes to everything is also a way of saying yes to nothing.", chaosNote: "Generosity is neutral. Chaos spikes when overcommitment means you break promises to specific people in order to chase abstract causes." },
        { text: "I'm blunt and tactless.", description: "Hedging feels dishonest and politics feels like a game for people who can't say what they mean. You say what you mean. The diplomatic cost is something you've decided to pay.", chaosNote: "Direct speech is neutral. Chaos spikes when bluntness actively harms someone's standing or safety in a situation that called for measured words." }
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
        { name: "Respect", alignment: "Good", description: "The thing that separates a noble from a tyrant is the recognition that the people below you are actually people. You've watched lords forget this in real time. You intend not to.", chaosNote: "Chaos cools when you extend genuine dignity to those with less power. Chaos spikes when 'respect' means deference on your terms — knowing their place rather than their worth." },
        { name: "Responsibility", alignment: "Lawful", description: "Power without obligation is theft. The estate, the title, the deference — none of it belongs to you personally. You hold it in trust for the people under your protection, and you take that trust seriously.", chaosNote: "Chaos cools when you sacrifice personal comfort to fulfill an obligation. Chaos spikes when 'responsibility' becomes a reason to control others rather than serve them." },
        { name: "Independence", alignment: "Chaotic", description: "The line of succession goes back eleven generations. You are the next, and you have decided your life will not be determined by the ones before you. The legacy is yours to inherit, not yours to be imprisoned by.", chaosNote: "Chaos cools when independence costs you something real. Chaos spikes when it means refusing obligations to people counting on the title you still carry." },
        { name: "Power", alignment: "Evil", description: "Position is the game. Allies are assets. Debts are leverage. You don't apologize for understanding how it works — you only observe that others play it while pretending they don't.", chaosNote: "Strategic navigation of power is neutral. Chaos spikes when accumulating power requires actively harming or betraying people who trusted you with access." },
        { name: "Family", alignment: "Any", description: "Every decision runs through one filter: what does this do to the family? Not sentiment — strategy. The house outlasts any of you, and its survival is the only thing that actually matters in the long run.", chaosNote: "Protecting family is neutral. Chaos spikes when family loyalty becomes a reason to actively harm people outside the family who deserve better." },
        { name: "Noblesse Oblige", alignment: "Good", description: "The old phrase means something: nobility obligates. Not charity as a performance of status, but actual service — harder decisions, greater sacrifice, higher standards, because you had advantages the others didn't.", chaosNote: "Chaos cools when your privilege becomes a cost you pay, not a benefit you collect. Chaos spikes when 'leading by example' is performance without actual sacrifice." }
      ],
      bonds: [
        { text: "My family is everything.", description: "Not the name — the people. The ones at the table, the ones who share the history. Whatever else changes, protecting them is the fixed point everything else arranges around.", chaosNote: "Chaos cools when family loyalty demands something difficult. Chaos spikes when it means actively sacrificing people outside the family who deserved protection." },
        { text: "I'll reclaim my family's honor.", description: "Something happened — a scandal, a defeat, a betrayal — and the name carries the stain of it. You're either going to undo it or die trying. Both feel equally possible some days.", chaosNote: "Chaos cools when the pursuit demands genuine sacrifice. Chaos spikes when 'restoring honor' justifies harming people who weren't involved in the original wrong." },
        { text: "My loyalty lies with my house.", description: "The house is a network of obligations, debts, and alliances accumulated across generations. You are one node in that network, and the network's stability depends on every node holding.", chaosNote: "Institutional loyalty is neutral. Chaos spikes when loyalty to the house means covering for genuine harm done in its name." },
        { text: "I love someone beneath my station.", description: "The feeling is real and the complications are also real. The gap between your worlds is structural — it creates pressures that neither of you fully controls and that don't resolve with sentiment.", chaosNote: "Chaos cools when you protect this person at cost to your standing. Chaos spikes when social pressure makes you treat them poorly to protect your own reputation." },
        { text: "The commoners must learn their place.", description: "This is the flaw you haven't examined yet. It's not cruelty — it's the water you swim in, absorbed from people who raised you. You believe it sincerely, which is its own kind of problem.", chaosNote: "Almost always a chaos spike. The only neutral ground is recognizing it as a belief worth questioning rather than a truth worth enforcing." },
        { text: "I owe my house's survival to a powerful ally.", description: "They pulled you back from the edge of ruin. The debt is real and the ally knows it. The terms of that debt are not fully stated, and at some point they will be.", chaosNote: "Honoring debts is neutral. Chaos spikes when repaying this ally requires harming people who had nothing to do with the original bargain." }
      ],
      flaws: [
        { text: "I secretly despise commoners.", description: "You were raised with contempt built in. It shows at the edges — a barely-controlled expression, a comment that lands wrong — and you've never really interrogated where it came from.", chaosNote: "Almost always a chaos spike when acted upon. Chaos cools in the moment you catch yourself and don't act on it." },
        { text: "I can't resist gossip.", description: "Information is currency, and gossip is the informal exchange rate. You collect it reflexively and spend it without always thinking about the cost to the people it concerns.", chaosNote: "Sharing information strategically is neutral. Chaos spikes when gossip actively harms someone's safety, standing, or livelihood." },
        { text: "I'm a terrible gambler.", description: "The money is almost beside the point — you're chasing a specific sensation of risk and resolution you don't get from running a manor. The losses escalate proportional to how bored you've been.", chaosNote: "Gambling with your own resources is neutral. Chaos spikes when losses start affecting the people or obligations you're responsible for." },
        { text: "I hold grudges.", description: "The slight is in a ledger you maintain with precision. It may have been years ago and the other person may have forgotten entirely. You have not.", chaosNote: "Remembering wrongs is neutral. Chaos spikes when old grudges make you act against someone who has since changed, or when you harm a third party to settle the score." },
        { text: "I crave luxury.", description: "Fine things aren't indulgence to you — they're the baseline. When they're absent, you notice sharply. You make decisions around maintaining them that you wouldn't want to defend out loud.", chaosNote: "Personal comfort is neutral. Chaos spikes when comfort becomes the reason you compromise your obligations or make decisions that harm others." },
        { text: "I'm vain and arrogant.", description: "Your opinion of yourself is high, and it's not entirely unfounded — which makes it harder to address. You're aware of this as a trait; you're less aware of the actual damage it does in conversations you thought went well.", chaosNote: "Confidence is neutral. Chaos spikes when arrogance makes you dismiss critical information, belittle allies, or make decisions without counsel from people who knew better." }
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
        { name: "Greater Good", alignment: "Good", description: "You have seen what it costs to do nothing. You've also seen what it costs to do the right thing at the wrong time. The calculation never gets easier, but you've committed to running it honestly every time.", chaosNote: "Chaos cools when you accept personal cost for a collective benefit. Chaos spikes when 'greater good' becomes a reason to override the suffering of specific people in front of you." },
        { name: "Responsibility", alignment: "Lawful", description: "Chain of command is not about blind obedience — it's about trust, and you've earned it and extended it both ways. When the chain breaks, something important breaks with it that can't always be rebuilt.", chaosNote: "Following legitimate orders is neutral. Chaos spikes when responsibility becomes the justification for following orders that are clearly and actively wrong." },
        { name: "Independence", alignment: "Chaotic", description: "You've taken enough orders from people who didn't know the ground to know that the plan never survives contact. You fight for yourself now — your own judgment, your own read of the situation, your own terms.", chaosNote: "Acting on superior field knowledge is neutral. Chaos spikes when independence becomes self-serving in a way that leaves your companions exposed." },
        { name: "Might", alignment: "Evil", description: "You've watched the side with better supply lines win. You've watched the side with more soldiers win. You've stopped attributing virtue to the winners — they won because they were stronger, full stop.", chaosNote: "Realism about power is neutral. Chaos spikes when 'the strong rule' becomes a reason to harm or exploit people who simply can't fight back." },
        { name: "Live and Let Live", alignment: "Neutral", description: "You've seen enough war to know what it's actually about, and it's not what the recruiters say. You want to be left alone and in exchange you'll leave others alone. This is not cynicism — it's arithmetic.", chaosNote: "Non-interference is neutral. Chaos spikes when 'live and let live' becomes a reason to stand by while something genuinely wrong happens right in front of you." },
        { name: "Nation", alignment: "Any", description: "Not the government — the land, the people, the thing that exists underneath whatever leadership happens to be in power this decade. You'd serve it under a different flag if that's what it needed.", chaosNote: "Patriotism is neutral. Chaos spikes when the nation becomes an abstraction that justifies harming specific people who are also part of it." }
      ],
      bonds: [
        { text: "I would die for my unit.", description: "Not sentiment — operational reality. The people in your unit are the reason you came back from places where you shouldn't have. The loyalty runs both directions and it's not theoretical.", chaosNote: "Protecting your people is neutral. Chaos spikes when unit loyalty means covering for genuine harm done by a member or against people outside the unit." },
        { text: "My honor is my life.", description: "In the world you come from, reputation was the only currency that transferred between postings. You've built yours carefully and you will not damage it for convenience.", chaosNote: "Chaos cools when honor costs you something real. Chaos spikes when defending your honor means harming someone who challenged it fairly." },
        { text: "I'll never forget a fallen comrade.", description: "You carry their name. You remember their face. You don't need a monument — the weight of it travels with you, and some days it's heavier than others.", chaosNote: "Honoring the dead through your actions is neutral. Chaos spikes when grief or guilt pushes you into choices that would have horrified them." },
        { text: "My weapon belonged to a mentor.", description: "It came down to you because they believed you were the right hands for it. Using it is a statement about who you are and whose legacy you carry forward.", chaosNote: "Chaos cools when you prove worthy of that trust. Chaos spikes when you use the weapon — or invoke their legacy — for something they'd have refused." },
        { text: "I seek glory.", description: "Not fame exactly — something more specific: the moment when you're exactly equal to the hardest situation you've ever faced. You've tasted it and you're looking for it again.", chaosNote: "Pursuing excellence is neutral. Chaos spikes when the pursuit puts companions at risk they didn't agree to for the sake of your personal moment." },
        { text: "I'm loyal to my commander.", description: "Specific loyalty to a specific person — not a rank, not an institution. This person earned it. You're not sure the next one will, and you don't extend the loyalty automatically.", chaosNote: "Personal loyalty is neutral. Chaos spikes when loyalty to the commander makes you execute orders that harm people who didn't deserve it." }
      ],
      flaws: [
        { text: "I follow orders even when wrong.", description: "The discipline that kept you alive also keeps you from questioning the chain when the chain has rusted. You know this. You haven't figured out which is the bigger risk: the wrong order or the breakdown of trust.", chaosNote: "Following orders in ambiguous situations is neutral. Chaos spikes when the order is unambiguously harmful and you follow it anyway." },
        { text: "I drink to forget.", description: "There are things from the field you have not processed and do not intend to process. The drink is the management strategy. It works right up until it stops working.", chaosNote: "Managing pain privately is neutral. Chaos spikes when the drinking makes you a danger to those around you or causes you to miss something important." },
        { text: "I'm reckless in battle.", description: "There is something that happens in combat — a particular clarity — that makes the calculation of survival feel irrelevant. You move faster and harder than the plan calls for and figure the rest out later.", chaosNote: "Aggressive tactics in high-stakes situations are neutral. Chaos spikes when recklessness gets a companion hurt because you chose momentum over coordination." },
        { text: "I despise the enemy.", description: "You've fought enough of them to have a full picture of what they are. The contempt is earned, you'll say. It also makes you stop seeing them as people, which makes certain mistakes more likely.", chaosNote: "Tactical depersonalization in combat is neutral. Chaos spikes when contempt makes you act brutally toward enemies who have surrendered or civilians caught in between." },
        { text: "I'm too blunt for politics.", description: "You've never learned to say things sideways. In a negotiation or a court situation, you say what you mean, everyone knows exactly what you think, and the diplomatic situation deteriorates rapidly.", chaosNote: "Direct speech is neutral. Chaos spikes when bluntness causes political damage that makes things worse for people depending on the outcome." },
        { text: "I secretly fear cowardice.", description: "Not death — cowardice. The possibility that under sufficient pressure you'll find out you're not who you thought you were. You take risks partly to keep proving otherwise, which has a cost of its own.", chaosNote: "Pushing yourself toward courage is neutral. Chaos spikes when fear of appearing cowardly makes you take unnecessary risks that endanger others." }
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
        { name: "Knowledge", alignment: "Neutral", description: "Understanding is the only currency that doesn't devalue with time. Everything you've accumulated — observations, texts, conversations with the dying — adds to a picture that exists in no other mind. The picture is never finished, and that's the point.", chaosNote: "Pursuing knowledge is neutral. Chaos spikes when the pursuit leads you to harm someone or release dangerous information without considering the consequences." },
        { name: "Beauty", alignment: "Good", description: "The thing crafted perfectly — a proof, a piece of music, a manuscript — is doing something the universe wouldn't do without it. When you protect it, you're protecting an irreplaceable contribution that cannot be rebuilt if lost.", chaosNote: "Preservation for its own sake is neutral. Chaos spikes when you prioritize the beautiful artifact over the suffering of the person standing in front of you." },
        { name: "Logic", alignment: "Lawful", description: "The universe operates on principles. Your emotions do not have access to those principles — they route around them. You think better when you set them aside, and you have been practicing for years.", chaosNote: "Reason-driven decisions are neutral. Chaos spikes when cold logic dismisses legitimate human suffering as a variable rather than a reality." },
        { name: "No Limits", alignment: "Chaotic", description: "The gates on knowledge were built by people who were afraid of what lay on the other side. The question worth asking is always the one you're not supposed to ask. Forbidden is just another word for interesting.", chaosNote: "Intellectual courage is neutral. Chaos spikes when the pursuit of forbidden knowledge puts others at risk who never agreed to be part of the experiment." },
        { name: "Power", alignment: "Evil", description: "The person who understands a system can operate it, modify it, or end it. Knowledge is not neutral — it is leverage. You are building an unassailable position one piece of understanding at a time.", chaosNote: "Accumulating knowledge is neutral. Chaos spikes when you use what you know to control, expose, or harm people who trusted you with access to their secrets." },
        { name: "Self-Improvement", alignment: "Any", description: "You are a rough draft. Every text you read, every skill you develop, every mistake you analyze — you are editing the next version. The project is ongoing and the deadline is death.", chaosNote: "Growth is neutral. Chaos spikes when self-improvement becomes self-absorption — when your own development eclipses people around you who needed your attention." }
      ],
      bonds: [
        { text: "My mentor is the most important person in my life.", description: "They changed the shape of your thinking, which means they changed the shape of your life. The relationship is complicated in the way deep relationships always are, but it's the most formative thing that happened to you.", chaosNote: "Chaos cools when you honor the relationship by doing work that surpasses what they taught. Chaos spikes when loyalty makes you defend their failures or cover their errors." },
        { text: "I must protect a library, university, or archive.", description: "The institution contains things that exist nowhere else. It is not a building — it is a continuity. What happens to it is what happens to every text it holds and every future thinker who needed those texts.", chaosNote: "Chaos cools when you defend it at real personal cost. Chaos spikes when protecting the institution means covering for harm done within it." },
        { text: "I own an ancient text that holds terrible secrets.", description: "You've read it. You understand what it is. You're still working out what to do with that understanding, and you've been at it long enough that it's starting to feel like the text chose you rather than the reverse.", chaosNote: "Keeping dangerous knowledge secure is neutral. Chaos spikes when you share it — or its implications — without understanding what it will set in motion." },
        { text: "I work to prove a theory that could rewrite history.", description: "Not 'update' — rewrite. The thing you believe, if correct, undoes something fundamental that people have built their understanding on. The implications are enormous. The resistance will be too.", chaosNote: "Chaos cools when you pursue the truth honestly even when inconvenient. Chaos spikes when you suppress contradictory evidence to protect the theory." },
        { text: "I've been wronged by another scholar and seek revenge.", description: "They stole work, claimed credit, sabotaged a career, or did something worse. The academic world has no good mechanism for redress, so you've built your own.", chaosNote: "Holding someone accountable is neutral. Chaos spikes when revenge extends to harming people adjacent to your target who had no role in the original wrong." },
        { text: "My life's work is nearly complete; I must see it through.", description: "Decades of work are converging. The end is visible for the first time. You will not die before you finish it, which means you've stopped treating your own safety as a fixed constraint.", chaosNote: "Commitment to completion is neutral. Chaos spikes when the work becomes more important than the people around you who need your attention now." }
      ],
      flaws: [
        { text: "I am easily distracted by promising information.", description: "An interesting thread will pull you off the path you were on. This is sometimes how discoveries happen. It is reliably bad when the path you were on had an urgent destination.", chaosNote: "Intellectual curiosity is neutral. Chaos spikes when a distraction causes you to miss something your companions were depending on you to do." },
        { text: "I speak condescendingly to the uneducated.", description: "You calibrate to what you assess the other person can understand, and your assessment is frequently wrong — or your calibration produces something that sounds like contempt even when it isn't.", chaosNote: "Simplifying complex ideas is neutral. Chaos spikes when condescension becomes visible enough to harm a relationship or undermine trust you needed." },
        { text: "I can't keep a secret to save my life.", description: "Information wants to be circulated — you believe this sincerely. Holding something back feels like hoarding. The problem is that some information has owners who didn't consent to the circulation.", chaosNote: "Transparency is usually neutral. Chaos spikes when you share something told to you in confidence and the exposure harms the person who trusted you." },
        { text: "I'm obsessed with my studies.", description: "There is always more to do. There is always a reason to stay at the desk one more hour. The world outside the study exists in theory, and you've been meaning to get back to it.", chaosNote: "Dedication is neutral. Chaos spikes when the obsession makes you neglect or abandon people who needed you to be present." },
        { text: "I disregard practical matters for theoretical ones.", description: "The question of whether it works is less interesting than the question of why it works. In environments that require working things, this is a known liability you underaddress.", chaosNote: "Prioritizing understanding is neutral. Chaos spikes when the disregard for practical reality causes concrete harm to people dealing with its consequences." },
        { text: "I'll risk anything for a big discovery.", description: "Your own safety is a negotiating position, not a fixed constraint. This has served you well in the past. It also means that 'anything' sometimes turns out to include things that didn't belong to you.", chaosNote: "Accepting personal risk for knowledge is neutral. Chaos spikes when 'anything' extends to risking the safety of people who didn't agree to the wager." }
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
        { name: "Change", alignment: "Chaotic", description: "The seasons shift, the herds move, the rivers change course. Everything that refuses to change eventually dies in a form that no longer fits the world around it. You move with the changes rather than against them.", chaosNote: "Embracing change is neutral. Chaos spikes when you change course in ways that abandon people who were depending on your consistency." },
        { name: "Greater Good", alignment: "Good", description: "The natural world doesn't belong to any single creature. You've seen what happens when one settlement takes more than it needs. The accounting always comes due, and you try to be part of the balance rather than the debt.", chaosNote: "Acting for collective benefit is neutral. Chaos spikes when 'the greater good' overrides the specific, urgent needs of a person directly in front of you." },
        { name: "Honor", alignment: "Lawful", description: "Your word is the only law where you come from. Contracts don't travel well into the deep wild, but a given word does. You don't break it for social, legal, or convenient reasons — breaking it would make you something you don't want to be.", chaosNote: "Keeping your word is neutral. Chaos spikes when honoring a promise to one person makes you betray a more urgent obligation to another." },
        { name: "Might", alignment: "Evil", description: "The strong survive. The weak serve or die. You've watched this operate without exception for your entire life. You're not cruel — you're reading the actual rules of the game, not the story your civilized companions tell each other.", chaosNote: "Realism about strength is neutral. Chaos spikes when 'the strong survive' justifies harming people who are simply weaker, not wrong." },
        { name: "Nature", alignment: "Neutral", description: "The forest doesn't care about your politics, your money, or your gods. It operates on older rules. You find this clarifying — civilization feels like noise, and the wild feels like signal.", chaosNote: "Connection to nature is neutral. Chaos spikes when reverence for the natural world makes you indifferent to human suffering the wild is actively causing." },
        { name: "Glory", alignment: "Any", description: "You measure yourself against the hardest things — not to impress others, but because you need to know what you're made of. The great deeds are the test you keep setting for yourself.", chaosNote: "Pursuing excellence through challenge is neutral. Chaos spikes when the pursuit of glory puts companions at risk they didn't agree to." }
      ],
      bonds: [
        { text: "My family, clan, or tribe is my life.", description: "Not sentiment — architecture. Everything you are was built by these people, in this place, over these years. The obligation runs in both directions and it doesn't have an off switch.", chaosNote: "Chaos cools when you sacrifice for your community. Chaos spikes when tribal loyalty justifies harming people from outside it who've done nothing to deserve it." },
        { text: "An injury to the wilderness is an injury to me.", description: "Deforestation, poisoned rivers, over-hunted grounds — these aren't abstractions. You can read the land, and reading damage in a place you know feels like reading it in yourself.", chaosNote: "Chaos cools when you protect natural places at real personal cost. Chaos spikes when the defense of wilderness becomes more important than the people living within it." },
        { text: "I will bring terrible wrath down on those who despoil nature.", description: "You've named this clearly and committed to it. The consequence of crossing you in this specific way is not something you're vague about — and you mean it.", chaosNote: "Protecting what you love is neutral. Chaos spikes when the wrath extends to people adjacent to the damage rather than those directly responsible." },
        { text: "I was once saved by a great beast; I owe it a debt.", description: "It knew what it was doing — you're sure of it. The debt is real, whether or not anyone else would recognize it, and you watch for opportunities to return it.", chaosNote: "Honoring an unusual debt is neutral. Chaos spikes when fulfilling it requires acting against the interests of people who are depending on you." },
        { text: "I seek vengeance on those who destroyed my home.", description: "There's a specific target — people with names, faces, motivations. The destruction was deliberate and you intend there to be consequences.", chaosNote: "Pursuing a legitimate wrong is neutral. Chaos spikes when vengeance spreads to people associated with your targets who had no role in the original act." },
        { text: "I want to see the world beyond the wilds.", description: "The edge of your territory is not the edge of the world, and you've known that for a long time. You want to know what's on the other side — in your hands and feet, not in a story told to you.", chaosNote: "Curiosity and exploration are neutral. Chaos spikes when the pursuit of new experiences makes you unreliable to people counting on you to be present." }
      ],
      flaws: [
        { text: "I am too quick to judge city folk.", description: "They're soft, ignorant of basics, building worlds inside walls to pretend the outside isn't real. Some of this assessment is accurate. The rest is a wall you've built from the other side.", chaosNote: "Skepticism about unfamiliar contexts is neutral. Chaos spikes when the quick judgment prevents you from using information or help that would have served your companions." },
        { text: "There's no room for mercy in the wild.", description: "The injured predator bites hardest. Leaving the enemy alive is leaving an asset active. This is correct in the wild and creates serious problems in most other situations.", chaosNote: "Efficiency in life-threatening situations is neutral. Chaos spikes when you apply 'no mercy' to people or creatures in situations that don't actually require it." },
        { text: "I struggle to adapt to civilized life.", description: "The rules are invisible, they change without notice, and they seem designed to be impenetrable for someone who learned in a different system. You do your best. It doesn't always read well.", chaosNote: "Adapting to unfamiliar environments is neutral. Chaos spikes when the struggle creates problems for companions depending on you to function in civilization." },
        { text: "I can't resist a good challenge.", description: "Something in you responds to a genuine test the way a hunting dog responds to a scent. You can't be sure if this is a strength or a vulnerability until after the challenge is over.", chaosNote: "Rising to a genuine challenge is neutral. Chaos spikes when accepting the challenge puts companions at risk who didn't agree to participate." },
        { text: "I hoard trophies of my kills.", description: "Each one means something specific — a specific day, a specific test, a specific outcome. The accumulation is not pride exactly. It's a record of what you've survived.", chaosNote: "Keeping personal records is neutral. Chaos spikes when the trophy habit creates conflict with people who find it disturbing or slows you at a moment requiring speed." },
        { text: "I believe every problem can be solved with survival skill.", description: "Build the shelter, read the weather, find the water — these are answers. Social problems, political problems, grief — you keep reaching for the same tools, and they keep not fitting.", chaosNote: "Applying known expertise is neutral. Chaos spikes when insisting on your approach delays addressing a problem the proper way, at cost to others." }
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
        { name: "Independence", alignment: "Chaotic", description: "No one tells you what to do — not a lord, not a guild, not a god with a preference. You've spent your life building a life that cannot be dictated by anyone but yourself, and that project is ongoing. The con is just the revenue model.", chaosNote: "Living outside others' control is neutral. Chaos spikes when you drag others into your independence without their consent — using them, then leaving them with the consequences." },
        { name: "Fairness", alignment: "Lawful", description: "There are marks worth taking and marks worth leaving alone. The widow with three children? Walk past. The merchant who's been running his own con on tenants for years? That's your kind of target. The line isn't complicated, and you don't cross it.", chaosNote: "Principled target selection is neutral. Chaos spikes when the line quietly moves toward whoever has money, regardless of circumstances." },
        { name: "Charity", alignment: "Good", description: "The coin moves upward naturally. You redirect it. You're not running these cons to retire in comfort — you understand where the excess is and where the shortage is, and you do the math.", chaosNote: "Genuine redistribution is neutral. Chaos spikes when 'charity' becomes the story you tell about what is, in practice, your own enrichment." },
        { name: "Creativity", alignment: "Chaotic", description: "Running the same con twice is a failure of imagination. Every mark is a new problem to solve, every situation is a new performance, every exit is an original composition. Boredom is the real enemy.", chaosNote: "Creative problem-solving is neutral. Chaos spikes when the drive for novelty makes you run cons on people who didn't deserve it just because the scenario interested you." },
        { name: "Friendship", alignment: "Good", description: "The masks come off somewhere. With specific people — the ones who have seen through the performance and stayed — you're actually yourself, whoever that is. Protecting that is the one thing you don't treat as negotiable.", chaosNote: "Chaos cools when you sacrifice for genuine friends at real cost. Chaos spikes when you pull them into a con and let them carry consequences you created." },
        { name: "Aspiration", alignment: "Any", description: "You're making something of yourself, from nothing, without the advantages the people at the top were born with. The methods are unconventional. The outcome is going to be real.", chaosNote: "Building something from nothing is neutral. Chaos spikes when aspiration requires actively destroying the dreams or livelihoods of people who are also building from nothing." }
      ],
      bonds: [
        { text: "I fleeced the wrong person and must work to ensure that this individual never crosses paths with me or those I care about.", description: "The job looked standard and it wasn't. The person you conned had reach you didn't anticipate, and now that reach is pointed in your direction. You manage it daily.", chaosNote: "Managing a dangerous situation pragmatically is neutral. Chaos spikes when protecting yourself means putting others in the path of the danger." },
        { text: "I owe everything to my mentor — a horrible person who's probably rotting in jail somewhere.", description: "They taught you everything, and they were not good. The skills are real. The gratitude is complicated. If they showed up today, you're not sure which way it would go.", chaosNote: "Complicated loyalty is neutral. Chaos spikes when defending or covering for the mentor requires you to harm people they've hurt." },
        { text: "Somewhere out there, I have a child who doesn't know me. I'm making the world better for him or her.", description: "You're not sure this project would survive their actual opinion of you, but you run it anyway. The child is real. The rationale for your choices, built around them, is also real.", chaosNote: "Chaos cools when you genuinely sacrifice for this child's future. Chaos spikes when the child becomes justification for choices that have nothing to do with their wellbeing." },
        { text: "I come from a noble family, and one day I'll reclaim my lands and title from those who stole them from me.", description: "The original wrong was real. The years since have changed you in ways the title never accounted for. Whether you want the lands or just the reckoning is something you haven't fully worked out.", chaosNote: "Pursuing legitimate restoration is neutral. Chaos spikes when the campaign to reclaim requires harming people innocent of the original theft." },
        { text: "A powerful person killed someone I love. Some day soon, I'll have my revenge.", description: "The grief is underneath the calculation. You've built the plan to stay busy enough not to feel it. The plan is good. The grief is still there.", chaosNote: "Pursuing justice for a genuine wrong is neutral. Chaos spikes when revenge expands to include people adjacent to your target who had nothing to do with the killing." },
        { text: "I swindled and ruined a person who didn't deserve it. I seek to atone for my misdeeds but might never be able to forgive myself.", description: "You made a choice knowing it was wrong and did it anyway. The person paid for it. You've been paying for it since in a different currency, and the exchange rate isn't favorable.", chaosNote: "Genuine atonement is neutral. Chaos cools when you do something that actually restores what was taken. Chaos spikes when 'seeking atonement' is performance that never reaches the person you wronged." }
      ],
      flaws: [
        { text: "I can't resist a pretty face.", description: "You've built a career on reading people clearly and acting on the read, which makes it notable that this particular variable consistently overrides the read. You know it. You continue.", chaosNote: "Personal attraction is neutral. Chaos spikes when it makes you betray your companions' trust or endanger them because someone's appearance distracted you." },
        { text: "I'm always in debt. I spend my ill-gotten gains on decadent luxuries faster than I bring them in.", description: "The money is supposed to be the point. It's not actually the point — the point is the spending, the feeling of the lifestyle it buys. The debt is the price of that feeling.", chaosNote: "Spending freely is neutral. Chaos spikes when debt creates obligations that compromise companions or you borrow from the wrong people." },
        { text: "I'm convinced that no one could ever fool me the way I fool others.", description: "You understand deception from the inside out. Consequently you believe you're immune to it. This is exactly the belief that successful deceivers cultivate in their targets.", chaosNote: "Confidence in your ability to read people is neutral. Chaos spikes when certainty makes you dismiss genuine warnings from companions who see something you didn't." },
        { text: "I'm too greedy for my own good. I can't resist taking a risk if there's money involved.", description: "Risk and money together produce a response in you that bypasses your judgment. The calculation of 'is this smart' stops running when the number is large enough.", chaosNote: "Taking calculated risks with your own resources is neutral. Chaos spikes when the greedy risk-taking puts companions in danger they didn't agree to." },
        { text: "I can't resist swindling people who are more powerful than me.", description: "There's a specific satisfaction in taking something from someone who thought their power made them safe. The danger is proportional to that power, and you find the danger part of the appeal.", chaosNote: "Targeting the powerful is neutral. Chaos spikes when the fallout lands on people around you who had no role in the choice." },
        { text: "I hate to admit it and will hate myself for it, but I'll run and preserve my own hide if the going gets tough.", description: "Survival is a value. You have chosen to be honest about what that means — in the worst moment, the self-preservation instinct is going to win, and you know that and don't fully know what to do about it.", chaosNote: "Self-preservation is neutral in genuinely hopeless situations. Chaos spikes when you run while companions are still fighting a battle that had a real chance." }
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
        { name: "Beauty", alignment: "Good", description: "The best performance you've ever given left the audience with something they didn't have before — a feeling, a question, a memory that slightly changed how they understood being alive. That is the only outcome worth working toward.", chaosNote: "Creating work that genuinely moves people is neutral. Chaos spikes when you use real people's pain as material without their knowledge or consent." },
        { name: "Tradition", alignment: "Lawful", description: "You know songs nobody performs anymore and stories that died with the last generation that remembered them. The act of performing them keeps something alive that wants to disappear. That's the whole job.", chaosNote: "Preserving cultural memory is neutral. Chaos spikes when tradition becomes a reason to refuse new voices or protect forms that have become hollow." },
        { name: "Creativity", alignment: "Chaotic", description: "The audience already knows how they expect this to go. Your job is to do what they didn't expect and make them glad they didn't see it coming. Rules exist to be broken by people who first understand why they exist.", chaosNote: "Innovation in art is neutral. Chaos spikes when 'bold action' means doing something genuinely harmful to an audience or subject who didn't choose to be part of the experiment." },
        { name: "Greed", alignment: "Evil", description: "Fame pays. Sentiment doesn't. You've figured out what the audience wants and you give it to them at scale, which is a kind of craft even if it's not the kind you'd put on a plaque.", chaosNote: "Working for money is neutral. Chaos spikes when greed makes you perform content you know is harmful — propaganda, incitement, manipulation — because someone is paying." },
        { name: "People", alignment: "Neutral", description: "The theory of art is interesting. What matters is the look on a specific face in the audience — that person, in that moment, when the performance lands. That's the entire job, right there.", chaosNote: "Connection with your audience is neutral. Chaos spikes when the desire to please people makes you tell them what they want to hear rather than what they need to hear." },
        { name: "Honesty", alignment: "Any", description: "Real art comes from somewhere real. You've watched performers cover themselves in affect and precision and produce nothing — technically impressive, emotionally hollow. What you put on stage is actually you. Terrifying, and the only way it works.", chaosNote: "Authentic self-expression is neutral. Chaos spikes when 'honesty in art' justifies exposing others' truths without their consent." }
      ],
      bonds: [
        { text: "My instrument is my most treasured possession, and it reminds me of someone I love.", description: "It carries a specific weight that has nothing to do with its market value. Playing it is a conversation with someone who is gone or distant. You maintain it like it's alive.", chaosNote: "Cherishing a meaningful object is neutral. Chaos spikes when attachment makes you hesitate to use it in a moment where it could actually matter." },
        { text: "Someone stole my precious instrument, and someday I'll get it back.", description: "Not 'a replacement' — this specific one. The loss is disproportionate to its monetary value, and you know that, and you don't care. You want this one back.", chaosNote: "Chaos cools when the pursuit is proportionate and focused. Chaos spikes when recovering it requires harming people only peripherally connected to the theft." },
        { text: "I want to be famous, whatever it takes.", description: "The 'whatever it takes' is the part that should concern you. You haven't fully defined it, which means the line hasn't been drawn, which means you're running a plan without a constraint.", chaosNote: "Ambition in your craft is neutral. Chaos spikes when 'whatever it takes' starts including sacrificing people who trusted you as stepping stones." },
        { text: "I idolize a hero of the old tales and measure my deeds against that person's.", description: "The stories shaped how you understand what a life is supposed to look like, and you've spent years trying to make yours match. The hero may have been partly invented. The standard is still real.", chaosNote: "Having aspirational models is neutral. Chaos spikes when measuring yourself against a legend makes you dismiss the actual people in front of you who need help, not heroics." },
        { text: "I will do anything to prove myself superior to my hated rival.", description: "There's one other performer who occupies your thoughts more than they should. They're good — that's the problem. You've started making artistic decisions that are actually about them.", chaosNote: "Healthy competition is neutral. Chaos spikes when rivalry makes you sabotage, defame, or actively harm the rival or people associated with them." },
        { text: "I would do anything for the other members of my old troupe.", description: "You built something together on the road — specific people, specific trust, specific shared history. Whatever path separated you, that's the reference point for what loyalty means to you.", chaosNote: "Chaos cools when troupe loyalty demands real sacrifice. Chaos spikes when protecting the troupe means covering for something they've done wrong." }
      ],
      flaws: [
        { text: "I'll do anything to win fame and renown.", description: "You're running the same undefined constraint problem as 'whatever it takes.' 'Anything' is a wide word and you haven't sat with what it actually includes yet.", chaosNote: "Striving for recognition is neutral. Chaos spikes when the drive for renown requires betraying or sacrificing companions who've invested in you." },
        { text: "I'm a sucker for a pretty face.", description: "You're in the business of reading emotional cues, which makes it notable that this particular variable still bypasses your read. You've been here before and you keep returning.", chaosNote: "Attraction is neutral. Chaos spikes when you compromise the group's safety or interests because someone's appearance overrode your judgment." },
        { text: "A scandal prevents me from ever going home again. That kind of trouble seems to follow me around.", description: "The original incident is what it is. The pattern since is worth looking at — similar situations, similar results, similar surprise on your part each time.", chaosNote: "Navigating existing trouble is neutral. Chaos spikes when the tendency to create scandal starts harming people with no connection to the original situation." },
        { text: "I once satirized a noble who still wants my head. It was a mistake that I will likely repeat.", description: "The art was worth it at the time. The consequences have been ongoing. You know you'd do it again, which is either courage or a pattern, and you're not entirely sure which.", chaosNote: "Artistic provocation of power is neutral. Chaos spikes when the resulting danger falls on companions rather than you." },
        { text: "I have trouble keeping my true feelings hidden. My sharp tongue lands me in trouble.", description: "The filter that should exist between thought and speech is unreliable in your case. This is sometimes refreshing. More often it's costly, and the cost is not always only yours.", chaosNote: "Honest expression is neutral. Chaos spikes when your sharp tongue damages the standing or safety of companions who needed that relationship intact." },
        { text: "Despite my best efforts, I am unreliable to my friends.", description: "You mean well. The meaning well is sincere and continuous. The follow-through has a pattern of failure that persists despite intention, which is its own kind of useful information about yourself.", chaosNote: "This is a slow-burn chaos concern. Chaos spikes when unreliability fails someone in a moment that mattered, especially if they had no other option." }
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
        { name: "Community", alignment: "Lawful", description: "The guild works because people fulfill their obligations to it, and it fulfills its obligations to them. Break that loop and the whole structure collapses — and everyone on the edges loses what protects them. You're part of the loop.", chaosNote: "Contributing to shared systems is neutral. Chaos spikes when 'community obligations' suppress individuals who are legitimately challenging something wrong inside the system." },
        { name: "Generosity", alignment: "Good", description: "The skill took years to build. It doesn't diminish when you share it — it compounds. The best thing you can do with craft is use it in a way that outlasts your own hands.", chaosNote: "Sharing your skills is neutral. Chaos spikes when generosity becomes a performance — a public act that costs you nothing and generates reputation rather than actually helping." },
        { name: "Freedom", alignment: "Chaotic", description: "The guild sets the rates, regulates the standards, defines who gets to call themselves what. There is real value in that structure and also a ceiling built into it. You want to see what's above the ceiling.", chaosNote: "Operating outside institutional constraints is neutral when you're not harming others. Chaos spikes when freedom from guild rules means cutting corners that affect the safety or livelihoods of customers." },
        { name: "Greed", alignment: "Evil", description: "You're very good at what you do, and being very good commands a premium. The premium is the point. The work is how you get to it. Anything else people tell themselves about craft is a story they find comforting.", chaosNote: "Earning money for your work is neutral. Chaos spikes when greed makes you produce inferior work or exploit workers below you in the supply chain." },
        { name: "People", alignment: "Neutral", description: "The customer who needs this piece, the apprentice who needs to learn, the colleague who needs the job — your obligations run specific. Abstract principles can figure themselves out.", chaosNote: "Person-specific loyalty is neutral. Chaos spikes when it means ignoring harm being done to people outside that circle who have a legitimate claim on your conscience." },
        { name: "Aspiration", alignment: "Any", description: "The journeyman who becomes a master changes something. You're not there yet and you work every day to get there — not for recognition, but because the work at the master level is simply better, and better work matters.", chaosNote: "Pursuing mastery is neutral. Chaos spikes when ambition leads you to claim credit that belongs to others or use their work to advance yourself." }
      ],
      bonds: [
        { text: "The workshop where I learned my trade is the most important place in the world to me.", description: "Not just where you learned the technique — where you learned what it meant to make something. The smell, the light, the specific people. It built the baseline you've measured everything against since.", chaosNote: "Chaos cools when you protect or support the workshop. Chaos spikes when nostalgia makes you ignore real problems that have developed there since." },
        { text: "I created a great work for someone, and then found them unworthy to receive it. I'm still looking for someone worthy.", description: "The work deserves the right hands. You know this sounds insufferable and you can't help it — the work is real, the standard is real, and the unworthy recipient is also real.", chaosNote: "Caring about how your work is used is neutral. Chaos spikes when the search for 'worthy' becomes a reason to withhold help from people who genuinely need it." },
        { text: "I owe my guild a great debt for forging me into the person I am today.", description: "It wasn't just training — it was structure, community, accountability. What you are now is built on a foundation they laid, and you carry that forward consciously.", chaosNote: "Chaos cools when you honor the guild even at inconvenience to yourself. Chaos spikes when guild loyalty requires covering for harm the guild is doing." },
        { text: "I pursue wealth to secure someone's love.", description: "There's a specific person for whom money feels like the only argument you know how to make. Whether they'd actually want this is a question you've been avoiding for a while.", chaosNote: "Providing for someone you love is neutral. Chaos spikes when the pursuit causes you to compromise your ethics or harm others along the way." },
        { text: "One day I will return to my guild and prove that I am the greatest artisan of them all.", description: "There's a specific moment in the guild's history this comes from — a dismissal, a slight, a failure witnessed by people who mattered. You haven't let it go and you don't intend to.", chaosNote: "Pursuing excellence to prove yourself is neutral. Chaos spikes when 'proving yourself' requires actively diminishing colleagues on their own legitimate paths." },
        { text: "I will get revenge on the evil forces that destroyed my place of business and ruined my livelihood.", description: "Real damage, deliberate act, specific actors. You've calculated what it cost you, and you have a figure in mind for what you intend to cost them.", chaosNote: "Seeking redress for genuine harm is neutral. Chaos spikes when revenge expands beyond the responsible parties to their associates or the institution they represented." }
      ],
      flaws: [
        { text: "I'll do anything to get my hands on something rare or priceless.", description: "Acquisition of exceptional objects is a reflex that predates any rational calculation. Something beautiful and singular produces a response in you that bypasses the question of whether obtaining it is a good idea.", chaosNote: "Collecting rare objects is neutral. Chaos spikes when 'anything' starts including things that belong to others or puts companions at risk." },
        { text: "I'm quick to assume that someone is trying to cheat me.", description: "The guild world is competitive and the margins are real — people do cut corners and take advantage. You've built a defensive posture that runs continuously whether or not the current situation warrants it.", chaosNote: "Skepticism in transactions is neutral. Chaos spikes when the assumption poisons relationships that were actually good or causes you to act against someone genuinely trying to help." },
        { text: "No one must ever learn that I once stole money from guild coffers.", description: "You know why you did it, and the reason was real enough. You also know context doesn't eliminate what it was. The secret shapes every guild interaction since.", chaosNote: "Carrying guilt privately is neutral. Chaos spikes when protecting the secret requires you to lie to or harm people asking legitimate questions." },
        { text: "I'm never satisfied with what I have — I always want more.", description: "The finished piece is already the previous piece. The current achievement is already behind you. You don't know if this is ambition or an inability to be present, and you suspect both.", chaosNote: "Drive is neutral. Chaos spikes when insatiability makes you take from others — credit, opportunity, resources — rather than build more for yourself." },
        { text: "I would kill to acquire a noble title.", description: "Not literally — probably. But the desire for the legitimacy that title represents runs deep enough that you've surprised yourself with how far you'd actually go. The word 'kill' bothers you less than it should.", chaosNote: "Ambition toward status is neutral. Chaos spikes when the desire for legitimacy starts requiring you to harm or undermine people standing between you and it." },
        { text: "I'm horribly jealous of anyone who can outshine my handiwork. Everywhere I go, I'm surrounded by rivals.", description: "Good work from someone else produces something in you that isn't quite admiration. You're aware it's ugly. You manage it with variable success.", chaosNote: "Competitive feelings are neutral. Chaos spikes when jealousy makes you actively sabotage, undermine, or take from someone whose work genuinely deserved recognition." }
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
        { name: "Respect", alignment: "Good", description: "Every sailor knows what it looks like when the chain of command breaks. A crew is not an abstraction — it's fifteen people in a hull in a storm, and mutual respect is the thing that makes the difference between coming through it and going under.", chaosNote: "Treating crew members with genuine respect is neutral. Chaos spikes when 'respect' means enforcing hierarchy instead of building actual trust." },
        { name: "Fairness", alignment: "Lawful", description: "The share system exists because the alternative — one person deciding what everyone gets — produces the kind of resentment that leads to mutinies. You split it even, you take your share, you don't take someone else's. Full stop.", chaosNote: "Equal distribution is neutral. Chaos spikes when fairness becomes inflexible in situations where someone genuinely needs more than their share and can't ask for it." },
        { name: "Freedom", alignment: "Chaotic", description: "The horizon is always a new horizon. No harbor is permanent, no port is home, no relationship survives the next destination indefinitely. This is not loss — it's the entire point of being out here.", chaosNote: "Living without fixed obligations is neutral when others aren't counting on you. Chaos spikes when the need for freedom makes you abandon people who were depending on your presence." },
        { name: "Mastery", alignment: "Evil", description: "The sea is a domain, and every ship on it is a potential asset or obstacle. You've stopped pretending otherwise. The predator's perspective is clearer and it produces better outcomes, at least for you.", chaosNote: "Tactical thinking about competitors is neutral. Chaos spikes when the predator frame extends to people who aren't actually threats — passengers, civilians, unarmed merchants." },
        { name: "People", alignment: "Neutral", description: "The crew matters. The theory of the sea does not. You're not a philosopher of maritime freedom — you're a person with specific obligations to specific people on this ship, and those obligations run to your bones.", chaosNote: "Crew loyalty is neutral. Chaos spikes when it justifies harm to people outside it who didn't deserve to be on the losing end." },
        { name: "Aspiration", alignment: "Any", description: "The ship has a captain. You want to be the captain — not the first mate of someone else's ambition, but the person who sets the course, reads the weather, makes the call. That's the destination.", chaosNote: "Ambition toward command is neutral. Chaos spikes when acquiring the position requires sabotaging the person currently in it." }
      ],
      bonds: [
        { text: "I'm loyal to my captain first, everything else second.", description: "Loyalty to a specific person who earned it — not a title, not a ship. This captain showed you something that matters. The sequence is clear in your head.", chaosNote: "Personal loyalty is neutral. Chaos spikes when loyalty to the captain requires you to follow them into something genuinely wrong." },
        { text: "The ship is most important — crewmates and captains come and go.", description: "People cycle through, leadership changes, disagreements happen and resolve or don't. The vessel is the constant — the thing everyone needs to work for the mission to function.", chaosNote: "Institutional thinking is neutral. Chaos spikes when commitment to the ship's welfare becomes an excuse to be indifferent to the people aboard it." },
        { text: "I'll always remember my first ship.", description: "Where you learned to read the wind, learned what salt air smells like before a storm, learned who you were when the world was nothing but water in every direction. No subsequent ship has replaced it.", chaosNote: "Nostalgia for your formation is neutral. Chaos spikes when attachment to the past makes you make bad decisions about the present." },
        { text: "In a harbor town, I have a paramour whose eyes nearly stole me from the sea.", description: "You think about them when the voyage is long and hard. You've told yourself stories about going back that you're not sure you believe. The feeling is real even if the resolution isn't.", chaosNote: "Caring about someone you've left is neutral. Chaos spikes when it becomes emotional leverage used against you, or when it justifies decisions that harm companions." },
        { text: "I was cheated out of my fair share of the profits, and I want to get my due.", description: "You did the work and someone took what it earned. This is a ledger item, not a grudge — specific people, specific amount, specific resolution you're working toward.", chaosNote: "Seeking what you're owed is neutral. Chaos spikes when collection starts harming people who weren't involved in the original cheat." },
        { text: "Ruthless pirates murdered my captain and crewmates, plundered our ship, and left me to die. Vengeance will be mine.", description: "This is the thing underneath everything else. It doesn't go away during good moments — it waits. You've kept the names and whatever you could learn about where they went.", chaosNote: "Pursuing justice for this specific act is neutral. Chaos spikes when vengeance expands to all pirates indiscriminately, or harms people in the way who've done nothing wrong." }
      ],
      flaws: [
        { text: "I follow orders, even if I think they're wrong.", description: "The sea teaches you that the wrong moment to debate the captain is when everyone is on deck in a storm. The habit extends past the storms, which is where it starts causing problems.", chaosNote: "Discipline in urgent situations is neutral. Chaos spikes when following a wrong order causes active harm and you had time and opportunity to refuse." },
        { text: "I'll say anything to avoid having to do extra work.", description: "Work aboard ship is shared or it isn't done — you know this. You also know the art of looking busy, the exactly credible excuse, the well-timed disappearance. It's a second skill set.", chaosNote: "Efficiency with your own effort is neutral. Chaos spikes when your avoidance puts extra burden on companions who can't afford it." },
        { text: "Once someone questions my courage, I never back down no matter how dangerous the situation.", description: "The reputation is operational — it determines how people treat you aboard ship. The reflex to defend it runs faster than your judgment about whether the situation actually warrants it.", chaosNote: "Standing firm when challenged is neutral. Chaos spikes when pride makes you take a risk that gets companions hurt because you couldn't afford to be seen backing down." },
        { text: "Once I start drinking, it's hard for me to stop.", description: "Life at sea involves a relationship with spirits that starts practical (water spoils, spirits don't) and ends somewhere else. You know the line and you know you cross it.", chaosNote: "Drinking to relax is neutral. Chaos spikes when you're impaired in a moment where companions are depending on your full capacity." },
        { text: "I can't help but pocket loose coins and other trinkets I come across.", description: "The sea taught you to take what's available now, because what's available now won't be available later. This logic has transferred badly to shore-based situations.", chaosNote: "Acquiring unattended objects is neutral at low stakes. Chaos spikes when pocketing is from companions or from people who needed what you took." },
        { text: "My pride will probably lead to my destruction.", description: "You know this about yourself clearly enough to state it as fact. The knowing doesn't help — you've tried the knowing, and the pride runs underneath awareness and operates independently.", chaosNote: "Pride in your abilities is neutral. Chaos spikes when it makes you dismiss better plans from companions, refuse help you need, or charge into avoidable situations." }
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
        { name: "Respect", alignment: "Good", description: "You know what it feels like to be invisible — walked past, spoken over, given nothing. That experience didn't produce bitterness in you; it produced a very specific attention to how you treat people who are in the same position you were.", chaosNote: "Treating the marginalized with dignity is neutral. Chaos spikes when you demand respect for yourself in ways that mirror exactly what was done to you — using status to disappear other people." },
        { name: "Community", alignment: "Lawful", description: "In the gutters, no one makes it alone. The person who helped you find food, the one who warned you about the guard's route, the one who showed you which doorway was safe — you owe a chain of unnamed debts that can only be paid forward.", chaosNote: "Contributing to communal survival is neutral. Chaos spikes when community becomes a closed circle — when 'we take care of our own' means actively refusing people from outside it." },
        { name: "Change", alignment: "Chaotic", description: "The system that produced your childhood is not a system that works — not 'could be improved,' but doesn't work, for the people it produces the most of. You want it to change and you've stopped waiting for permission.", chaosNote: "Working for systemic change is neutral. Chaos spikes when frustration with the system makes you harm specific people who are merely part of it rather than directing it." },
        { name: "Retribution", alignment: "Evil", description: "The people above you had every advantage and they still looked down. You want to show them what looking down from nothing actually produces. The education is going to be specific and personal.", chaosNote: "Anger at inequality is neutral. Chaos spikes when retribution moves from the people who actually wronged you to anyone who represents wealth or power, regardless of their specific acts." },
        { name: "People", alignment: "Neutral", description: "Abstract loyalty is for people who've never had to choose between the abstraction and an actual person in front of them. You choose the person. Every time. It's the only loyalty that's ever actually kept anyone alive.", chaosNote: "Person-specific loyalty is neutral. Chaos spikes when it requires harming people from outside your circle who are also vulnerable and also deserve protection." },
        { name: "Aspiration", alignment: "Any", description: "You have seen what the bottom looks like from the inside. You are building something different, deliberately, with the specific knowledge that you have no safety net underneath the attempt.", chaosNote: "Building toward a better life is neutral. Chaos spikes when ambition requires pulling the ladder up behind you — succeeding by ensuring others from your origin can't follow." }
      ],
      bonds: [
        { text: "My town or city is my home, and I'll fight to defend it.", description: "Not the version of the city the wealthy see — the specific streets, the specific people, the routes and communities that kept you alive. That's the thing worth defending.", chaosNote: "Chaos cools when you defend it at real personal cost. Chaos spikes when defending 'the city' means harming the most vulnerable people within it." },
        { text: "I sponsor an orphanage to keep others from enduring what I was forced to endure.", description: "You know exactly what that institution means in practical terms — what it changes about a child's day. The money you put toward it is the most honest spending you do.", chaosNote: "Chaos cools when this commitment costs you something. Chaos spikes when the orphanage becomes reputation management rather than an actual improvement in children's lives." },
        { text: "I owe my survival to another urchin who taught me to live on the streets.", description: "They knew what they were doing when they shared what they knew with you. The debt is personal, specific, and you keep it current.", chaosNote: "Honoring this debt is neutral. Chaos spikes when fulfilling it puts companions at risk without their understanding or consent." },
        { text: "I owe a debt I can never repay to the person who took pity on me.", description: "They didn't have to help. They chose to. The help was real and the debt is real, and the fact that it can't be repaid in kind doesn't mean you stop trying.", chaosNote: "Recognizing what you owe is neutral. Chaos spikes when the debt to this person becomes a reason to compromise your ethics or your companions." },
        { text: "I escaped my life of poverty by robbing an important person, and I'm wanted for it.", description: "The escape was real and the wanted status is real. The math was: stay or go. You went. The consequences travel with you.", chaosNote: "Surviving by necessity is neutral. Chaos spikes when current comfort leads you to make the same choice again in situations that don't actually require it." },
        { text: "No one else should have to endure the hardships I've been through.", description: "The conviction is real. It's also broad enough to be dangerous — 'no one else should endure this' can justify a range of actions, some of them good, some of them drastic.", chaosNote: "Protecting others from suffering is neutral. Chaos spikes when the conviction makes you take drastic action against people who aren't actually causing the suffering you're fighting." }
      ],
      flaws: [
        { text: "If I'm outnumbered, I will run away from a fight.", description: "Survival arithmetic is not cowardice — it's how you made it to adulthood. The problem is that people running the old calculation don't always wait to check if their companions made it out first.", chaosNote: "Tactical retreat in losing situations is neutral. Chaos spikes when you run while companions are still fighting and the exit has real consequences for them." },
        { text: "Gold seems like a lot of money to me, and I'll do just about anything for more of it.", description: "You grew up in a context where a few coins was the difference between eating and not. That calibration doesn't update with your circumstances — the urgency feels the same regardless.", chaosNote: "Valuing money is neutral. Chaos spikes when 'just about anything' starts including things that harm people who are as vulnerable as you were." },
        { text: "I will never fully trust anyone other than myself.", description: "Trust cost you things you couldn't afford to lose. The lesson took. You're functional in groups — you can coordinate, follow a lead — but the full handover of trust doesn't happen.", chaosNote: "Protective skepticism is neutral. Chaos spikes when distrust makes you betray people genuinely trying to protect you, or prevents you from allowing help when you actually need it." },
        { text: "I'd rather kill someone in their sleep than fight fair.", description: "Fair fights are for people who can afford to lose. You've never been one of those people, and the ethics of the approach are secondary to the outcome in your experience.", chaosNote: "Strategic efficiency in genuine conflict is neutral. Chaos spikes when the preference for ambush extends to people who were willing to fight fair and didn't deserve the asymmetry." },
        { text: "It's not stealing if I need it more than someone else.", description: "This logic held in the gutters where it was built. It doesn't carry the same load in all contexts. You apply it anyway, usually without pausing to recalculate.", chaosNote: "Taking to survive genuine deprivation is neutral. Chaos spikes when the logic is applied to situations where your need is preference rather than necessity." },
        { text: "People who can't take care of themselves get what they deserve.", description: "You made it through circumstances most people would use as an excuse. The contempt for what you read as weakness comes from the same place the survival came from — and it's worth examining.", chaosNote: "Almost always a chaos spike when acted upon. The only exception is when it motivates you to build capacity in others rather than abandon them." }
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