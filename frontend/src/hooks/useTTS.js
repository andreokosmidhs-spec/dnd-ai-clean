import { useState, useRef, useCallback, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const BROWSER_TTS_KEY = 'dnd_browser_tts_enabled';

// Kokoro voice map — matches backend tts_service.py
const KOKORO_VOICE_MAP = {
  onyx:    'bm_george',  // deep British male — DM voice
  alloy:   'af_sky',
  echo:    'am_adam',
  fable:   'bf_emma',
  nova:    'af_heart',
  shimmer: 'af_sky',
};

// Module-level singleton so all hook instances share one model
let _kokoroTTS = null;
let _kokoroLoadPromise = null;
let _kokoroFailed = false;

async function _loadKokoro(onProgress) {
  if (_kokoroTTS) return _kokoroTTS;
  if (_kokoroFailed) return null;
  if (_kokoroLoadPromise) return _kokoroLoadPromise;

  _kokoroLoadPromise = (async () => {
    try {
      const { KokoroTTS } = await import('kokoro-js');
      _kokoroTTS = await KokoroTTS.from_pretrained('onnx-community/Kokoro-82M-v1.0', {
        dtype: 'q4',
        progress_callback: (info) => {
          if (typeof onProgress === 'function' && info?.progress != null) {
            onProgress(Math.round(info.progress));
          }
        },
      });
      console.log('✅ Kokoro TTS loaded in browser');
      return _kokoroTTS;
    } catch (err) {
      console.warn('⚠️ Kokoro browser TTS failed to load:', err);
      _kokoroFailed = true;
      _kokoroLoadPromise = null;
      return null;
    }
  })();

  return _kokoroLoadPromise;
}

let _audioCtx = null;
function _getAudioCtx() {
  if (!_audioCtx || _audioCtx.state === 'closed') {
    _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  return _audioCtx;
}

async function _playFloat32(float32, sampleRate) {
  const ctx = _getAudioCtx();
  if (ctx.state === 'suspended') await ctx.resume();
  const buffer = ctx.createBuffer(1, float32.length, sampleRate);
  buffer.getChannelData(0).set(float32);
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  source.connect(ctx.destination);
  source.start();
  return source;
}

function _speakFallback(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const clean = text.replace(/[*_~`#>]/g, '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').trim();
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 0.9;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => /daniel|george|arthur|oliver|en-gb/i.test(v.name + v.lang))
    || voices.find(v => /en/i.test(v.lang));
  if (preferred) utterance.voice = preferred;
  window.speechSynthesis.speak(utterance);
}


// ── Browser Speech Synthesis (free, no backend needed) ────────────────────────
export const useBrowserTTS = () => {
  const [enabled, setEnabled] = useState(() => {
    try { const s = localStorage.getItem(BROWSER_TTS_KEY); return s === null ? true : s === 'true'; } catch { return true; }
  });
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;

  const toggle = useCallback(() => {
    setEnabled(prev => {
      const next = !prev;
      try { localStorage.setItem(BROWSER_TTS_KEY, String(next)); } catch {}
      if (!next && supported) window.speechSynthesis.cancel();
      return next;
    });
  }, [supported]);

  const speak = useCallback((text) => {
    if (!enabled || !supported || !text) return;
    window.speechSynthesis.cancel();
    const clean = text.replace(/[*_~`#>]/g, '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').trim();
    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v => /daniel|george|arthur|oliver|en-gb/i.test(v.name + v.lang))
      || voices.find(v => /en/i.test(v.lang));
    if (preferred) utterance.voice = preferred;
    window.speechSynthesis.speak(utterance);
  }, [enabled, supported]);

  const stop = useCallback(() => {
    if (supported) window.speechSynthesis.cancel();
  }, [supported]);

  useEffect(() => () => { if (supported) window.speechSynthesis.cancel(); }, [supported]);

  return { enabled, toggle, speak, stop, supported };
};


// ── Main TTS hook — Kokoro (browser) → OpenAI API → speechSynthesis ──────────
export const useTTS = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [kokoroProgress, setKokoroProgress] = useState(0); // 0-100 during first download
  const [isTTSEnabled, setIsTTSEnabled] = useState(() => {
    const saved = localStorage.getItem('rpg-tts-enabled');
    return saved === null ? true : saved === 'true';
  });
  const audioRef = useRef(null);
  const audioCache = useRef(new Map());
  const currentKokoroSourceRef = useRef(null);

  useEffect(() => {
    localStorage.setItem('rpg-tts-enabled', isTTSEnabled.toString());
  }, [isTTSEnabled]);

  // Kick off Kokoro model download in the background as soon as the hook mounts
  // so it's ready by the time the first narration arrives.
  useEffect(() => {
    if (!_kokoroTTS && !_kokoroFailed) {
      _loadKokoro((pct) => setKokoroProgress(pct)).catch(() => {});
    }
  }, []);

  const generateSpeech = useCallback(async (text, voice = 'onyx', autoPlay = false) => {
    if (!text) return null;

    const cacheKey = `${voice}:${text}`;

    // ── 1. Cache hit ──────────────────────────────────────────────────────────
    if (audioCache.current.has(cacheKey)) {
      const cached = audioCache.current.get(cacheKey);
      if (autoPlay) {
        if (cached.type === 'kokoro') {
          try {
            if (currentKokoroSourceRef.current) {
              try { currentKokoroSourceRef.current.stop(); } catch (_) {}
            }
            currentKokoroSourceRef.current = await _playFloat32(cached.audio, cached.sampleRate);
          } catch (_) {}
        } else if (audioRef.current) {
          audioRef.current.src = cached.url;
          await audioRef.current.play().catch(() => {});
        }
      }
      return cached.url || null;
    }

    setIsLoading(true);
    setError(null);

    try {
      // ── 2. Kokoro browser TTS ───────────────────────────────────────────────
      if (!_kokoroFailed) {
        const tts = await _loadKokoro((pct) => setKokoroProgress(pct));
        if (tts) {
          const clean = text.replace(/[*_~`#>]/g, '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').trim();
          if (clean) {
            const kokoroVoice = KOKORO_VOICE_MAP[voice] || 'bm_george';
            const result = await tts.generate(clean, { voice: kokoroVoice });
            const float32 = result.audio;
            const sampleRate = result.sampling_rate || 24000;

            audioCache.current.set(cacheKey, { type: 'kokoro', audio: float32, sampleRate });

            if (autoPlay) {
              if (currentKokoroSourceRef.current) {
                try { currentKokoroSourceRef.current.stop(); } catch (_) {}
              }
              currentKokoroSourceRef.current = await _playFloat32(float32, sampleRate);
            }
            console.log('✅ TTS via Kokoro (browser, free)');
            return null; // no URL needed — audio played directly
          }
        }
      }

      // ── 3. Free browser speechSynthesis fallback (Kokoro unavailable) ────────
      console.log('⚠️ Kokoro unavailable, using free browser speechSynthesis');
      _speakFallback(text);
      return null;

    } catch (err) {
      setError(err.message);
      console.error('TTS Error:', err);
      try { _speakFallback(text); } catch (_) {}
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const playAudio = useCallback((audioUrl) => {
    if (audioRef.current && audioUrl) {
      audioRef.current.src = audioUrl;
      audioRef.current.play().catch(() => {});
    }
  }, []);

  const stopAudio = useCallback(() => {
    if (currentKokoroSourceRef.current) {
      try { currentKokoroSourceRef.current.stop(); } catch (_) {}
      currentKokoroSourceRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  }, []);

  const toggleTTS = useCallback(() => {
    setIsTTSEnabled(prev => !prev);
  }, []);

  const cleanup = useCallback(() => {
    audioCache.current.forEach(entry => {
      if (entry.url) URL.revokeObjectURL(entry.url);
    });
    audioCache.current.clear();
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);

  return {
    audioRef,
    isLoading,
    error,
    kokoroProgress,
    isTTSEnabled,
    generateSpeech,
    playAudio,
    stopAudio,
    toggleTTS,
    cleanup,
  };
};
