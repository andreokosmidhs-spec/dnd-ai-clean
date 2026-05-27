import React from 'react';
import { Sword, Shield, Dices } from 'lucide-react';

const HIT_DICE = {
  barbarian: 12, fighter: 10, paladin: 10, ranger: 10,
  bard: 8, cleric: 8, druid: 8, monk: 8, rogue: 8, warlock: 8,
  sorcerer: 6, wizard: 6,
};

const CONDITION_COLORS = {
  poisoned:   { bg: 'rgba(74,124,27,0.25)',  border: 'rgba(132,204,22,0.45)', text: '#a3e635' },
  frightened: { bg: 'rgba(120,53,15,0.25)',  border: 'rgba(234,179,8,0.45)',  text: '#fbbf24' },
  stunned:    { bg: 'rgba(88,28,135,0.25)',  border: 'rgba(168,85,247,0.45)', text: '#c084fc' },
  charmed:    { bg: 'rgba(131,24,67,0.25)',  border: 'rgba(244,114,182,0.45)',text: '#f472b6' },
  exhausted:  { bg: 'rgba(55,65,81,0.35)',   border: 'rgba(156,163,175,0.4)', text: '#9ca3af' },
  fatigued:   { bg: 'rgba(55,65,81,0.35)',   border: 'rgba(156,163,175,0.4)', text: '#9ca3af' },
};

function conditionStyle(name) {
  return CONDITION_COLORS[name.toLowerCase()] || {
    bg: 'rgba(55,65,81,0.35)', border: 'rgba(156,163,175,0.35)', text: '#9ca3af',
  };
}

function SpellSlotPips({ level, remaining, max }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
      <span style={{ color: '#6b7280', fontSize: 10, minWidth: 10 }}>{level}</span>
      <div style={{ display: 'flex', gap: 2 }}>
        {Array.from({ length: max }).map((_, i) => (
          <span
            key={i}
            style={{
              width: 8, height: 8,
              borderRadius: '50%',
              background: i < remaining ? '#60a5fa' : 'transparent',
              border: `1.5px solid ${i < remaining ? '#3b82f6' : '#374151'}`,
              display: 'inline-block',
              transition: 'background 0.2s',
            }}
          />
        ))}
      </div>
    </div>
  );
}

function RestPips({ remaining, total = 2 }) {
  return (
    <div style={{ display: 'flex', gap: 3 }}>
      {Array.from({ length: total }).map((_, i) => (
        <span
          key={i}
          style={{
            width: 8, height: 8,
            borderRadius: '50%',
            background: i < remaining ? '#2dd4bf' : 'transparent',
            border: `1.5px solid ${i < remaining ? '#14b8a6' : '#374151'}`,
            display: 'inline-block',
            transition: 'background 0.2s',
          }}
        />
      ))}
    </div>
  );
}

