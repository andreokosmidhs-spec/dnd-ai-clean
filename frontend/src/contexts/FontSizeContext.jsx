/**
 * FontSizeContext — three reading-comfort presets the player can flip between
 * from the in-game ESC menu. Persists to localStorage and applies a CSS
 * variable (`--app-font-scale`) on <html> so anything declared in `rem`
 * scales accordingly. Also stamps a `data-font-size` attribute so we can
 * target preset-specific overrides if needed.
 */
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

const STORAGE_KEY = 'rpg-font-size-preset';

// 'comfortable' = current default (1.0). Larger presets bump everything up.
const PRESETS = {
  comfortable: { label: 'Comfortable', scale: 1.0 },
  large:       { label: 'Large',        scale: 1.15 },
  xlarge:      { label: 'Extra Large',  scale: 1.30 },
};

const ORDER = ['comfortable', 'large', 'xlarge'];

const FontSizeContext = createContext({
  preset: 'comfortable',
  scale: 1.0,
  setPreset: () => {},
  presets: PRESETS,
  order: ORDER,
});

export const FontSizeProvider = ({ children }) => {
  const [preset, setPresetState] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved && PRESETS[saved]) return saved;
    } catch {}
    return 'comfortable';
  });

  // Apply the scale to <html> so all rem-based sizes pick it up.
  useEffect(() => {
    const root = document.documentElement;
    const cfg = PRESETS[preset] || PRESETS.comfortable;
    root.style.setProperty('--app-font-scale', String(cfg.scale));
    root.setAttribute('data-font-size', preset);
    // Keep the base font in sync — Tailwind's `text-*` classes are in rem,
    // so adjusting the root font size cascades cleanly.
    root.style.fontSize = `${cfg.scale * 16}px`;
  }, [preset]);

  const setPreset = useCallback((next) => {
    if (!PRESETS[next]) return;
    setPresetState(next);
    try { localStorage.setItem(STORAGE_KEY, next); } catch {}
  }, []);

  return (
    <FontSizeContext.Provider value={{
      preset,
      scale: (PRESETS[preset] || PRESETS.comfortable).scale,
      setPreset,
      presets: PRESETS,
      order: ORDER,
    }}>
      {children}
    </FontSizeContext.Provider>
  );
};

export const useFontSize = () => useContext(FontSizeContext);
