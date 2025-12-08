import { useState, useRef, useCallback, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export const useTTS = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isTTSEnabled, setIsTTSEnabled] = useState(() => {
    // Load TTS preference from localStorage
    const saved = localStorage.getItem('rpg-tts-enabled');
    return saved === 'true';
  });
  const audioRef = useRef(null);
  const audioCache = useRef(new Map()); // Cache audio URLs by narration text

  // Save TTS preference to localStorage
  useEffect(() => {
    localStorage.setItem('rpg-tts-enabled', isTTSEnabled.toString());
  }, [isTTSEnabled]);

  const generateSpeech = useCallback(async (text, voice = 'onyx', autoPlay = false) => {
    console.log('🎙️ TTS generateSpeech called:', { textLength: text.length, voice, autoPlay });
    
    // Check cache first
    if (audioCache.current.has(text)) {
      const cachedUrl = audioCache.current.get(text);
      console.log('✅ TTS using cached audio');
      if (autoPlay && audioRef.current) {
        audioRef.current.src = cachedUrl;
        try {
          console.log('🔊 Auto-playing cached audio');
          await audioRef.current.play();
        } catch (err) {
          console.warn('⚠️ Auto-play prevented:', err);
        }
      }
      return cachedUrl;
    }

    setIsLoading(true);
    setError(null);

    try {
      console.log('🌐 Fetching TTS from API...');
      const response = await fetch(`${API_BASE_URL}/api/tts/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          voice,
          model: 'tts-1-hd'
        })
      });

      if (!response.ok) {
        throw new Error(`TTS generation failed: ${response.statusText}`);
      }

      const audioBlob = await response.blob();
      const url = URL.createObjectURL(audioBlob);
      console.log('✅ TTS audio generated, size:', audioBlob.size, 'bytes');
      
      // Cache the URL
      audioCache.current.set(text, url);

      if (autoPlay && audioRef.current) {
        audioRef.current.src = url;
        try {
          console.log('🔊 Auto-playing new audio');
          await audioRef.current.play();
          console.log('✅ Audio playback started');
        } catch (err) {
          console.warn('⚠️ Auto-play prevented:', err);
        }
      }

      return url;
    } catch (err) {
      setError(err.message);
      console.error('TTS Error:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const playAudio = useCallback((audioUrl) => {
    if (audioRef.current && audioUrl) {
      audioRef.current.src = audioUrl;
      audioRef.current.play().catch(err => {
        console.warn('Playback error:', err);
      });
    }
  }, []);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  }, []);

  const toggleTTS = useCallback(() => {
    setIsTTSEnabled(prev => !prev);
  }, []);

  const cleanup = useCallback(() => {
    // Revoke all cached object URLs
    audioCache.current.forEach(url => URL.revokeObjectURL(url));
    audioCache.current.clear();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    audioRef,
    isLoading,
    error,
    isTTSEnabled,
    generateSpeech,
    playAudio,
    stopAudio,
    toggleTTS,
    cleanup
  };
};
