import React, { useState, useRef, useEffect, useCallback, useImperativeHandle, forwardRef } from 'react';
import { Card, CardContent } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dice6, MessageSquare, Loader2, User, Sparkles, Volume2, X, BookOpen, Bookmark, BookmarkCheck, Scroll, Flag, ThumbsUp, ThumbsDown } from 'lucide-react';
import { useGameState } from '../contexts/GameStateContext';
import { useAuth } from '../contexts/AuthContext';
import UsageBanner from './UsageBanner';
// CheckRequestCard and RollResultCard removed - CheckRollPanel handles all rolls now
import NarrationAudioPlayer from './NarrationAudioPlayer';
import NPCMentionHighlighter from './NPCMentionHighlighter';
import { EntityNarrationParser } from './EntityLink';
import { EntityQuickInspect } from './EntityQuickInspect';
import { CampaignLogPanel } from './CampaignLogPanel';
import CombatHUD from './CombatHUD';
import CampaignTopBar from './CampaignTopBar';
import ActiveInvestigationPanel, { StorylineRewardModal } from './ActiveInvestigationPanel';
import RememberCardDialog from './RememberCardDialog';
import SceneReportDialog from './SceneReportDialog';
import DefeatModal from './DefeatModal';
import CanonBar from './CanonBar';
import CanonReferences from './CanonReferences';
import AutoSaveIndicator from './AutoSaveIndicator';
import MissionPhaseBadge from './MissionPhaseBadge';
import useCanonTerms, { findCanonMentions } from '../hooks/useCanonTerms';
import { useTargetMode, pickWordFromClick } from '../contexts/TargetModeContext';
import { SearchTargetModal } from './TargetModeBanner';
import { getCheckOutcome, getAbilityModifier, isProficient } from '../utils/dndMechanics';
import { useTTS } from '../hooks/useTTS';
import sessionManager from '../state/SessionManager';
import { toast } from 'sonner';
import '../styles/adventurePapyrus.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdventureLogWithDM = forwardRef(({ onLoadingChange, ...props }, ref) => {
  // Get the entire context object to ensure fresh reads
  const gameStateContext = useGameState();
  const { patchUsage } = useAuth();
  const {
    sessionId,
    setSessionId,
    campaignId,
    worldBlueprint,
    buildActionPayload,
    worldState,
    updateWorld,
    updateCharacter: updateCharContext
  } = gameStateContext;
  
  const [messages, setMessages] = useState([]);
  const [currentOptions, setCurrentOptions] = useState([]);

  // Canon term index — proper-noun terms harvested from every canon
  // scene's title/facts, mapped back to their originating scene. Used
  // to detect when a DM narration honors canon and surface a pulsing
  // emerald chip linking back to that scene.
  const { termsMap: canonTermsMap } = useCanonTerms(campaignId);

  // Target Mode — when Observe/Search is active, clicks on DM narration
  // pick a word and either auto-send an inspection (observe) or open the
  // "what are you looking for?" modal (search).
  const { mode: targetMode, clearMode: clearTargetMode } = useTargetMode();
  const [searchTarget, setSearchTarget] = useState(null);  // word in pending search
  // Live underline overlay — tracks the word under the cursor while
  // a target mode is active so the player can SEE what they're about to
  // pick. Uses a single fixed-position element driven by Range bounding
  // rects; rAF-throttled on mousemove to avoid layout thrash.
  const [hoverHighlight, setHoverHighlight] = useState(null);  // { left, top, width, height, word }
  const hoverRafRef = useRef(0);

  const updateHover = useCallback((e) => {
    if (!targetMode) {
      if (hoverHighlight) setHoverHighlight(null);
      return;
    }
    if (hoverRafRef.current) cancelAnimationFrame(hoverRafRef.current);
    const { clientX, clientY } = e;
    hoverRafRef.current = requestAnimationFrame(() => {
      let range = null;
      try {
        if (typeof document.caretRangeFromPoint === 'function') {
          range = document.caretRangeFromPoint(clientX, clientY);
        } else if (typeof document.caretPositionFromPoint === 'function') {
          const pos = document.caretPositionFromPoint(clientX, clientY);
          if (pos) {
            range = document.createRange();
            range.setStart(pos.offsetNode, pos.offset);
            range.collapse(true);
          }
        }
        if (!range) { setHoverHighlight(null); return; }
        const node = range.startContainer;
        const text = (node && node.textContent) || '';
        if (!text || node.nodeType !== 3) { setHoverHighlight(null); return; }
        let s = range.startOffset;
        let end = range.startOffset;
        const isWordChar = (ch) => /[A-Za-z0-9'’\-]/.test(ch);
        while (s > 0 && isWordChar(text[s - 1])) s -= 1;
        while (end < text.length && isWordChar(text[end])) end += 1;
        if (end <= s) { setHoverHighlight(null); return; }
        const wordRange = document.createRange();
        wordRange.setStart(node, s);
        wordRange.setEnd(node, end);
        const rect = wordRange.getBoundingClientRect();
        if (!rect || rect.width === 0) { setHoverHighlight(null); return; }
        setHoverHighlight({
          left: rect.left,
          top: rect.top,
          width: rect.width,
          height: rect.height,
          word: text.slice(s, end),
        });
      } catch {
        setHoverHighlight(null);
      }
    });
  }, [targetMode, hoverHighlight]);

  const clearHover = useCallback(() => setHoverHighlight(null), []);

  // Drop the overlay whenever the target mode turns off.
  useEffect(() => {
    if (!targetMode && hoverHighlight) setHoverHighlight(null);
  }, [targetMode, hoverHighlight]);

  const handleNarrationClick = (e) => {
    if (!targetMode) return;
    const word = pickWordFromClick(e);
    if (!word) return;
    e.preventDefault();
    e.stopPropagation();
    setHoverHighlight(null);
    if (targetMode === 'observe') {
      // Send an inspection command and exit observe mode.
      const command = `I focus on the ${word} and study it more closely — what stands out?`;
      sendPlayerMessage(command);
      clearTargetMode();
    } else if (targetMode === 'search') {
      // Open the "what are you looking for?" modal; submission happens
      // inside SearchTargetModal.
      setSearchTarget(word);
    }
  };

  const submitTargetedSearch = (query) => {
    const word = searchTarget;
    setSearchTarget(null);
    clearTargetMode();
    if (!word || !query) return;
    const command = `I search the ${word} carefully — I'm looking for ${query}. What do I find?`;
    sendPlayerMessage(command);
  };
  const [isLoading, setIsLoading] = useState(false);
  const [intentMode, setIntentMode] = useState('action');
  const [pendingCheck, setPendingCheck] = useState(null);
  const [combatState, setCombatState] = useState(null);
  const [isCombatActive, setIsCombatActive] = useState(false);
  const [quests, setQuests] = useState([]);
  const [showDefeatModal, setShowDefeatModal] = useState(false);
  const [defeatInfo, setDefeatInfo] = useState(null);
  const [selectedNpc, setSelectedNpc] = useState(null);
  const [showIntro, setShowIntro] = useState(false);
  
  // Entity Profile Panel state
  const [selectedEntity, setSelectedEntity] = useState(null);
  
  // Campaign Log Panel state
  const [showCampaignLog, setShowCampaignLog] = useState(false);
  // Count of newly-minted cards the player hasn't hovered yet — drives the
  // glowing badge on the "Campaign Log" button. Refreshes whenever a new
  // storyline-target mint broadcasts the `rpg:cards-refreshed` event, when
  // a card is hovered/seen, and once on mount.
  const [newCardCount, setNewCardCount] = useState(0);

  useEffect(() => {
    if (!campaignId) return;
    let cancelled = false;
    const fetchCount = () => {
      fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/log/cards`)
        .then((r) => (r.ok ? r.json() : null))
        .then((d) => {
          if (cancelled || !d) return;
          const cards = Array.isArray(d) ? d : (d?.cards || []);
          const n = cards.filter((c) => c && c.is_new).length;
          setNewCardCount(n);
        })
        .catch(() => {});
    };
    fetchCount();
    const onRefresh = () => fetchCount();
    const onSeen = () => setNewCardCount((n) => Math.max(0, n - 1));
    window.addEventListener('rpg:cards-refreshed', onRefresh);
    window.addEventListener('rpg:cards-seen', onSeen);
    return () => {
      cancelled = true;
      window.removeEventListener('rpg:cards-refreshed', onRefresh);
      window.removeEventListener('rpg:cards-seen', onSeen);
    };
  }, [campaignId]);

  // Active investigation (multi-beat storyline). It is set ONLY when the
  // player's action engages a hook in this session — never auto-restored from
  // the server on mount. The player can dismiss it; the storyline keeps
  // existing server-side and shows up in the Quest Log either way.
  const [activeStoryline, setActiveStoryline] = useState(null);
  const [showRewardModal, setShowRewardModal] = useState(null);
  // Pending off-hook clarification — when the spawn probe asks the DM to
  // clarify what the player is trying to do (e.g. "I look for a sloop"),
  // we hold the original action here and join the player's next reply to
  // it on a second spawn-from-action call.
  const [pendingClarification, setPendingClarification] = useState(null);
  // Lightweight "hook hint" popover: when the player hovers/clicks an inline
  // hook in a DM message, we surface a small tip suggesting how to engage.
  const [hookHint, setHookHint] = useState(null);
  
  // TTS Hook
  const { 
    audioRef, 
    isLoading: isTTSLoading, 
    isTTSEnabled, 
    generateSpeech, 
    toggleTTS 
  } = useTTS();
  
  const scrollRef = useRef();
  const introStartedRef = useRef(false);
  const worldBriefAutoPlayedRef = useRef(false);
  
  // Notify parent of loading state changes
  useEffect(() => {
    if (onLoadingChange) {
      onLoadingChange(isLoading);
    }
  }, [isLoading, onLoadingChange]);

  // Auto-play the macro chronicler ("World Brief") narration the first time
  // a session opens, so every campaign starts with a Mercer-style cold open.
  // Gated by:
  //   - `isTTSEnabled` (respects the user's global TTS preference)
  //   - per-session localStorage flag (`dm-world-brief-played-{sessionId}`)
  //     so reopening the same adventure doesn't replay it
  //   - per-mount ref so React StrictMode / re-renders don't double-fire
  useEffect(() => {
    if (!sessionId || !isTTSEnabled || !generateSpeech) return;
    if (worldBriefAutoPlayedRef.current) return;
    if (!messages || messages.length === 0) return;

    const briefIdx = messages.findIndex(
      (m) => m && m.type === 'dm' && m.isWorldBrief && (m.text || m.message)
    );
    if (briefIdx === -1) return;

    const playedKey = `dm-world-brief-played-${sessionId}`;
    if (localStorage.getItem(playedKey) === '1') return;

    const brief = messages[briefIdx];
    if (brief.audioUrl) return;

    worldBriefAutoPlayedRef.current = true;
    localStorage.setItem(playedKey, '1');

    const text = brief.text || brief.message || '';
    (async () => {
      try {
        const audioUrl = await generateSpeech(text, 'onyx', true);
        if (audioUrl) {
          setMessages((prev) =>
            prev.map((m, i) => (i === briefIdx ? { ...m, audioUrl } : m))
          );
        }
      } catch (err) {
        console.warn('World-brief auto-narration failed:', err);
      }
    })();
  }, [sessionId, isTTSEnabled, generateSpeech, messages]);

  // One-time backfill: legacy localStorage caches stored chronicle / intro
  // messages with empty `entity_mentions: []`. When this component mounts
  // with a campaignId, fetch the latest backend snapshot and patch in
  // mentions so locations / factions / NPCs become clickable in older
  // sessions too. Idempotent — only runs when at least one chronicle/intro
  // entry is missing mentions.
  const entityBackfillRan = useRef(false);
  useEffect(() => {
    if (!campaignId) return;
    if (entityBackfillRan.current) return;
    if (!messages || messages.length === 0) return;

    const needsBackfill = messages.some((m) =>
      m && m.type === 'dm'
      && (
        m.isWorldBrief
        || m.source === 'intro'
        || m.isIntro
        || (m.isCinematic && (!m.hooks || m.hooks.length === 0))
      )
      && (
        (!m.entity_mentions || m.entity_mentions.length === 0)
        || (!m.hooks || m.hooks.length === 0)
      )
    );
    if (!needsBackfill) {
      entityBackfillRan.current = true;
      return;
    }

    entityBackfillRan.current = true;
    (async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}`);
        if (!res.ok) return;
        const data = await res.json();
        const ss = data?.starting_scene || {};
        const briefMentions = ss.world_brief_entity_mentions || [];
        const introMentions = ss.entity_mentions || [];
        const introHooks = ss.hooks || [];
        if (briefMentions.length === 0 && introMentions.length === 0 && introHooks.length === 0) return;

        const introText = (ss.introText || '').trim();

        setMessages((prev) =>
          prev.map((m) => {
            if (!m || m.type !== 'dm') return m;
            if (m.isWorldBrief && (!m.entity_mentions || m.entity_mentions.length === 0)) {
              return { ...m, entity_mentions: briefMentions };
            }
            // Match the intro by source flag OR by text equality (covers legacy
            // messages saved without `source: 'intro'`).
            const isIntro = m.source === 'intro' || m.isIntro
              || (introText && (m.text || '').trim() === introText);
            if (isIntro) {
              const next = { ...m };
              if ((!m.entity_mentions || m.entity_mentions.length === 0) && introMentions.length) {
                next.entity_mentions = introMentions;
              }
              if ((!m.hooks || m.hooks.length === 0) && introHooks.length) {
                next.hooks = introHooks;
              }
              return next;
            }
            return m;
          })
        );
      } catch (err) {
        console.warn('Entity/hook backfill failed (non-fatal):', err);
      }
    })();
  }, [campaignId, messages]);

  // Lean DM: campaign-scoped endpoint built on campaigns.py + knowledge cards.
  // Falls back to the legacy dungeon_forge endpoint if no campaignId is in scope.
  const apiEndpoint = campaignId
    ? `${BACKEND_URL}/api/campaigns/${campaignId}/dm/action`
    : `${BACKEND_URL}/api/rpg_dm/action`;
  const diceEndpoint = `${BACKEND_URL}/api/dice`;

  // Auto-scroll to bottom (with message count instead of array reference)
  const messageCount = messages.length;
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messageCount]);

  // (No mount-time storyline auto-restore: the investigation panel only
  // surfaces when the player's CURRENT action engages a hook in this session.
  // The storyline still lives server-side and stays linked to the Quest Log.)

  // Initialize session and load messages
  useEffect(() => {
    const storedIntent = localStorage.getItem('dm-intent-mode');
    if (storedIntent) setIntentMode(storedIntent);

    if (!sessionId) return;

    const messagesKey = `dm-log-messages-${sessionId}`;
    const queueKey = `dm-pending-beats-${sessionId}`;

    // Drain any map-event arrival beats that were queued while this component
    // was unmounted (the World Map tab unmounts the Adventure Log). We MERGE
    // them into the persisted message log atomically before setMessages so
    // StrictMode's double-mount can't drop the beats between renders.
    let stored = [];
    try {
      stored = JSON.parse(localStorage.getItem(messagesKey) || '[]');
      if (!Array.isArray(stored)) stored = [];
    } catch {
      stored = [];
    }

    try {
      const raw = localStorage.getItem(queueKey);
      if (raw) {
        const queue = JSON.parse(raw);
        if (Array.isArray(queue) && queue.length) {
          const newBeats = queue
            .filter((b) => b && (b.text || '').trim())
            .map((b) => ({
              type: 'dm',
              text: b.text,
              message: b.text,
              timestamp: b.timestamp || Date.now(),
              isCinematic: true,
              source: b.source || 'map-event',
              meta: {
                questTitle: b.quest?.name,
                eventTitle: b.eventTitle,
              },
            }));
          if (newBeats.length) {
            stored = [...stored, ...newBeats].slice(-200);
            localStorage.setItem(messagesKey, JSON.stringify(stored));
          }
        }
        localStorage.removeItem(queueKey);
      }
    } catch {
      // ignore queue read errors
    }

    if (stored.length) {
      console.log(`📜 Loaded ${stored.length} messages from localStorage for session:`, sessionId);
      setMessages(stored);
    }

    const storedOptions = localStorage.getItem(`dm-log-options-${sessionId}`);
    if (storedOptions) {
      try {
        const parsedOptions = JSON.parse(storedOptions);
        setCurrentOptions(parsedOptions);
      } catch (error) {
        console.error('Failed to parse stored options:', error);
      }
    }
  }, [sessionId, setSessionId]);
  
  // Auto-load intro on first game load
  useEffect(() => {
    const introPlayed = localStorage.getItem('dm-intro-played');
    
    // Only load intro if we have all required data
    if (
      campaignId && 
      worldBlueprint && 
      !introPlayed && 
      messages.length === 0 && 
      !introStartedRef.current
    ) {
      console.log('🎬 Auto-loading intro for new campaign');
      // Small delay to ensure all data is loaded
      setTimeout(() => {
        startCinematicIntro();
      }, 500);
    }
  }, [campaignId, worldBlueprint, messages.length]);

  // Save messages whenever they change (DIRECT localStorage)
  useEffect(() => {
    if (messages.length > 0 && sessionId) {
      // Trim to last 200 messages to prevent localStorage overflow
      const trimmed = messages.slice(-200);
      localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(trimmed));
    }
  }, [messages.length, sessionId]);

  // Save options whenever they change (DIRECT localStorage)
  useEffect(() => {
    if (currentOptions.length > 0 && sessionId) {
      localStorage.setItem(`dm-log-options-${sessionId}`, JSON.stringify(currentOptions));
    }
  }, [currentOptions, sessionId]);

  // Keyboard shortcuts for intent toggle
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.altKey && e.key === 'd') {
        e.preventDefault();
        setIntentMode('dm-question');
      } else if (e.altKey && e.key === 'a') {
        e.preventDefault();
        setIntentMode('action');
      } else if (e.altKey && e.key === 's') {
        e.preventDefault();
        setIntentMode('say');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // World-map event broadcast: when the player accepts a map event, the
  // WorldMapGraph fires a 'rpg:dm-beat' event carrying an arrival beat
  // (a Mercer-style 1-2 sentence narration). Append it to the Adventure Log
  // so the hook lands as narrative, not just a silent quest card.
  useEffect(() => {
    const handler = (e) => {
      const detail = e?.detail || {};
      const text = (detail.text || '').trim();
      if (!text || !sessionId) return;
      const beat = {
        type: 'dm',
        text,
        message: text,
        timestamp: Date.now(),
        isCinematic: true,
        source: detail.source || 'map-event',
        meta: {
          questTitle: detail.quest?.name,
          eventTitle: detail.eventTitle,
          regionName: detail.regionName,
        },
      };
      setMessages((prev) => {
        const next = [...prev, beat].slice(-200);
        try {
          localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(next));
        } catch {
          /* ignore */
        }
        return next;
      });
      // Re-fetch the quest log so the new active quest surfaces immediately.
      if (campaignId) {
        fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/quests`)
          .then((r) => (r.ok ? r.json() : null))
          .then((d) => { if (d?.quests) setQuests(d.quests); })
          .catch(() => {});
      }
    };
    window.addEventListener('rpg:dm-beat', handler);
    return () => window.removeEventListener('rpg:dm-beat', handler);
  }, [campaignId, sessionId]);

  // Generate TTS for a specific message
  // Helper function to safely extract narration text from any response structure
  const extractNarration = (data) => {
    // If data is null/undefined, return empty string
    if (!data) return '';
    
    // If data is a string, check if it's JSON
    if (typeof data === 'string') {
      let trimmed = data.trim();
      
      // Remove code fence markers if present
      if (trimmed.startsWith('```json') || trimmed.startsWith('```')) {
        trimmed = trimmed.replace(/^```(json)?/g, '').replace(/```$/g, '').trim();
      }
      
      // Remove 'json' prefix if present (e.g., "json{...}")
      if (trimmed.startsWith('json{') || trimmed.startsWith('json[')) {
        trimmed = trimmed.substring(4).trim();
      }
      
      // Check if it looks like JSON (starts with { or [)
      if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
        try {
          const parsed = JSON.parse(trimmed);
          return extractNarration(parsed);
        } catch (e) {
          // Not valid JSON, return as-is
          console.warn('Failed to parse JSON intro:', e);
          return data;
        }
      }
      return data;
    }
    
    // If data is an object, try to extract narration field
    if (typeof data === 'object') {
      return data.narration || data.intro_markdown || data.text || '';
    }
    
    return String(data);
  };

  const generateAudioForMessage = async (messageIndex) => {
    const message = messages[messageIndex];
    if (!message || message.type !== 'dm' || message.audioUrl) {
      return;
    }

    setIsLoading(true);

    try {
      const audioUrl = await generateSpeech(message.text, 'onyx', false);
      
      // Update message in local state
      const updatedMessages = [...messages];
      updatedMessages[messageIndex] = { ...message, audioUrl, isGeneratingAudio: false };
      setMessages(updatedMessages);
    } catch (err) {
      console.error('Failed to generate audio:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // "Remember this" — opens a dialog so the player can edit the auto-derived
  // title and type before committing to the Knowledge Deck.
  const [rememberDialog, setRememberDialog] = useState({
    open: false,
    messageIndex: null,
    saving: false,
  });

  // "Report this scene" — one-click dev snapshot for off-feeling DM turns.
  const [reportDialog, setReportDialog] = useState({
    open: false,
    messageIndex: null,
    saving: false,
  });

  const handleOpenReport = (messageIndex) => {
    const message = messages[messageIndex];
    if (!message || message.type !== 'dm') return;
    if (!campaignId) {
      window.showToast && window.showToast('No active campaign to report against.', 'error');
      return;
    }
    setReportDialog({ open: true, messageIndex, saving: false });
  };

  const handleReportConfirm = async ({ note, tags }) => {
    const { messageIndex } = reportDialog;
    const message = messageIndex != null ? messages[messageIndex] : null;
    if (!message || !campaignId) {
      setReportDialog({ open: false, messageIndex: null, saving: false });
      return;
    }
    // Find the most recent player action before this DM beat — provides rich
    // context to the report without requiring the client to pass turn history.
    let priorActionText = '';
    for (let i = messageIndex - 1; i >= 0; i -= 1) {
      const m = messages[i];
      if (m && (m.type === 'player' || m.type === 'action' || m.type === 'say')) {
        priorActionText = m.text || m.message || '';
        break;
      }
    }
    setReportDialog((d) => ({ ...d, saving: true }));
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/scene-reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messageText: message.text,
          playerActionText: priorActionText,
          userNote: note || '',
          tags: tags || [],
        }),
      });
      if (!res.ok) throw new Error(`Report failed: ${res.status}`);
      await res.json();
      // Mark the message so the flag button turns red + disables.
      setMessages((prev) =>
        prev.map((m, i) => (i === messageIndex ? { ...m, reported: true } : m))
      );
      window.showToast && window.showToast('Scene reported. Thanks — full context captured.', 'success');
      setReportDialog({ open: false, messageIndex: null, saving: false });
    } catch (err) {
      console.error('Scene report failed:', err);
      window.showToast && window.showToast('Could not file report. Try again.', 'error');
      setReportDialog((d) => ({ ...d, saving: false }));
    }
  };

  const handleRememberBeat = (messageIndex) => {
    const message = messages[messageIndex];
    if (!message || message.type !== 'dm' || message.remembered) return;
    if (!campaignId) {
      window.showToast && window.showToast('No active campaign to remember this in.', 'error');
      return;
    }
    setRememberDialog({ open: true, messageIndex, saving: false });
  };

  const handleRememberConfirm = async ({ title, type }) => {
    const { messageIndex } = rememberDialog;
    const message = messageIndex != null ? messages[messageIndex] : null;
    if (!message || !campaignId) {
      setRememberDialog({ open: false, messageIndex: null, saving: false });
      return;
    }

    setRememberDialog((d) => ({ ...d, saving: true }));
    setMessages((prev) =>
      prev.map((m, i) => (i === messageIndex ? { ...m, remembering: true } : m))
    );

    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/log/cards/remember`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: message.text,
          title,
          type,
          tags: ['remembered', 'dm-beat'],
        }),
      });
      if (!res.ok) throw new Error(`Remember failed: ${res.status}`);
      const data = await res.json();
      setMessages((prev) =>
        prev.map((m, i) =>
          i === messageIndex
            ? { ...m, remembered: true, remembering: false, rememberedCardId: data?.card?.id }
            : m
        )
      );
      window.showToast &&
        window.showToast(`Pinned to Knowledge Deck: "${data?.card?.title || title}"`, 'success');
      setRememberDialog({ open: false, messageIndex: null, saving: false });
    } catch (err) {
      console.error('Failed to remember beat:', err);
      setMessages((prev) =>
        prev.map((m, i) => (i === messageIndex ? { ...m, remembering: false } : m))
      );
      window.showToast && window.showToast('Could not save that beat. Try again.', 'error');
      setRememberDialog((d) => ({ ...d, saving: false }));
    }
  };

  // 👍 / 👎 — react to a DM narration beat. The backend distills the reaction
  // (with the surrounding narration) into a persistent DM Lesson: 👍 becomes
  // a style_preference, 👎 becomes a taboo. Lessons are then injected into
  // future DM turns so the model gets better with every interaction.
  const handleBeatReaction = async (messageIndex, reaction) => {
    const message = messages[messageIndex];
    if (!message || message.type !== 'dm') return;
    if (!campaignId) {
      toast.error('No active campaign — load a game first.');
      return;
    }
    if (message.reaction === reaction) return;  // already tapped
    // Optimistic UI — mark the reaction immediately
    setMessages((prev) => prev.map((m, i) =>
      i === messageIndex ? { ...m, reaction, reactionBusy: true } : m
    ));
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/dm-lessons/reaction`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            reaction,
            narration: message.text || message.message || '',
            beat_title: message.chronicleTitle || (message.isCinematic ? 'Cinematic Intro' : null),
            character_id: gameStateContext?.characterState?.id || null,
            message_id: `msg_${messageIndex}_${message.timestamp || ''}`,
          }),
        }
      );
      if (!res.ok) throw new Error(`Reaction failed: ${res.status}`);
      const data = await res.json();
      setMessages((prev) => prev.map((m, i) =>
        i === messageIndex ? { ...m, reactionBusy: false, lessonId: data.lesson?.id } : m
      ));
      if (data.lesson) {
        const action = data.action === 'merged' ? 'reinforced an existing lesson' : 'added a new lesson';
        toast.success(
          reaction === 'like'
            ? `Noted — DM ${action} (style: keep doing this).`
            : `Got it — DM ${action} (avoid this pattern).`,
          { duration: 3500 }
        );
      } else {
        toast('Reaction noted, but no clear lesson to distill.', { duration: 2500 });
      }
    } catch (e) {
      // Roll back the optimistic mark on failure
      setMessages((prev) => prev.map((m, i) =>
        i === messageIndex ? { ...m, reaction: null, reactionBusy: false } : m
      ));
      toast.error(e.message || 'Could not save reaction.');
    }
  };

  // "Pin as quest" — promote a DM narration beat into an ACTIVE quest card that
  // shows up in the Quest Log AND gets prioritized by the DM.
  const handlePinAsQuest = async (messageIndex) => {
    const message = messages[messageIndex];
    if (!message || message.type !== 'dm' || message.pinnedAsQuest) return;
    if (!campaignId) {
      window.showToast && window.showToast('No active campaign to pin a quest in.', 'error');
      return;
    }
    setMessages(prev => prev.map((m, i) => (i === messageIndex ? { ...m, pinningQuest: true } : m)));
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/log/cards/remember-as-quest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: message.text }),
      });
      if (!res.ok) throw new Error(`Pin quest failed: ${res.status}`);
      const data = await res.json();
      setMessages(prev =>
        prev.map((m, i) =>
          i === messageIndex
            ? { ...m, pinnedAsQuest: true, pinningQuest: false, pinnedQuestId: data?.quest?.quest_id }
            : m
        )
      );
      window.showToast && window.showToast(`Pinned as quest: "${data?.quest?.name || 'lead'}"`, 'success');
      // Refresh quest log
      fetchQuests();
    } catch (err) {
      console.error('Failed to pin as quest:', err);
      setMessages(prev => prev.map((m, i) => (i === messageIndex ? { ...m, pinningQuest: false } : m)));
      window.showToast && window.showToast('Could not pin as quest. Try again.', 'error');
    }
  };

  // Fetch quests from the backend and hydrate the local `quests` state.
  const fetchQuests = useCallback(async () => {
    if (!campaignId) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/quests`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setQuests(data?.quests || []);
    } catch (err) {
      console.warn('Failed to load quests:', err);
    }
  }, [campaignId]);

  // Load quests on mount / when campaign changes
  useEffect(() => {
    fetchQuests();
  }, [fetchQuests]);

  const handleUpdateQuestStatus = async (questId, status) => {
    if (!campaignId || !questId) return;
    // Optimistic update
    setQuests(prev => prev.map(q => (q.quest_id === questId ? { ...q, status } : q)));
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/quests/${questId}/status`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status }),
        }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      window.showToast && window.showToast(`Quest marked ${status}.`, 'success');
    } catch (err) {
      console.error('Quest status update failed:', err);
      window.showToast && window.showToast('Could not update quest. Retrying…', 'error');
      fetchQuests(); // revert via source of truth
    }
  };

  const startCinematicIntro = async () => {
    console.log('🎬 Checking for intro...');
    
    if (introStartedRef.current) {
      console.log('⏭️ Intro already played');
      return;
    }
    
    introStartedRef.current = true;
    setIsLoading(true);
    
    try {
      // CRITICAL: Check if intro already exists in localStorage with entity_mentions
      // This prevents overwriting the properly formatted intro from RPGGame
      const storedMessages = localStorage.getItem(`dm-log-messages-${sessionId}`);
      if (storedMessages) {
        try {
          const parsed = JSON.parse(storedMessages);
          if (parsed.length > 0 && parsed[0].text) {
            console.log('✅ Intro already in localStorage with', parsed[0].entity_mentions?.length || 0, 'entity mentions');
            console.log('⏭️ Using stored intro instead of worldBlueprint.intro');
            setMessages(parsed);
            localStorage.setItem('dm-intro-played', '1');
            setIsLoading(false);
            return;
          }
        } catch (e) {
          console.warn('Failed to parse stored messages:', e);
        }
      }
      
      // Safety check: ensure worldBlueprint and intro exist
      if (!worldBlueprint) {
        console.warn('⚠️ worldBlueprint not loaded yet');
        localStorage.setItem('dm-intro-played', '1');
        return;
      }
      
      const intro = worldBlueprint.intro;
      
      // Use extractNarration to safely handle any response structure
      const cleanIntro = extractNarration(intro);
      
      if (!cleanIntro || cleanIntro.trim().length === 0) {
        console.warn('⚠️ No valid intro found in worldBlueprint');
        localStorage.setItem('dm-intro-played', '1');
        return;
      }
      
      // Intro is valid, display it (FALLBACK PATH - should rarely be used)
      console.log('⚠️ Loading intro from worldBlueprint (no entity_mentions):', cleanIntro.substring(0, Math.min(100, cleanIntro.length)) + '...');
      
      // Add intro as first message
      const introMessage = {
        type: 'dm',
        text: cleanIntro,
        timestamp: Date.now(),
        isIntro: true,
        entity_mentions: [] // Empty array - this is fallback path
      };
      
      setMessages([introMessage]);
      
      // Mark intro as played
      localStorage.setItem('dm-intro-played', '1');
      
      // Generate TTS if enabled
      if (isTTSEnabled && generateSpeech) {
        try {
          const audioUrl = await generateSpeech(cleanIntro, 'onyx', false);
          if (audioUrl) {
            const updatedIntroMessage = { ...introMessage, audioUrl };
            setMessages([updatedIntroMessage]);
          }
        } catch (err) {
          console.error('Failed to generate intro audio:', err);
        }
      }
    } catch (error) {
      console.error('❌ Failed to load intro:', error);
      // Mark as played to avoid infinite retry
      localStorage.setItem('dm-intro-played', '1');
    } finally {
      setIsLoading(false);
      setShowIntro(false);
    }
  };

  const sendToAPI = async (payload, isCinematic = false) => {
    const startTime = performance.now();
    console.log('📤 Sending to DM API:', payload);

    setIsLoading(true);

    try {
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const duration = Math.round(performance.now() - startTime);
      console.log(`⏱️ DM responded in ${duration}ms`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const response_envelope = await response.json();
      console.log('📥 DUNGEON FORGE Response:', response_envelope);

      // Extract data from standard envelope {success, data, error}
      const data = response_envelope.data || response_envelope;

      // Sync turn usage into AuthContext so UsageBanner updates without extra fetch
      if (data.usage) patchUsage(data.usage);

      // DUNGEON FORGE: Handle world_state_update
      if (data.world_state_update && Object.keys(data.world_state_update).length > 0) {
        console.log('🗺️ WORLD STATE UPDATE:', data.world_state_update);
        updateWorld(data.world_state_update);

        // Roleplay alignment + chaos meter notifications
        const chaosInfo = data.world_state_update.chaos;
        if (chaosInfo) {
          const align = chaosInfo.alignment || {};
          if (align.severity > 0 && align.reason) {
            const tone = align.severity >= 3 ? 'error' : align.severity === 2 ? 'warning' : 'info';
            const sigil = align.severity >= 3 ? '🩸' : '⚠';
            const axis = align.axis ? `${align.axis.charAt(0).toUpperCase() + align.axis.slice(1)} broken — ` : '';
            const msg = `${sigil} ${axis}${align.reason} (Chaos +${chaosInfo.delta})`;
            if (window.showToast) window.showToast(msg, tone);
            else toast[tone === 'error' ? 'error' : 'warning'](msg);
          }
          if (chaosInfo.drafted_curse) {
            const c = chaosInfo.drafted_curse;
            const msg = `☠️ Curse drafted: ${c.title} (${c.rarity}) — ${c.description.slice(0, 100)}…`;
            toast.error(msg, { duration: 8000 });
          }
        }
      }

      // P3: Update quests from world_state
      if (data.world_state_update && data.world_state_update.quests) {
        setQuests(data.world_state_update.quests);
      }

      // P3: Handle player_updates (XP, level-ups, defeat)
      if (data.player_updates && Object.keys(data.player_updates).length > 0) {
        console.log('✨ PLAYER UPDATES:', data.player_updates);
        
        // Update character stats
        if (data.player_updates.xp_gained) {
          updateCharContext({ 
            current_xp: (gameStateContext.characterState?.current_xp || 0) + data.player_updates.xp_gained 
          });
        }
        
        // XP gained notification
        if (data.player_updates.xp_gained > 0) {
          const xpReason = data.player_updates.xp_reason || '';
          const xpMsg = xpReason 
            ? `+${data.player_updates.xp_gained} XP: ${xpReason}`
            : `+${data.player_updates.xp_gained} XP`;
          if (window.showToast) {
            window.showToast(xpMsg, 'success');
          }
        }
        
        // Level up notifications
        if (data.player_updates.level_up_events && data.player_updates.level_up_events.length > 0) {
          for (const event of data.player_updates.level_up_events) {
            const level = event.split(':')[1];
            const levelMsg = `🎉 LEVEL UP! You are now level ${level}!`;
            if (window.showToast) {
              window.showToast(levelMsg, 'info');
            }
          }
        }
        
        // Rest recovery — update HP and spell slots immediately
        if (data.player_updates.rest_result) {
          const rr = data.player_updates.rest_result;
          const patch = { hp: rr.hp };
          if (rr.spell_slots !== undefined) patch.spell_slots = rr.spell_slots;
          if (rr.spell_slots_max !== undefined) patch.spell_slots_max = rr.spell_slots_max;
          if (rr.conditions !== undefined) patch.conditions = rr.conditions;
          if (rr.hit_dice_remaining !== undefined) patch.hit_dice_remaining = rr.hit_dice_remaining;
          if (rr.hit_dice_max !== undefined) patch.hit_dice_max = rr.hit_dice_max;
          updateCharContext(patch);
          if (window.showToast) {
            const diceInfo = rr.hit_dice_remaining !== undefined
              ? ` (${rr.hit_dice_remaining}/${rr.hit_dice_max} hit dice)`
              : '';
            const msg = rr.rest_type === 'long'
              ? `💤 Long Rest — fully restored! +${rr.hp_gained} HP`
              : rr.no_hit_dice
                ? `⏸️ Short Rest — no hit dice remaining`
                : `⏸️ Short Rest — +${rr.hp_gained} HP${diceInfo}`;
            window.showToast(msg, 'success');
          }
        }

        // Defeat handled - show modal
        if (data.player_updates.defeat_handled) {
          setShowDefeatModal(true);
          setDefeatInfo({
            currentHP: data.player_updates.hp_restored,
            maxHP: gameStateContext.characterState?.hp?.max || gameStateContext.characterState?.max_hp || 10,
            injuryCount: data.player_updates.injury_count,
            xpPenalty: data.player_updates.xp_penalty || 0
          });
          
          // Update character HP
          if (data.player_updates.hp_restored !== undefined) {
            updateCharContext({ 
              hp: { ...gameStateContext.characterState?.hp, current: data.player_updates.hp_restored } 
            });
          }
          
          // P3.5: Show XP penalty toast if any
          if (data.player_updates.xp_penalty > 0 && window.showToast) {
            window.showToast(`-${data.player_updates.xp_penalty} XP`, 'error');
          }
        }
      }

      // DUNGEON FORGE: Handle check_request (v3.1 compatibility: also handles requested_check)
      const checkRequest = data.check_request || data.requested_check;
      if (checkRequest) {
        console.log('🎯 NEW CHECK REQUEST:', checkRequest);
        console.log('🎯 Check request received:', checkRequest);
        console.log('🎯 DC value:', checkRequest.dc);
        setPendingCheck(checkRequest);
        
        // Notify parent component (FocusedRPG)
        if (props.onCheckRequest) {
          props.onCheckRequest(checkRequest);
        }
      }

      // DUNGEON FORGE: Handle combat
      if (data.combat_started) {
        console.log('⚔️ Combat started!');
        setIsCombatActive(true);
        const cs = { isActive: true, combatId: `combat-${Date.now()}`, ...(data.combat_state || {}) };
        setCombatState(cs);
        // Bubble up to RPGGame → triggers full-screen CombatScreen
        if (props.onCombatStart) props.onCombatStart(cs);
      }

      if (data.combat_active && data.combat_state) {
        console.log('⚔️ Combat continues...');
        setIsCombatActive(true);
        const cs = { isActive: true, ...data.combat_state };
        setCombatState(cs);
        // If RPGGame doesn't have the screen up yet, open it
        if (props.onCombatStart) props.onCombatStart(cs);
      }

      if (data.combat_over) {
        console.log('⚔️ Combat ended:', data.outcome);
        setIsCombatActive(false);
        setCombatState({
          isActive: false,
          outcome: data.outcome,
          combatId: null,
          participants: [],
          turnOrder: [],
          currentTurnIndex: 0,
        });
      }

      // Add DM message to log
      if (data.narration) {
        console.log('💬 Received DM narration:', data.narration.substring(0, 100) + '...');
        const msgId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const dmMsg = {
          id: msgId,
          type: 'dm',
          text: data.narration,
          options: data.options || [],
          checkRequest: data.check_request || data.requested_check || null,
          npcMentions: data.npc_mentions || [],
          entity_mentions: data.entity_mentions || [],
          hooks: data.hooks || [],
          engagedHookId: data.engaged_hook_id || null,
          intentHint: data.intent_hint || null,  // {check_type, matched, confidence}
          timestamp: Date.now(),
          isCinematic: isCinematic,
          audioUrl: null,
          isGeneratingAudio: false
        };

        console.log('📝 Adding DM message to state, current message count:', messages.length);
        setMessages(prev => {
          const updated = [...prev, dmMsg];
          console.log('📝 New message count will be:', updated.length);
          return updated;
        });

        // If the player's action engaged a hook and the backend drafted a
        // storyline, surface it as the new active investigation. This drives
        // the side panel + reward flow.
        if (data.storyline) {
          setActiveStoryline(data.storyline);
          window.showToast &&
            window.showToast(
              `New investigation: ${data.storyline.title}`,
              'success'
            );
          // Refresh quests so the linked quest card appears in the log.
          if (campaignId) {
            fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/quests`)
              .then((r) => (r.ok ? r.json() : null))
              .then((d) => { if (d?.quests) setQuests(d.quests); })
              .catch(() => {});
          }
        }

        // Auto-generate TTS if enabled (non-blocking)
        if (isTTSEnabled && !isCinematic) {
          setTimeout(async () => {
            try {
              const audioUrl = await generateSpeech(data.narration, 'onyx', true);
              setMessages(prev => prev.map(msg => 
                msg.id === msgId ? { ...msg, audioUrl } : msg
              ));
            } catch (err) {
              console.error('TTS auto-generation failed:', err);
            }
          }, 100);
        }

        if (isCinematic) {
          setShowIntro(false);
        }
        
        setCurrentOptions(data.options || []);

        // Autosave signal — the DM response was persisted server-side as
        // soon as it landed. Pulse the AutoSaveIndicator so the player
        // sees a tactile confirmation that their progress is safe.
        try {
          window.dispatchEvent(new CustomEvent('rpg:autosaved', {
            detail: { reason: 'action' },
          }));
        } catch {}
      }

      // Paused-quest obligation reminder — injected as a separate world-event
      // beat immediately after the main DM narration (if one fired this turn).
      if (data.obligation_reminder && data.obligation_reminder.narration) {
        const reminder = data.obligation_reminder;
        const reminderMsg = {
          id: `obligation-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
          type: 'dm',
          text: reminder.narration,
          timestamp: Date.now() + 10,
          isCinematic: true,
          source: 'obligation-reminder',
          meta: {
            storylineTitle: reminder.storyline_title,
            npcName: reminder.npc_name,
            deliveryMethod: reminder.delivery_method,
            urgency: reminder.urgency,
            storylineId: reminder.storyline_id,
          },
        };
        setMessages((prev) => {
          const next = [...prev, reminderMsg].slice(-200);
          if (sessionId) {
            try { localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(next)); } catch {}
          }
          return next;
        });
      }

      // Spontaneous world event — an NPC approaches the player in character.
      // Injected as a distinct beat after obligation reminders.
      if (data.world_event && data.world_event.narration) {
        const evt = data.world_event;
        const evtMsg = {
          id: `world-event-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
          type: 'dm',
          text: evt.narration,
          timestamp: Date.now() + 20,
          isCinematic: true,
          source: 'world-event',
          meta: {
            npcName: evt.npc_name,
            eventType: evt.event_type,
            category: evt.category,
          },
        };
        setMessages((prev) => {
          const next = [...prev, evtMsg].slice(-200);
          if (sessionId) {
            try { localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(next)); } catch {}
          }
          return next;
        });
      }

    } catch (error) {
      console.error('❌ DM API Error:', error);
      const errorMsg = {
        id: `error-${Date.now()}`,
        type: 'error',
        text: `Connection error: ${error.message}`,
        timestamp: Date.now(),
        retry: true
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // buildActionPayload is now provided by GameStateContext

  const sendPlayerMessage = async (playerMessage, messageType = null, checkResult = null) => {
    if (!playerMessage.trim() || !sessionId) return;

    const actualType = messageType || intentMode || 'action';

    // Add player message to log with intent
    const msgId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const playerMsg = {
      id: msgId,
      type: 'player',
      text: playerMessage,
      messageType: actualType,
      timestamp: Date.now()
    };
    setMessages(prev => [...prev, playerMsg]);
    setCurrentOptions([]);

    // DUNGEON FORGE: Use buildActionPayload from context
    const actionPayload = buildActionPayload(playerMessage, checkResult);
    
    if (!actionPayload) {
      console.error('❌ Cannot send action: missing campaign_id or character_id');
      const errorMsg = {
        id: `error-${Date.now()}`,
        type: 'error',
        text: 'Cannot send action: Campaign not initialized. Please create a new character.',
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMsg]);
      return;
    }

    console.log('🚀 Sending DUNGEON FORGE action payload:', actionPayload);

    // ─── OFF-HOOK SPAWN PROBE ───────────────────────────────────────────
    // Before falling through to lean_dm, see if the player's action is
    // off-hook enough to deserve its own storyline. Only fire for typed
    // "action" messages — skip narrate/dialogue intents and short check
    // confirmations.
    const isProbeEligible = (
      campaignId &&
      actualType === 'action' &&
      !checkResult &&
      playerMessage.trim().length >= 4 &&
      !/^(roll|i roll|check|proceed)\b/i.test(playerMessage.trim())
    );
    if (isProbeEligible) {
      // If we already asked the player to clarify and this IS the reply,
      // join the original action + the clarification into one richer
      // payload so the spawn endpoint can ground the storyline.
      const probeAction = pendingClarification
        ? pendingClarification.originalAction
        : playerMessage;
      const probeNarrationContext = pendingClarification
        ? `Player clarification: ${playerMessage}`
        : '';

      try {
        const probeRes = await fetch(
          `${BACKEND_URL}/api/campaigns/${campaignId}/storylines/spawn-from-action`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              character_id: actionPayload.character_id,
              player_action: probeAction,
              current_storyline_id: activeStoryline?.id || null,
              narration_context: probeNarrationContext || null,
            }),
          }
        );
        if (probeRes.ok) {
          const probe = await probeRes.json();

          // ── Clarification branch (vague verb, < 6 words) ──
          if (probe.needs_clarification && probe.clarification_question) {
            setPendingClarification({
              originalAction: probeAction,
              tentativeSlug: probe.tentative_mission_type_slug || null,
            });
            const askBeat = {
              type: 'dm',
              text: probe.clarification_question,
              message: probe.clarification_question,
              timestamp: Date.now(),
              isCinematic: false,
              source: 'spawn-clarify',
            };
            setMessages((prev) => {
              const next = [...prev, askBeat].slice(-200);
              if (sessionId) {
                try { localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(next)); } catch {}
              }
              return next;
            });
            return; // wait for player's clarification reply
          }

          // ── Spawn branch ──
          if (probe.spawned && probe.storyline) {
            // Clear any pending clarification — we've used it.
            setPendingClarification(null);
            // 1. Pause-summary cue (if applicable)
            if (probe.paused_summary_narration) {
              const b = {
                type: 'dm', text: probe.paused_summary_narration,
                message: probe.paused_summary_narration, timestamp: Date.now(),
                isCinematic: true, source: 'storyline-paused',
                meta: { storylineTitle: probe.storyline.title },
              };
              setMessages((prev) => [...prev, b].slice(-200));
            }
            // 2. Transition narration ("DM plays along")
            if (probe.transition_narration) {
              const b = {
                type: 'dm', text: probe.transition_narration,
                message: probe.transition_narration, timestamp: Date.now() + 1,
                isCinematic: true, source: 'spawn-transition',
                meta: { missionType: probe.mission_type?.name },
              };
              setMessages((prev) => [...prev, b].slice(-200));
            }
            // 3. First beat of the new storyline
            const firstBeat = (probe.storyline.beats || [])[0] || {};
            if (firstBeat.description) {
              const b = {
                type: 'dm', text: firstBeat.description,
                message: firstBeat.description, timestamp: Date.now() + 2,
                isCinematic: true, source: 'spawn-first-beat',
                meta: { storylineTitle: probe.storyline.title },
              };
              setMessages((prev) => [...prev, b].slice(-200));
            }
            setActiveStoryline(probe.storyline);
            const mt = probe.mission_type || {};
            if (window.showToast) {
              window.showToast(
                `${mt.icon || '🎯'} New thread: ${probe.storyline.title}`,
                'success'
              );
            }
            // Don't fall through to lean_dm — the spawn IS the response.
            return;
          }
        }
      } catch (probeErr) {
        console.warn('Spawn probe failed (falling back to lean_dm):', probeErr);
      }
    }
    // ────────────────────────────────────────────────────────────────────

    // Clear pending clarification if the player's input went through
    // without triggering the spawn path (e.g. they answered with check input).
    if (pendingClarification) setPendingClarification(null);

    await sendToAPI(actionPayload);
  };

  const handleOptionClick = (option) => {
    console.log('🎯 OPTION CLICKED:', option);
    
    // AGGRESSIVE PROCEED DETECTION
    const isProceedAction = (
      option.toLowerCase().includes('proceed') || 
      option.toLowerCase().includes('stealth check') ||
      option.toLowerCase().includes('investigation check') ||
      option.toLowerCase().includes('perception check') ||
      option.toLowerCase().includes('athletics check') ||
      option.toLowerCase().includes('dexterity') ||
      option.toLowerCase().includes('strength') ||
      option.toLowerCase().includes('constitution') ||
      option.toLowerCase().includes('intelligence') ||
      option.toLowerCase().includes('wisdom') ||
      option.toLowerCase().includes('charisma') ||
      (option.toLowerCase().includes('check') && option.length < 50) ||
      option.toLowerCase().includes('roll')
    );
    
    // OLD: Auto-roll logic removed - CheckRollPanel handles all rolls now
    // if (isProceedAction && pendingCheck) {
    //   console.log('🎲 DETECTED CHECK CONFIRMATION - EXECUTING DICE ROLL');
    //   ...
    // }
    
    console.log('📤 SENDING AS REGULAR MESSAGE');
    sendPlayerMessage(option, 'action');
  };

  const getCheckFormula = (checkRequest) => {
    if (!checkRequest) {
      console.error('No checkRequest provided to getCheckFormula');
      return '1d20+0';
    }
    
    const { mode = 'normal', situational_bonus = 0, ability = 'DEX', skill = 'Stealth' } = checkRequest;
    
    console.log('🎲 Building formula for:', checkRequest);
    console.log('🎲 Character stats:', gameStateContext.characterState?.stats);
    console.log('🎲 Character proficiencies:', gameStateContext.characterState?.proficiencies);
    
    // Calculate modifier from character state and skill
    const abilityModifier = getAbilityModifier(gameStateContext.characterState?.stats, ability.toLowerCase()) || 0;
    const proficiencyBonus = isProficient(gameStateContext.characterState?.proficiencies, skill) ? (gameStateContext.characterState?.proficiency_bonus || 2) : 0;
    const totalModifier = abilityModifier + proficiencyBonus + situational_bonus;
    
    console.log('🎲 Ability modifier:', abilityModifier);
    console.log('🎲 Proficiency bonus:', proficiencyBonus);
    console.log('🎲 Total modifier:', totalModifier);
    
    // Build formula based on advantage/disadvantage
    if (mode === 'advantage') {
      return `2d20kh1${totalModifier >= 0 ? '+' : ''}${totalModifier}`;
    } else if (mode === 'disadvantage') {
      return `2d20kl1${totalModifier >= 0 ? '+' : ''}${totalModifier}`;
    } else {
      return `1d20${totalModifier >= 0 ? '+' : ''}${totalModifier}`;
    }
  };

  const handleRetry = (messageIndex) => {
    const allMsgs = messages.slice(0, messageIndex);
    const lastPlayerMsg = allMsgs.reverse().find(m => m.type === 'player');
    if (lastPlayerMsg) {
      sendPlayerMessage(lastPlayerMsg.text);
    }
  };

  // OLD: handleDiceRoll function removed - CheckRollPanel handles all rolls now
  /*
  const handleDiceRoll = async ({ mode, formula, d20, modifier, total }) => {
    console.log('🎲 Processing dice roll:', { mode, formula, d20, modifier, total });
    
    if (!pendingCheck) {
      console.error('❌ No pending check found for dice roll');
      const errorMsg = {
        id: `error-${Date.now()}`,
        type: 'error',
        text: 'No active ability check to roll for. Please request a check first.',
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMsg]);
      return;
    }
    
    if (mode === 'auto') {
      try {
        const response = await fetch(diceEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ formula })
        });

        if (!response.ok) {
          throw new Error(`Dice API error: ${response.status}`);
        }

        const responseData = await response.json();
        console.log('🎲 Dice API response:', responseData);
        
        // Extract data from API wrapper {success, data, error}
        const rollData = responseData.data || responseData;
        console.log('🎲 Extracted roll data:', rollData);
        console.log('🎲 Modifier from API:', rollData.modifier);

        // Add roll result message
        const msgId = `roll-${Date.now()}`;
        const rollMsg = {
          id: msgId,
          type: 'roll_result',
          rollData: rollData,
          checkRequest: pendingCheck,
          timestamp: Date.now()
        };
        setMessages(prev => [...prev, rollMsg]);
        
        // Process check outcome
        const outcome = getCheckOutcome(rollData.total, pendingCheck.dc);
        console.log(`📊 Check outcome: ${outcome} (${rollData.total} vs DC ${pendingCheck.dc})`);
        
        // Send outcome to DM for continued narration
        const outcomeMessage = `I rolled ${rollData.total} for the ${pendingCheck.ability} check (DC ${pendingCheck.dc}). Result: ${outcome}.`;
        console.log('🎯 Building outcome payload with message:', outcomeMessage);
        const outcomePayload = buildActionPayload(outcomeMessage, rollData.total);
        console.log('📦 Outcome payload:', outcomePayload);
        
        if (!outcomePayload) {
          console.error('❌ Failed to build outcome payload!');
          const errorMsg = {
            id: `error-${Date.now()}`,
            type: 'error',
            text: 'Failed to send check result to DM. Campaign may not be initialized.',
            timestamp: Date.now()
          };
          setMessages(prev => [...prev, errorMsg]);
          return;
        }
        
        // Clear pending check and continue story
        setPendingCheck(null);
        console.log('🚀 Sending outcome to DM API...');
        await sendToAPI(outcomePayload);
        console.log('✅ DM response should now be visible');
        
      } catch (error) {
        console.error('❌ Dice roll error:', error);
        const errorMsg = {
          id: `error-${Date.now()}`,
          type: 'error',
          text: `Dice roll failed: ${error.message}`,
          timestamp: Date.now()
        };
        setMessages(prev => [...prev, errorMsg]);
      }
    } else {
      // Handle manual roll
      const rollData = {
        formula,
        rolls: [d20],
        kept: [d20],
        sum_kept: d20,
        modifier,
        total
      };

      const msgId = `roll-${Date.now()}`;
      const rollMsg = {
        id: msgId,
        type: 'roll_result',
        rollData: rollData,
        checkRequest: pendingCheck,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, rollMsg]);
      
      const outcome = getCheckOutcome(total, pendingCheck.dc);
      console.log(`📊 Manual check outcome: ${outcome} (${total} vs DC ${pendingCheck.dc})`);
      
      const outcomeMessage = `I rolled ${total} for the ${pendingCheck.ability} check (DC ${pendingCheck.dc}). Result: ${outcome}.`;
      const outcomePayload = buildActionPayload(outcomeMessage, total);
      
      setPendingCheck(null);
      await sendToAPI(outcomePayload);
    }
  };
  */

  const resetAdventureHandler = () => {
    console.log('🔄 Resetting adventure...');
    
    setMessages([]);
    setPendingCheck(null);
    setIsCombatActive(false);
    setCombatState({ 
      isActive: false, 
      combatId: null, 
      participants: [], 
      turnOrder: [], 
      currentTurnIndex: 0 
    });
    setShowIntro(false);
    setCurrentOptions([]);
    setShowDefeatModal(false);
    setDefeatInfo(null);
    
    if (window.showToast) {
      window.showToast('🔄 Adventure reset!', 'success');
    }
  };

  // Expose sendPlayerMessage to parent via ref
  useImperativeHandle(ref, () => ({
    sendMessage: sendPlayerMessage,
    isLoading: isLoading,
    intentMode: intentMode || 'action',
    setIntentMode: (mode) => setIntentMode(mode),
    resetAdventure: resetAdventureHandler
  }));

  const formatMessage = (message) => {
    if (typeof message !== 'string') return message;
    
    // Handle both actual newlines and literal \n sequences
    // First, replace literal \n\n with actual newlines
    let cleanedMessage = message.replace(/\\n\\n/g, '\n\n').replace(/\\n/g, '\n');
    
    // Split on double newlines to create paragraphs
    const paragraphs = cleanedMessage.split(/\n\s*\n/).filter(p => p.trim());
    
    // If only one paragraph, just return it
    if (paragraphs.length <= 1) return cleanedMessage;
    
    // Return paragraphs with proper spacing
    return paragraphs.map((paragraph, idx) => (
      <p key={idx} className={idx > 0 ? 'mt-3' : ''}>
        {paragraph.split('\n').map((line, lineIdx) => (
          <React.Fragment key={lineIdx}>
            {lineIdx > 0 && <br />}
            {line}
          </React.Fragment>
        ))}
      </p>
    ));
  };

  return (
    <Card className="adventure-papyrus h-full bg-black/95 border-amber-600/30 backdrop-blur-sm overflow-hidden flex flex-col">
      <CardContent className="p-0 flex-1 flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="p-3 border-b border-amber-600/20 flex-shrink-0">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <h2 className="adv-papyrus-title text-amber-400 font-semibold text-sm flex items-center gap-2 shrink-0">
                <Dice6 className="h-4 w-4" />
                Adventure Log
              </h2>
              {activeStoryline?.mission_type && (
                <MissionPhaseBadge storyline={activeStoryline} />
              )}
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {/* TTS Toggle */}
              <Button
                onClick={toggleTTS}
                variant="ghost"
                size="sm"
                className={`h-7 px-2 ${isTTSEnabled ? 'bg-purple-600/20 text-purple-400' : 'text-gray-400'}`}
                title={isTTSEnabled ? 'Disable narration audio' : 'Enable narration audio'}
              >
                <Volume2 className="h-4 w-4 mr-1" />
                <span className="text-xs">TTS</span>
              </Button>
            </div>
          </div>
        </div>

        {/* Selected NPC Indicator */}
        {selectedNpc && intentMode === 'say' && (
          <div className="px-3 py-2 bg-purple-900/30 border-b border-purple-600/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-purple-400" />
              <span className="text-purple-300 text-sm">
                Talking to: <span className="font-semibold">{selectedNpc.name}</span>
              </span>
              {selectedNpc.role === 'primary' && (
                <Badge variant="outline" className="text-xs border-purple-400/50 text-purple-300">Primary</Badge>
              )}
            </div>
            <Button
              onClick={() => setSelectedNpc(null)}
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 text-purple-400 hover:text-purple-200"
              title="Clear NPC selection"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Combat HUD - only show inline when parent has no full-screen CombatScreen handler */}
        {isCombatActive && combatState && !props.onCombatStart && (
          <div className="px-3 pt-3">
            <CombatHUD characterState={gameStateContext.characterState} combatState={combatState} />
          </div>
        )}

        {/* Turn usage indicator */}
        <div style={{ padding: "4px 8px" }}>
          <UsageBanner />
        </div>

        {/* Compact top bar — Realm + Quests open as right-side slide-overs.
            Replaces the chunky inline collapsible cards so the chat owns
            the vertical real-estate. */}
        {(worldBlueprint || campaignId) && (
          <CampaignTopBar
            worldBlueprint={worldBlueprint}
            currentLocation={worldState?.current_location || worldState?.location}
            quests={quests}
            onUpdateQuestStatus={handleUpdateQuestStatus}
            campaignId={campaignId}
            worldState={worldState}
            characterId={gameStateContext.characterState?.id || gameStateContext.characterState?.character_id}
            characterName={gameStateContext.characterState?.identity?.name || gameStateContext.characterState?.name}
            onPausedThreadResumed={(payload) => {
              const { storyline, ruling, new_lead_card } = payload || {};
              const isExpired = ruling?.ruling === 'expired';
              if (ruling?.narration) {
                const dmBeat = {
                  type: 'dm',
                  text: ruling.narration,
                  message: ruling.narration,
                  timestamp: Date.now(),
                  isCinematic: true,
                  source: isExpired ? 'storyline-expired' : 'storyline-resume',
                  meta: {
                    ruling: ruling.ruling,
                    storylineTitle: storyline?.title,
                    consequence: ruling.consequence,
                  },
                };
                const beats = [dmBeat];
                // If the thread expired AND the DM minted a new lead, surface
                // it as a second beat immediately after the closure narration.
                if (isExpired && new_lead_card?.description) {
                  beats.push({
                    type: 'dm',
                    text: new_lead_card.description,
                    message: new_lead_card.description,
                    timestamp: Date.now() + 10,
                    isCinematic: true,
                    source: 'lead-revealed',
                    meta: { leadTitle: new_lead_card.title },
                  });
                }
                setMessages((prev) => {
                  const next = [...prev, ...beats].slice(-200);
                  if (sessionId) {
                    try {
                      localStorage.setItem(
                        `dm-log-messages-${sessionId}`,
                        JSON.stringify(next)
                      );
                    } catch {}
                  }
                  return next;
                });
              }
              // Reopen the investigation panel only if the DM ruled it alive.
              if (
                storyline &&
                storyline.status === 'active' &&
                (ruling?.ruling === 'active' || ruling?.ruling === 'cold')
              ) {
                setActiveStoryline(storyline);
              }
            }}
          />
        )}

        {/* Campaign Log Button - Only show when campaignId exists */}
        {campaignId && (
          <div className="px-3 pt-3">
            <Button
              onClick={() => setShowCampaignLog(true)}
              variant="outline"
              className="relative w-full bg-orange-600/10 border-orange-600/30 hover:bg-orange-600/20 text-orange-400 hover:text-orange-300"
              data-testid="campaign-log-open-btn"
            >
              <BookOpen className="h-4 w-4 mr-2" />
              Campaign Log
              {newCardCount > 0 && (
                <span
                  className="absolute -top-1.5 -right-1.5 min-w-[22px] h-[22px] px-1.5 rounded-full bg-emerald-500 text-stone-950 text-[11px] font-black flex items-center justify-center border-2 border-stone-950 shadow-[0_0_12px_rgba(16,185,129,0.7)] animate-pulse"
                  data-testid="campaign-log-new-count"
                >
                  +{newCardCount}
                </span>
              )}
            </Button>
          </div>
        )}

        {/* Active Investigation — centered modal with blurred backdrop. */}
        {campaignId && activeStoryline && activeStoryline.status === 'active' && (
          <ActiveInvestigationPanel
            campaignId={campaignId}
            character={gameStateContext.characterState}
            storyline={activeStoryline}
            onUpdate={(sl) => setActiveStoryline(sl)}
            onClose={() => setActiveStoryline(null)}
            onComplication={(text, sl) => {
              if (!text) return;
              const beat = {
                type: 'dm', text, message: text,
                timestamp: Date.now(),
                isCinematic: true,
                source: 'storyline-complication',
                meta: { storylineTitle: sl?.title },
              };
              setMessages((prev) => {
                const next = [...prev, beat].slice(-200);
                if (sessionId) {
                  try { localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(next)); } catch {}
                }
                return next;
              });
            }}
            onCreativeNarration={(text, judgment, sl) => {
              if (!text) return;
              // Caller may signal a non-creative source via judgment.kind
              // (e.g. {kind:'storyline-paused'}). Default to 'storyline-creative'.
              const sourceKind = (judgment && judgment.kind) ? judgment.kind : 'storyline-creative';
              const judgmentLabel = (judgment && !judgment.kind) ? judgment : null;
              const beat = {
                type: 'dm', text, message: text,
                timestamp: Date.now(),
                isCinematic: true,
                source: sourceKind,
                meta: { judgment: judgmentLabel, storylineTitle: sl?.title },
              };
              setMessages((prev) => {
                const next = [...prev, beat].slice(-200);
                if (sessionId) {
                  try { localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(next)); } catch {}
                }
                return next;
              });
            }}
            onLeadMinted={(lead) => {
              if (!lead) return;
              const isSealed = lead.status === 'sealed';
              const text = isSealed
                ? `A lead worth pursuing slips through your fingers — for now. The card "${lead.title}" is in your deck, sealed. You can try to unravel it later by finding someone who can help, or revisiting the puzzle with a fresh angle.`
                : `A new lead falls into place: "${lead.title}". ${(lead.description || '').slice(0, 220)}`;
              const msg = {
                type: 'dm', text, message: text,
                timestamp: Date.now(),
                isCinematic: false,
                source: isSealed ? 'lead-sealed' : 'lead-revealed',
                meta: { leadTitle: lead.title, leadId: lead.id, sealed: isSealed },
              };
              setMessages((prev) => {
                const next = [...prev, msg].slice(-200);
                if (sessionId) {
                  try { localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(next)); } catch {}
                }
                return next;
              });
            }}
            onTargetCardsMinted={(cards) => {
              if (!Array.isArray(cards) || cards.length === 0) return;
              // Adventure-Log beat that lists the auto-pinned entities so the
              // player sees their deck just grew.
              const lines = cards
                .map((c) => `• ${(c.type || 'card').toUpperCase()} — ${c.title}`)
                .join('\n');
              const text =
                `New cards added to your Knowledge Deck:\n${lines}\n\n` +
                `These names dropped during the investigation. Pull them up from the deck whenever you're ready to act on them.`;
              const msg = {
                type: 'dm', text, message: text,
                timestamp: Date.now(),
                isCinematic: false,
                source: 'cards-auto-minted',
                meta: { count: cards.length, titles: cards.map((c) => c.title) },
              };
              setMessages((prev) => {
                const next = [...prev, msg].slice(-200);
                if (sessionId) {
                  try { localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(next)); } catch {}
                }
                return next;
              });
              // Toast so the chip pop is unmissable.
              try {
                window.showToast &&
                  window.showToast(
                    `+${cards.length} card${cards.length === 1 ? '' : 's'} added to your deck`,
                    'success'
                  );
              } catch {}
              // Broadcast a refresh event so any open Knowledge Deck / Campaign
              // Log panel can re-fetch and surface the new cards immediately.
              try {
                window.dispatchEvent(
                  new CustomEvent('rpg:cards-refreshed', {
                    detail: { campaignId, source: 'storyline-target', cards },
                  })
                );
              } catch {}
            }}
            onNpcFieldsRevealed={(reveals) => {
              if (!Array.isArray(reveals) || reveals.length === 0) return;
              // Friendly labels matching the NPCIdentityPanel.
              const FRIENDLY = {
                'personality.trait': 'Trait',
                'personality.ideal': 'Ideal',
                'personality.bond':  'Bond',
                'personality.flaw':  'Flaw',
                'speech_style':      'Speech style',
                'mannerisms':        'Mannerisms',
                'background':        'Background',
                'current_motivation':'Current motive',
                'allegiances':       'Allegiances',
                'passive_insight':   'Passive Insight',
                'stats.ac':          'AC',
                'stats.hp':          'HP',
                'stats.intimidation_dc': 'Intimidation DC',
                'stats.persuasion_dc':   'Persuasion DC',
                'stats.deception_dc':    'Deception DC',
                'stats.insight_dc':      'Insight DC',
                'secret_0':          'Secret 1',
                'secret_1':          'Secret 2',
              };
              const lines = reveals.map((p) => {
                const fields = (p.newly_revealed || []).map((f) => FRIENDLY[f] || f).join(', ');
                return `• ${p.title} — ${fields}`;
              }).join('\n');
              const text =
                `Codex Update — your read on these people just got sharper:\n${lines}\n\n` +
                `Open their cards in the deck to see the freshly-revealed details. ` +
                `Future pitches against them can now leverage what you've learned.`;
              const msg = {
                type: 'dm', text, message: text,
                timestamp: Date.now(),
                isCinematic: false,
                source: 'npc-fields-revealed',
                meta: {
                  count: reveals.length,
                  titles: reveals.map((r) => r.title),
                  fields: reveals.flatMap((r) => r.newly_revealed || []),
                },
              };
              setMessages((prev) => {
                const next = [...prev, msg].slice(-200);
                if (sessionId) {
                  try { localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(next)); } catch {}
                }
                return next;
              });
            }}
            onComplete={(sl, reward, completionNarration, playerUpdates) => {
              // Inject a small "investigation closes…" DM beat into the
              // Adventure Log so the player sees the wrap-up land
              // before the reward modal opens.
              const text = completionNarration || sl?.epilogue;
              if (text) {
                const beat = {
                  type: 'dm',
                  text,
                  message: text,
                  timestamp: Date.now(),
                  isCinematic: true,
                  source: 'storyline-complete',
                  meta: { storylineTitle: sl?.title },
                };
                setMessages((prev) => {
                  const next = [...prev, beat].slice(-200);
                  if (sessionId) {
                    try { localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(next)); } catch {}
                  }
                  return next;
                });
              }

              // Wire the storyline reward XP into the character state so
              // the XP bar in FocusedRPG animates forward. The backend has
              // already persisted these values + handled level-up rollover.
              if (playerUpdates && playerUpdates.xp_gained > 0) {
                updateCharContext({
                  current_xp: playerUpdates.current_xp,
                  xp_to_next: playerUpdates.xp_to_next,
                  level: playerUpdates.level,
                  // Mirror to `experience` for any consumer still reading
                  // the cumulative D&D 5e-style total.
                  experience: (gameStateContext.characterState?.experience || 0)
                    + playerUpdates.xp_gained,
                });
                const xpMsg = `+${playerUpdates.xp_gained} XP — ${playerUpdates.xp_reason || 'Investigation resolved'}`;
                if (window.showToast) window.showToast(xpMsg, 'success');
                (playerUpdates.level_up_events || []).forEach((evt) => {
                  const lvl = (evt || '').split(':')[1];
                  if (lvl && window.showToast) {
                    window.showToast(`🎉 LEVEL UP! You are now level ${lvl}!`, 'success');
                  }
                });
              }

              setActiveStoryline(null);
              setShowRewardModal(reward);
              if (campaignId) {
                fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/quests`)
                  .then((r) => (r.ok ? r.json() : null))
                  .then((d) => { if (d?.quests) setQuests(d.quests); })
                  .catch(() => {});
              }
            }}
          />
        )}

        {/* Canon anchor strip — always shows the current locked-in scene */}
        <div className="flex items-stretch gap-2">
          <div className="flex-1 min-w-0">
            <CanonBar campaignId={campaignId} />
          </div>
          <div className="flex items-center px-3 border-b border-stone-700/40 bg-stone-900/40">
            <AutoSaveIndicator />
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1" ref={scrollRef}>
          <div className="p-3 space-y-3">
            {messages.map((entry, idx) => (
              <div key={idx}>
                {/* DM Message */}
                {entry.type === 'dm' && (
                  <div className={`p-4 rounded-lg ${
                    entry.isWorldBrief
                      ? 'bg-gradient-to-br from-amber-900/30 via-stone-800/40 to-amber-950/30 border-2 border-amber-600/50 shadow-inner shadow-amber-900/40'
                      : entry.source === 'storyline-expired'
                        ? 'bg-stone-900/60 border border-rose-900/50 border-l-4 border-l-rose-700'
                        : entry.source === 'obligation-reminder'
                          ? 'bg-gradient-to-r from-amber-900/20 to-stone-800/30 border border-amber-700/50 border-l-4 border-l-amber-500'
                          : entry.source === 'world-event'
                            ? 'bg-gradient-to-r from-stone-800/50 to-zinc-900/50 border border-stone-600/60 border-l-4 border-l-stone-400'
                            : entry.isCinematic
                            ? 'bg-gradient-to-r from-violet-600/30 to-purple-600/30 border-2 border-violet-400/50'
                            : 'bg-violet-600/20 border-l-4 border-violet-400'
                  } animate-in slide-in-from-left-5 duration-300`}
                  data-testid={entry.isWorldBrief ? 'world-brief-message' : undefined}
                  >
                    <div className="flex items-start gap-3">
                      {entry.isWorldBrief ? (
                        <BookOpen className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                      ) : entry.source === 'obligation-reminder' ? (
                        <span className="text-amber-400 flex-shrink-0 mt-0.5 text-base leading-none">🪶</span>
                      ) : entry.source === 'world-event' ? (
                        <span className="text-stone-300 flex-shrink-0 mt-0.5 text-base leading-none">⚡</span>
                      ) : (
                        <Dice6 className="h-5 w-5 text-violet-400 flex-shrink-0 mt-0.5" />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`font-semibold text-sm ${entry.isWorldBrief ? 'text-amber-300 italic' : entry.source === 'storyline-expired' ? 'text-rose-400 italic' : entry.source === 'obligation-reminder' ? 'text-amber-400 italic' : entry.source === 'world-event' ? 'text-stone-300 italic' : 'text-violet-400'}`}>
                            {entry.isWorldBrief
                              ? `📜 ${entry.chronicleTitle || 'A Chronicle of the Realm'}`
                              : entry.source === 'map-event'
                                ? `🪶 A Lead Reaches You${entry.meta?.questTitle ? ` — ${entry.meta.questTitle}` : ''}`
                                : entry.source === 'storyline-complication'
                                  ? `⚠️ Complication${entry.meta?.storylineTitle ? ` — ${entry.meta.storylineTitle}` : ''}`
                                  : entry.source === 'storyline-creative'
                                    ? `✨ A Different Approach${entry.meta?.judgment ? ` (${entry.meta.judgment})` : ''}`
                                    : entry.source === 'storyline-complete'
                                      ? `🎬 Investigation Closes${entry.meta?.storylineTitle ? ` — ${entry.meta.storylineTitle}` : ''}`
                                      : entry.source === 'storyline-paused'
                                        ? `⏸ Thread Set Aside${entry.meta?.storylineTitle ? ` — ${entry.meta.storylineTitle}` : ''}`
                                        : entry.source === 'storyline-expired'
                                          ? `⌛ Thread Lost${entry.meta?.storylineTitle ? ` — ${entry.meta.storylineTitle}` : ''}`
                                          : entry.source === 'storyline-resume'
                                            ? `🔁 Reconnect${entry.meta?.ruling ? ` (${entry.meta.ruling})` : ''}`
                                          : entry.source === 'spawn-clarify'
                                            ? '❓ DM asks…'
                                            : entry.source === 'spawn-transition'
                                              ? `🧭 New Direction${entry.meta?.missionType ? ` — ${entry.meta.missionType}` : ''}`
                                              : entry.source === 'spawn-first-beat'
                                                ? `🪶 Scene Opens${entry.meta?.storylineTitle ? ` — ${entry.meta.storylineTitle}` : ''}`
                                                : entry.source === 'lead-revealed'
                                                  ? `🪄 New Lead — ${entry.meta?.leadTitle || ''}`
                                                  : entry.source === 'lead-sealed'
                                                    ? `🔒 Sealed Lead — ${entry.meta?.leadTitle || ''}`
                                                    : entry.source === 'obligation-reminder'
                                                      ? `🪶 A Word Reaches You${entry.meta?.storylineTitle ? ` — ${entry.meta.storylineTitle}` : ''}`
                                                      : entry.source === 'world-event'
                                                        ? `⚡ ${entry.meta?.npcName || 'Someone'} approaches`
                                                        : entry.isCinematic
                                                          ? '🎭 The Adventure Begins'
                                                          : 'Dungeon Master'}
                          </span>
                          {entry.isCinematic && !entry.isWorldBrief && entry.source !== 'world-event' && (
                            <Sparkles className="h-3 w-3 text-violet-400 animate-pulse" />
                          )}
                          {/* TTS Audio Player - Available for ALL DM messages including cinematic */}
                          <div className="ml-auto flex items-center gap-2">
                            <NarrationAudioPlayer
                              text={entry.text}
                              audioUrl={entry.audioUrl}
                              onGenerateAudio={() => generateAudioForMessage(idx)}
                              isGenerating={entry.isGeneratingAudio}
                            />
                            {/* 👍 — train the DM: this beat is the kind of writing the player wants more of */}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleBeatReaction(idx, 'like')}
                              disabled={entry.reactionBusy || !campaignId}
                              title={entry.reaction === 'like' ? 'You liked this beat — DM has noted it' : 'I liked this — train the DM to do more of this'}
                              data-testid={`beat-like-${idx}`}
                              className={`h-7 w-7 p-0 ${
                                entry.reaction === 'like'
                                  ? 'text-emerald-300 hover:text-emerald-200'
                                  : 'text-violet-300 hover:text-emerald-300 hover:bg-emerald-600/20'
                              }`}
                            >
                              {entry.reactionBusy && entry.reaction === 'like' ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <ThumbsUp className="h-4 w-4" />
                              )}
                            </Button>
                            {/* 👎 — train the DM: avoid this pattern */}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleBeatReaction(idx, 'dislike')}
                              disabled={entry.reactionBusy || !campaignId}
                              title={entry.reaction === 'dislike' ? 'You flagged this beat — DM will avoid this pattern' : "Didn't land — train the DM to avoid this"}
                              data-testid={`beat-dislike-${idx}`}
                              className={`h-7 w-7 p-0 ${
                                entry.reaction === 'dislike'
                                  ? 'text-rose-300 hover:text-rose-200'
                                  : 'text-violet-300 hover:text-rose-300 hover:bg-rose-600/20'
                              }`}
                            >
                              {entry.reactionBusy && entry.reaction === 'dislike' ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <ThumbsDown className="h-4 w-4" />
                              )}
                            </Button>
                            {/* Remember this → pin into Knowledge Deck */}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleRememberBeat(idx)}
                              disabled={entry.remembered || entry.remembering || !campaignId}
                              title={entry.remembered ? 'Saved to Knowledge Deck' : 'Remember this beat'}
                              data-testid={`remember-beat-${idx}`}
                              className={`h-7 w-7 p-0 ${
                                entry.remembered
                                  ? 'text-amber-300 hover:text-amber-300'
                                  : 'text-violet-300 hover:text-amber-300 hover:bg-violet-600/20'
                              }`}
                            >
                              {entry.remembering ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : entry.remembered ? (
                                <BookmarkCheck className="h-4 w-4" />
                              ) : (
                                <Bookmark className="h-4 w-4" />
                              )}
                            </Button>
                            {/* Pin as quest → adds an active lead to the Quest Log */}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handlePinAsQuest(idx)}
                              disabled={entry.pinnedAsQuest || entry.pinningQuest || !campaignId}
                              title={entry.pinnedAsQuest ? 'Pinned to Quest Log' : 'Pin as quest — adds to Quest Log & prioritized by DM'}
                              data-testid={`pin-quest-${idx}`}
                              className={`h-7 w-7 p-0 ${
                                entry.pinnedAsQuest
                                  ? 'text-amber-300 hover:text-amber-300'
                                  : 'text-violet-300 hover:text-amber-300 hover:bg-violet-600/20'
                              }`}
                            >
                              {entry.pinningQuest ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Scroll className="h-4 w-4" />
                              )}
                            </Button>
                            {/* Report this scene → dev snapshot for off-feeling turns */}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleOpenReport(idx)}
                              disabled={entry.reported || !campaignId}
                              title={entry.reported ? 'Scene already reported' : 'Report this scene — captures full context for debugging'}
                              data-testid={`report-scene-${idx}`}
                              className={`h-7 w-7 p-0 ${
                                entry.reported
                                  ? 'text-rose-400 hover:text-rose-400'
                                  : 'text-violet-300 hover:text-rose-400 hover:bg-violet-600/20'
                              }`}
                            >
                              <Flag className="h-4 w-4" />
                            </Button>
                            {/* Regenerate Intro Button (only for first cinematic message) */}
                            {entry.isCinematic && idx === 0 && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={startCinematicIntro}
                                disabled={isLoading}
                                className="text-xs border-violet-400/50 text-violet-300 hover:bg-violet-600/20 hover:text-violet-200"
                              >
                                {isLoading ? (
                                  <>
                                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                    Generating...
                                  </>
                                ) : (
                                  <>
                                    <Sparkles className="h-3 w-3 mr-1" />
                                    Regenerate Intro
                                  </>
                                )}
                              </Button>
                            )}
                          </div>
                        </div>
                        <div className={`text-base leading-relaxed ${
                          entry.isWorldBrief ? 'text-amber-50/90 italic font-serif tracking-wide' : 'text-violet-50'
                        }`}>
                          {/* Intent classifier hint — flashes a small chip
                              above the narration when the player's prior
                              action triggered a hard rule (e.g. Stealth /
                              Intimidation / Persuasion). Helps the player
                              see the rule fired even if the DM still hedged. */}
                          {entry.intentHint?.check_type && (
                            <div
                              className="inline-flex items-center gap-1.5 mb-2 px-2 py-0.5 rounded-md border border-amber-400/60 bg-amber-950/40 text-amber-100 text-[11px] not-italic font-bold tracking-wide"
                              data-testid="intent-hint-chip"
                              title={`Detected '${entry.intentHint.matched}' — DM was nudged to require a ${entry.intentHint.check_type} check.`}
                            >
                              <Dice6 className="w-3 h-3" />
                              <span>{entry.intentHint.check_type} check expected</span>
                              <span className="text-amber-300/70 italic font-normal">
                                · cued by "{entry.intentHint.matched}"
                              </span>
                            </div>
                          )}
                          {/* Entity Links + Hooks: parse entity markup AND inline DM hook spans */}
                          <div
                            onClick={handleNarrationClick}
                            onMouseMove={targetMode ? updateHover : undefined}
                            onMouseLeave={targetMode ? clearHover : undefined}
                            className={targetMode ? 'select-text' : ''}
                            data-testid="dm-narration-clickable"
                          >
                          {(
                            (entry.entity_mentions && entry.entity_mentions.length > 0) ||
                            (entry.hooks && entry.hooks.length > 0)
                          ) ? (
                            <EntityNarrationParser
                              text={entry.text}
                              entityMentions={entry.entity_mentions || []}
                              hooks={entry.hooks || []}
                              onEntityClick={(entity) => setSelectedEntity(entity)}
                              onHookClick={(hook) => setHookHint(hook)}
                            />
                          ) : entry.npcMentions && entry.npcMentions.length > 0 ? (
                            <NPCMentionHighlighter
                              text={entry.text}
                              npcMentions={entry.npcMentions}
                              onNPCClick={(npc) => setSelectedNpc(npc)}
                              selectedNpcId={selectedNpc?.id}
                            />
                          ) : (
                            formatMessage(entry.text)
                          )}
                          </div>
                        </div>
                        {/* Canon references — pulsing emerald chips for any
                            canonized entity this narration just touched. */}
                        <CanonReferences
                          campaignId={campaignId}
                          mentions={findCanonMentions(entry.text, canonTermsMap)}
                        />
                        <div className="text-xs opacity-60 mt-2">
                          {new Date(entry.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Player Message */}
                {entry.type === 'player' && (
                  <div className="p-4 rounded-lg bg-cyan-600/20 border-l-4 border-cyan-400 ml-8 animate-in slide-in-from-right-5 duration-300">
                    <div className="flex items-start gap-3">
                      <User className="h-4 w-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <div className="text-cyan-400 font-semibold text-sm">You</div>
                          <Badge 
                            variant="outline" 
                            className={`text-xs px-2 ${
                              entry.messageType === 'say' 
                                ? 'border-purple-400/50 text-purple-300 bg-purple-600/10' 
                                : entry.messageType === 'dm-question'
                                ? 'border-blue-400/50 text-blue-300 bg-blue-600/10'
                                : 'border-cyan-400/50 text-cyan-300 bg-cyan-600/10'
                            }`}
                          >
                            {entry.messageType === 'say' ? '💬 Say' : entry.messageType === 'dm-question' ? '🎲 DM?' : '⚔️ Action'}
                          </Badge>
                        </div>
                        <div className="text-cyan-50 text-base leading-relaxed">
                          {entry.messageType === 'say' ? (
                            <span className="italic">"{entry.text}"</span>
                          ) : entry.messageType === 'dm-question' ? (
                            <span className="text-blue-200">[Out of Character] {entry.text}</span>
                          ) : (
                            entry.text
                          )}
                        </div>
                        <div className="text-xs opacity-60 mt-2">
                          {new Date(entry.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Error Message */}
                {entry.type === 'error' && (
                  <div className="p-4 rounded-lg bg-red-600/20 border-l-4 border-red-400 animate-in fade-in duration-300">
                    <div className="flex items-start gap-3">
                      <div className="w-2 h-2 bg-red-400 rounded-full flex-shrink-0 mt-2"></div>
                      <div className="flex-1 min-w-0">
                        <div className="text-red-400 font-semibold text-sm mb-1">Connection Error</div>
                        <div className="text-red-50 text-sm">{entry.text}</div>
                        {entry.retry && (
                          <Button
                            onClick={() => handleRetry(idx)}
                            size="sm"
                            className="mt-2 bg-red-700 hover:bg-red-600 text-white"
                          >
                            Retry
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Roll Result Card */}
                {/* Roll results are now handled by CheckRollPanel, not inline */}

                {/* Check Summary (non-interactive - CheckRollPanel handles rolls) */}
                {entry.type === 'dm' && entry.checkRequest && idx === messages.length - 1 && !showIntro && (
                  <div className="ml-8 mt-3">
                    <div className="bg-gradient-to-r from-amber-600/10 to-yellow-600/10 border-2 border-amber-400/30 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Dice6 className="h-5 w-5 text-amber-400" />
                        <p className="text-amber-400 font-bold">
                          Ability Check: {entry.checkRequest.skill || entry.checkRequest.ability}
                        </p>
                      </div>
                      <div className="space-y-1 text-sm">
                        <p className="text-white">
                          <span className="text-gray-400">DC:</span> <span className="font-bold text-amber-300">{entry.checkRequest.dc}</span>
                        </p>
                        {entry.checkRequest.reason && (
                          <p className="text-gray-400 text-xs mt-2">{entry.checkRequest.reason}</p>
                        )}
                        <p className="text-amber-400/60 text-xs mt-3 italic">
                          Use the check panel to roll →
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Options (rendered after the last DM message if available and no check request card) */}
                {entry.type === 'dm' && idx === messages.length - 1 && (currentOptions || []).length > 0 && !showIntro && !entry.checkRequest && (
                  <div className="ml-8 mt-3 animate-in slide-in-from-bottom-5 duration-500">
                    <div className="text-amber-400 text-xs font-medium mb-2 flex items-center gap-2">
                      <MessageSquare className="h-3 w-3" />
                      Choose your action:
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {(currentOptions || []).map((option, optIdx) => (
                        <Button
                          key={optIdx}
                          onClick={() => handleOptionClick(option)}
                          disabled={isLoading}
                          size="sm"
                          className="bg-amber-700/80 hover:bg-amber-600 text-black font-medium text-xs h-auto p-2 text-left whitespace-normal hover:scale-105 transition-transform"
                        >
                          <span className="mr-1 text-amber-900 font-bold">{optIdx + 1}.</span>
                          {option}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {/* Loading State */}
            {isLoading && (
              <div className="flex items-center gap-3 text-violet-400 p-4">
                <Loader2 className="animate-spin h-4 w-4 flex-shrink-0" />
                <span className="text-sm">
                  {showIntro ? 'The Dungeon Master weaves your tale...' : 'The Dungeon Master considers your action...'}
                </span>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
      
      {/* Hidden Audio Element for TTS Playback */}
      <audio ref={audioRef} style={{ display: 'none' }} />

      {/* Remember-beat dialog (edit title + type before saving) */}
      <RememberCardDialog
        open={rememberDialog.open}
        saving={rememberDialog.saving}
        beatText={
          rememberDialog.messageIndex != null
            ? messages[rememberDialog.messageIndex]?.text || ''
            : ''
        }
        onOpenChange={(open) =>
          setRememberDialog((d) => (open ? d : { ...d, open: false }))
        }
        onConfirm={handleRememberConfirm}
      />

      {/* Scene report dialog (one-click debug snapshot) */}
      <SceneReportDialog
        open={reportDialog.open}
        saving={reportDialog.saving}
        beatText={
          reportDialog.messageIndex != null
            ? messages[reportDialog.messageIndex]?.text || ''
            : ''
        }
        playerActionText={(() => {
          const mi = reportDialog.messageIndex;
          if (mi == null) return '';
          for (let i = mi - 1; i >= 0; i -= 1) {
            const m = messages[i];
            if (m && (m.type === 'player' || m.type === 'action' || m.type === 'say')) {
              return m.text || m.message || '';
            }
          }
          return '';
        })()}
        onOpenChange={(open) =>
          setReportDialog((d) => (open ? d : { ...d, open: false }))
        }
        onConfirm={handleReportConfirm}
      />
      
      {/* P3: Defeat Modal */}
      {showDefeatModal && defeatInfo && (
        <DefeatModal
          isOpen={showDefeatModal}
          onContinue={() => {
            setShowDefeatModal(false);
            setDefeatInfo(null);
          }}
          playerName={gameStateContext.characterState?.name}
          currentHP={defeatInfo.currentHP}
          maxHP={defeatInfo.maxHP}
          injuryCount={defeatInfo.injuryCount}
          xpPenalty={defeatInfo.xpPenalty || 0}
        />
      )}

      {/* Search Target — "what are you looking for?" prompt when the
          player picked a word while in Search mode */}
      <SearchTargetModal
        open={!!searchTarget}
        target={searchTarget}
        onClose={() => setSearchTarget(null)}
        onSubmit={submitTargetedSearch}
      />

      {/* Live word-hover underline — visible only while a target mode is
          active. Tracks the word under the cursor across the narration. */}
      {targetMode && hoverHighlight && (
        <div
          className={`fixed pointer-events-none z-[125] transition-[left,top,width] duration-75 ease-out ${
            targetMode === 'observe'
              ? 'border-emerald-300 shadow-[0_0_10px_rgba(52,211,153,0.55)]'
              : 'border-amber-300 shadow-[0_0_10px_rgba(251,191,36,0.55)]'
          }`}
          style={{
            left: hoverHighlight.left - 2,
            top: hoverHighlight.top + hoverHighlight.height - 1,
            width: hoverHighlight.width + 4,
            height: 2,
            borderBottomWidth: 2,
            borderBottomStyle: 'dashed',
          }}
          data-testid="target-mode-hover-underline"
          aria-hidden="true"
        />
      )}
      
      {/* Entity Quick Inspect Panel - Opens when clicking entity links */}
      {selectedEntity && (
        <EntityQuickInspect
          entity={selectedEntity}
          campaignId={campaignId}
          characterId={gameStateContext.characterState?.id}
          onClose={() => setSelectedEntity(null)}
        />
      )}
      
      {/* Campaign Log Panel - Full-page modal */}
      {showCampaignLog && (
        <CampaignLogPanel
          campaignId={campaignId}
          characterId={gameStateContext.characterState?.id}
          onClose={() => setShowCampaignLog(false)}
        />
      )}

      {/* Storyline reward modal — appears when an investigation completes */}
      <StorylineRewardModal
        open={!!showRewardModal}
        reward={showRewardModal}
        onClose={() => {
          setShowRewardModal(null);
          // Inject a brief "what's next" DM prompt so the player isn't left
          // staring at a blank log after the reward modal closes.
          const nextStepText = "The matter is settled. Pull a new card from your deck — another thread will find you, if you’re willing to pull it.";
          const nextStep = {
            type: 'dm',
            text: nextStepText,
            message: nextStepText,
            timestamp: Date.now(),
            source: 'storyline-next-step',
          };
          setMessages((prev) => {
            const next = [...prev, nextStep].slice(-200);
            if (sessionId) {
              try { localStorage.setItem(`dm-log-messages-${sessionId}`, JSON.stringify(next)); } catch {}
            }
            return next;
          });
        }}
      />

      {/* Hook hint popover — small tip when player clicks an inline hook */}
      {hookHint && (
        <div
          className="fixed bottom-4 right-4 z-50 max-w-sm bg-stone-950 border-2 border-amber-500/70 text-amber-50 rounded-md shadow-2xl p-4"
          data-testid="hook-hint-popover"
        >
          <div className="text-[11px] text-amber-300 font-bold uppercase tracking-wider mb-1.5">
            Point of interest · {hookHint.verb_hint || 'examine'}
          </div>
          <div className="text-sm italic font-serif text-amber-50">
            "{hookHint.text}"
          </div>
          <div className="text-[12px] text-amber-100/95 mt-2.5 leading-snug">
            Type something like <em className="text-amber-200">"{hookHint.verb_hint || 'examine'} {hookHint.topic || hookHint.text}"</em> to engage.
            The DM will weave it into a multi-beat investigation.
          </div>
          <div className="flex justify-end mt-2">
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-amber-100 hover:text-amber-50 hover:bg-amber-500/15"
              onClick={() => setHookHint(null)}
              data-testid="hook-hint-close-btn"
            >
              Dismiss
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
});

AdventureLogWithDM.displayName = 'AdventureLogWithDM';

// Export Intent Toggle Component for use in FocusedRPG
export const IntentToggle = ({ mode, onChange }) => {
  return (
    <div className="flex items-center gap-1 bg-gray-900/80 border border-amber-600/30 rounded-lg p-1">
      <Button
        type="button"
        size="sm"
        onClick={() => onChange('dm-question')}
        className={`h-8 px-3 text-xs font-medium transition-all ${
          mode === 'dm-question'
            ? 'bg-blue-700 text-white hover:bg-blue-600'
            : 'bg-transparent text-gray-400 hover:text-white hover:bg-gray-700/50'
        }`}
        title="Ask the DM (out-of-character) (Alt+D)"
      >
        🎲 DM?
      </Button>
      <Button
        type="button"
        size="sm"
        onClick={() => onChange('action')}
        className={`h-8 px-3 text-xs font-medium transition-all ${
          mode === 'action'
            ? 'bg-amber-700 text-black hover:bg-amber-600'
            : 'bg-transparent text-gray-400 hover:text-white hover:bg-gray-700/50'
        }`}
        title="Perform an action (Alt+A)"
      >
        ⚔️ Action
      </Button>
      <Button
        type="button"
        size="sm"
        onClick={() => onChange('say')}
        className={`h-8 px-3 text-xs font-medium transition-all ${
          mode === 'say'
            ? 'bg-purple-700 text-white hover:bg-purple-600'
            : 'bg-transparent text-gray-400 hover:text-white hover:bg-gray-700/50'
        }`}
        title="Speak in-character (Alt+S)"
      >
        💬 Say
      </Button>
    </div>
  );
};

export default AdventureLogWithDM;