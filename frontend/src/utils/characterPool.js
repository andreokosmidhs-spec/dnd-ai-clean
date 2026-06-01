// Character pool capacity — keep in sync with backend if/when one is added.
// Surfaced here so a single import point governs every "new character" entry.
export const CHARACTER_POOL_LIMIT = 10;

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

/**
 * Fetch the current character count from the backend.
 * Returns -1 on network failure so callers can decide whether to allow
 * creation (we fail-open: if we can't check, we don't block the user).
 */
export const fetchCharacterCount = async () => {
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 5000);
    const res = await fetch(`${BACKEND_URL}/api/characters/v2/`, { signal: ctrl.signal });
    clearTimeout(timer);
    if (!res.ok) return -1;
    const data = await res.json();
    return Array.isArray(data) ? data.length : -1;
  } catch (_e) {
    return -1;
  }
};

/**
 * Returns true when the user is allowed to create a new character.
 * If at limit: shows a toast and returns false.
 * If we can't determine the count (network error): allows creation
 * (fail-open) so a transient backend hiccup never bricks the wizard.
 */
export const canCreateCharacter = async () => {
  const count = await fetchCharacterCount();
  if (count === -1) return true;
  if (count >= CHARACTER_POOL_LIMIT) {
    const msg = `Character pool full (${count}/${CHARACTER_POOL_LIMIT}). Delete one of your existing heroes to forge a new one.`;
    if (typeof window !== "undefined" && window.showToast) {
      window.showToast(msg, "error");
    } else if (typeof window !== "undefined") {
      // Last-resort fallback so the user still sees something
      // even if the toast bridge is missing.
      window.alert(msg);
    }
    return false;
  }
  return true;
};
