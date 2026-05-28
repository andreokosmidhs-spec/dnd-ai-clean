/**
 * NPCIdentityPanel — renders the hidden NPC identity sheet on a Character
 * Knowledge Card. Public fields (already in `revealed_fields`) show clearly;
 * everything else is BLURRED with a lock icon, hinting "earn this through
 * play." The sheet lives on `card.secret_content` and gets populated by the
 * backend at auto-mint time.
 *
 * Field structure (matches backend `_generate_npc_identity_sheet`):
 *   stats: { ac, hp, intimidation_dc, persuasion_dc, deception_dc, insight_dc, passive_insight }
 *   personality: { trait, ideal, bond, flaw }
 *   background, mannerisms[], speech_style, secrets[], allegiances[], current_motivation
 */
import React, { useState, useRef } from 'react';
import { Lock, Eye, Sword, Heart, ScrollText, EyeOff, History, Volume2, Loader2, MessageCircle } from 'lucide-react';
import { NpcDialogueStream } from '../NpcDialogueStream';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const EMOTIONS = ['neutral','calm','happy','excited','angry','nervous','fearful','sad','tired','whispering','contemptuous','suspicious'];

const VoicePlayer = ({ card, campaignId }) => {
  const [emotion, setEmotion] = useState('neutral');
  const [loading, setLoading] = useState(false);
  const audioRef = useRef(null);

  const voiceProfile = card?.voiceProfile;
  if (!voiceProfile?.assignedVoice || !campaignId) return null;

  const npcId = card?.npcId || card?.id || card?.title?.toLowerCase().replace(/\s+/g, '_');

  const handleSpeak = async () => {
    const text = card?.description || card?.title || '';
    if (!text || !npcId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/voices/speak/${campaignId}/${npcId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.slice(0, 300), emotion, tier: 1, useCache: true }),
      });
      if (!res.ok) throw new Error(await res.text());
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.src = url;
        audioRef.current.play().catch(() => {});
      }
    } catch (e) {
      console.error('[voice]', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-3 border-t border-amber-500/20 pt-3">
      <div className="text-[10px] uppercase tracking-[0.18em] text-stone-400 flex items-center gap-1.5 mb-2">
        <Volume2 className="w-3 h-3" /> Voice — {voiceProfile.assignedVoice}
      </div>
      <div className="flex items-center gap-2 flex-wrap">
        <select
          value={emotion}
          onChange={e => setEmotion(e.target.value)}
          className="text-[10px] bg-stone-900 border border-amber-500/30 text-amber-200 rounded px-1.5 py-0.5"
        >
          {EMOTIONS.map(em => <option key={em} value={em}>{em}</option>)}
        </select>
        <button
          onClick={handleSpeak}
          disabled={loading}
          className="flex items-center gap-1 text-[10px] text-amber-300 border border-amber-500/40 rounded px-2 py-0.5 hover:bg-amber-600/10 disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Volume2 className="w-3 h-3" />}
          {loading ? 'Generating…' : 'Listen'}
        </button>
        {voiceProfile.voiceTags?.length > 0 && (
          <div className="flex gap-1 flex-wrap">
            {voiceProfile.voiceTags.slice(0, 5).map(t => (
              <span key={t} className="text-[9px] bg-stone-800 text-stone-400 rounded px-1">{t}</span>
            ))}
          </div>
        )}
      </div>
      <audio ref={audioRef} className="hidden" />
    </div>
  );
};

const RedactedRow = ({ label, value, revealed, hint, testid }) => {
  if (revealed) {
    return (
      <div className="flex items-start gap-2 text-sm" data-testid={testid}>
        <span className="text-amber-300 font-bold uppercase tracking-wider text-[10px] min-w-[88px] mt-0.5">
          {label}
        </span>
        <span className="text-amber-50 leading-relaxed flex-1">{value || '—'}</span>
      </div>
    );
  }
  return (
    <div className="flex items-start gap-2 text-sm relative" data-testid={testid}>
      <span className="text-stone-500 font-bold uppercase tracking-wider text-[10px] min-w-[88px] mt-0.5">
        {label}
      </span>
      <div className="flex-1 relative">
        {/* Blurred text — players see something is there but can't read it. */}
        <span className="text-stone-400 leading-relaxed select-none blur-[5px] inline-block">
          {value || hint || 'Hidden — uncover through play.'}
        </span>
        <span className="absolute inset-0 flex items-center gap-1.5 text-stone-500 italic text-xs">
          <Lock className="w-3 h-3" />
          {hint || 'Hidden — uncover through play.'}
        </span>
      </div>
    </div>
  );
};

