import React, { useState, useCallback } from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const RARITY_STYLES = {
  common:    { border: '#9d9d9d', glow: 'rgba(157,157,157,0.3)', label: '#c6c6c6' },
  uncommon:  { border: '#1eff00', glow: 'rgba(30,255,0,0.3)',   label: '#1eff00' },
  rare:      { border: '#0070ff', glow: 'rgba(0,112,255,0.35)', label: '#4da6ff' },
  epic:      { border: '#a335ee', glow: 'rgba(163,53,238,0.35)', label: '#c78fff' },
  legendary: { border: '#ff8000', glow: 'rgba(255,128,0,0.35)', label: '#ffa04d' },
};

function rarityStyle(rarity) {
  return RARITY_STYLES[rarity] || RARITY_STYLES.common;
}

function ItemCard({ item, selected, onToggle, disabled }) {
  const rs = rarityStyle(item.rarity);
  return (
    <div
      onClick={() => !disabled && onToggle(item.name)}
      style={{
        cursor: disabled ? 'default' : 'pointer',
        border: `1px solid ${selected ? rs.border : '#3a3a4a'}`,
        borderRadius: 8,
        padding: '10px 12px',
        background: selected ? `rgba(20,20,30,0.9)` : 'rgba(10,10,18,0.7)',
        boxShadow: selected ? `0 0 8px ${rs.glow}` : 'none',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
        transition: 'all 0.15s ease',
        userSelect: 'none',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ color: '#e8e0d4', fontWeight: 600, fontSize: 13 }}>{item.name}</span>
        <span style={{
          fontSize: 10,
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          color: rs.label,
        }}>
          {item.rarity}
        </span>
      </div>
      {item.description && (
        <span style={{ color: '#8a8090', fontSize: 11, lineHeight: 1.4 }}>{item.description}</span>
      )}
      <div style={{ display: 'flex', gap: 8, marginTop: 2 }}>
        {item.type && (
          <span style={{ fontSize: 10, color: '#5a5570', textTransform: 'capitalize' }}>{item.type}</span>
        )}
        {item.value > 0 && (
          <span style={{ fontSize: 10, color: '#c89b3c' }}>{item.value} gp</span>
        )}
        {item.damage_die && (
          <span style={{ fontSize: 10, color: '#7a90c0' }}>{item.damage_die} {item.damage_type}</span>
        )}
        {item.magic_bonus > 0 && (
          <span style={{ fontSize: 10, color: '#c080ff' }}>+{item.magic_bonus} magic</span>
        )}
      </div>
      {!disabled && (
        <div style={{
          marginTop: 4,
          fontSize: 10,
          color: selected ? rs.label : '#444',
          display: 'flex',
          alignItems: 'center',
          gap: 4,
        }}>
          <span style={{
            width: 12, height: 12,
            border: `1px solid ${selected ? rs.border : '#444'}`,
            borderRadius: 2,
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: selected ? rs.border : 'transparent',
            fontSize: 9,
          }}>
            {selected ? '✓' : ''}
          </span>
          {selected ? 'Selected' : 'Click to select'}
        </div>
      )}
    </div>
  );
}

function EnemyLootSection({ lootEntry, selectedItems, onToggle, disabled }) {
  const allItems = [...(lootEntry.guaranteed || []), ...(lootEntry.hidden || [])];
  if (allItems.length === 0 && !lootEntry.gold) return null;

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{
        fontSize: 12,
        fontWeight: 700,
        color: '#c89b3c',
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
        marginBottom: 8,
        borderBottom: '1px solid #2a2030',
        paddingBottom: 4,
      }}>
        {lootEntry.enemy_name || 'Enemy'}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {allItems.map((item, i) => (
          <ItemCard
            key={`${item.name}-${i}`}
            item={item}
            selected={selectedItems.has(item.name)}
            onToggle={onToggle}
            disabled={disabled}
          />
        ))}
        {lootEntry.gold > 0 && (
          <div style={{
            fontSize: 12,
            color: '#c89b3c',
            padding: '6px 12px',
            background: 'rgba(200,155,60,0.08)',
            borderRadius: 6,
            border: '1px solid rgba(200,155,60,0.25)',
          }}>
            💰 {lootEntry.gold} gold pieces
          </div>
        )}
        {lootEntry.searched && lootEntry.investigation_total !== undefined && (
          <div style={{ fontSize: 10, color: '#5a5570', paddingLeft: 2 }}>
            Investigation: {lootEntry.investigation_total} (DC {lootEntry.investigation_dc})
            {lootEntry.hidden?.length > 0 && ' — hidden items found!'}
          </div>
        )}
      </div>
    </div>
  );
}