const CombatHUD = ({ characterState, combatState }) => {
  if (!characterState) return null;

  // ── HP ────────────────────────────────────────────────────────────────────
  const playerHP    = characterState.hp?.current ?? characterState.hp ?? 10;
  const playerMaxHP = characterState.hp?.max ?? characterState.max_hp ?? 10;
  const hpPercent   = Math.max(0, Math.min(100, (playerHP / playerMaxHP) * 100));

  const getHPColor = (pct) => pct > 60 ? '#22c55e' : pct > 30 ? '#eab308' : '#ef4444';

  // ── XP / Level ───────────────────────────────────────────────────────────
  const level    = characterState.level || 1;
  const currentXP = characterState.current_xp || 0;
  const xpToNext  = characterState.xp_to_next || 100;
  const xpPercent = xpToNext > 0 ? Math.min(100, (currentXP / xpToNext) * 100) : 100;

  // ── Spell slots ───────────────────────────────────────────────────────────
  const rawSlots    = characterState.spell_slots || {};
  const rawMax      = characterState.spell_slots_max || {};
  const slotEntries = Object.keys(rawSlots)
    .map(k => parseInt(k, 10))
    .filter(lvl => !isNaN(lvl))
    .sort((a, b) => a - b)
    .map(lvl => ({
      level: lvl,
      remaining: rawSlots[lvl] ?? 0,
      max: rawMax[lvl] ?? rawSlots[lvl] ?? 0,
    }))
    .filter(e => e.max > 0);

  // ── Hit dice ──────────────────────────────────────────────────────────────
  const cls             = (characterState.class || '').toLowerCase();
  const hitDieSize      = HIT_DICE[cls] || 8;
  const hitDiceMax      = characterState.hit_dice_max ?? level;
  const hitDiceRemain   = characterState.hit_dice_remaining ?? level;

  // ── Short rests ───────────────────────────────────────────────────────────
  const shortRestsTaken  = characterState.short_rests_taken ?? 0;
  const shortRestsRemain = Math.max(0, 2 - shortRestsTaken);

  // ── Conditions ────────────────────────────────────────────────────────────
  const conditions = (characterState.conditions || []).filter(Boolean);

  // ── Combat enemies ────────────────────────────────────────────────────────
  const enemies      = combatState?.enemies || [];
  const aliveEnemies = enemies.filter(e => e.hp > 0);
  const isInCombat   = !!combatState;

  const borderColor = isInCombat ? '#7f1d1d' : 'rgba(180,130,60,0.2)';
  const headerColor = isInCombat ? '#f87171' : '#a78bfa';

  return (
    <div style={{
      background: 'rgba(10,10,18,0.92)',
      border: `1.5px solid ${borderColor}`,
      borderRadius: 10,
      padding: '12px 14px',
      marginBottom: 8,
      boxShadow: isInCombat ? '0 0 12px rgba(239,68,68,0.15)' : 'none',
    }}>

      {/* ── Combat header ──────────────────────────────────────────────────── */}
      {isInCombat && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          marginBottom: 10, paddingBottom: 8,
          borderBottom: '1px solid rgba(127,29,29,0.6)',
        }}>
          <Sword size={16} color="#ef4444" />
          <span style={{ color: '#f87171', fontWeight: 700, fontSize: 14, letterSpacing: '0.05em' }}>
            ⚔️ COMBAT
          </span>
          <span style={{ marginLeft: 'auto', color: '#6b7280', fontSize: 12 }}>
            Round {combatState.round || 1}
          </span>
        </div>
      )}

      {/* ── Player status row ─────────────────────────────────────────────── */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Shield size={14} color="#60a5fa" />
            <span style={{ color: '#f3f4f6', fontWeight: 600, fontSize: 13 }}>
              {characterState.name || 'You'}
            </span>
            <span style={{ color: '#a78bfa', fontSize: 11, fontWeight: 700 }}>Lv{level}</span>
          </div>
          <span style={{ color: '#d1d5db', fontSize: 12 }}>
            {playerHP}<span style={{ color: '#4b5563' }}>/{playerMaxHP}</span> HP
          </span>
        </div>

        {/* HP bar */}
        <div style={{ width: '100%', background: '#1f2937', borderRadius: 6, height: 10, overflow: 'hidden', marginBottom: 6 }}>
          <div style={{
            height: '100%',
            width: `${hpPercent}%`,
            background: getHPColor(hpPercent),
            borderRadius: 6,
            transition: 'width 0.3s, background 0.3s',
          }} />
        </div>

        {/* XP bar */}
        {xpToNext > 0 && (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
              <span style={{ color: '#7c3aed', fontSize: 10 }}>XP</span>
              <span style={{ color: '#7c3aed', fontSize: 10 }}>{currentXP}/{xpToNext}</span>
            </div>
            <div style={{ width: '100%', background: '#1f2937', borderRadius: 6, height: 6, overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                width: `${xpPercent}%`,
                background: '#7c3aed',
                borderRadius: 6,
                transition: 'width 0.3s',
              }} />
            </div>
          </>
        )}
      </div>

      {/* ── Resources ─────────────────────────────────────────────────────── */}
      <div style={{
        paddingTop: 10,
        borderTop: '1px solid rgba(55,65,81,0.7)',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}>

        {/* Spell slots */}
        {slotEntries.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            <span style={{ color: '#60a5fa', fontSize: 11, minWidth: 16 }}>✦</span>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {slotEntries.map(e => (
                <SpellSlotPips key={e.level} {...e} />
              ))}
            </div>
            <span style={{ color: '#374151', fontSize: 10, marginLeft: 2 }}>slots</span>
          </div>
        )}

        {/* Hit dice + Short rests */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <Dices size={12} color="#f59e0b" />
            <span style={{ color: '#9ca3af', fontSize: 11 }}>
              d{hitDieSize}
            </span>
            <span style={{ color: '#f59e0b', fontSize: 11, fontWeight: 600 }}>
              {hitDiceRemain}
            </span>
            <span style={{ color: '#374151', fontSize: 10 }}>/{hitDiceMax}</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ fontSize: 12 }}>🌙</span>
            <RestPips remaining={shortRestsRemain} />
            <span style={{ color: '#374151', fontSize: 10 }}>rests</span>
          </div>
        </div>

        {/* Conditions */}
        {conditions.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {conditions.map(c => {
              const cs = conditionStyle(c);
              return (
                <span key={c} style={{
                  fontSize: 10,
                  fontWeight: 600,
                  textTransform: 'capitalize',
                  padding: '2px 7px',
                  borderRadius: 4,
                  background: cs.bg,
                  border: `1px solid ${cs.border}`,
                  color: cs.text,
                  letterSpacing: '0.04em',
                }}>
                  {c}
                </span>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Enemies ───────────────────────────────────────────────────────── */}
      {isInCombat && (
        <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid rgba(127,29,29,0.4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
            <Sword size={13} color="#f87171" />
            <span style={{ color: '#9ca3af', fontSize: 12, fontWeight: 600 }}>Enemies</span>
          </div>

          {aliveEnemies.length === 0 ? (
            <p style={{ color: '#6b7280', fontSize: 12, fontStyle: 'italic' }}>No enemies remaining</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {aliveEnemies.map((enemy, idx) => (
                <div key={enemy.id || idx} style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '4px 8px',
                  background: 'rgba(31,41,55,0.5)',
                  borderRadius: 6,
                  borderLeft: '2px solid rgba(239,68,68,0.5)',
                }}>
                  <span style={{ color: '#fca5a5', fontSize: 12, fontWeight: 600 }}>{enemy.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Combat tip ────────────────────────────────────────────────────── */}
      {isInCombat && (
        <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(55,65,81,0.5)' }}>
          <p style={{ color: '#4b5563', fontSize: 11, fontStyle: 'italic' }}>
            💡 Type your combat action or click an option below
          </p>
        </div>
      )}
    </div>
  );
};

export default CombatHUD;
