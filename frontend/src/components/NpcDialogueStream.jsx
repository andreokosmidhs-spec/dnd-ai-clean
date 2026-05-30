/**
 * NpcDialogueStream — cinematic word-by-word NPC dialogue with:
 *   - Character portrait + name header
 *   - Word-fade-in streaming text
 *   - Karaoke highlight on the currently spoken word
 *   - Emotion selector
 *   - Player input box
 *   - Audio playback via useDialogueStream hook
 */
import React, { useState, useRef, useEffect } from 'react';
import { Mic, X, Send, Volume2, Loader2 } from 'lucide-react';
import { useDialogueStream } from '../hooks/useDialogueStream';

const EMOTIONS = [
  'neutral','calm','happy','excited','angry','nervous',
  'fearful','sad','tired','whispering','contemptuous','suspicious',
];

function WordSpan({ word, state }) {
  return (
    <span
      className={`dialogue-word dialogue-word--${state}`}
      data-state={state}
    >
      {word}{' '}
    </span>
  );
}

export function NpcDialogueStream({ campaignId, npcId, npcName, npcPortrait, onClose }) {
  const [playerInput, setPlayerInput] = useState('');
  const [emotion, setEmotion] = useState('neutral');
  const [history, setHistory] = useState([]);
  const bottomRef = useRef(null);

  const { words, streamState, error, send } = useDialogueStream({ campaignId, npcId });

  const isStreaming = streamState === 'streaming' || streamState === 'connecting';

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [words.length]);

  const handleSend = () => {
    const text = playerInput.trim();
    if (!text || isStreaming) return;

    setHistory(h => [...h, { role: 'user', content: text }]);
    setPlayerInput('');
    send({ text, emotion, history });
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Collect last NPC response text from words
  const npcResponseText = words.map(w => w.word).join(' ');
  useEffect(() => {
    if (streamState === 'done' && npcResponseText) {
      setHistory(h => {
        const last = h[h.length - 1];
        if (last?.role === 'assistant' && last.content === npcResponseText) return h;
        return [...h, { role: 'assistant', content: npcResponseText }];
      });
    }
  }, [streamState, npcResponseText]);

  return (
    <div className="npc-dialogue-panel flex flex-col h-full bg-stone-950 border border-amber-500/30 rounded-lg overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-amber-500/20 bg-stone-900">
        {npcPortrait ? (
          <img
            src={npcPortrait}
            alt={npcName}
            className="w-10 h-10 rounded-full object-cover border border-amber-500/40"
          />
        ) : (
          <div className="w-10 h-10 rounded-full bg-amber-900/40 flex items-center justify-center text-amber-300 font-bold text-lg">
            {(npcName || '?')[0].toUpperCase()}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="text-amber-200 font-bold text-sm truncate">{npcName || npcId}</div>
          <div className="text-stone-500 text-[10px] uppercase tracking-wider">
            {isStreaming ? (
              <span className="text-emerald-400 flex items-center gap-1">
                <Loader2 className="w-2.5 h-2.5 animate-spin inline" /> Speaking…
              </span>
            ) : streamState === 'done' ? 'Done' : 'Ready'}
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-stone-500 hover:text-stone-200 transition-colors p-1"
          aria-label="Close dialogue"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Transcript + streaming text */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 text-sm">
        {/* History (previous turns) */}
        {history.map((h, i) => (
          <div
            key={i}
            className={`flex ${h.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-3 py-2 text-[13px] leading-relaxed ${
                h.role === 'user'
                  ? 'bg-amber-900/30 text-amber-100 border border-amber-700/30'
                  : 'bg-stone-800/60 text-amber-50 border border-stone-700/40'
              }`}
            >
              {h.content}
            </div>
          </div>
        ))}

        {/* Current streaming NPC response */}
        {words.length > 0 && (
          <div className="flex justify-start">
            <div className="max-w-[80%] bg-stone-800/60 border border-stone-700/40 rounded-lg px-3 py-2 leading-relaxed text-[13px] text-amber-50">
              {words.map(w => (
                <WordSpan key={w.wordIndex} word={w.word} state={w.state} />
              ))}
              {isStreaming && (
                <span className="inline-block w-1 h-3 bg-amber-400 animate-pulse ml-0.5 align-middle" />
              )}
            </div>
          </div>
        )}

        {error && (
          <div className="text-red-400 text-xs text-center italic">{error}</div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input row */}
      <div className="border-t border-amber-500/20 bg-stone-900 px-3 py-3 space-y-2">
        {/* Emotion selector */}
        <div className="flex items-center gap-2">
          <Volume2 className="w-3 h-3 text-stone-500 shrink-0" />
          <select
            value={emotion}
            onChange={e => setEmotion(e.target.value)}
            className="text-[10px] bg-stone-800 border border-amber-500/20 text-amber-300 rounded px-1.5 py-0.5 flex-shrink-0"
          >
            {EMOTIONS.map(em => <option key={em} value={em}>{em}</option>)}
          </select>
          <span className="text-[10px] text-stone-600 italic">NPC voice emotion</span>
        </div>

        {/* Text input */}
        <div className="flex items-end gap-2">
          <textarea
            value={playerInput}
            onChange={e => setPlayerInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder={`Say something to ${npcName || 'them'}…`}
            rows={2}
            disabled={isStreaming}
            className="flex-1 bg-stone-800 border border-amber-500/20 rounded-lg px-3 py-2 text-amber-50 text-sm placeholder-stone-600 resize-none focus:outline-none focus:border-amber-500/50 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isStreaming || !playerInput.trim()}
            className="p-2.5 bg-amber-700/80 hover:bg-amber-600/80 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-amber-100 transition-colors shrink-0"
            aria-label="Send"
          >
            {isStreaming
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Send className="w-4 h-4" />
            }
          </button>
        </div>
      </div>
    </div>
  );
}

export default NpcDialogueStream;
