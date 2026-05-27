import React, { useState, useMemo, useCallback } from 'react';
import { X, Plus, Minus, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { KnowledgeCard } from './KnowledgeCard';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// ─── Card type definitions ────────────────────────────────────────────────────

const CARD_TYPES = [
  { key: 'npc',      label: 'NPC',      color: 'from-blue-600 to-blue-800',     ring: 'ring-blue-500' },
  { key: 'location', label: 'Location', color: 'from-emerald-600 to-emerald-800', ring: 'ring-emerald-500' },
  { key: 'faction',  label: 'Faction',  color: 'from-purple-600 to-purple-800', ring: 'ring-purple-500' },
  { key: 'item',     label: 'Item',     color: 'from-orange-500 to-amber-700',  ring: 'ring-orange-500' },
  { key: 'spell',    label: 'Spell',    color: 'from-violet-600 to-indigo-800', ring: 'ring-violet-500' },
  { key: 'quest',    label: 'Quest',    color: 'from-amber-500 to-amber-700',   ring: 'ring-amber-500' },
  { key: 'favor',    label: 'Favor',    color: 'from-pink-600 to-rose-800',     ring: 'ring-pink-500' },
  { key: 'curse',    label: 'Curse',    color: 'from-red-700 to-red-900',       ring: 'ring-red-600' },
];

const BIOMES = [
  { key: 'forest',    label: 'Forest' },
  { key: 'plains',    label: 'Plains' },
  { key: 'desert',    label: 'Desert' },
  { key: 'mountain',  label: 'Mountain' },
  { key: 'swamp',     label: 'Swamp' },
  { key: 'coast',     label: 'Coast' },
  { key: 'tundra',    label: 'Tundra' },
  { key: 'underdark', label: 'Underdark' },
  { key: 'volcanic',  label: 'Volcanic' },
  { key: 'urban',     label: 'Urban' },
  { key: 'fey',       label: 'Feywild' },
  { key: 'shadow',    label: 'Shadowfell' },
];

const ITEM_TYPES   = ['equipment', 'consumable', 'material', 'currency'];
const EQUIP_SLOTS  = ['weapon', 'armor', 'accessory', 'offhand'];
const SKILLS_LIST  = [
  'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma',
  'acrobatics', 'athletics', 'deception', 'history', 'insight', 'intimidation',
  'investigation', 'medicine', 'nature', 'perception', 'performance', 'persuasion',
  'religion', 'sleight of hand', 'stealth', 'survival',
];

// ─── Small reusable helpers ───────────────────────────────────────────────────

const Label = ({ children }) => (
  <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
    {children}
  </span>
);

const FieldGroup = ({ label, children }) => (
  <div className="space-y-1">
    {label && <Label>{label}</Label>}
    {children}
  </div>
);

const Divider = () => <div className="border-t border-gray-700/50 my-4" />;

const TextInput = ({ value, onChange, placeholder, className = '' }) => (
  <input
    value={value}
    onChange={e => onChange(e.target.value)}
    placeholder={placeholder}
    className={`w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-gray-500 focus:ring-1 focus:ring-gray-500/50 ${className}`}
  />
);

const TextArea = ({ value, onChange, placeholder, rows = 3 }) => (
  <textarea
    value={value}
    onChange={e => onChange(e.target.value)}
    placeholder={placeholder}
    rows={rows}
    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-gray-500 focus:ring-1 focus:ring-gray-500/50 resize-none"
  />
);

const SelectInput = ({ value, onChange, options, placeholder }) => (
  <select
    value={value}
    onChange={e => onChange(e.target.value)}
    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-gray-500"
  >
    {placeholder && <option value="">{placeholder}</option>}
    {options.map(o => (
      <option key={o.key || o} value={o.key || o}>{o.label || o}</option>
    ))}
  </select>
);

const NumberInput = ({ value, onChange, min = 0, max, placeholder }) => (
  <input
    type="number"
    value={value}
    onChange={e => onChange(Number(e.target.value))}
    min={min}
    max={max}
    placeholder={placeholder}
    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-gray-500"
  />
);

// Tag list — enter to add, × to remove
const TagList = ({ items, onChange, placeholder }) => {
  const [draft, setDraft] = useState('');
  const add = () => {
    const trimmed = draft.trim();
    if (!trimmed) return;
    onChange([...items, trimmed]);
    setDraft('');
  };
  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add(); } }}
          placeholder={placeholder}
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-gray-500"
        />
        <button
          type="button"
          onClick={add}
          className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-gray-300 transition-colors"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>
      {items.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {items.map((item, i) => (
            <span key={i} className="flex items-center gap-1 bg-gray-700/70 text-gray-300 text-xs px-2 py-1 rounded-full">
              {item}
              <button type="button" onClick={() => onChange(items.filter((_, j) => j !== i))} className="text-gray-500 hover:text-red-400 ml-0.5">
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

const CollapsibleSection = ({ title, children, defaultOpen = false }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-700/60 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-800/60 hover:bg-gray-700/60 transition-colors text-left"
      >
        <span className="text-sm font-semibold text-gray-300">{title}</span>
        {open ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
      </button>
      {open && <div className="p-4 space-y-4 bg-gray-800/20">{children}</div>}
    </div>
  );
};

// ─── Type-specific form sections ──────────────────────────────────────────────

const NpcForm = ({ f, set }) => (
  <div className="space-y-4">
    <FieldGroup label="Current Location">
      <TextInput value={f.at_location} onChange={v => set('at_location', v)} placeholder="e.g. The Rusty Flagon tavern" />
    </FieldGroup>

    <CollapsibleSection title="DM Sheet — Social Mechanics">
      <FieldGroup label="Speech Style">
        <TextInput value={f.speech_style} onChange={v => set('speech_style', v)} placeholder="e.g. speaks in riddles, heavy accent" />
      </FieldGroup>
      <FieldGroup label="Current Motivation">
        <TextInput value={f.current_motivation} onChange={v => set('current_motivation', v)} placeholder="What do they want right now?" />
      </FieldGroup>
      <div className="grid grid-cols-2 gap-3">
        <FieldGroup label="Trait">
          <TextInput value={f.trait} onChange={v => set('trait', v)} placeholder="Positive trait" />
        </FieldGroup>
        <FieldGroup label="Flaw">
          <TextInput value={f.flaw} onChange={v => set('flaw', v)} placeholder="Weakness or vice" />
        </FieldGroup>
      </div>
      <FieldGroup label="Mannerisms (up to 3)">
        <div className="space-y-1.5">
          {[0, 1, 2].map(i => (
            <TextInput key={i} value={f.mannerisms[i] || ''} onChange={v => {
              const next = [...f.mannerisms];
              next[i] = v;
              set('mannerisms', next);
            }} placeholder={`Mannerism ${i + 1}`} />
          ))}
        </div>
      </FieldGroup>

      <div>
        <Label>Social DCs (base values)</Label>
        <div className="grid grid-cols-2 gap-3 mt-1">
          {[['persuasion_dc', 'Persuasion'], ['deception_dc', 'Deception'], ['intimidation_dc', 'Intimidation'], ['insight_dc', 'Insight']].map(([key, label]) => (
            <div key={key} className="flex items-center gap-2">
              <span className="text-xs text-gray-400 w-24 shrink-0">{label}</span>
              <NumberInput value={f[key]} onChange={v => set(key, v)} min={5} max={30} placeholder="DC" />
            </div>
          ))}
        </div>
      </div>

      <FieldGroup label="Secrets">
        <TagList items={f.secrets} onChange={v => set('secrets', v)} placeholder="Add a secret (Enter)" />
      </FieldGroup>
      <FieldGroup label="Allegiances">
        <TagList items={f.allegiances} onChange={v => set('allegiances', v)} placeholder="Add an allegiance (Enter)" />
      </FieldGroup>
    </CollapsibleSection>
  </div>
);

const LocationForm = ({ f, set }) => (
  <div className="space-y-4">
    <FieldGroup label="Biome">
      <SelectInput value={f.biome} onChange={v => set('biome', v)} options={BIOMES} placeholder="— select biome —" />
    </FieldGroup>
  </div>
);

// Hierarchy tier builder for factions
const HierarchyBuilder = ({ tiers, onChange }) => {
  const add = () => onChange([...tiers, { role: '', function: '', min_level: 1, filled_by: '' }]);
  const remove = i => onChange(tiers.filter((_, j) => j !== i));
  const update = (i, key, val) => {
    const next = tiers.map((t, j) => j === i ? { ...t, [key]: val } : t);
    onChange(next);
  };
  return (
    <div className="space-y-2">
      {tiers.map((t, i) => (
        <div key={i} className="border border-gray-700/50 rounded-lg p-3 space-y-2 bg-gray-800/30">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400 font-semibold">Tier {i + 1}</span>
            <button type="button" onClick={() => remove(i)} className="text-gray-600 hover:text-red-400"><X className="w-3.5 h-3.5" /></button>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <TextInput value={t.role} onChange={v => update(i, 'role', v)} placeholder="Role (e.g. Lieutenant)" />
            <TextInput value={t.function} onChange={v => update(i, 'function', v)} placeholder="Function" />
          </div>
          <div className="flex gap-2">
            <div className="flex-1">
              <TextInput value={t.filled_by} onChange={v => update(i, 'filled_by', v)} placeholder="Filled by (NPC name)" />
            </div>
            <div className="w-20">
              <NumberInput value={t.min_level} onChange={v => update(i, 'min_level', v)} min={1} max={20} placeholder="Lvl" />
            </div>
          </div>
        </div>
      ))}
      <button type="button" onClick={add} className="w-full py-2 border border-dashed border-gray-600 rounded-lg text-gray-500 hover:text-gray-300 hover:border-gray-500 text-sm transition-colors flex items-center justify-center gap-1">
        <Plus className="w-4 h-4" /> Add Tier
      </button>
    </div>
  );
};

// Perk builder for factions
const PerkBuilder = ({ perks, onChange }) => {
  const add = () => onChange([...perks, { name: '', bonus: '', requirements: [] }]);
  const remove = i => onChange(perks.filter((_, j) => j !== i));
  const update = (i, key, val) => {
    const next = perks.map((p, j) => j === i ? { ...p, [key]: val } : p);
    onChange(next);
  };
  return (
    <div className="space-y-2">
      {perks.map((p, i) => (
        <div key={i} className="border border-gray-700/50 rounded-lg p-3 space-y-2 bg-gray-800/30">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400 font-semibold">Perk {i + 1}</span>
            <button type="button" onClick={() => remove(i)} className="text-gray-600 hover:text-red-400"><X className="w-3.5 h-3.5" /></button>
          </div>
          <TextInput value={p.name} onChange={v => update(i, 'name', v)} placeholder="Perk name" />
          <TextInput value={p.bonus} onChange={v => update(i, 'bonus', v)} placeholder="Bonus description (e.g. +2 Intimidation)" />
        </div>
      ))}
      <button type="button" onClick={add} className="w-full py-2 border border-dashed border-gray-600 rounded-lg text-gray-500 hover:text-gray-300 hover:border-gray-500 text-sm transition-colors flex items-center justify-center gap-1">
        <Plus className="w-4 h-4" /> Add Perk
      </button>
    </div>
  );
};

const FactionForm = ({ f, set }) => (
  <div className="space-y-4">
    <FieldGroup label="Purpose">
      <TextArea value={f.purpose} onChange={v => set('purpose', v)} placeholder="What does this faction exist to do?" rows={2} />
    </FieldGroup>

    <FieldGroup label="Values (what this faction attracts)">
      <TagList items={f.values} onChange={v => set('values', v)} placeholder="Add a value (Enter)" />
    </FieldGroup>

    <FieldGroup label="Tenets (social manipulation hooks)">
      <TagList items={f.tenets} onChange={v => set('tenets', v)} placeholder="Add a tenet (Enter)" />
    </FieldGroup>

    <CollapsibleSection title="Resources">
      <div className="grid grid-cols-2 gap-3">
        <FieldGroup label="Income (gp/month)">
          <NumberInput value={f.income_gp} onChange={v => set('income_gp', v)} placeholder="0" />
        </FieldGroup>
        <FieldGroup label="Treasury (gp)">
          <NumberInput value={f.treasury_gp} onChange={v => set('treasury_gp', v)} placeholder="0" />
        </FieldGroup>
        <FieldGroup label="Recruitment Rate">
          <NumberInput value={f.recruitment_rate} onChange={v => set('recruitment_rate', v)} placeholder="0" />
        </FieldGroup>
        <FieldGroup label="Reputation">
          <NumberInput value={f.reputation} onChange={v => set('reputation', Math.max(-100, Math.min(100, v)))} min={-100} max={100} placeholder="0" />
        </FieldGroup>
      </div>
      <FieldGroup label="Hideout">
        <TextInput value={f.hideout} onChange={v => set('hideout', v)} placeholder="e.g. Sewers beneath the merchant quarter" />
      </FieldGroup>
      <FieldGroup label="Controlled Areas">
        <TagList items={f.controlled_areas} onChange={v => set('controlled_areas', v)} placeholder="Add an area (Enter)" />
      </FieldGroup>
      <FieldGroup label="Important Items">
        <TagList items={f.important_items} onChange={v => set('important_items', v)} placeholder="Add an item (Enter)" />
      </FieldGroup>
    </CollapsibleSection>

    <CollapsibleSection title="Hierarchy">
      <HierarchyBuilder tiers={f.hierarchy} onChange={v => set('hierarchy', v)} />
    </CollapsibleSection>

    <CollapsibleSection title="Tier Perks">
      <PerkBuilder perks={f.tier_perks} onChange={v => set('tier_perks', v)} />
    </CollapsibleSection>
  </div>
);

// Bonus pair builder for equipment items
const BonusBuilder = ({ bonuses, onChange }) => {
  const add = () => onChange([...bonuses, { check: '', modifier: 1 }]);
  const remove = i => onChange(bonuses.filter((_, j) => j !== i));
  const update = (i, key, val) => {
    const next = bonuses.map((b, j) => j === i ? { ...b, [key]: val } : b);
    onChange(next);
  };
  return (
    <div className="space-y-2">
      {bonuses.map((b, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="flex-1">
            <SelectInput value={b.check} onChange={v => update(i, 'check', v)} options={SKILLS_LIST} placeholder="Skill / check" />
          </div>
          <div className="w-24">
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">+</span>
              <input
                type="number"
                value={b.modifier}
                onChange={e => update(i, 'modifier', Number(e.target.value))}
                min={-10}
                max={20}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-7 pr-2 py-2 text-sm text-white focus:outline-none focus:border-gray-500"
              />
            </div>
          </div>
          <button type="button" onClick={() => remove(i)} className="text-gray-600 hover:text-red-400 shrink-0"><X className="w-4 h-4" /></button>
        </div>
      ))}
      <button type="button" onClick={add} className="w-full py-2 border border-dashed border-gray-600 rounded-lg text-gray-500 hover:text-gray-300 hover:border-gray-500 text-sm transition-colors flex items-center justify-center gap-1">
        <Plus className="w-4 h-4" /> Add Bonus
      </button>
    </div>
  );
};

const ItemForm = ({ f, set }) => {
  const isEquipment = f.item_type === 'equipment';
  const isStackable = ['consumable', 'material', 'currency'].includes(f.item_type);

  return (
    <div className="space-y-4">
      <FieldGroup label="Item Type">
        <div className="flex gap-2 flex-wrap">
          {ITEM_TYPES.map(t => (
            <button
              key={t}
              type="button"
              onClick={() => set('item_type', t)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium capitalize transition-colors ${
                f.item_type === t
                  ? 'bg-orange-600 text-white'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-gray-200'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </FieldGroup>

      {isEquipment && (
        <>
          <FieldGroup label="Equip Slot">
            <SelectInput value={f.equip_slot} onChange={v => set('equip_slot', v)} options={EQUIP_SLOTS} placeholder="— select slot —" />
          </FieldGroup>
          <FieldGroup label="Bonuses">
            <BonusBuilder bonuses={f.grants_bonus} onChange={v => set('grants_bonus', v)} />
          </FieldGroup>
        </>
      )}

      {isStackable && (
        <FieldGroup label="Quantity">
          <NumberInput value={f.quantity} onChange={v => set('quantity', Math.max(1, v))} min={1} placeholder="1" />
        </FieldGroup>
      )}
    </div>
  );
};

const SpellForm = ({ f, set }) => (
  <div className="space-y-4">
    <FieldGroup label="Spell Level">
      <SelectInput
        value={f.spell_level}
        onChange={v => set('spell_level', v)}
        options={[
          { key: '0', label: 'Cantrip' },
          ...Array.from({ length: 9 }, (_, i) => ({ key: String(i + 1), label: `Level ${i + 1}` })),
        ]}
        placeholder="— select level —"
      />
    </FieldGroup>
    <FieldGroup label="School of Magic">
      <SelectInput
        value={f.school}
        onChange={v => set('school', v)}
        options={['abjuration', 'conjuration', 'divination', 'enchantment', 'evocation', 'illusion', 'necromancy', 'transmutation']}
        placeholder="— select school —"
      />
    </FieldGroup>
  </div>
);

const QuestForm = ({ f, set }) => (
  <div className="space-y-4">
    <FieldGroup label="Quest Status">
      <SelectInput
        value={f.quest_status}
        onChange={v => set('quest_status', v)}
        options={[
          { key: 'active', label: 'Active' },
          { key: 'completed', label: 'Completed' },
          { key: 'failed', label: 'Failed' },
          { key: 'abandoned', label: 'Abandoned' },
        ]}
        placeholder="— select status —"
      />
    </FieldGroup>
    <FieldGroup label="Quest Giver">
      <TextInput value={f.quest_giver} onChange={v => set('quest_giver', v)} placeholder="Who gave this quest?" />
    </FieldGroup>
  </div>
);

// ─── Default form state per type ─────────────────────────────────────────────

const DEFAULT_FIELDS = {
  npc: {
    at_location: '', speech_style: '', current_motivation: '',
    trait: '', flaw: '', mannerisms: ['', '', ''],
    persuasion_dc: 12, deception_dc: 14, intimidation_dc: 13, insight_dc: 11,
    secrets: [], allegiances: [],
  },
  location: { biome: '' },
  faction: {
    purpose: '', values: [], tenets: [],
    income_gp: 0, treasury_gp: 0, recruitment_rate: 0, reputation: 0,
    hideout: '', controlled_areas: [], important_items: [],
    hierarchy: [], tier_perks: [],
  },
  item: { item_type: 'equipment', equip_slot: '', grants_bonus: [], quantity: 1 },
  spell: { spell_level: '', school: '' },
  quest: { quest_status: 'active', quest_giver: '' },
  favor: {},
  curse: {},
};

// ─── Payload builder ─────────────────────────────────────────────────────────

function buildPayload(type, common, fields) {
  const base = {
    type,
    title: common.title.trim(),
    content: common.content.trim(),
  };

  switch (type) {
    case 'npc': {
      const dmSheet = {
        speech_style: fields.speech_style || undefined,
        current_motivation: fields.current_motivation || undefined,
        trait: fields.trait || undefined,
        flaw: fields.flaw || undefined,
        mannerisms: fields.mannerisms.filter(Boolean),
      };
      const baseDcs = {
        persuasion: fields.persuasion_dc || 12,
        deception: fields.deception_dc || 14,
        intimidation: fields.intimidation_dc || 13,
        insight: fields.insight_dc || 11,
      };
      return {
        ...base,
        at_location: fields.at_location || undefined,
        dm_sheet: dmSheet,
        base_stats: { social_dcs: baseDcs },
        secrets: fields.secrets,
        allegiances: fields.allegiances,
      };
    }

    case 'location':
      return { ...base, biome: fields.biome || undefined };

    case 'faction': {
      const resources = {
        income_gp: fields.income_gp || 0,
        treasury_gp: fields.treasury_gp || 0,
        recruitment_rate: fields.recruitment_rate || 0,
        hideout: fields.hideout || '',
        controlled_areas: fields.controlled_areas,
        important_items: fields.important_items,
      };
      return {
        ...base,
        purpose: fields.purpose || '',
        values: fields.values,
        tenets: fields.tenets,
        reputation: fields.reputation || 0,
        hierarchy: fields.hierarchy,
        tier_perks: fields.tier_perks,
        resources,
        known_members: [],
      };
    }

    case 'item': {
      const isEquipment = fields.item_type === 'equipment';
      const isStackable = ['consumable', 'material', 'currency'].includes(fields.item_type);
      return {
        ...base,
        item_type: fields.item_type,
        equip_slot: isEquipment ? (fields.equip_slot || undefined) : undefined,
        grants_bonus: isEquipment ? fields.grants_bonus : [],
        quantity: isStackable ? (fields.quantity || 1) : undefined,
        status: 'acquired',
      };
    }

    case 'spell':
      return {
        ...base,
        spell_level: fields.spell_level ? Number(fields.spell_level) : undefined,
        school: fields.school || undefined,
        status: 'known',
      };

    case 'quest':
      return {
        ...base,
        status: fields.quest_status || 'active',
        quest_giver: fields.quest_giver || undefined,
      };

    default:
      return base;
  }
}

// Preview data — what KnowledgeCard needs to render the card visually
function buildPreviewData(type, common, fields) {
  const base = {
    id: 'preview',
    type,
    title: common.title || 'Untitled',
    content: common.content || '',
    is_new: false,
  };

  if (type === 'location') {
    const biome = BIOMES.find(b => b.key === fields.biome);
    if (biome && fields.biome) {
      // Map biome key to accent gradient (mirrors biomes.py)
      const BIOME_ACCENTS = {
        forest: 'from-emerald-600 to-emerald-800',
        plains: 'from-yellow-500 to-amber-700',
        desert: 'from-amber-500 to-orange-700',
        mountain: 'from-stone-500 to-stone-800',
        swamp: 'from-teal-700 to-emerald-900',
        coast: 'from-sky-500 to-cyan-800',
        tundra: 'from-cyan-300 to-blue-700',
        underdark: 'from-purple-700 to-fuchsia-900',
        volcanic: 'from-red-600 to-orange-800',
        urban: 'from-slate-500 to-slate-800',
        fey: 'from-pink-500 to-fuchsia-700',
        shadow: 'from-zinc-700 to-zinc-900',
      };
      return { ...base, biome: fields.biome, biome_label: biome.label, biome_accent: BIOME_ACCENTS[fields.biome] };
    }
  }

  if (type === 'item') {
    return {
      ...base,
      item_type: fields.item_type,
      equip_slot: fields.equip_slot,
      grants_bonus: fields.grants_bonus,
      quantity: fields.quantity,
      status: 'acquired',
    };
  }

  if (type === 'faction') {
    return {
      ...base,
      reputation: fields.reputation || 0,
      tier_perks: fields.tier_perks,
      hierarchy: fields.hierarchy,
      resources: { controlled_areas: fields.controlled_areas },
      known_members: [],
    };
  }

  if (type === 'spell') {
    return { ...base, spell_level: fields.spell_level, school: fields.school, status: 'known' };
  }

  if (type === 'quest') {
    return { ...base, status: fields.quest_status || 'active' };
  }

  return base;
}

// ─── Main modal component ─────────────────────────────────────────────────────

export default function CardCreationModal({ campaignId, onClose, onCardCreated }) {
  const [selectedType, setSelectedType] = useState('npc');
  const [common, setCommon] = useState({ title: '', content: '' });
  const [fields, setFields] = useState(DEFAULT_FIELDS.npc);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const setCommonField = useCallback((key, val) => setCommon(prev => ({ ...prev, [key]: val })), []);

  const handleTypeChange = useCallback(type => {
    setSelectedType(type);
    setFields(DEFAULT_FIELDS[type] || {});
    setError(null);
  }, []);

  const setField = useCallback((key, val) => setFields(prev => ({ ...prev, [key]: val })), []);

  const previewData = useMemo(
    () => buildPreviewData(selectedType, common, fields),
    [selectedType, common, fields],
  );

  // Map selectedType to the normalized type KnowledgeCard expects
  const previewCardType = {
    npc: 'npcs', location: 'locations', faction: 'factions',
    item: 'items', spell: 'spells', quest: 'quests',
    favor: 'favors', curse: 'curses',
  }[selectedType] || selectedType;

  const handleSubmit = async () => {
    if (!common.title.trim()) { setError("Title is required."); return; }
    setSaving(true);
    setError(null);
    try {
      const payload = buildPayload(selectedType, common, fields);
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/cards`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      const created = await res.json();
      onCardCreated?.(created);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create card.');
    } finally {
      setSaving(false);
    }
  };

  const typeConfig = CARD_TYPES.find(t => t.key === selectedType);

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 shrink-0">
          <div>
            <h2 className="text-lg font-bold text-white">Create Card</h2>
            <p className="text-xs text-gray-500 mt-0.5">DM tool — card appears immediately in the campaign deck</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg text-gray-500 hover:text-white hover:bg-gray-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Type Selector */}
        <div className="px-6 py-3 border-b border-gray-800 shrink-0">
          <div className="flex flex-wrap gap-2">
            {CARD_TYPES.map(t => (
              <button
                key={t.key}
                type="button"
                onClick={() => handleTypeChange(t.key)}
                className={`px-3.5 py-1.5 rounded-full text-sm font-semibold transition-all ${
                  selectedType === t.key
                    ? `bg-gradient-to-r ${t.color} text-white shadow-lg ring-2 ${t.ring}/50`
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Body — two columns */}
        <div className="flex flex-1 overflow-hidden">

          {/* Left — form */}
          <div className="flex-1 overflow-y-auto p-6 space-y-5 border-r border-gray-800">

            {/* Common fields */}
            <FieldGroup label="Title *">
              <TextInput
                value={common.title}
                onChange={v => setCommonField('title', v)}
                placeholder={`${typeConfig?.label || 'Card'} name…`}
                className="text-base"
              />
            </FieldGroup>

            <FieldGroup label="Description / Notes">
              <TextArea
                value={common.content}
                onChange={v => setCommonField('content', v)}
                placeholder="What the player knows about this card…"
                rows={4}
              />
            </FieldGroup>

            <Divider />

            {/* Type-specific fields */}
            {selectedType === 'npc'      && <NpcForm      f={fields} set={setField} />}
            {selectedType === 'location' && <LocationForm  f={fields} set={setField} />}
            {selectedType === 'faction'  && <FactionForm   f={fields} set={setField} />}
            {selectedType === 'item'     && <ItemForm      f={fields} set={setField} />}
            {selectedType === 'spell'    && <SpellForm     f={fields} set={setField} />}
            {selectedType === 'quest'    && <QuestForm     f={fields} set={setField} />}
            {(selectedType === 'favor' || selectedType === 'curse') && (
              <p className="text-xs text-gray-500 italic">No extra fields for this card type. Fill in the description above.</p>
            )}

            {error && (
              <div className="rounded-lg bg-red-900/30 border border-red-700/50 px-4 py-2.5 text-sm text-red-300">
                {error}
              </div>
            )}
          </div>

          {/* Right — live preview */}
          <div className="w-60 shrink-0 flex flex-col items-center justify-start p-6 gap-4 bg-gray-950/50">
            <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold self-start">Preview</span>
            <div className="w-full max-w-[180px]">
              <KnowledgeCard
                data={previewData}
                type={previewCardType}
                isSelected={false}
                isPinned={false}
                onSelect={() => {}}
                campaignId={campaignId}
              />
            </div>
            <p className="text-[10px] text-gray-600 text-center leading-relaxed">
              Card updates as you type
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-800 shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={saving || !common.title.trim()}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all bg-gradient-to-r ${typeConfig?.color || 'from-gray-600 to-gray-700'} text-white disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 shadow-lg`}
          >
            {saving ? 'Creating…' : `Create ${typeConfig?.label || 'Card'}`}
          </button>
        </div>
      </div>
    </div>
  );
}
