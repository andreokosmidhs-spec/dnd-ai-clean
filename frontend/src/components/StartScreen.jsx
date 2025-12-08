import React, { useState } from 'react';
import { Sparkles, RefreshCw, Play, ChevronDown, ChevronUp } from 'lucide-react';

const StartScreen = ({ onCharacterCreated, onSkip }) => {
  const [step, setStep] = useState('questions'); // 'questions' | 'generating' | 'summary'
  const [vibe, setVibe] = useState('');
  const [theme, setTheme] = useState('');
  const [ruleOfCool, setRuleOfCool] = useState(0.3);
  const [character, setCharacter] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [error, setError] = useState('');

  const vibes = [
    { value: 'Stoic knight', label: 'Stoic knight', icon: '🛡️' },
    { value: 'Cunning rogue', label: 'Cunning rogue', icon: '🗡️' },
    { value: 'Wild mage', label: 'Wild mage', icon: '✨' },
    { value: 'Devoted healer', label: 'Devoted healer', icon: '🙏' },
    { value: 'Lone tracker', label: 'Lone tracker', icon: '🏹' },
    { value: 'Surprise me', label: 'Surprise me', icon: '🎲' }
  ];

  const themes = [
    { value: 'Justice', label: 'Justice', icon: '⚖️' },
    { value: 'Freedom', label: 'Freedom', icon: '🕊️' },
    { value: 'Loyalty', label: 'Loyalty', icon: '🤝' },
    { value: 'Redemption', label: 'Redemption', icon: '🔥' },
    { value: 'Discovery', label: 'Discovery', icon: '🔍' },
    { value: 'Surprise me', label: 'Surprise me', icon: '🎲' }
  ];

  const generateCharacter = async (mode = 'guided') => {
    setStep('generating');
    setError('');

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const payload = {
        mode: mode,
        rule_of_cool: ruleOfCool,
        level_or_cr: 3
      };

      if (mode === 'guided' && vibe && theme) {
        payload.answers = {
          vibe: vibe === 'Surprise me' ? null : vibe,
          theme: theme === 'Surprise me' ? null : theme
        };
      }

      const response = await fetch(`${backendUrl}/api/generate_character`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate character');
      }

      const data = await response.json();
      setCharacter(data);
      setStep('summary');
    } catch (err) {
      console.error('Character generation error:', err);
      setError(err.message || 'Failed to generate character. Please try again.');
      setStep('questions');
    }
  };

  const handleReroll = () => {
    generateCharacter('reroll');
  };

  const handleInstantStart = () => {
    generateCharacter('instant');
  };

  const handleStartAdventure = () => {
    if (character) {
      onCharacterCreated({
        character: character.sheet,
        summary: character.summary
      });
    }
  };

  if (step === 'generating') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
        <div className="text-center">
          <Sparkles className="w-16 h-16 text-amber-400 mx-auto animate-pulse mb-4" />
          <h2 className="text-2xl font-bold text-amber-400 mb-2">Forging Your Character...</h2>
          <p className="text-slate-300">The AI is crafting your unique hero</p>
        </div>
      </div>
    );
  }

  if (step === 'summary' && character) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full">
          {/* Character Summary Card */}
          <div className="bg-slate-800 rounded-xl p-8 shadow-2xl border-2 border-amber-500">
            <div className="text-center mb-6">
              <h1 className="text-4xl font-bold text-amber-400 mb-2">{character.summary.name}</h1>
              <p className="text-xl text-purple-300">{character.summary.role}</p>
              <p className="text-slate-300 italic mt-2">{character.summary.tagline}</p>
            </div>

            <div className="space-y-3 mb-6">
              <h3 className="text-amber-400 font-semibold">Your Story:</h3>
              {character.summary.hooks.map((hook, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-amber-400 font-bold">•</span>
                  <p className="text-slate-200">{hook}</p>
                </div>
              ))}
            </div>

            {/* Details Toggle */}
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="w-full flex items-center justify-center gap-2 py-2 text-slate-400 hover:text-amber-400 transition-colors mb-4"
            >
              {showDetails ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              {showDetails ? 'Hide' : 'Show'} Full Character Sheet
            </button>

            {showDetails && (
              <div className="bg-slate-900 rounded-lg p-4 mb-6 max-h-96 overflow-y-auto">
                <div className="text-sm text-slate-300 space-y-2">
                  <div>
                    <span className="text-amber-400 font-semibold">Race:</span> {character.sheet.meta.race}
                  </div>
                  <div>
                    <span className="text-amber-400 font-semibold">Class:</span> {character.sheet.meta.class_or_archetype}
                  </div>
                  <div>
                    <span className="text-amber-400 font-semibold">Background:</span> {character.sheet.meta.background}
                  </div>
                  <div>
                    <span className="text-amber-400 font-semibold">Level:</span> {character.sheet.meta.level_or_cr} (Proficiency +{character.sheet.meta.proficiency_bonus})
                  </div>
                  
                  {character.sheet.dnd_stats && (
                    <>
                      <div className="mt-3">
                        <span className="text-amber-400 font-semibold">Abilities:</span>
                        <div className="grid grid-cols-3 gap-2 mt-1">
                          {Object.entries(character.sheet.dnd_stats.abilities).map(([stat, value]) => (
                            <div key={stat} className="bg-slate-800 rounded px-2 py-1">
                              <span className="text-purple-300">{stat}</span>: {value}
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="text-amber-400 font-semibold">HP:</span> {character.sheet.dnd_stats.hp.current}/{character.sheet.dnd_stats.hp.max}
                      </div>
                      <div>
                        <span className="text-amber-400 font-semibold">AC:</span> {character.sheet.dnd_stats.ac}
                      </div>
                    </>
                  )}
                  
                  {character.sheet.identity?.emotion_slots && (
                    <div className="mt-3">
                      <span className="text-amber-400 font-semibold">Core Values:</span>
                      <div className="space-y-1 mt-1">
                        {Object.entries(character.sheet.identity.emotion_slots)
                          .sort((a, b) => b[1].bias - a[1].bias)
                          .slice(0, 3)
                          .map(([emotion, slot]) => (
                            <div key={emotion} className="text-xs">
                              <span className="text-purple-300">{emotion}:</span> {slot.ideal} (strength: {Math.round(slot.bias * 100)}%)
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={handleStartAdventure}
                className="flex-1 bg-amber-500 hover:bg-amber-600 text-slate-900 font-bold py-3 px-6 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Play size={20} />
                Start Adventure
              </button>
              <button
                onClick={handleReroll}
                className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center transition-colors"
                title="Generate a new character"
              >
                <RefreshCw size={20} />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Questions Step
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <div className="max-w-3xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-amber-400 mb-4">Begin Your Adventure</h1>
          <p className="text-xl text-slate-300">Answer two quick questions and let the AI forge your hero</p>
        </div>

        <div className="bg-slate-800 rounded-xl p-8 shadow-2xl border-2 border-purple-500">
          {error && (
            <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded mb-6">
              {error}
            </div>
          )}

          {/* Question 1: Vibe */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-amber-400 mb-4">1. Pick a vibe:</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {vibes.map((v) => (
                <button
                  key={v.value}
                  onClick={() => setVibe(v.value)}
                  className={`py-4 px-4 rounded-lg font-semibold transition-all ${
                    vibe === v.value
                      ? 'bg-amber-500 text-slate-900 scale-105 shadow-lg'
                      : 'bg-slate-700 text-slate-200 hover:bg-slate-600'
                  }`}
                >
                  <span className="text-2xl mr-2">{v.icon}</span>
                  {v.label}
                </button>
              ))}
            </div>
          </div>

          {/* Question 2: Theme */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-amber-400 mb-4">2. Pick a theme to test:</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {themes.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setTheme(t.value)}
                  className={`py-4 px-4 rounded-lg font-semibold transition-all ${
                    theme === t.value
                      ? 'bg-purple-500 text-white scale-105 shadow-lg'
                      : 'bg-slate-700 text-slate-200 hover:bg-slate-600'
                  }`}
                >
                  <span className="text-2xl mr-2">{t.icon}</span>
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Rule of Cool Slider */}
          <div className="mb-8">
            <label className="block text-amber-400 font-semibold mb-2">
              Rule of Cool: {ruleOfCool.toFixed(2)}
            </label>
            <p className="text-sm text-slate-400 mb-2">How cinematic should your adventure be?</p>
            <input
              type="range"
              min="0"
              max="0.5"
              step="0.05"
              value={ruleOfCool}
              onChange={(e) => setRuleOfCool(parseFloat(e.target.value))}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>Realistic</span>
              <span>Epic</span>
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={() => generateCharacter('guided')}
            disabled={!vibe || !theme}
            className={`w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center gap-2 transition-all ${
              vibe && theme
                ? 'bg-gradient-to-r from-amber-500 to-purple-500 hover:from-amber-600 hover:to-purple-600 text-white shadow-lg'
                : 'bg-slate-700 text-slate-500 cursor-not-allowed'
            }`}
          >
            <Sparkles size={24} />
            Generate Character
          </button>

          {/* Instant Start Option */}
          <div className="mt-4 text-center">
            <button
              onClick={handleInstantStart}
              className="text-slate-400 hover:text-amber-400 underline transition-colors"
            >
              Or skip questions and generate instantly
            </button>
          </div>

          {/* Dev Skip */}
          {onSkip && (
            <div className="mt-4 text-center">
              <button
                onClick={onSkip}
                className="text-slate-500 hover:text-purple-400 text-sm transition-colors"
              >
                Skip to Adventure (Dev)
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StartScreen;