const TalkButton = ({ card, campaignId }) => {
  const [open, setOpen] = useState(false);
  if (!campaignId) return null;

  const npcId = card?.npcId || card?.id || (card?.title || '').toLowerCase().replace(/\s+/g, '_');
  if (!npcId) return null;

  return (
    <div className="mt-3 border-t border-amber-500/20 pt-3">
      {!open ? (
        <button
          onClick={() => setOpen(true)}
          className="flex items-center gap-1.5 text-[11px] text-amber-300 border border-amber-500/40 rounded px-3 py-1.5 hover:bg-amber-600/10 transition-colors w-full justify-center"
        >
          <MessageCircle className="w-3.5 h-3.5" />
          Talk to {card?.title || npcId}
        </button>
      ) : (
        <div className="h-[420px]">
          <NpcDialogueStream
            campaignId={campaignId}
            npcId={npcId}
            npcName={card?.title}
            npcPortrait={card?.portraitUrl || card?.imageUrl}
            onClose={() => setOpen(false)}
          />
        </div>
      )}
    </div>
  );
};

export const NPCIdentityPanel = ({ card, campaignId }) => {
  if (!card || (card.type !== 'character' && card.type !== 'npc')) return null;
  const secret = card.secret_content || {};
  // No sheet generated yet (older NPC cards or generation failed) — skip the
  // section entirely rather than show a useless "all hidden" panel.
  if (!secret || Object.keys(secret).length === 0) return null;

  const revealed = new Set(card.revealed_fields || ['title', 'description']);
  const has = (k) => revealed.has(k);

  const stats = secret.stats || {};
  const personality = secret.personality || {};
  const mannerisms = secret.mannerisms || [];
  const secrets = secret.secrets || [];
  const allegiances = secret.allegiances || [];
  const discoveryLog = Array.isArray(card.discovery_log) ? card.discovery_log : [];

  // Friendly label for a revealed-field path (e.g. "personality.flaw" → "Flaw")
  const friendlyField = (f) => {
    const map = {
      'personality.trait': 'Trait',
      'personality.ideal': 'Ideal',
      'personality.bond': 'Bond',
      'personality.flaw': 'Flaw',
      'speech_style': 'Speech style',
      'mannerisms': 'Mannerisms',
      'background': 'Background',
      'current_motivation': 'Current motive',
      'allegiances': 'Allegiances',
      'passive_insight': 'Passive Insight',
      'stats.ac': 'AC',
      'stats.hp': 'HP',
      'stats.intimidation_dc': 'Intimidation DC',
      'stats.persuasion_dc': 'Persuasion DC',
      'stats.deception_dc': 'Deception DC',
      'stats.insight_dc': 'Insight DC',
      'secret_0': 'Secret 1',
      'secret_1': 'Secret 2',
    };
    return map[f] || f;
  };

  const formatTime = (iso) => {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      return d.toLocaleString(undefined, {
        month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch {
      return '';
    }
  };

  return (
    <div
      className="border-t border-amber-500/20 pt-4 mt-4 space-y-4"
      data-testid="npc-identity-panel"
    >
      <div className="flex items-center gap-2 text-xs text-amber-300">
        <Eye className="w-3.5 h-3.5" />
        <span className="uppercase tracking-wider font-bold">Identity Sheet</span>
        <span className="ml-auto text-[10px] text-stone-500 italic font-normal">
          Locked fields reveal as you play
        </span>
      </div>

      {/* Personality — the actor's notes */}
      <div className="space-y-2">
        <div className="text-[10px] uppercase tracking-[0.18em] text-stone-400 flex items-center gap-1.5">
          <Heart className="w-3 h-3" /> Personality
        </div>
        <div className="space-y-1.5 pl-4 border-l border-amber-500/20">
          <RedactedRow
            label="Trait"
            value={personality.trait}
            revealed={has('personality.trait')}
            hint="Read them to learn this"
            testid="npc-trait-row"
          />
          <RedactedRow
            label="Ideal"
            value={personality.ideal}
            revealed={has('personality.ideal')}
            hint="What they believe in"
          />
          <RedactedRow
            label="Bond"
            value={personality.bond}
            revealed={has('personality.bond')}
            hint="What they care about"
          />
          <RedactedRow
            label="Flaw"
            value={personality.flaw}
            revealed={has('personality.flaw')}
            hint="What trips them up"
          />
        </div>
      </div>

      {/* Mannerisms + speech style */}
      <div className="space-y-2">
        <div className="text-[10px] uppercase tracking-[0.18em] text-stone-400 flex items-center gap-1.5">
          <ScrollText className="w-3 h-3" /> Manner
        </div>
        <div className="space-y-1.5 pl-4 border-l border-amber-500/20">
          <RedactedRow
            label="Speech"
            value={secret.speech_style}
            revealed={has('speech_style')}
            hint="How they talk"
          />
          <RedactedRow
            label="Tics"
            value={mannerisms.length ? mannerisms.join(' · ') : ''}
            revealed={has('mannerisms')}
            hint="Body-language habits"
          />
          <RedactedRow
            label="Background"
            value={secret.background}
            revealed={has('background')}
            hint="Their backstory"
          />
        </div>
      </div>

      {/* Combat / contest stats */}
      <div className="space-y-2">
        <div className="text-[10px] uppercase tracking-[0.18em] text-stone-400 flex items-center gap-1.5">
          <Sword className="w-3 h-3" /> Stats
        </div>
        <div className="grid grid-cols-2 gap-1.5 pl-4 border-l border-amber-500/20">
          <RedactedRow
            label="AC"
            value={stats.ac}
            revealed={has('stats.ac')}
            hint="???"
          />
          <RedactedRow
            label="HP"
            value={stats.hp}
            revealed={has('stats.hp')}
            hint="???"
          />
          <RedactedRow
            label="Intimidate"
            value={stats.intimidation_dc != null ? `DC ${stats.intimidation_dc}` : null}
            revealed={has('stats.intimidation_dc')}
            hint="Untested"
          />
          <RedactedRow
            label="Persuade"
            value={stats.persuasion_dc != null ? `DC ${stats.persuasion_dc}` : null}
            revealed={has('stats.persuasion_dc')}
            hint="Untested"
          />
          <RedactedRow
            label="Deceive"
            value={stats.deception_dc != null ? `DC ${stats.deception_dc}` : null}
            revealed={has('stats.deception_dc')}
            hint="Untested"
          />
          <RedactedRow
            label="Read them"
            value={stats.insight_dc != null ? `DC ${stats.insight_dc}` : null}
            revealed={has('stats.insight_dc')}
            hint="Untested"
          />
        </div>
      </div>

      {/* Allegiances + secrets */}
      <div className="space-y-2">
        <div className="text-[10px] uppercase tracking-[0.18em] text-stone-400 flex items-center gap-1.5">
          <EyeOff className="w-3 h-3" /> Allegiances & Secrets
        </div>
        <div className="space-y-1.5 pl-4 border-l border-amber-500/20">
          <RedactedRow
            label="Loyal to"
            value={allegiances.length ? allegiances.join(', ') : ''}
            revealed={has('allegiances')}
            hint="Hidden — who pulls their strings?"
          />
          <RedactedRow
            label="Motive"
            value={secret.current_motivation}
            revealed={has('current_motivation')}
            hint="Hidden — what do they want from you?"
          />
          {secrets.map((s, i) => (
            <RedactedRow
              key={i}
              label={`Secret ${i + 1}`}
              value={s}
              revealed={has(`secret_${i}`)}
              hint="Buried deep — extract via skill or pressure"
            />
          ))}
        </div>
      </div>

      {/* Discovery Log — timeline of WHEN and HOW each redacted field was
          uncovered. Reverse-chronological. Only renders when there's at
          least one entry. Builds investigative satisfaction and gives the
          player a record they can scroll back to during play. */}
      {discoveryLog.length > 0 && (
        <div className="space-y-2 pt-2" data-testid="discovery-log-section">
          <div className="text-[10px] uppercase tracking-[0.18em] text-stone-400 flex items-center gap-1.5">
            <History className="w-3 h-3" />
            Discovery Log
            <span className="ml-auto text-stone-500 normal-case tracking-normal italic">
              {discoveryLog.length} {discoveryLog.length === 1 ? 'entry' : 'entries'}
            </span>
          </div>
          <ol className="pl-4 border-l-2 border-emerald-500/30 space-y-1.5">
            {[...discoveryLog].reverse().slice(0, 12).map((entry, i) => (
              <li
                key={i}
                className="relative text-[12px] text-amber-50 leading-snug"
                data-testid={`discovery-log-entry-${i}`}
              >
                {/* Bullet dot anchored on the timeline line */}
                <span className="absolute -left-[19px] top-1 w-2 h-2 rounded-full bg-emerald-400 ring-2 ring-stone-950" />
                <div className="flex flex-wrap items-baseline gap-x-1.5">
                  <span className="font-bold text-emerald-200">
                    {friendlyField(entry.field)}
                  </span>
                  <span className="text-stone-400">revealed via</span>
                  <span className="font-bold text-amber-200">{entry.check_type}</span>
                </div>
                <div className="text-[11px] text-stone-400 italic">
                  in <span className="text-stone-300 not-italic">"{entry.storyline_title}"</span>
                  {entry.beat_title && entry.beat_title !== entry.storyline_title && (
                    <> · beat <span className="text-stone-300 not-italic">"{entry.beat_title}"</span></>
                  )}
                  {entry.at && <> · <span className="text-stone-500">{formatTime(entry.at)}</span></>}
                </div>
              </li>
            ))}
            {discoveryLog.length > 12 && (
              <li className="text-[11px] text-stone-500 italic pt-1">
                + {discoveryLog.length - 12} earlier entries
              </li>
            )}
          </ol>
        </div>
      )}

      <VoicePlayer card={card} campaignId={campaignId} />

      <TalkButton card={card} campaignId={campaignId} />
    </div>
  );
};

export default NPCIdentityPanel;
