import React, { useEffect, useState, useCallback } from 'react';
import { X, Star, MapPin, Clock } from 'lucide-react';
import {
  CARD_TYPE_CONFIG,
  getCardTitle,
  normalizeCardType,
  getRarity,
  RARITY_CONFIG,
  getMechanicalRows,
  getStatusStyle,
} from './cardTypeConfig';

const DELTA_TYPE_LABEL = {
  attitude: 'Attitude',
  secret:   'Learned',
  favour:   'Favour',
  promise:  'Promise',
  item:     'Item',
  location: 'Moved to',
  note:     'Note',
};

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CardModal = ({ card, type, isOpen, onClose, isPinned, onTogglePin, campaignId }) => {
  const [itemStatus, setItemStatus] = useState(card?.status || 'acquired');
  const [itemQty, setItemQty] = useState(card?.quantity || 1);

  useEffect(() => {
    setItemStatus(card?.status || 'acquired');
    setItemQty(card?.quantity || 1);
  }, [card?.id, card?.status, card?.quantity]);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  const handleToggleEquip = useCallback(async () => {
    if (!campaignId || !card?.id) return;
    const prev = itemStatus;
    const next = prev === 'equipped' ? 'unequipped' : 'equipped';
    setItemStatus(next);
    try {
      await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/cards/${card.id}/equip`, { method: 'PATCH' });
    } catch {
      setItemStatus(prev);
    }
  }, [campaignId, card?.id, itemStatus]);

  const handleConsume = useCallback(async () => {
    if (!campaignId || !card?.id) return;
    const prevQty = itemQty;
    const prevStatus = itemStatus;
    const newQty = Math.max(0, prevQty - 1);
    setItemQty(newQty);
    if (newQty === 0) setItemStatus('consumed');
    try {
      await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/cards/${card.id}/consume`, { method: 'PATCH' });
    } catch {
      setItemQty(prevQty);
      setItemStatus(prevStatus);
    }
  }, [campaignId, card?.id, itemQty, itemStatus]);

  if (!isOpen || !card) return null;

  const normalized = normalizeCardType(type);
  const config = CARD_TYPE_CONFIG[normalized] || CARD_TYPE_CONFIG.locations;
  const Icon = config.icon;
  const title = getCardTitle(card, type);
  const rarity = getRarity(card, normalized);
  const rarityConf = RARITY_CONFIG[rarity];
  const mechRows = getMechanicalRows(card, normalized);
  const biomeAccent = card?.biome_accent || null;
  const headerGradient = normalized === 'locations' && biomeAccent ? biomeAccent : config.gradient;

  const rarityBorder =
    rarity === 'legendary' ? 'border-yellow-500/60' :
    rarity === 'rare'      ? 'border-blue-500/60'   :
    rarity === 'uncommon'  ? 'border-green-500/50'  :
    config.border;

  const deltas = card?.character_deltas || [];

  // Full mechanical detail sections per type
  const mechanicalDetails = [];
  if (normalized === 'npcs') {
    const stats = card?.secret_content?.stats;
    if (stats) {
      mechanicalDetails.push({ label: 'Social DCs', rows: [
        `Persuasion: ${stats.persuasion_dc || 12}`,
        `Intimidation: ${stats.intimidation_dc || 10}`,
        `Deception (vs): ${stats.deception_dc || 11}`,
        `Insight (to read): ${stats.insight_dc || 12}`,
      ]});
    }
    if (card?.at_location) mechanicalDetails.push({ label: 'Last seen', rows: [card.at_location] });
  }
  if (normalized === 'locations') {
    const rows = [];
    if (card?.biome_label) rows.push(`Biome: ${card.biome_label}`);
    if (card?.biome_survival_dc_mod !== undefined) rows.push(`Survival DC modifier: ${card.biome_survival_dc_mod >= 0 ? '+' : ''}${card.biome_survival_dc_mod}`);
    if (card?.biome_nature_dc_mod !== undefined) rows.push(`Nature DC modifier: ${card.biome_nature_dc_mod >= 0 ? '+' : ''}${card.biome_nature_dc_mod}`);
    if ((card?.biome_resources || []).length) rows.push(`Resources: ${card.biome_resources.slice(0, 5).join(', ')}`);
    if ((card?.biome_monsters || []).length) rows.push(`Threats: ${card.biome_monsters.slice(0, 5).join(', ')}`);
    if (rows.length) mechanicalDetails.push({ label: 'Environment', rows });
  }
  if (normalized === 'curses' && card?.mechanical) {
    mechanicalDetails.push({ label: 'Mechanical effect', rows: [card.mechanical] });
  }
  if (normalized === 'items') {
    const bonuses = card?.grants_bonus || [];
    const itemType = card?.item_type;
    const slot = card?.equip_slot;
    const rows = [];
    if (itemType) rows.push(`Type: ${itemType}${slot ? ` · ${slot}` : ''}`);
    bonuses.forEach(b => rows.push(`+${b.modifier} to ${b.check} checks (when equipped)`));
    if (itemQty > 0) rows.push(`Quantity: ×${itemQty}`);
    if (rows.length) mechanicalDetails.push({ label: 'Item properties', rows });
  }

  // Faction details computed outside JSX for clarity
  const factionHierarchy = normalized === 'factions' ? (card?.hierarchy || []) : [];
  const factionPerks = normalized === 'factions' ? (card?.tier_perks || []) : [];
  const factionMembers = normalized === 'factions' ? (card?.known_members || []) : [];
  const factionRep = normalized === 'factions' ? (card?.reputation ?? null) : null;
  const factionRepLabel = factionRep === null ? null
    : factionRep <= -60 ? 'Reviled' : factionRep <= -20 ? 'Hostile'
    : factionRep < 20 ? 'Neutral' : factionRep < 50 ? 'Respected'
    : factionRep < 80 ? 'Honored' : 'Exalted';

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
        onClick={onClose}
      >
        {/* Card container — click inside doesn't close */}
        <div
          className={`relative w-[320px] max-h-[85vh] rounded-xl overflow-hidden flex flex-col bg-gray-900 border-2 ${rarityBorder} shadow-2xl`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className={`flex-shrink-0 h-8 bg-gradient-to-r ${headerGradient} flex items-center justify-between px-3 border-b border-black/40`}>
            <div className="flex items-center gap-1.5 min-w-0">
              <Icon className="w-3.5 h-3.5 text-white/90 shrink-0" />
              <span className="text-[9px] font-bold text-white/90 uppercase tracking-wider truncate">
                {config.label}
              </span>
              <span className={`text-[11px] leading-none ml-1 ${rarityConf.color}`}>{rarityConf.gem}</span>
            </div>
            <div className="flex items-center gap-1.5 flex-shrink-0">
              {onTogglePin && (
                <button onClick={() => onTogglePin(card.id)} className="text-white/60 hover:text-yellow-400 transition-colors">
                  <Star className={`w-3.5 h-3.5 ${isPinned ? 'fill-yellow-400 text-yellow-400' : ''}`} />
                </button>
              )}
              <button onClick={onClose} className="text-white/60 hover:text-white transition-colors">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Art well */}
          <div
            className={`flex-shrink-0 h-32 bg-gradient-to-br ${headerGradient} overflow-hidden relative`}
            style={card?.image_url ? { backgroundImage: `url(${card.image_url})`, backgroundSize: 'cover', backgroundPosition: 'center' } : undefined}
          >
            {!card?.image_url && (
              <div className="absolute inset-0 flex items-center justify-center opacity-20">
                <Icon className="w-14 h-14 text-white" />
              </div>
            )}
          </div>

          {/* Type-line: title + status + item actions */}
          <div className="flex-shrink-0 px-3 py-2 bg-stone-950/80 border-t border-b border-black/30 flex items-center justify-between gap-2">
            <h3 className="font-bold text-white text-sm leading-tight truncate">{title}</h3>
            <div className="flex items-center gap-1 flex-shrink-0">
              {/* Equip / Unequip button for equipment items */}
              {normalized === 'items' && card?.item_type === 'equipment' && itemStatus !== 'consumed' && (
                <button
                  onClick={handleToggleEquip}
                  className={`px-1.5 py-0.5 rounded text-[8px] font-semibold uppercase tracking-wide transition-colors ${
                    itemStatus === 'equipped'
                      ? 'bg-green-600/80 text-green-100 hover:bg-gray-600/80 hover:text-gray-300'
                      : 'bg-gray-600/80 text-gray-300 hover:bg-green-600/80 hover:text-green-100'
                  }`}
                >
                  {itemStatus === 'equipped' ? 'Equipped ✓' : 'Equip'}
                </button>
              )}
              {/* Consume button for consumables/materials/currency */}
              {normalized === 'items' && card?.item_type !== 'equipment' && itemStatus !== 'consumed' && (
                <button
                  onClick={handleConsume}
                  className="px-1.5 py-0.5 rounded text-[8px] font-semibold uppercase tracking-wide bg-orange-700/80 text-orange-200 hover:bg-orange-600/80 transition-colors"
                >
                  Use ×1
                </button>
              )}
              {/* Status pill */}
              {(normalized !== 'items' ? card?.status : itemStatus) && (
                <span className={`px-1.5 py-0.5 rounded text-[8px] font-semibold uppercase tracking-wide ${getStatusStyle(normalized === 'items' ? itemStatus : card?.status)}`}>
                  {normalized === 'items' ? itemStatus : card?.status}
                </span>
              )}
            </div>
          </div>

          {/* Scrollable body */}
          <div className="overflow-y-auto flex-1 px-3 py-2 space-y-3">
            {/* Narration / description */}
            {(card?.content || card?.description) && (
              <div>
                <p className="text-gray-200 text-[11px] leading-relaxed font-serif italic">
                  {card.content || card.description}
                </p>
              </div>
            )}

            {/* Mechanical stat blocks */}
            {mechanicalDetails.map((block, i) => (
              <div key={i}>
                <p className="text-[8px] text-gray-500 uppercase tracking-widest mb-1">{block.label}</p>
                <div className="space-y-0.5">
                  {block.rows.map((row, j) => (
                    <p key={j} className="text-[10px] text-cyan-300 font-mono">{row}</p>
                  ))}
                </div>
              </div>
            ))}

            {/* All mechanical rows */}
            {mechRows.filter(r => r.kind !== 'status').length > 0 && (
              <div>
                <p className="text-[8px] text-gray-500 uppercase tracking-widest mb-1">Details</p>
                <div className="space-y-0.5">
                  {mechRows.filter(r => r.kind !== 'status').map((row, i) => (
                    <p key={i} className={`text-[10px] ${row.kind === 'warn' ? 'text-amber-400' : row.kind === 'stat' ? 'text-cyan-300 font-mono' : row.kind === 'delta' ? 'text-gray-400 italic' : 'text-gray-300'}`}>
                      {row.label}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Tags */}
            {(card?.tags || []).length > 0 && (
              <div className="flex flex-wrap gap-1">
                {card.tags.map((tag, i) => (
                  <span key={i} className={`px-1.5 py-0 rounded text-[8px] border ${config.badge}`}>{tag}</span>
                ))}
              </div>
            )}

            {/* ── FACTION SECTIONS ── */}
            {normalized === 'factions' && (
              <>
                {/* Reputation + identity */}
                {(factionRep !== null || card?.purpose || (card?.values || []).length > 0) && (
                  <div>
                    <p className="text-[8px] text-gray-500 uppercase tracking-widest mb-1">Identity</p>
                    <div className="space-y-0.5">
                      {factionRep !== null && (
                        <p className="text-[10px] font-mono text-cyan-300">
                          Reputation: {factionRep >= 0 ? '+' : ''}{factionRep} — {factionRepLabel}
                        </p>
                      )}
                      {card?.purpose && <p className="text-[10px] text-gray-300">{card.purpose}</p>}
                      {(card?.values || []).length > 0 && (
                        <p className="text-[10px] text-gray-400 italic">Values: {card.values.join(' · ')}</p>
                      )}
                      {(card?.tenets || []).length > 0 && (
                        <p className="text-[10px] text-amber-400">Tenets: {card.tenets.join(' · ')}</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Hierarchy */}
                {factionHierarchy.length > 0 && (
                  <div>
                    <p className="text-[8px] text-gray-500 uppercase tracking-widest mb-1">Hierarchy</p>
                    <div className="space-y-1">
                      {factionHierarchy.map((tier, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <span className="text-[8px] text-purple-400 font-bold shrink-0 w-4 text-right">{tier.tier}</span>
                          <div className="min-w-0">
                            <span className="text-[9px] text-white font-semibold">{tier.role}</span>
                            {tier.filled_by && (
                              <span className="text-[9px] text-green-400 ml-1">← {tier.filled_by}</span>
                            )}
                            {!tier.filled_by && (
                              <span className="text-[9px] text-red-400/70 ml-1 italic">vacant</span>
                            )}
                            {tier.function && (
                              <p className="text-[8px] text-gray-500 truncate">{tier.function}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tier perks */}
                {factionPerks.length > 0 && (
                  <div>
                    <p className="text-[8px] text-gray-500 uppercase tracking-widest mb-1">Perks</p>
                    <div className="space-y-1.5">
                      {factionPerks.map((perk, i) => {
                        const reqs = perk.requirements || [];
                        // Client-side requirement check (approximate — no live resource data)
                        const hasHierarchyPerk = factionHierarchy.some(
                          h => h.tier === perk.tier && h.filled_by
                        );
                        const isActive = reqs.length === 0 || hasHierarchyPerk;
                        return (
                          <div key={i} className="flex gap-2 items-start">
                            <span className={`text-[8px] shrink-0 mt-0.5 ${isActive ? 'text-green-400' : 'text-red-400/60'}`}>
                              {isActive ? '●' : '○'}
                            </span>
                            <div className="min-w-0">
                              <p className={`text-[9px] font-semibold ${isActive ? 'text-white' : 'text-gray-500'}`}>
                                {perk.name}
                                {perk.bonus_modifier && perk.bonus_check && (
                                  <span className="ml-1 text-cyan-400 font-mono">
                                    +{perk.bonus_modifier} {perk.bonus_check}
                                  </span>
                                )}
                              </p>
                              {perk.description && (
                                <p className="text-[8px] text-gray-500">{perk.description}</p>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Resources */}
                {(card?.income_gp || card?.treasury_gp || card?.hideout || (card?.controlled_areas || []).length > 0) && (
                  <div>
                    <p className="text-[8px] text-gray-500 uppercase tracking-widest mb-1">Resources</p>
                    <div className="space-y-0.5">
                      {card?.income_gp != null && <p className="text-[10px] text-cyan-300 font-mono">Income: {card.income_gp} gp/month</p>}
                      {card?.treasury_gp != null && <p className="text-[10px] text-cyan-300 font-mono">Treasury: {card.treasury_gp} gp</p>}
                      {card?.recruitment_rate != null && <p className="text-[10px] text-gray-300">Recruitment: {card.recruitment_rate}/month</p>}
                      {(card?.controlled_areas || []).length > 0 && <p className="text-[10px] text-gray-300">Controls: {card.controlled_areas.join(', ')}</p>}
                      {card?.hideout && <p className="text-[10px] text-gray-300">Hideout: {card.hideout}</p>}
                      {(card?.important_items || []).length > 0 && <p className="text-[10px] text-amber-400">Key items: {card.important_items.join(', ')}</p>}
                    </div>
                  </div>
                )}

                {/* Known members */}
                {factionMembers.length > 0 && (
                  <div>
                    <p className="text-[8px] text-gray-500 uppercase tracking-widest mb-1">Known members</p>
                    <div className="space-y-0.5">
                      {factionMembers.map((m, i) => (
                        <div key={i} className="flex gap-2 items-center">
                          <span className="text-[10px] text-white">{m.name}</span>
                          {m.role && <span className="text-[8px] text-purple-400">[{m.role}]</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* NPC relationship history */}
            {deltas.length > 0 && (
              <div>
                <p className="text-[8px] text-gray-500 uppercase tracking-widest mb-1">Relationship history</p>
                <div className="space-y-1.5">
                  {[...deltas].reverse().slice(0, 10).map((d, i) => (
                    <div key={i} className="flex gap-2 items-start">
                      <span className="text-[8px] text-gray-500 font-semibold shrink-0 uppercase mt-0.5">
                        {DELTA_TYPE_LABEL[d.type] || d.type}
                      </span>
                      <span className="text-[10px] text-gray-300 leading-snug">{d.fact}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="border-t border-gray-800 pt-2 flex items-center gap-3 text-gray-600 text-[8px]">
              {card?.location_origin && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-2.5 h-2.5" />
                  {card.location_origin}
                </span>
              )}
              {card?.createdAt && (
                <span className="flex items-center gap-1">
                  <Clock className="w-2.5 h-2.5" />
                  {new Date(card.createdAt).toLocaleDateString()}
                </span>
              )}
              <span className={`ml-auto font-semibold uppercase tracking-widest ${rarityConf.color}`}>
                {rarityConf.label}
              </span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default CardModal;
