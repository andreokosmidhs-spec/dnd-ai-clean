/**
 * useCanonTerms — fetches every canon scene for a campaign and indexes the
 * proper-noun terms (NPC names, item names, locations from titles + facts)
 * back to their scene. Refreshes when the global `rpg:canon-updated` event
 * fires so newly-canonized scenes immediately become linkable in DM narration.
 *
 * Returns:
 *   {
 *     termsMap: Map<string-lowercase, { term: original, scene }>,
 *     scenesById: Map<id, scene>,
 *     ready: bool,
 *     refresh: () => void,
 *   }
 */
import { useEffect, useState, useMemo, useCallback } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Words that look proper-noun-ish but should NEVER trip canon links —
// pronouns, sentence-start filler, generic D&D nouns, and common past-
// tense verbs that frequently appear capitalized at sentence start.
// Keep lowercase.
const STOP_TERMS = new Set([
  'the', 'a', 'an', 'you', 'i', 'we', 'they', 'he', 'she', 'it',
  'this', 'that', 'these', 'those', 'his', 'her', 'their',
  'mr', 'mrs', 'ms', 'sir', 'madam', 'lord', 'lady',
  'before', 'after', 'during', 'while', 'whilst',
  'inside', 'outside', 'across', 'beyond',
  'morning', 'evening', 'night', 'noon', 'dawn', 'dusk',
  'north', 'south', 'east', 'west',
  // Common past-tense / participle verbs and helper words that
  // frequently appear capitalized at the start of canon facts.
  'returned', 'found', 'gave', 'took', 'said', 'told', 'asked',
  'went', 'came', 'left', 'stayed', 'arrived', 'departed',
  'opened', 'closed', 'spoke', 'walked', 'ran', 'looked',
  'turned', 'stopped', 'started', 'finished', 'began', 'ended',
  'passed', 'failed', 'noticed', 'watched', 'saw', 'heard',
  'felt', 'thought', 'knew', 'remembered', 'forgot',
  'made', 'did', 'got', 'put', 'set', 'kept', 'held',
  'next', 'first', 'last', 'final',
  'yes', 'no', 'okay', 'well',
  // Abstract proper-noun leaders that scene titles frequently begin with —
  // matching the lowercase form in narration would create false-positive
  // canon chips on everyday words. Only filter the standalone form; the
  // multi-word phrases still survive ("Secrets of Veillane" → "Veillane").
  'secrets', 'shadows', 'whispers', 'beginning', 'journey', 'echoes',
  'tales', 'legends', 'truths', 'lies', 'memories', 'dreams', 'nightmares',
  'mysteries', 'rumors', 'silence', 'fate', 'destiny', 'fortune',
  'darkness', 'light', 'shade', 'mist', 'fog', 'storm',
]);

function extractProperNouns(text) {
  if (!text) return [];
  // Split by sentence-ending punctuation so we don't pair words across
  // sentence boundaries (e.g. "returned. Aleric" → "Returned Aleric").
  const segments = text.split(/[.!?:;,]\s+/);
  const out = new Set();
  for (const seg of segments) {
    const matches = seg.match(/\b[A-Z][a-zA-Z']{2,}(?:\s+[A-Z][a-zA-Z']{2,})?\b/g) || [];
    for (const m of matches) {
      const low = m.toLowerCase();
      if (STOP_TERMS.has(low)) continue;
      // Drop 2-word phrases that lead with an article — "The Locket" is
      // fine as a phrase but "The Aleric" would be a junk pairing.
      const first = low.split(/\s+/)[0];
      if (first === 'the' || first === 'a' || first === 'an') {
        // Keep only the second token in that case
        const tail = m.split(/\s+/).slice(1).join(' ');
        if (tail && !STOP_TERMS.has(tail.toLowerCase())) out.add(tail);
        continue;
      }
      out.add(m);
    }
  }
  return Array.from(out);
}

export default function useCanonTerms(campaignId) {
  const [scenes, setScenes] = useState([]);
  const [ready, setReady] = useState(false);

  const refresh = useCallback(async () => {
    if (!campaignId) {
      setScenes([]);
      setReady(true);
      return;
    }
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/canon`);
      if (!res.ok) {
        setScenes([]);
      } else {
        const data = await res.json();
        setScenes(data.scenes || []);
      }
    } catch {
      setScenes([]);
    } finally {
      setReady(true);
    }
  }, [campaignId]);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    const onUpdate = () => refresh();
    window.addEventListener('rpg:canon-updated', onUpdate);
    return () => window.removeEventListener('rpg:canon-updated', onUpdate);
  }, [refresh]);

  const { termsMap, scenesById } = useMemo(() => {
    const tMap = new Map();
    const sById = new Map();
    scenes.forEach((scene) => {
      sById.set(scene.id, scene);
      const corpus = [scene.title, ...(scene.facts || [])].join('. ');
      const nouns = extractProperNouns(corpus);
      // Prefer the scene where the noun FIRST appeared (most-recent canon
      // is listed first in the API, so we walk in reverse — older scenes
      // get priority since they "established" the term first).
      nouns.forEach((n) => {
        const key = n.toLowerCase();
        if (!tMap.has(key)) tMap.set(key, { term: n, scene });
      });
    });
    return { termsMap: tMap, scenesById: sById };
  }, [scenes]);

  return { termsMap, scenesById, ready, refresh };
}

/**
 * findCanonMentions — given a narration string and a termsMap from
 * useCanonTerms, return one entry per UNIQUE referenced scene (so
 * paragraphs referencing the locket 3 times produce one chip, not three).
 * Each entry: { scene, terms: [matchedString, ...] }.
 */
export function findCanonMentions(narration, termsMap) {
  if (!narration || !termsMap || termsMap.size === 0) return [];
  const lower = narration.toLowerCase();
  const bySceneId = new Map(); // sceneId -> { scene, terms: Set }
  for (const [key, { term, scene }] of termsMap.entries()) {
    // Word-boundary match — avoid "Anvil" matching inside "Anvilshire"
    const idx = lower.indexOf(key);
    if (idx === -1) continue;
    // Cheap word-boundary guard
    const before = idx === 0 ? ' ' : lower[idx - 1];
    const after = idx + key.length >= lower.length ? ' ' : lower[idx + key.length];
    if (/[a-z']/i.test(before) || /[a-z']/i.test(after)) continue;
    const entry = bySceneId.get(scene.id) || { scene, terms: new Set() };
    entry.terms.add(term);
    bySceneId.set(scene.id, entry);
  }
  return Array.from(bySceneId.values()).map(({ scene, terms }) => ({
    scene,
    terms: Array.from(terms).slice(0, 4),
  }));
}
