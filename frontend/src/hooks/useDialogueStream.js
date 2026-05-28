/**
 * useDialogueStream — WebSocket hook for cinematic NPC dialogue.
 *
 * Connects to /ws/dialogue/{campaignId}/{npcId}, streams word tokens
 * with fade-in animation, plays chunk audio via Web Audio API queue,
 * and drives karaoke word highlighting via timing data.
 *
 * Usage:
 *   const { words, state, send, close } = useDialogueStream({ campaignId, npcId });
 *   send({ text: "Hello", emotion: "neutral", history: [] });
 */

import { useState, useRef, useCallback, useEffect } from 'react';

const WS_BASE = (process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001')
  .replace(/^http/, 'ws');

export function useDialogueStream({ campaignId, npcId }) {
  // words: [{ word, wordIndex, chunkId, state: 'pending'|'speaking'|'spoken' }]
  const [words, setWords] = useState([]);
  // state: 'idle' | 'connecting' | 'streaming' | 'done' | 'error'
  const [streamState, setStreamState] = useState('idle');
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const audioCtxRef = useRef(null);
  const audioQueueRef = useRef([]); // { chunkId, buffer, timings, chunkWordStartIndex }
  const isPlayingRef = useRef(false);
  const currentChunkIdRef = useRef(-1);

  // Lazy init AudioContext on first use (requires user gesture)
  const getAudioCtx = useCallback(() => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtxRef.current.state === 'suspended') {
      audioCtxRef.current.resume().catch(() => {});
    }
    return audioCtxRef.current;
  }, []);

  const highlightWords = useCallback((chunkId, timings, chunkWordStartIndex) => {
    let cumulativeMs = 0;
    timings.forEach((durationMs, i) => {
      const wordIdx = chunkWordStartIndex + i;
      const delay = cumulativeMs;
      setTimeout(() => {
        setWords(prev => prev.map(w =>
          w.wordIndex === wordIdx
            ? { ...w, state: 'speaking' }
            : w.wordIndex < wordIdx && w.state === 'speaking'
              ? { ...w, state: 'spoken' }
              : w
        ));
      }, delay);
      setTimeout(() => {
        setWords(prev => prev.map(w =>
          w.wordIndex === wordIdx && w.state === 'speaking'
            ? { ...w, state: 'spoken' }
            : w
        ));
      }, delay + durationMs);
      cumulativeMs += durationMs;
    });
  }, []);

  const playNextInQueue = useCallback(async () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) return;
    isPlayingRef.current = true;

    const item = audioQueueRef.current.shift();
    const { buffer, timings, chunkWordStartIndex } = item;
    const ctx = getAudioCtx();

    try {
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);

      // Start karaoke highlighting
      highlightWords(item.chunkId, timings, chunkWordStartIndex);

      source.onended = () => {
        isPlayingRef.current = false;
        playNextInQueue();
      };
      source.start();
    } catch (e) {
      console.error('[dialogue] Audio playback error', e);
      isPlayingRef.current = false;
      playNextInQueue();
    }
  }, [getAudioCtx, highlightWords]);

  const handleMessage = useCallback(async (event) => {
    let msg;
    try {
      msg = JSON.parse(event.data);
    } catch {
      return;
    }

    switch (msg.type) {
      case 'token': {
        setWords(prev => [
          ...prev,
          { word: msg.word, wordIndex: msg.wordIndex, chunkId: msg.chunkId, state: 'pending' }
        ]);
        break;
      }
      case 'audio': {
        try {
          const ctx = getAudioCtx();
          const raw = atob(msg.data);
          const bytes = new Uint8Array(raw.length);
          for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
          const audioBuffer = await ctx.decodeAudioData(bytes.buffer);
          audioQueueRef.current.push({
            chunkId: msg.chunkId,
            buffer: audioBuffer,
            timings: msg.timings || [],
            chunkWordStartIndex: msg.chunkWordStartIndex || 0,
          });
          playNextInQueue();
        } catch (e) {
          console.error('[dialogue] Audio decode error', e);
        }
        break;
      }
      case 'done': {
        setStreamState('done');
        break;
      }
      case 'error': {
        setError(msg.message);
        setStreamState('error');
        break;
      }
      default:
        break;
    }
  }, [getAudioCtx, playNextInQueue]);

  const send = useCallback((payload) => {
    // Reset state
    setWords([]);
    setStreamState('connecting');
    setError(null);
    audioQueueRef.current = [];
    isPlayingRef.current = false;

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.onmessage = null;
      wsRef.current.close();
      wsRef.current = null;
    }

    const url = `${WS_BASE}/ws/dialogue/${campaignId}/${npcId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStreamState('streaming');
      ws.send(JSON.stringify(payload));
    };

    ws.onmessage = handleMessage;

    ws.onerror = () => {
      setError('WebSocket connection failed');
      setStreamState('error');
    };

    ws.onclose = (ev) => {
      if (streamState === 'streaming') {
        setStreamState('done');
      }
    };
  }, [campaignId, npcId, handleMessage, streamState]);

  const close = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStreamState('idle');
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.onmessage = null;
        wsRef.current.close();
      }
    };
  }, []);

  return { words, streamState, error, send, close };
}
