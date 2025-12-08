import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { User, Sparkles, Crown, Zap, Star } from 'lucide-react';
import { mockData } from '../data/mockData';
import StatForge from './StatForge';
import { isDevMode, generateDevCharacter } from '../utils/devMode';
import { applyRaceToCharacter, calculateBaseStats, getModifierString, hasSubraces, getSubraces } from '../utils/raceHelpers';
import { getRaceData } from '../data/raceData';
import { CLASS_SKILLS, SKILL_ABILITIES } from '../data/classSkills';
import { STARTING_EQUIPMENT } from '../data/startingEquipment';
import { CLASS_PROFICIENCIES } from '../data/classProficiencies';
import { getAvailableCantrips, CANTRIPS } from '../data/spellData';
import CantripSelection from './CantripSelection';
import LoadingModal from './LoadingModal';

const CharacterCreation = ({ onCharacterCreated }) => {
  const [character, setCharacter] = useState({
    // Basic Info
    name: '',
    race: '',
    subrace: '', // Subrace variant (e.g., "High Elf", "Mountain Dwarf")
    class: '',
    background: '',
    backgroundVariantKey: '', // Key for the selected variant (e.g., "Base", "Hermit", "Spy")
    level: 1,
    size: 'Medium', // Default size
    speed: 30, // Default speed
    
    // Age
    age: null,
    age_category: '', // Young, Adult, Veteran, Elder
    
    // Stats
    stats: {
      strength: 10,
      dexterity: 10,
      constitution: 10,
      intelligence: 10,
      wisdom: 10,
      charisma: 10
    },
    stat_flavors: {}, // How each stat manifests in daily life
    
    // HP & Combat
    hitPoints: 10,
    experience: 0,
    spellSlots: [],
    proficiencies: [],
    cantrips: [], // Known cantrips
    spells: [], // Known spells
    
    // Racial Mechanics
    racial_asi: [], // Racial ability score increases
    racial_traits: [], // Racial traits with descriptions
    racial_languages_base: [], // Automatic racial languages
    racial_language_choices: 0, // Number of language choices from race
    
    // Background & Culture (homeland removed - AI will pick from world)
    languages: [],
    education_level: '',
    
    // Personality Architecture
    traits: [], // Initialize as empty array
    ideals: [{ principle: '', inspiration: '' }],
    bonds: [{ person_or_cause: '', shared_event: '' }],
    flaws_detailed: [{ habit: '', interference: '', intensity: 0.5 }],
    
    // Moral Core
    alignment_vector: { lawful_chaotic: '', good_evil: '' },
    moral_tension: '',
    
    // Aspiration
    aspiration: {
      goal: '',
      motivation: '',
      sacrifice_threshold: 5,
      milestones: []
    },
    
    // Relationships
    vip_hooks: [
      { name: '', relation: '', shared_event: '', personal_aspiration: '' },
      { name: '', relation: '', shared_event: '', personal_aspiration: '' }
    ] // Initialize with 2 empty VIP hooks
  });

  const [creationStep, setCreationStep] = useState(0);
  const [statsAssigned, setStatsAssigned] = useState(false);
  const [showDevMode, setShowDevMode] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  // Check for dev mode
  useEffect(() => {
    setShowDevMode(isDevMode());
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'A') {
        e.preventDefault();
        if (showDevMode) {
          skipToAdventure();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showDevMode]);

  const getStatModifier = (stat) => {
    return Math.floor((stat - 10) / 2);
  };

  const getStatModifierString = (stat) => {
    const mod = getStatModifier(stat);
    return mod >= 0 ? `+${mod}` : `${mod}`;
  };

  // Age → Life Stage Auto-Mapping
  const determineLifeStage = (age) => {
    const numAge = parseInt(age);
    if (isNaN(numAge) || numAge < 10) return 'Young';
    
    if (numAge >= 10 && numAge <= 25) return 'Young';
    if (numAge >= 26 && numAge <= 45) return 'Adult';
    if (numAge >= 46 && numAge <= 65) return 'Veteran';
    if (numAge >= 66) return 'Elder';
    
    return 'Young'; // Default fallback
  };

  // Auto-update Life Stage when Age changes
  useEffect(() => {
    if (character.age) {
      const calculatedStage = determineLifeStage(character.age);
      if (character.age_category !== calculatedStage) {
        setCharacter(prev => ({ ...prev, age_category: calculatedStage }));
      }
    }
  }, [character.age]);

  // Auto-calculate Languages based on Race, Background, and Class
  useEffect(() => {
    const calculateLanguages = () => {
      const languages = {
        automatic: [],
        choicesNeeded: 0,
        chosen: character.languages || []
      };

      // 1. Race Languages (Primary Source) - Use racial_languages_base if available
      if (character.racial_languages_base) {
        languages.automatic.push(...character.racial_languages_base);
      } else if (character.race) {
        const selectedRace = mockData.races.find(r => r.name === character.race);
        if (selectedRace?.languages) {
          languages.automatic.push(...selectedRace.languages.automatic);
        }
      }

      // Add racial language choices
      if (character.racial_language_choices) {
        languages.choicesNeeded += character.racial_language_choices;
      } else if (character.race) {
        const selectedRace = mockData.races.find(r => r.name === character.race);
        if (selectedRace?.languages) {
          languages.choicesNeeded += selectedRace.languages.choices;
        }
      }

      // 2. Background Languages (Secondary Source)
      if (character.background) {
        const selectedBg = mockData.backgrounds.find(b => b.name === character.background);
        if (selectedBg?.variants && character.backgroundVariantKey) {
          const variant = selectedBg.variants[character.backgroundVariantKey];
          if (variant?.languages) {
            languages.choicesNeeded += variant.languages;
          }
        } else if (selectedBg?.languages) {
          languages.choicesNeeded += selectedBg.languages;
        }
      }

      // 3. Class Languages (Rare - Monk, Druid)
      if (character.class) {
        const selectedClass = mockData.classes.find(c => c.name === character.class);
        if (selectedClass?.languages) {
          languages.automatic.push(...selectedClass.languages.automatic);
          languages.choicesNeeded += selectedClass.languages.choices;
        }
      }

      return languages;
    };

    const calculatedLanguages = calculateLanguages();
    
    // Store calculated languages in character state for UI display
    setCharacter(prev => ({
      ...prev,
      _languageCalculation: calculatedLanguages // Internal calculation for UI
    }));
  }, [character.race, character.class, character.background, character.backgroundVariantKey, character.racial_languages_base, character.racial_language_choices]);

  // Auto-generate VIP relationships using AI
  const [generatingRelationships, setGeneratingRelationships] = useState(false);
  
  const generateRelationships = async () => {
    if (generatingRelationships) return;
    
    setGeneratingRelationships(true);
    try {
      // Generate simple placeholder relationships without complex AI calls
      // to avoid React rendering errors
      const generatedHooks = [
        {
          name: `${character.background || 'Past'} Mentor`,
          relation: 'Mentor',
          shared_event: `Taught ${character.name || 'the hero'} essential skills during their early days.`,
          personal_aspiration: 'Wants to see their student succeed and surpass them.'
        },
        {
          name: `Childhood Friend`,
          relation: 'Ally',
          shared_event: `Grew up together, sharing dreams of adventure.`,
          personal_aspiration: 'Hopes to reunite and share their own stories.'
        }
      ];
      
      setCharacter(prev => ({
        ...prev,
        vip_hooks: generatedHooks
      }));
    } catch (error) {
      console.error('Failed to generate relationships:', error);
    } finally {
      setGeneratingRelationships(false);
    }
  };

  // Auto-generate relationships when reaching Review step
  useEffect(() => {
    const reviewStepIndex = steps.indexOf('Review');
    if (creationStep === reviewStepIndex && character.vip_hooks.every(h => !h.name)) {
      // Use setTimeout to avoid blocking React render cycle
      setTimeout(() => {
        generateRelationships();
      }, 100);
    }
  }, [creationStep]);


  const updateCharacterClass = (selectedClass) => {
    const classData = mockData.classes.find(c => c.name === selectedClass);
    let hitPoints = 10;
    let spellSlots = [];
    
    if (classData) {
      hitPoints = classData.hitDie + getStatModifier(character.stats.constitution);
      if (classData.spellcaster) {
        spellSlots = classData.spellSlots[1] || [];
      }
    }

    setCharacter(prev => ({
      ...prev,
      class: selectedClass,
      hitPoints,
      spellSlots,
      proficiencies: classData?.proficiencies || []
    }));
  };

  const updateCharacterRace = (selectedRace) => {
    // Apply racial mechanics (ASI, size, speed, languages, traits)
    // Reset subrace when changing race
    setCharacter(prev => applyRaceToCharacter(selectedRace, { ...prev, subrace: '' }));
  };

  const updateCharacterSubrace = (selectedSubrace) => {
    // Apply subrace bonuses on top of base race
    setCharacter(prev => applyRaceToCharacter(prev.race, prev, selectedSubrace));
  };

  const onStatsComplete = (stats) => {
    setStatsAssigned(true);
    setCharacter(prev => ({
      ...prev,
      stats: stats
    }));
    
    // Recalculate hit points based on new constitution
    if (character.class) {
      const classData = mockData.classes.find(c => c.name === character.class);
      if (classData) {
        const newHitPoints = classData.hitDie + getStatModifier(stats.constitution);
        setCharacter(prev => ({
          ...prev,
          hitPoints: newHitPoints
        }));
      }
    }
  };

  const skipToAdventure = () => {
    console.log('⚡ Dev mode: Skipping to Adventure');
    const devChar = generateDevCharacter();
    
    // Clear any existing session data
    localStorage.removeItem('dm-intro-played');
    localStorage.removeItem('dm-session-id');
    
    // Create fresh session
    const newSessionId = `sess-${Date.now()}`;
    localStorage.setItem('dm-session-id', newSessionId);
    
    if (window.showToast) {
      window.showToast('⚡ Dev mode: Auto-created character!', 'info');
    }
    
    // Show loading modal
    setIsLoading(true);
    setLoadingProgress(0);
    
    // Pass character with progress callback
    onCharacterCreated(devChar, (progress) => {
      setLoadingProgress(progress);
      
      // Hide loading modal when complete
      if (progress >= 100) {
        setTimeout(() => {
          setIsLoading(false);
        }, 500);
      }
    });
  };

  const handleCreateCharacter = () => {
    if (!character.name || !character.race || !character.class || !character.background || !statsAssigned) {
      alert('Please complete all character creation steps!');
      return;
    }
    
    // Add starting equipment, gold, proficiencies, and speed based on class/race
    const startingGear = STARTING_EQUIPMENT[character.class];
    const classProficiencies = CLASS_PROFICIENCIES[character.class];
    
    // Calculate speed based on race
    const raceSpeedMap = {
      "Human": 30,
      "Elf": 30,
      "Dwarf": 25,
      "Halfling": 25,
      "Gnome": 25,
      "Half-Orc": 30,
      "Half-Elf": 30,
      "Tiefling": 30,
      "Dragonborn": 30
    };
    const baseSpeed = raceSpeedMap[character.race] || 30;
    
    // Serialize cantrips to only include essential data (name and description)
    const serializedCantrips = (character.cantrips || []).map(cantrip => ({
      name: cantrip.name,
      description: cantrip.description,
      damage: cantrip.damage,
      range: cantrip.range,
      castingTime: cantrip.castingTime
    }));

    const finalCharacter = {
      ...character,
      cantrips: serializedCantrips, // Use serialized cantrips
      gold: startingGear?.gold || 0,
      inventory: startingGear?.items || [],
      tool_proficiencies: classProficiencies?.tools || [],
      weapon_proficiencies: classProficiencies?.weapons || [],
      armor_proficiencies: classProficiencies?.armor || [],
      saving_throws: classProficiencies?.savingThrows || [],
      speed: baseSpeed
    };
    
    console.log('✅ Added starting equipment and proficiencies:', {
      class: character.class,
      gold: finalCharacter.gold,
      items: finalCharacter.inventory,
      toolProf: finalCharacter.tool_proficiencies,
      weaponProf: finalCharacter.weapon_proficiencies,
      armorProf: finalCharacter.armor_proficiencies
    });
    
    // Show loading modal
    setIsLoading(true);
    setLoadingProgress(0);
    
    // Pass character with progress callback
    onCharacterCreated(finalCharacter, (progress) => {
      setLoadingProgress(progress);
      
      // Hide loading modal when complete
      if (progress >= 100) {
        setTimeout(() => {
          setIsLoading(false);
        }, 500);
      }
    });
  };

  const steps = [
    'Identity',        // Name + Race + Class + Age
    'Stats',           // StatForge + flavor text
    'Background',      // Background + culture
    'Personality',     // Traits/Ideals/Bonds/Flaws
    'Alignment',       // Moral core
    'Aspiration',      // Endgame goal
    'Review'           // Final review (Relationships auto-generated by AI)
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6 relative">
      {/* Dev Mode: Skip to Adventure */}
      {showDevMode && (
        <div className="absolute top-0 right-0 z-50">
          <Button
            onClick={skipToAdventure}
            size="sm"
            className="bg-purple-700/90 hover:bg-purple-600 text-white font-semibold shadow-lg border-2 border-purple-400/50"
            title="Ctrl+Shift+A"
          >
            <Zap className="h-4 w-4 mr-2" />
            Skip to Adventure (Dev)
          </Button>
        </div>
      )}
      
      <Card className="bg-black/90 border-amber-600/30 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-3xl text-center text-amber-400 font-bold flex items-center justify-center gap-2">
            <Crown className="h-8 w-8" />
            Character Creation
            <Crown className="h-8 w-8" />
          </CardTitle>
          <div className="flex justify-center space-x-2 mt-4">
            {steps.map((step, idx) => (
              <Badge 
                key={idx}
                variant={idx === creationStep ? "default" : "outline"}
                className={idx === creationStep ? 
                  "bg-amber-600 text-black" : 
                  "border-amber-600/50 text-amber-300"
                }
              >
                {step}
              </Badge>
            ))}
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          
          {/* Step 0: Identity Core */}
          {creationStep === 0 && (
            <div className="space-y-6 max-w-2xl mx-auto">
              <div className="text-center mb-6">
                <User className="h-16 w-16 text-amber-400 mx-auto mb-2" />
                <h3 className="text-2xl text-amber-400">Who Are You?</h3>
                <p className="text-gray-400">Define your character's fundamental identity</p>
              </div>
              
              {/* Name */}
              <div>
                <Label htmlFor="name" className="text-amber-400 text-lg">Character Name</Label>
                <Input
                  id="name"
                  value={character.name}
                  onChange={(e) => setCharacter(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter your character's name..."
                  className="bg-gray-800/50 border-amber-600/30 text-white placeholder-gray-400 text-center text-lg font-semibold"
                />
              </div>

              <Separator className="bg-amber-600/20" />

              {/* Race & Class */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label className="text-amber-400 text-lg">Race</Label>
                  <Select value={character.race} onValueChange={updateCharacterRace}>
                    <SelectTrigger className="bg-gray-800/50 border-amber-600/30 text-white">
                      <SelectValue placeholder="Choose race..." />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-amber-600/30">
                      {mockData.races.map(race => (
                        <SelectItem key={race.name} value={race.name} className="text-white hover:bg-amber-600/20">
                          {race.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  {/* Subrace Selection (if available) */}
                  {character.race && hasSubraces(character.race) && (
                    <div className="mt-3">
                      <Label className="text-amber-400 text-sm">Subrace</Label>
                      <Select value={character.subrace} onValueChange={updateCharacterSubrace}>
                        <SelectTrigger className="bg-gray-800/50 border-amber-600/30 text-white">
                          <SelectValue placeholder="Choose subrace..." />
                        </SelectTrigger>
                        <SelectContent className="bg-gray-800 border-amber-600/30">
                          {getSubraces(character.race).map(subrace => (
                            <SelectItem key={subrace} value={subrace} className="text-white hover:bg-amber-600/20">
                              {subrace}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  {/* Racial Traits Preview */}
                  {character.race && (() => {
                    const raceData = getRaceData(character.race);
                    if (!raceData) return null;
                    
                    // Get all traits (base + subrace)
                    let allTraits = [...raceData.traits];
                    let speed = raceData.speed;
                    let additionalASI = [];
                    
                    if (character.subrace && raceData.subraces && raceData.subraces[character.subrace]) {
                      const subraceData = raceData.subraces[character.subrace];
                      allTraits = [...allTraits, ...subraceData.traits];
                      if (subraceData.speed) speed = subraceData.speed;
                      additionalASI = subraceData.asi;
                    }
                    
                    return (
                      <div className="mt-3 p-3 bg-blue-900/20 rounded border border-blue-600/30">
                        <p className="text-blue-400 text-xs font-semibold mb-2">
                          Racial Traits:
                          {character.subrace && <span className="text-amber-400 ml-1">({character.subrace})</span>}
                        </p>
                        
                        {/* ASI Display */}
                        <div className="mb-2 text-xs text-green-400">
                          <span className="font-semibold">Ability Bonuses: </span>
                          {raceData.asi.map((bonus, idx) => (
                            <span key={idx}>
                              {bonus.ability === "ALL" ? "All +1" : `${bonus.ability} +${bonus.value}`}
                              {idx < raceData.asi.length - 1 && ", "}
                            </span>
                          ))}
                          {additionalASI.length > 0 && (
                            <span>
                              {" + "}
                              {additionalASI.map((bonus, idx) => (
                                <span key={idx}>
                                  {bonus.ability === "CHOICE" ? "Choice +1" : `${bonus.ability} +${bonus.value}`}
                                  {idx < additionalASI.length - 1 && ", "}
                                </span>
                              ))}
                            </span>
                          )}
                        </div>
                        
                        <div className="space-y-1">
                          {allTraits.map((trait, idx) => (
                            <div key={idx} className="text-gray-300 text-xs">
                              <span className="font-semibold text-blue-300">{trait.name}:</span> {trait.summary}
                            </div>
                          ))}
                        </div>
                        <p className="text-gray-400 text-xs mt-2">
                          Size: {raceData.size} | Speed: {speed} ft.
                        </p>
                      </div>
                    );
                  })()}
                </div>

                <div>
                  <Label className="text-amber-400 text-lg">Class</Label>
                  <Select value={character.class} onValueChange={(val) => setCharacter(prev => ({...prev, class: val}))}>
                    <SelectTrigger className="bg-gray-800/50 border-amber-600/30 text-white">
                      <SelectValue placeholder="Choose class..." />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-amber-600/30">
                      {mockData.classes.map(cls => (
                        <SelectItem key={cls.name} value={cls.name} className="text-white hover:bg-amber-600/20">
                          {cls.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Separator className="bg-amber-600/20" />

              {/* Age */}
              <div className="space-y-4">
                <Label className="text-amber-400 text-lg">Age & Experience</Label>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-300 text-sm">Age (years)</Label>
                    <Input
                      type="number"
                      value={character.age || ''}
                      onChange={(e) => setCharacter(prev => ({ ...prev, age: parseInt(e.target.value) || null }))}
                      placeholder="e.g., 25"
                      className="bg-gray-800/50 border-amber-600/30 text-white"
                    />
                  </div>
                  <div>
                    <Label className="text-gray-300 text-sm">Life Stage <span className="text-purple-400 text-xs">(Auto-calculated)</span></Label>
                    <div className="bg-gray-800/50 border border-amber-600/30 rounded-md px-3 py-2 text-white flex items-center justify-between">
                      <span className={character.age_category ? 'text-white' : 'text-gray-500'}>
                        {character.age_category || 'Enter age above'}
                      </span>
                      <Badge variant="outline" className={
                        character.age_category === 'Young' ? 'border-green-400/50 text-green-300' :
                        character.age_category === 'Adult' ? 'border-blue-400/50 text-blue-300' :
                        character.age_category === 'Veteran' ? 'border-purple-400/50 text-purple-300' :
                        character.age_category === 'Elder' ? 'border-amber-400/50 text-amber-300' :
                        'border-gray-400/50 text-gray-400'
                      }>
                        {character.age_category && (() => {
                          if (character.age_category === 'Young') return '10-25';
                          if (character.age_category === 'Adult') return '26-45';
                          if (character.age_category === 'Veteran') return '46-65';
                          if (character.age_category === 'Elder') return '66+';
                          return '';
                        })()}
                      </Badge>
                    </div>
                  </div>
                </div>
                <p className="text-gray-400 text-xs italic">
                  Life stage auto-calculates from age and affects how the world perceives you
                </p>
              </div>
            </div>
          )}

          {/* Step 1: Stats */}
          {creationStep === 1 && (
            <StatForge 
              onComplete={onStatsComplete}
              character={character}
              setCharacter={setCharacter}
            />
          )}

          {/* Step 2: Skill Proficiencies */}
          {creationStep === 2 && character.class && (() => {
            const classSkillData = CLASS_SKILLS[character.class];
            if (!classSkillData) return <div className="text-white">Class not found</div>;

            const selectedCount = character.proficiencies?.length || 0;
            const requiredCount = classSkillData.count;

            const toggleSkill = (skill) => {
              const current = character.proficiencies || [];
              if (current.includes(skill)) {
                setCharacter(prev => ({
                  ...prev,
                  proficiencies: current.filter(s => s !== skill)
                }));
              } else {
                if (current.length < requiredCount) {
                  setCharacter(prev => ({
                    ...prev,
                    proficiencies: [...current, skill]
                  }));
                }
              }
            };

            return (
              <div className="space-y-6 max-w-3xl mx-auto">
                <div className="text-center mb-6">
                  <h3 className="text-2xl text-amber-400">Skill Proficiencies</h3>
                  <p className="text-gray-400">Choose {requiredCount} skills your {character.class} is proficient in</p>
                  <p className="text-amber-500 mt-2">Selected: {selectedCount}/{requiredCount}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {classSkillData.skills.map(skill => {
                    const isSelected = character.proficiencies?.includes(skill);
                    const ability = SKILL_ABILITIES[skill];
                    const abilityScore = character.stats?.[ability.toLowerCase()] || 10;
                    const abilityMod = Math.floor((abilityScore - 10) / 2);
                    const profBonus = 2; // Level 1 proficiency bonus
                    const totalMod = isSelected ? abilityMod + profBonus : abilityMod;

                    return (
                      <button
                        key={skill}
                        onClick={() => toggleSkill(skill)}
                        disabled={!isSelected && selectedCount >= requiredCount}
                        className={`
                          p-4 rounded-lg border-2 text-left transition-all
                          ${isSelected 
                            ? 'border-amber-500 bg-amber-500/20' 
                            : 'border-gray-600 bg-gray-800/30 hover:border-amber-600/50'
                          }
                          ${!isSelected && selectedCount >= requiredCount ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                        `}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="text-white font-semibold">{skill}</div>
                            <div className="text-gray-400 text-sm">{ability}</div>
                          </div>
                          <div className="text-right">
                            <div className={`text-lg font-bold ${isSelected ? 'text-amber-400' : 'text-gray-500'}`}>
                              {totalMod >= 0 ? '+' : ''}{totalMod}
                            </div>
                            {isSelected && (
                              <div className="text-xs text-amber-500">
                                ({abilityMod >= 0 ? '+' : ''}{abilityMod} + {profBonus})
                              </div>
                            )}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })()}

          {/* Cantrip Selection (if applicable) - Insert between steps */}
          {creationStep === 2 && character.race && character.subrace && (() => {
            const availableCantrips = getAvailableCantrips(character.race, character.subrace, character.class);
            
            if (!availableCantrips) return null;
            
            if (availableCantrips.type === 'choice') {
              return (
                <div className="mt-8 max-w-3xl mx-auto">
                  <Separator className="bg-purple-600/30 mb-6" />
                  <CantripSelection
                    cantrips={availableCantrips.list}
                    count={availableCantrips.count}
                    selectedCantrips={character.cantrips || []}
                    onSelect={(cantrips) => setCharacter(prev => ({ ...prev, cantrips }))}
                    source={availableCantrips.source}
                  />
                </div>
              );
            }
            
            // Automatic cantrips - just show info
            if (availableCantrips.type === 'automatic') {
              return (
                <div className="mt-8 max-w-3xl mx-auto">
                  <Separator className="bg-purple-600/30 mb-6" />
                  <div className="p-4 bg-purple-900/20 rounded border border-purple-600/50">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="h-5 w-5 text-purple-400" />
                      <h4 className="text-purple-400 font-semibold">Racial Cantrip</h4>
                    </div>
                    <p className="text-sm text-gray-400 mb-3">
                      From: <span className="text-purple-300">{availableCantrips.source}</span>
                    </p>
                    {availableCantrips.list.map(cantrip => (
                      <div key={cantrip.name} className="p-3 bg-gray-800/50 rounded">
                        <h5 className="font-semibold text-white mb-1">{cantrip.name}</h5>
                        <p className="text-sm text-gray-300">{cantrip.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              );
            }
            
            return null;
          })()}

          {/* Step 3: Background & Culture */}
          {creationStep === 3 && (
            <div className="space-y-6 max-w-2xl mx-auto">
              <div className="text-center mb-6">
                <h3 className="text-2xl text-amber-400">Your Origins</h3>
                <p className="text-gray-400">Where did your story begin?</p>
              </div>
              
              {/* Background */}
              <div>
                <Label className="text-amber-400 text-lg">Background</Label>
                <Select 
                  value={character.background} 
                  onValueChange={(value) => {
                    const bg = mockData.backgrounds.find(b => b.name === value);
                    // Auto-select Base variant or first variant when background changes
                    const defaultVariant = bg?.variants ? 'Base' : null;
                    setCharacter(prev => ({ 
                      ...prev, 
                      background: value,
                      backgroundVariantKey: defaultVariant 
                    }));
                  }}
                >
                  <SelectTrigger className="bg-gray-800/50 border-amber-600/30 text-white">
                    <SelectValue placeholder="Choose your background..." />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-amber-600/30">
                    {mockData.backgrounds.map(bg => (
                      <SelectItem key={bg.name} value={bg.name} className="text-white hover:bg-amber-600/20">
                        {bg.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                {character.background && (() => {
                  const selectedBg = mockData.backgrounds.find(b => b.name === character.background);
                  if (!selectedBg) return null;

                  // Check if background has variants
                  const hasVariants = selectedBg.variants && Object.keys(selectedBg.variants).length > 1;
                  
                  // Get the selected variant data (or use base background data for non-variant backgrounds)
                  let variantData;
                  if (selectedBg.variants) {
                    const variantKey = character.backgroundVariantKey || 'Base';
                    variantData = selectedBg.variants[variantKey];
                  } else {
                    // For backgrounds without variants (Charlatan, Urchin)
                    variantData = {
                      label: selectedBg.name,
                      skills: selectedBg.skills,
                      toolProficiencies: selectedBg.toolProficiencies,
                      languages: selectedBg.languages,
                      equipment: selectedBg.equipment,
                      feature: selectedBg.feature
                    };
                  }

                  if (!variantData) return null;

                  return (
                    <div className="mt-3 space-y-3">
                      {/* Variant Selector - only show if multiple variants exist */}
                      {hasVariants && (
                        <div>
                          <Label className="text-purple-400 text-sm mb-1">Variant</Label>
                          <Select 
                            value={character.backgroundVariantKey || 'Base'} 
                            onValueChange={(value) => setCharacter(prev => ({ ...prev, backgroundVariantKey: value }))}
                          >
                            <SelectTrigger className="bg-gray-800/50 border-purple-600/30 text-white">
                              <SelectValue placeholder="Choose variant..." />
                            </SelectTrigger>
                            <SelectContent className="bg-gray-800 border-purple-600/30">
                              {Object.keys(selectedBg.variants).map(variantKey => (
                                <SelectItem key={variantKey} value={variantKey} className="text-white hover:bg-purple-600/20">
                                  {selectedBg.variants[variantKey].label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}

                      {/* Theme & Description */}
                      <div className="p-3 bg-gray-800/30 rounded border border-amber-600/20">
                        <p className="text-amber-300 text-sm font-semibold mb-1">{selectedBg.theme}</p>
                        <p className="text-gray-300 text-sm">{selectedBg.description}</p>
                        {variantData.label !== selectedBg.name && (
                          <p className="text-purple-300 text-xs mt-2 italic">Variant: {variantData.label}</p>
                        )}
                      </div>
                      
                      {/* Skills & Proficiencies */}
                      <div className="grid grid-cols-2 gap-3">
                        <div className="p-3 bg-gray-800/20 rounded">
                          <p className="text-purple-400 text-xs font-semibold mb-1">Skill Proficiencies</p>
                          <p className="text-gray-300 text-sm">{variantData.skills.join(', ')}</p>
                        </div>
                        <div className="p-3 bg-gray-800/20 rounded">
                          <p className="text-blue-400 text-xs font-semibold mb-1">Tools & Languages</p>
                          <p className="text-gray-300 text-sm">
                            {variantData.toolProficiencies && variantData.toolProficiencies.length > 0 
                              ? variantData.toolProficiencies.join(', ') 
                              : ''}
                            {variantData.toolProficiencies && variantData.toolProficiencies.length > 0 && variantData.languages > 0 && ', '}
                            {variantData.languages > 0 
                              ? `${variantData.languages} language${variantData.languages > 1 ? 's' : ''}` 
                              : ''}
                            {(!variantData.toolProficiencies || variantData.toolProficiencies.length === 0) && variantData.languages === 0 && 'None'}
                          </p>
                        </div>
                      </div>
                      
                      {/* Feature */}
                      <div className="p-3 bg-amber-900/20 rounded border border-amber-600/30">
                        <p className="text-amber-400 text-sm font-semibold mb-1">
                          Feature: {variantData.feature.name}
                        </p>
                        <p className="text-gray-300 text-xs">{variantData.feature.description}</p>
                      </div>
                      
                      {/* Equipment */}
                      <div className="p-2 bg-gray-800/20 rounded">
                        <p className="text-green-400 text-xs font-semibold mb-1">Starting Equipment</p>
                        <p className="text-gray-400 text-xs">{variantData.equipment}</p>
                      </div>
                    </div>
                  );
                })()}
              </div>

              <Separator className="bg-amber-600/20" />

              {/* Languages */}
              {character._languageCalculation && (
                <div className="space-y-3">
                  <div>
                    <Label className="text-blue-400 text-lg mb-2 flex items-center gap-2">
                      Languages
                      <span className="text-xs text-gray-400 font-normal">(Auto-calculated from Race, Background & Class)</span>
                    </Label>
                    
                    {/* Automatic Languages */}
                    {character._languageCalculation.automatic.length > 0 && (
                      <div className="p-3 bg-blue-900/20 rounded border border-blue-600/30 mb-3">
                        <p className="text-blue-400 text-xs font-semibold mb-2">Automatic Languages:</p>
                        <div className="flex flex-wrap gap-2">
                          {character._languageCalculation.automatic.map((lang, idx) => (
                            <Badge key={idx} variant="outline" className="border-blue-400/50 text-blue-300">
                              {lang}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Language Choices */}
                    {character._languageCalculation.choicesNeeded > 0 && (
                      <div className="p-3 bg-purple-900/20 rounded border border-purple-600/30">
                        <p className="text-purple-400 text-xs font-semibold mb-2">
                          Choose {character._languageCalculation.choicesNeeded} Additional Language{character._languageCalculation.choicesNeeded > 1 ? 's' : ''}:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {mockData.availableLanguages
                            .filter(lang => !character._languageCalculation.automatic.includes(lang))
                            .map((lang) => {
                              const isSelected = character.languages.includes(lang);
                              const canSelect = character.languages.length < character._languageCalculation.choicesNeeded;
                              
                              return (
                                <Badge
                                  key={lang}
                                  variant="outline"
                                  className={`cursor-pointer transition-colors ${
                                    isSelected 
                                      ? 'bg-purple-600/30 border-purple-400 text-purple-200' 
                                      : canSelect || isSelected
                                      ? 'border-purple-400/30 text-gray-300 hover:bg-purple-600/10'
                                      : 'border-gray-600/30 text-gray-600 cursor-not-allowed'
                                  }`}
                                  onClick={() => {
                                    if (isSelected) {
                                      // Remove language
                                      setCharacter(prev => ({
                                        ...prev,
                                        languages: prev.languages.filter(l => l !== lang)
                                      }));
                                    } else if (canSelect) {
                                      // Add language
                                      setCharacter(prev => ({
                                        ...prev,
                                        languages: [...prev.languages, lang]
                                      }));
                                    }
                                  }}
                                >
                                  {lang}
                                </Badge>
                              );
                            })}
                        </div>
                        <p className="text-xs text-gray-400 mt-2">
                          Selected: {character.languages.length} / {character._languageCalculation.choicesNeeded}
                        </p>
                      </div>
                    )}

                    {/* Total Languages Summary */}
                    <div className="p-2 bg-gray-800/30 rounded border border-gray-600/20 mt-2">
                      <p className="text-gray-400 text-xs">
                        <span className="font-semibold">Total Languages:</span> {' '}
                        {[...character._languageCalculation.automatic, ...character.languages].join(', ') || 'None selected'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <Separator className="bg-amber-600/20" />

              {/* Education Level */}
              <div>
                <Label className="text-amber-400">Education Level</Label>
                <Select value={character.education_level || ''} onValueChange={(val) => setCharacter(prev => ({...prev, education_level: val}))}>
                  <SelectTrigger className="bg-gray-800/50 border-amber-600/30 text-white">
                    <SelectValue placeholder="Select..." />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-amber-600/30">
                    <SelectItem value="None" className="text-white">None (Street-taught)</SelectItem>
                    <SelectItem value="Basic" className="text-white">Basic (Reading/Writing)</SelectItem>
                    <SelectItem value="Trained" className="text-white">Trained (Apprenticeship)</SelectItem>
                    <SelectItem value="Scholarly" className="text-white">Scholarly (University)</SelectItem>
                    <SelectItem value="Master" className="text-white">Master (Expert)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          {/* Step 4: Personality (Select from Background) */}
          {creationStep === 4 && (() => {
            const selectedBg = mockData.backgrounds.find(b => b.name === character.background);
            
            if (!selectedBg) {
              return (
                <div className="text-center p-8">
                  <p className="text-amber-400 text-lg">Please select a background first</p>
                  <p className="text-gray-400 mt-2">Go back to the Background step to choose your character's origin</p>
                </div>
              );
            }
            
            return (
              <div className="space-y-6 max-w-3xl mx-auto">
                <div className="text-center mb-6">
                  <h3 className="text-2xl text-amber-400">Shape Your Soul</h3>
                  <p className="text-gray-400">Choose from your {selectedBg.name} background traits</p>
                </div>

                {/* Personality Traits - Choose 2 */}
                <div className="bg-purple-900/20 p-6 rounded border border-purple-600/30">
                  <Label className="text-purple-400 text-lg mb-3 block">Personality Traits (Choose 2)</Label>
                  <div className="space-y-2">
                    {selectedBg.personalityTraits.map((trait, idx) => (
                      <label key={idx} className="flex items-start gap-3 p-3 bg-gray-800/30 rounded hover:bg-gray-800/50 cursor-pointer transition-colors">
                        <input
                          type="checkbox"
                          checked={character.traits.some(t => t.text === trait)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              if (character.traits.length < 2) {
                                setCharacter(prev => ({
                                  ...prev,
                                  traits: [...prev.traits, { text: trait, root_event: `From my ${selectedBg.name} background` }]
                                }));
                              }
                            } else {
                              setCharacter(prev => ({
                                ...prev,
                                traits: prev.traits.filter(t => t.text !== trait)
                              }));
                            }
                          }}
                          disabled={!character.traits.some(t => t.text === trait) && character.traits.length >= 2}
                          className="mt-1"
                        />
                        <span className="text-gray-200 text-sm">{trait}</span>
                      </label>
                    ))}
                  </div>
                  <p className="text-gray-500 text-xs mt-2">Selected: {character.traits.length} / 2</p>
                </div>

                {/* Ideals - Choose 1 */}
                <div className="bg-blue-900/20 p-6 rounded border border-blue-600/30">
                  <Label className="text-blue-400 text-lg mb-3 block">Guiding Ideal (Choose 1)</Label>
                  <div className="space-y-2">
                    {selectedBg.ideals.map((ideal, idx) => (
                      <label key={idx} className="flex items-start gap-3 p-3 bg-gray-800/30 rounded hover:bg-gray-800/50 cursor-pointer transition-colors">
                        <input
                          type="radio"
                          name="ideal"
                          checked={character.ideals[0]?.principle === ideal.name}
                          onChange={() => {
                            setCharacter(prev => ({
                              ...prev,
                              ideals: [{ 
                                principle: ideal.name, 
                                inspiration: `${ideal.description} (${ideal.alignment})` 
                              }]
                            }));
                          }}
                          className="mt-1"
                        />
                        <div>
                          <span className="text-gray-200 text-sm font-semibold">{ideal.name}</span>
                          <span className="text-amber-400 text-xs ml-2">({ideal.alignment})</span>
                          <p className="text-gray-400 text-xs mt-1">{ideal.description}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Bonds - Choose 1 */}
                <div className="bg-green-900/20 p-6 rounded border border-green-600/30">
                  <Label className="text-green-400 text-lg mb-3 block">Sacred Bond (Choose 1)</Label>
                  <div className="space-y-2">
                    {selectedBg.bonds.map((bond, idx) => (
                      <label key={idx} className="flex items-start gap-3 p-3 bg-gray-800/30 rounded hover:bg-gray-800/50 cursor-pointer transition-colors">
                        <input
                          type="radio"
                          name="bond"
                          checked={character.bonds[0]?.person_or_cause === bond}
                          onChange={() => {
                            setCharacter(prev => ({
                              ...prev,
                              bonds: [{ 
                                person_or_cause: bond, 
                                shared_event: `Connected through my ${selectedBg.name} past` 
                              }]
                            }));
                          }}
                          className="mt-1"
                        />
                        <span className="text-gray-200 text-sm">{bond}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Flaws - Choose 1 */}
                <div className="bg-red-900/20 p-6 rounded border border-red-600/30">
                  <Label className="text-red-400 text-lg mb-3 block">Fatal Flaw (Choose 1)</Label>
                  <div className="space-y-2">
                    {selectedBg.flaws.map((flaw, idx) => (
                      <label key={idx} className="flex items-start gap-3 p-3 bg-gray-800/30 rounded hover:bg-gray-800/50 cursor-pointer transition-colors">
                        <input
                          type="radio"
                          name="flaw"
                          checked={character.flaws_detailed[0]?.habit === flaw}
                          onChange={() => {
                            setCharacter(prev => ({
                              ...prev,
                              flaws_detailed: [{ 
                                habit: flaw, 
                                interference: 'This flaw often causes problems in social situations and decision-making',
                                intensity: 0.6
                              }]
                            }));
                          }}
                          className="mt-1"
                        />
                        <span className="text-gray-200 text-sm">{flaw}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            );
          })()}

          {/* Step 5: Alignment & Moral Core */}
          {creationStep === 5 && (
            <div className="space-y-6 max-w-2xl mx-auto">
              <div className="text-center mb-6">
                <h3 className="text-2xl text-amber-400">Your Moral Compass</h3>
                <p className="text-gray-400">How do you navigate right and wrong?</p>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <Label className="text-amber-400 text-lg">Law vs Chaos</Label>
                  <Select 
                    value={character.alignment_vector?.lawful_chaotic || ''} 
                    onValueChange={(val) => setCharacter(prev => ({
                      ...prev, 
                      alignment_vector: { ...prev.alignment_vector, lawful_chaotic: val }
                    }))}
                  >
                    <SelectTrigger className="bg-gray-800/50 border-amber-600/30 text-white">
                      <SelectValue placeholder="Select..." />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-amber-600/30">
                      <SelectItem value="Lawful" className="text-white">Lawful (Order, tradition)</SelectItem>
                      <SelectItem value="Neutral" className="text-white">Neutral (Pragmatic)</SelectItem>
                      <SelectItem value="Chaotic" className="text-white">Chaotic (Freedom, instinct)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-amber-400 text-lg">Good vs Evil</Label>
                  <Select 
                    value={character.alignment_vector?.good_evil || ''} 
                    onValueChange={(val) => setCharacter(prev => ({
                      ...prev, 
                      alignment_vector: { ...prev.alignment_vector, good_evil: val }
                    }))}
                  >
                    <SelectTrigger className="bg-gray-800/50 border-amber-600/30 text-white">
                      <SelectValue placeholder="Select..." />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-800 border-amber-600/30">
                      <SelectItem value="Good" className="text-white">Good (Altruistic)</SelectItem>
                      <SelectItem value="Neutral" className="text-white">Neutral (Self-interested)</SelectItem>
                      <SelectItem value="Evil" className="text-white">Evil (Selfish, cruel)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {character.alignment_vector?.lawful_chaotic && character.alignment_vector?.good_evil && (
                <div className="bg-amber-900/20 p-4 rounded border border-amber-600/30">
                  <p className="text-amber-300 text-center font-semibold text-lg">
                    {character.alignment_vector.lawful_chaotic} {character.alignment_vector.good_evil}
                  </p>
                </div>
              )}

              <Separator className="bg-amber-600/20" />

              <div>
                <Label className="text-amber-400 text-lg">Moral Tension</Label>
                <p className="text-gray-400 text-sm mb-3">Describe the conflict between your Ideal and your Flaw</p>
                <textarea
                  value={character.moral_tension || ''}
                  onChange={(e) => setCharacter(prev => ({ ...prev, moral_tension: e.target.value }))}
                  placeholder="e.g., 'I seek redemption but my greed constantly tempts me back to old ways'"
                  className="w-full bg-gray-800/50 border border-amber-600/30 text-white p-3 rounded min-h-[100px]"
                />
              </div>
            </div>
          )}

          {/* Step 6: Aspiration (Endgame Goal) */}
          {creationStep === 6 && (
            <div className="space-y-6 max-w-2xl mx-auto">
              <div className="text-center mb-6">
                <h3 className="text-2xl text-amber-400">Your Ultimate Quest</h3>
                <p className="text-gray-400">What do you ultimately want?</p>
              </div>

              <div>
                <Label className="text-amber-400 text-lg">Endgame Goal</Label>
                <Input
                  value={character.aspiration?.goal || ''}
                  onChange={(e) => setCharacter(prev => ({
                    ...prev,
                    aspiration: { ...prev.aspiration, goal: e.target.value }
                  }))}
                  placeholder="e.g., 'Clear my family name', 'Destroy the cult that killed my mentor'"
                  className="bg-gray-800/50 border-amber-600/30 text-white"
                />
              </div>

              <div>
                <Label className="text-amber-400">Why does it matter?</Label>
                <textarea
                  value={character.aspiration?.motivation || ''}
                  onChange={(e) => setCharacter(prev => ({
                    ...prev,
                    aspiration: { ...prev.aspiration, motivation: e.target.value }
                  }))}
                  placeholder="Describe your motivation..."
                  className="w-full bg-gray-800/50 border border-amber-600/30 text-white p-3 rounded min-h-[100px]"
                />
              </div>

              <div>
                <Label className="text-amber-400">What are you willing to risk?</Label>
                <p className="text-gray-400 text-sm mb-2">Sacrifice Threshold: {character.aspiration?.sacrifice_threshold || 5} / 10</p>
                <input
                  type="range"
                  min="0"
                  max="10"
                  step="1"
                  value={character.aspiration?.sacrifice_threshold || 5}
                  onChange={(e) => setCharacter(prev => ({
                    ...prev,
                    aspiration: { ...prev.aspiration, sacrifice_threshold: parseInt(e.target.value) }
                  }))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>Nothing (0)</span>
                  <span>Everything (10)</span>
                </div>
              </div>
            </div>
          )}

          {/* Step 7: Review (Relationships auto-generated by AI) */}
          {creationStep === 7 && (
            <div className="space-y-6">
              <h3 className="text-xl text-amber-400 text-center">Your Legend Awaits</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="bg-gray-800/50 p-4 rounded border border-amber-600/30">
                    <h4 className="text-amber-400 font-semibold mb-2">Basic Information</h4>
                    <div className="space-y-1 text-sm">
                      <div><span className="text-gray-400">Name:</span> <span className="text-white font-semibold">{character.name}</span></div>
                      <div><span className="text-gray-400">Race:</span> <span className="text-white">{character.race}</span></div>
                      <div><span className="text-gray-400">Class:</span> <span className="text-white">{character.class}</span></div>
                      <div>
                        <span className="text-gray-400">Background:</span> 
                        <span className="text-white"> {character.background}</span>
                        {(() => {
                          const bg = mockData.backgrounds.find(b => b.name === character.background);
                          if (bg?.variants && character.backgroundVariantKey) {
                            const variant = bg.variants[character.backgroundVariantKey];
                            if (variant && variant.label !== character.background) {
                              return <span className="text-purple-300 text-xs ml-1">({variant.label})</span>;
                            }
                          }
                          return null;
                        })()}
                      </div>
                      <div><span className="text-gray-400">Level:</span> <span className="text-white">{character.level}</span></div>
                      <div><span className="text-gray-400">Hit Points:</span> <span className="text-white">{character.hitPoints}</span></div>
                      <div><span className="text-gray-400">Size:</span> <span className="text-white">{character.size || 'Medium'}</span></div>
                      <div><span className="text-gray-400">Speed:</span> <span className="text-white">{character.speed || 30} ft.</span></div>
                    </div>
                  </div>

                  {/* Languages Section */}
                  {character._languageCalculation && (
                    <div className="bg-gray-800/50 p-4 rounded border border-blue-600/30">
                      <h4 className="text-blue-400 font-semibold mb-2">Languages</h4>
                      <div className="flex flex-wrap gap-2">
                        {[...character._languageCalculation.automatic, ...character.languages].map((lang, idx) => (
                          <Badge key={idx} variant="outline" className="border-blue-400/50 text-blue-300">
                            {lang}
                          </Badge>
                        ))}
                        {[...character._languageCalculation.automatic, ...character.languages].length === 0 && (
                          <span className="text-gray-400 text-sm">No languages selected</span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Racial Traits Section */}
                  {character.racial_traits && character.racial_traits.length > 0 && (
                    <div className="bg-gray-800/50 p-4 rounded border border-green-600/30">
                      <h4 className="text-green-400 font-semibold mb-2">Racial Traits ({character.race})</h4>
                      <div className="space-y-3">
                        {character.racial_traits.map((trait, idx) => (
                          <div key={idx} className="text-sm">
                            <p className="text-green-300 font-semibold">{trait.name}</p>
                            <p className="text-gray-300 text-xs mt-1">{trait.description}</p>
                            {trait.mechanical_effect && (
                              <p className="text-blue-400 text-xs mt-1 italic">• {trait.mechanical_effect}</p>
                            )}
                          </div>
                        ))}
                      </div>
                      <div className="mt-3 pt-3 border-t border-gray-700/50 text-xs text-gray-400">
                        <span className="font-semibold">Size:</span> {character.size || 'Medium'} | <span className="font-semibold">Speed:</span> {character.speed || 30} ft.
                      </div>
                    </div>
                  )}

                  {character.traits?.length > 0 && character.traits.some(t => t?.text) && (
                    <div className="bg-gray-800/50 p-4 rounded border border-purple-600/30">
                      <h4 className="text-purple-400 font-semibold mb-2">Personality Traits</h4>
                      <div className="space-y-2">
                        {character.traits.filter(t => t?.text).map((trait, idx) => (
                          <div key={idx} className="text-sm">
                            <span className="text-purple-300 font-semibold">{String(trait.text)}</span>
                            {trait.root_event && typeof trait.root_event === 'string' && (
                              <p className="text-gray-400 text-xs mt-1 italic">Origin: {trait.root_event}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="space-y-4">
                  <div className="bg-gray-800/50 p-4 rounded border border-blue-600/30">
                    <h4 className="text-blue-400 font-semibold mb-2">Ability Scores</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      {Object.entries(character.stats).map(([stat, value]) => {
                        // Calculate base stat (without racial bonus)
                        let baseValue = value;
                        let racialBonus = 0;
                        
                        // racial_asi is now an object like {dexterity: 2, charisma: 1}
                        if (character.racial_asi && typeof character.racial_asi === 'object') {
                          racialBonus = character.racial_asi[stat] || 0;
                          baseValue = value - racialBonus;
                        }
                        
                        return (
                          <div key={stat} className="flex justify-between items-center">
                            <span className="text-gray-400 capitalize">{stat.slice(0, 3)}:</span>
                            <div className="text-right">
                              <span className="text-white font-semibold">
                                {value} ({getStatModifierString(value)})
                              </span>
                              {racialBonus > 0 && (
                                <div className="text-xs text-blue-400">
                                  ({baseValue} base + {racialBonus} racial)
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {character.spellSlots.length > 0 && (
                    <div className="bg-gray-800/50 p-4 rounded border border-cyan-600/30">
                      <h4 className="text-cyan-400 font-semibold mb-2">Spell Slots</h4>
                      <div className="text-sm text-white">
                        Level 1: {character.spellSlots.filter(slot => slot === 1).length} slots
                      </div>
                    </div>
                  )}

                  {/* Ideals */}
                  {character.ideals?.[0]?.principle && typeof character.ideals[0].principle === 'string' && (
                    <div className="bg-gray-800/50 p-4 rounded border border-blue-600/30">
                      <h4 className="text-blue-400 font-semibold mb-2">Guiding Ideal</h4>
                      <p className="text-blue-300 font-semibold text-sm">{String(character.ideals[0].principle)}</p>
                      {character.ideals[0].inspiration && typeof character.ideals[0].inspiration === 'string' && (
                        <p className="text-gray-400 text-xs mt-1 italic">Inspired by: {String(character.ideals[0].inspiration)}</p>
                      )}
                    </div>
                  )}

                  {/* Bonds */}
                  {character.bonds?.[0]?.person_or_cause && typeof character.bonds[0].person_or_cause === 'string' && (
                    <div className="bg-gray-800/50 p-4 rounded border border-green-600/30">
                      <h4 className="text-green-400 font-semibold mb-2">Sacred Bond</h4>
                      <p className="text-green-300 font-semibold text-sm">{String(character.bonds[0].person_or_cause)}</p>
                      {character.bonds[0].shared_event && typeof character.bonds[0].shared_event === 'string' && (
                        <p className="text-gray-400 text-xs mt-1 italic">{String(character.bonds[0].shared_event)}</p>
                      )}
                    </div>
                  )}

                  {/* Flaws */}
                  {character.flaws_detailed?.[0]?.habit && typeof character.flaws_detailed[0].habit === 'string' && (
                    <div className="bg-gray-800/50 p-4 rounded border border-red-600/30">
                      <h4 className="text-red-400 font-semibold mb-2">Fatal Flaw</h4>
                      <p className="text-red-300 font-semibold text-sm">{String(character.flaws_detailed[0].habit)}</p>
                      {character.flaws_detailed[0].interference && typeof character.flaws_detailed[0].interference === 'string' && (
                        <p className="text-gray-400 text-xs mt-1">{String(character.flaws_detailed[0].interference)}</p>
                      )}
                      <p className="text-gray-400 text-xs mt-1">Intensity: {Math.round((character.flaws_detailed[0].intensity || 0) * 10)}/10</p>
                    </div>
                  )}

                  {/* Alignment */}
                  {character.alignment_vector?.lawful_chaotic && (
                    <div className="bg-gray-800/50 p-4 rounded border border-amber-600/30">
                      <h4 className="text-amber-400 font-semibold mb-2">Alignment</h4>
                      <p className="text-amber-300 font-semibold">{character.alignment_vector.lawful_chaotic} {character.alignment_vector.good_evil}</p>
                    </div>
                  )}

                  {/* Aspiration */}
                  {character.aspiration?.goal && typeof character.aspiration.goal === 'string' && (
                    <div className="bg-gray-800/50 p-4 rounded border border-yellow-600/30">
                      <h4 className="text-yellow-400 font-semibold mb-2">Ultimate Goal</h4>
                      <p className="text-yellow-300 font-semibold text-sm">{String(character.aspiration.goal)}</p>
                      {character.aspiration.motivation && typeof character.aspiration.motivation === 'string' && (
                        <p className="text-gray-400 text-xs mt-1">{String(character.aspiration.motivation)}</p>
                      )}
                      <p className="text-gray-400 text-xs mt-1">Willing to sacrifice: {character.aspiration.sacrifice_threshold || 5}/10</p>
                    </div>
                  )}

                  {/* VIP Relationships - AI Generated */}
                  <div className="bg-gray-800/50 p-4 rounded border border-pink-600/30 col-span-2">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-pink-400 font-semibold">Key Relationships (AI Generated)</h4>
                      <button
                        onClick={generateRelationships}
                        disabled={generatingRelationships}
                        className="text-xs bg-pink-600 hover:bg-pink-700 disabled:bg-gray-600 text-white px-3 py-1 rounded transition-colors flex items-center gap-1"
                      >
                        {generatingRelationships ? (
                          <>
                            <Sparkles className="w-3 h-3 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-3 h-3" />
                            Regenerate
                          </>
                        )}
                      </button>
                    </div>
                    {generatingRelationships ? (
                      <div className="text-center py-4 text-gray-400 text-sm">
                        <Sparkles className="w-6 h-6 mx-auto mb-2 animate-pulse text-pink-400" />
                        AI is creating meaningful relationships...
                      </div>
                    ) : character.vip_hooks.some(h => h.name) ? (
                      <div className="space-y-2">
                        {character.vip_hooks.filter(h => h.name).map((hook, idx) => (
                          <div key={idx} className="text-sm bg-gray-900/30 p-3 rounded">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-pink-300 font-semibold">{hook.name}</span>
                              {hook.relation && <Badge variant="outline" className="text-xs border-pink-600/50 text-pink-300">{hook.relation}</Badge>}
                            </div>
                            {hook.shared_event && (
                              <p className="text-gray-400 text-xs italic mb-1">{hook.shared_event}</p>
                            )}
                            {hook.personal_aspiration && (
                              <p className="text-gray-500 text-xs">→ {hook.personal_aspiration}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm text-center py-2">No relationships generated yet</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          <Separator className="bg-amber-600/30" />

          {/* Navigation */}
          <div className="flex justify-between">
            <Button 
              onClick={() => setCreationStep(Math.max(0, creationStep - 1))}
              disabled={creationStep === 0}
              variant="outline"
              className="border-amber-600 text-amber-400 hover:bg-amber-600/20"
            >
              Previous
            </Button>
            
            {creationStep < 7 ? (
              <Button 
                onClick={() => setCreationStep(creationStep + 1)}
                className="bg-amber-700 hover:bg-amber-600 text-black font-semibold"
                disabled={
                  (creationStep === 0 && (!character.name || !character.race || !character.class)) ||
                  (creationStep === 1 && !statsAssigned) ||
                  (creationStep === 2 && (() => {
                    const classSkillData = CLASS_SKILLS[character.class];
                    return !classSkillData || (character.proficiencies?.length || 0) < classSkillData.count;
                  })()) ||
                  (creationStep === 3 && !character.background)
                }
              >
                Next
              </Button>
            ) : (
              <Button 
                onClick={handleCreateCharacter}
                className="bg-green-700 hover:bg-green-600 text-white font-semibold px-8"
                size="lg"
              >
                <Crown className="h-5 w-5 mr-2" />
                Forge My Legend
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
      
      {/* Loading Modal */}
      <LoadingModal progress={loadingProgress} isOpen={isLoading} />
    </div>
  );
};

export default CharacterCreation;