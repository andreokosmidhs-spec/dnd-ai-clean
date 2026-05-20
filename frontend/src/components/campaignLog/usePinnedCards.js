import { useState, useEffect, useCallback } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const localKey = (campaignId) => `pinned-cards-${campaignId || 'default'}`;

export const usePinnedCards = (campaignId) => {
  const [pinnedIds, setPinnedIds] = useState(() => {
    try {
      const stored = localStorage.getItem(localKey(campaignId));
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Re-seed from localStorage when campaignId changes (e.g. user switches campaign)
  useEffect(() => {
    try {
      const stored = localStorage.getItem(localKey(campaignId));
      setPinnedIds(stored ? JSON.parse(stored) : []);
    } catch {
      setPinnedIds([]);
    }
  }, [campaignId]);

  useEffect(() => {
    try {
      localStorage.setItem(localKey(campaignId), JSON.stringify(pinnedIds));
    } catch (err) {
      console.warn('Failed to save pinned cards:', err);
    }
  }, [pinnedIds, campaignId]);

  const togglePin = useCallback((cardId) => {
    // Optimistic update — instant UI response
    setPinnedIds(prev => {
      if (prev.includes(cardId)) return prev.filter(id => id !== cardId);
      return [...prev, cardId];
    });
    // Sync to backend so DM prompt sees the pinned state
    if (campaignId && cardId) {
      fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/cards/${cardId}/pin`, {
        method: 'PATCH',
      }).catch(() => {});
    }
  }, [campaignId]);

  const isPinned = useCallback((cardId) => pinnedIds.includes(cardId), [pinnedIds]);

  return { pinnedIds, togglePin, isPinned, pinnedCount: pinnedIds.length };
};

export default usePinnedCards;
