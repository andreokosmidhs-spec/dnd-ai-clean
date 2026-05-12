/**
 * TargetModeContext — global state for "click a word to target it" UI.
 *
 * Two modes:
 *   - 'observe' (eye cursor): clicking any word in DM narration sends an
 *     observation request — the DM auto-narrates a richer description of
 *     that target.
 *   - 'search'  (magnifier cursor): clicking any word in DM narration
 *     opens a "What are you looking for?" prompt; on submit the DM
 *     receives a targeted investigation.
 *
 * Activation is exclusive (only one mode at a time). Cancel via Escape
 * or by clicking the floating cancel chip.
 */
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';

const TargetModeContext = createContext({
  mode: null,
  setMode: () => {},
  clearMode: () => {},
});

export const useTargetMode = () => useContext(TargetModeContext);

export const TargetModeProvider = ({ children }) => {
  const [mode, setModeState] = useState(null);  // null | 'observe' | 'search'

  const setMode = useCallback((next) => {
    setModeState((cur) => (cur === next ? null : next));
  }, []);
  const clearMode = useCallback(() => setModeState(null), []);

  // Body class toggles the cursor for the whole chat surface.
  useEffect(() => {
    document.body.classList.remove('cursor-target-observe', 'cursor-target-search');
    if (mode === 'observe') document.body.classList.add('cursor-target-observe');
    if (mode === 'search') document.body.classList.add('cursor-target-search');
    return () => {
      document.body.classList.remove('cursor-target-observe', 'cursor-target-search');
    };
  }, [mode]);

  // Escape cancels. Use capture phase + stopPropagation so the pause
  // menu's Escape handler doesn't ALSO fire when the player is just
  // trying to cancel target mode.
  useEffect(() => {
    if (!mode) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        clearMode();
      }
    };
    window.addEventListener('keydown', onKey, true);
    return () => window.removeEventListener('keydown', onKey, true);
  }, [mode, clearMode]);

  return (
    <TargetModeContext.Provider value={{ mode, setMode, clearMode }}>
      {children}
    </TargetModeContext.Provider>
  );
};

/**
 * Helper for narration containers — given a click event inside a text
 * block, returns the clicked word (or empty string). Uses the browser's
 * caretRangeFromPoint to identify where the click landed, then walks
 * outward to a word boundary.
 */
export function pickWordFromClick(e) {
  try {
    // Prefer modern API; fall back to caretPositionFromPoint.
    let range = null;
    if (typeof document.caretRangeFromPoint === 'function') {
      range = document.caretRangeFromPoint(e.clientX, e.clientY);
    } else if (typeof document.caretPositionFromPoint === 'function') {
      const pos = document.caretPositionFromPoint(e.clientX, e.clientY);
      if (pos) {
        range = document.createRange();
        range.setStart(pos.offsetNode, pos.offset);
        range.collapse(true);
      }
    }
    if (!range) return '';
    const node = range.startContainer;
    const text = (node && node.textContent) || '';
    if (!text) return '';
    let s = range.startOffset;
    let end = range.startOffset;
    const isWordChar = (ch) => /[A-Za-z0-9'’\-]/.test(ch);
    while (s > 0 && isWordChar(text[s - 1])) s -= 1;
    while (end < text.length && isWordChar(text[end])) end += 1;
    const word = text.slice(s, end).trim();
    // Strip enclosing punctuation just in case
    return word.replace(/^[^A-Za-z0-9'’\-]+|[^A-Za-z0-9'’\-]+$/g, '');
  } catch {
    return '';
  }
}