export default function LootPanel({ pendingLoot, campaignId, characterId, onClose }) {
  const [selectedItems, setSelectedItems] = useState(() => {
    const all = new Set();
    pendingLoot?.forEach(entry => {
      [...(entry.guaranteed || []), ...(entry.hidden || [])].forEach(item => all.add(item.name));
    });
    return all;
  });
  const [taking, setTaking] = useState(false);
  const [done, setDone] = useState(false);
  const [result, setResult] = useState(null);

  const totalGold = pendingLoot?.reduce((s, e) => s + (e.gold || 0), 0) || 0;
  const allItems = pendingLoot?.flatMap(e => [...(e.guaranteed || []), ...(e.hidden || [])]) || [];

  const toggleItem = useCallback((name) => {
    setSelectedItems(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelectedItems(new Set(allItems.map(i => i.name)));
  }, [allItems]);

  const deselectAll = useCallback(() => {
    setSelectedItems(new Set());
  }, []);

  const handleTake = useCallback(async (takeAll) => {
    if (taking) return;
    setTaking(true);
    try {
      const body = {
        character_id: characterId,
        take_item_names: takeAll ? null : [...selectedItems],
      };
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/combat/take-loot`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        }
      );
      const data = await res.json();
      if (data.ok) {
        setResult({ items: data.items_added, gold: data.gold_added });
        setDone(true);
      }
    } catch (e) {
      console.error('take-loot failed:', e);
    } finally {
      setTaking(false);
    }
  }, [taking, characterId, campaignId, selectedItems]);

  const hasLoot = allItems.length > 0 || totalGold > 0;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.85)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
    }}>
      <div style={{
        background: 'linear-gradient(160deg, #12101a 0%, #1a1520 100%)',
        border: '1px solid #3a2a50',
        borderRadius: 12,
        width: 480,
        maxWidth: '95vw',
        maxHeight: '85vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 8px 40px rgba(0,0,0,0.8)',
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid #2a2030',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#e8dfc8', letterSpacing: '0.03em' }}>
              ⚔️ Victory — Claim Your Spoils
            </div>
            {!done && hasLoot && (
              <div style={{ fontSize: 11, color: '#7a7080', marginTop: 2 }}>
                Select items to take, then confirm
              </div>
            )}
          </div>
          {done && (
            <button
              onClick={onClose}
              style={{
                background: '#2a4020',
                border: '1px solid #4a7040',
                borderRadius: 6,
                color: '#80c060',
                padding: '6px 14px',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              Continue
            </button>
          )}
        </div>

        {/* Body */}
        <div style={{ overflowY: 'auto', flex: 1, padding: '16px 20px' }}>
          {done ? (
            <div style={{ textAlign: 'center', padding: '24px 0' }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>🎒</div>
              <div style={{ color: '#c89b3c', fontSize: 16, fontWeight: 700, marginBottom: 8 }}>
                Loot Added to Inventory
              </div>
              {result?.items?.length > 0 && (
                <div style={{ color: '#9080a0', fontSize: 13, marginBottom: 6 }}>
                  {result.items.join(', ')}
                </div>
              )}
              {result?.gold > 0 && (
                <div style={{ color: '#c89b3c', fontSize: 14, fontWeight: 600 }}>
                  +{result.gold} gold pieces
                </div>
              )}
            </div>
          ) : !hasLoot ? (
            <div style={{ textAlign: 'center', padding: '24px 0', color: '#5a5570', fontSize: 13 }}>
              No loot found.
            </div>
          ) : (
            <>
              {pendingLoot?.map((entry, i) => (
                <EnemyLootSection
                  key={entry.enemy_id || i}
                  lootEntry={entry}
                  selectedItems={selectedItems}
                  onToggle={toggleItem}
                  disabled={taking}
                />
              ))}
            </>
          )}
        </div>

        {/* Footer */}
        {!done && hasLoot && (
          <div style={{
            padding: '12px 20px',
            borderTop: '1px solid #2a2030',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  onClick={selectAll}
                  disabled={taking}
                  style={{
                    background: 'transparent',
                    border: '1px solid #3a3050',
                    borderRadius: 4,
                    color: '#7a7090',
                    padding: '4px 10px',
                    cursor: 'pointer',
                    fontSize: 11,
                  }}
                >
                  All
                </button>
                <button
                  onClick={deselectAll}
                  disabled={taking}
                  style={{
                    background: 'transparent',
                    border: '1px solid #3a3050',
                    borderRadius: 4,
                    color: '#7a7090',
                    padding: '4px 10px',
                    cursor: 'pointer',
                    fontSize: 11,
                  }}
                >
                  None
                </button>
              </div>
              <div style={{ color: '#c89b3c', fontSize: 12 }}>
                {totalGold > 0 && `+${totalGold} gp`}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => handleTake(false)}
                disabled={taking || selectedItems.size === 0}
                style={{
                  flex: 1,
                  background: selectedItems.size > 0 ? '#1a2840' : '#111',
                  border: `1px solid ${selectedItems.size > 0 ? '#2a4870' : '#222'}`,
                  borderRadius: 6,
                  color: selectedItems.size > 0 ? '#80a8e0' : '#444',
                  padding: '8px 0',
                  cursor: selectedItems.size > 0 && !taking ? 'pointer' : 'default',
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                {taking ? 'Taking...' : `Take Selected (${selectedItems.size})`}
              </button>
              <button
                onClick={() => handleTake(true)}
                disabled={taking}
                style={{
                  flex: 1,
                  background: taking ? '#111' : 'linear-gradient(135deg, #2a1a40 0%, #3a2060 100%)',
                  border: '1px solid #5a3080',
                  borderRadius: 6,
                  color: taking ? '#444' : '#c090ff',
                  padding: '8px 0',
                  cursor: taking ? 'default' : 'pointer',
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                {taking ? 'Taking...' : 'Take All'}
              </button>
            </div>

            <button
              onClick={onClose}
              disabled={taking}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#5a5570',
                fontSize: 12,
                cursor: 'pointer',
                padding: '2px 0',
                textDecoration: 'underline',
              }}
            >
              Leave everything behind
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
