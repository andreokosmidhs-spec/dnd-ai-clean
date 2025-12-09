// API function for creating V2 characters
import axios from './axiosConfig';

export const createCharacterV2 = async (characterData) => {
  const res = await axios.post('/api/characters_v2/create', characterData);
  return res.data;
};

// Simple step labels – we’ll flesh out the others later
const STEP_KEYS = [
  'identity',
  'race',
  'class',
  'background',
  'stats',
  'appearance',
  'review',
];

const STEP_LABELS = {
  identity: 'Identity',
  race: 'Race',
  class: 'Class',
  background: 'Background',
  stats: 'Ability Scores',
  appearance: 'Appearance',
  review: 'Review & Save',
};

const CharacterCreationV2 = ({ onComplete }) => {
  // --- master character state for V2 schema ---
  const [character, setCharacter] = useState({
    // STEP 1 – identity
    identity: {
      name: '',
      sex: null,                 // 'male' | 'female' | 'other' | null
      genderExpression: 50,      // 0 = very masculine, 100 = very feminine
    },

    // STEP 2 – race (placeholder for now)
    race: {
      key: null,                 // e.g. 'human', 'elf'
      variantKey: null,          // e.g. 'high_elf'
    },

    // STEP 3 – class (placeholder)
    class: {
      key: null,                 // e.g. 'wizard'
      subclassKey: null,         // e.g. 'evoker'
      level: 1,
    },

    // STEP 4 – background (placeholder)
    background: {
      key: null,                 // e.g. 'criminal'
      variantKey: null,
    },

    // STEP 5 – stats (placeholder)
    stats: {
      str: null,
      dex: null,
      con: null,
      int: null,
      wis: null,
      cha: null,
      method: 'standard_array',  // or 'point_buy', 'rolled'
    },

    // STEP 6 – appearance (placeholder)
    appearance: {
      ageCategory: null,         // 'young' | 'adult' | 'veteran' | 'elder'
      heightCm: null,
      build: null,               // 'slim', 'average', 'muscular', etc.
      skinTone: null,
      hairColor: null,
      eyeColor: null,
      notableFeatures: [],       // array of strings
    },

    // meta / system fields (optional for now)
    meta: {
      version: 2,
    },
  });

  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const currentStepKey = STEP_KEYS[currentStepIndex];

  // --- navigation helpers ---
  const goNext = () => {
    setCurrentStepIndex((idx) => Math.min(idx + 1, STEP_KEYS.length - 1));
  };

  const goPrev = () => {
    setCurrentStepIndex((idx) => Math.max(idx - 1, 0));
  };

  const goToStep = (index) => {
    if (index < 0 || index >= STEP_KEYS.length) return;
    setCurrentStepIndex(index);
  };

  // --- per-step change helpers ---
  const updateSection = (sectionKey, updater) => {
    setCharacter((prev) => ({
      ...prev,
      [sectionKey]:
        typeof updater === 'function'
          ? updater(prev[sectionKey])
          : updater,
    }));
  };

  const handleIdentityChange = (newIdentity) => {
    updateSection('identity', newIdentity);
  };

  // --- save to backend (Review step) ---
  const handleSaveCharacter = async () => {
    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      const payload = character; // Already shaped for the V2 API
      const saved = await createCharacterV2(payload);

      setSaveSuccess(true);
      if (onComplete) {
        onComplete(saved);
      }
    } catch (err) {
      console.error('Failed to create character V2', err);
      setSaveError(
        err?.response?.data?.detail ||
          err?.message ||
          'Failed to save character.'
      );
    } finally {
      setIsSaving(false);
    }
  };

  // --- step renderers ---

  const renderStep = () => {
    switch (currentStepKey) {
      case 'identity':
        return (
          <IdentityStep
            value={character.identity}
            onChange={handleIdentityChange}
            onNext={goNext}
          />
        );

      case 'race':
      case 'class':
      case 'background':
      case 'stats':
      case 'appearance':
        // Simple placeholder panels until we implement full UIs
        return (
          <div className="p-6 bg-slate-900/60 rounded-2xl border border-slate-700 text-slate-100">
            <h2 className="text-xl font-semibold mb-3">
              {STEP_LABELS[currentStepKey]} (Coming Soon)
            </h2>
            <p className="text-sm text-slate-300">
              This step will be rebuilt with the new 5e-compliant flow. For
              now, you can navigate between steps, and the new Identity
              step is fully functional.
            </p>

            <div className="mt-6 flex justify-between">
              <button
                type="button"
                onClick={goPrev}
                className="px-4 py-2 rounded-md bg-slate-800 text-slate-100 hover:bg-slate-700"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={goNext}
                className="px-4 py-2 rounded-md bg-amber-600 text-slate-900 hover:bg-amber-500"
              >
                Next
              </button>
            </div>
          </div>
        );

      case 'review':
        return (
          <div className="p-6 bg-slate-900/60 rounded-2xl border border-slate-700 text-slate-100">
            <h2 className="text-xl font-semibold mb-3">
              Review & Save (V2)
            </h2>

            <p className="text-sm text-slate-300 mb-4">
              This is a lightweight review step for the new character
              schema. We&apos;ll expand this into a full summary once the
              rest of the flow has been migrated.
            </p>

            <div className="space-y-3 text-sm">
              <div>
                <h3 className="font-semibold text-slate-100">Identity</h3>
                <p>Name: {character.identity.name || '—'}</p>
                <p>Sex: {character.identity.sex || '—'}</p>
                <p>
                  Gender Expression:{' '}
                  {character.identity.genderExpression}
                  /100
                </p>
              </div>

              {/* Placeholders for later */}
              <div>
                <h3 className="font-semibold text-slate-100">Race</h3>
                <p>{character.race.key || 'Not selected yet'}</p>
              </div>

              <div>
                <h3 className="font-semibold text-slate-100">Class</h3>
                <p>{character.class.key || 'Not selected yet'}</p>
              </div>
            </div>

            {saveError && (
              <div className="mt-4 text-sm text-red-400">
                {saveError}
              </div>
            )}

            {saveSuccess && (
              <div className="mt-4 text-sm text-emerald-400">
                Character saved successfully!
              </div>
            )}

            <div className="mt-6 flex justify-between">
              <button
                type="button"
                onClick={goPrev}
                className="px-4 py-2 rounded-md bg-slate-800 text-slate-100 hover:bg-slate-700"
                disabled={isSaving}
              >
                Previous
              </button>
              <button
                type="button"
                onClick={handleSaveCharacter}
                className="px-4 py-2 rounded-md bg-emerald-500 text-slate-900 hover:bg-emerald-400 disabled:opacity-60"
                disabled={isSaving}
              >
                {isSaving ? 'Saving…' : 'Save Character (V2)'}
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  // --- step header navigation ---
  const renderStepTabs = () => {
    return (
      <div className="flex flex-wrap gap-2 mb-6">
        {STEP_KEYS.map((key, index) => {
          const isActive = index === currentStepIndex;
          const isCompleted = index < currentStepIndex;

          return (
            <button
              key={key}
              type="button"
              onClick={() => goToStep(index)}
              className={[
                'px-3 py-1.5 rounded-full text-xs font-medium border',
                isActive
                  ? 'bg-amber-500 text-slate-900 border-amber-400'
                  : isCompleted
                  ? 'bg-slate-800 text-slate-100 border-slate-600 hover:bg-slate-700'
                  : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800',
              ].join(' ')}
            >
              {STEP_LABELS[key]}
            </button>
          );
        })}
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-slate-100">
          Character Creation (V2 Prototype)
        </h1>
        <p className="text-sm text-slate-300 mt-1">
          Identity step is fully wired to the new backend schema. Race,
          Class, Background, Stats, and Appearance will be migrated next.
        </p>
      </div>

      {renderStepTabs()}

      {renderStep()}
    </div>
  );
};

export default CharacterCreationV2;
