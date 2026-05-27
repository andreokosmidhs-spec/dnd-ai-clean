import React from 'react';

const TONES = [
  { id: 'balanced', label: 'Balanced',  icon: '⚖️', desc: 'Classic D&D — adventurous and immersive' },
  { id: 'heroic',   label: 'Heroic',    icon: '⚔️', desc: 'Epic deeds, soaring stakes, legends born' },
  { id: 'gritty',   label: 'Gritty',    icon: '🩸', desc: 'Dark realism — wounds hurt, victory costs' },
  { id: 'dark',     label: 'Dark',      icon: '🌑', desc: 'Gothic dread, shadows, moral ambiguity' },
  { id: 'comedic',  label: 'Comedic',   icon: '🎭', desc: 'Witty and playful, absurdist moments welcome' },
];

const FREE_TONES = ['balanced', 'heroic'];

export default function ToneSelector({ value, onChange, plan = 'free' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {TONES.map(tone => {
        const locked = plan === 'free' && !FREE_TONES.includes(tone.id);
        const active  = value === tone.id;
        return (
          <button
            key={tone.id}
            onClick={() => !locked && onChange(tone.id)}
            disabled={locked}
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 12px',
              borderRadius: 8,
              border: `1.5px solid ${active ? '#f59e0b' : 'rgba(255,255,255,0.1)'}`,
              background: active ? 'rgba(245,158,11,0.12)' : 'rgba(255,255,255,0.03)',
              cursor: locked ? 'default' : 'pointer',
              opacity: locked ? 0.45 : 1,
              textAlign: 'left',
              transition: 'all 0.15s',
            }}
          >
            <span style={{ fontSize: 18, width: 24, textAlign: 'center' }}>{tone.icon}</span>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ color: active ? '#f59e0b' : '#e5e7eb', fontWeight: 600, fontSize: 13 }}>
                  {tone.label}
                </span>
                {locked && (
                  <span style={{
                    fontSize: 9, fontWeight: 700, textTransform: 'uppercase',
                    color: '#6b7280', border: '1px solid #374151',
                    borderRadius: 3, padding: '1px 4px', letterSpacing: '0.05em',
                  }}>
                    Adventurer+
                  </span>
                )}
              </div>
              <span style={{ color: '#6b7280', fontSize: 11 }}>{tone.desc}</span>
            </div>
            {active && <span style={{ color: '#f59e0b', fontSize: 14 }}>✓</span>}
          </button>
        );
      })}
    </div>
  );
}
