import { useState, useEffect, useCallback } from 'react';

const PINNED_CARDS_KEY = 'pinned-campaign-cards';

/**
 * Custom hook for managing pinned cards with localStorage persistence
 */
export const usePinnedCards = () => {
  const [pinnedIds, setPinnedIds] = useState(() => {
    try {
      const stored = localStorage.getItem(PINNED_CARDS_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Save pinned IDs to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(PINNED_CARDS_KEY, JSON.stringify(pinnedIds));
    } catch (err) {
      console.warn('Failed to save pinned cards:', err);
    }
  }, [pinnedIds]);

  const togglePin = useCallback((cardId) => {
    setPinnedIds(prev => {
      if (prev.includes(cardId)) {
        return prev.filter(id => id !== cardId);
      }
      return [...prev, cardId];
    });
  }, []);

  const isPinned = useCallback((cardId) => {
    return pinnedIds.includes(cardId);
  }, [pinnedIds]);

  const pinnedCount = pinnedIds.length;

  return {
    pinnedIds,
    togglePin,
    isPinned,
    pinnedCount,
  };
};

export default usePinnedCards;
