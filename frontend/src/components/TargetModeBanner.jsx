/**
 * TargetModeBanner — small floating chip at the top of the chat surface
 * that tells the player they're in Observe / Search mode and gives them
 * a Cancel affordance. Visible only when targetMode is non-null.
 *
 * SearchTargetModal — when search mode picks a word, this modal asks
 * "What are you looking for?" before submitting the search to the DM.
 */
import React, { useEffect, useState } from 'react';
import { Eye, Search, X, Wand2 } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { useTargetMode } from '../contexts/TargetModeContext';

export const TargetModeBanner = () => {
  const { mode, clearMode } = useTargetMode();
  if (!mode) return null;
  const isObserve = mode === 'observe';
  const Icon = isObserve ? Eye : Search;
  const label = isObserve ? 'Observe' : 'Search';
  const tone = isObserve
    ? 'border-emerald-400/70 bg-emerald-950/70 text-emerald-50'
    : 'border-amber-400/70 bg-amber-950/70 text-amber-50';
  return (
    <div
      className={`fixed top-3 left-1/2 -translate-x-1/2 z-[120] flex items-center gap-2.5 px-3 py-1.5 rounded-full border-2 ${tone} backdrop-blur-sm shadow-[0_6px_24px_rgba(0,0,0,0.5)] animate-in fade-in slide-in-from-top-2 duration-200`}
      data-testid={`target-mode-banner-${mode}`}
      role="status"
      aria-live="polite"
    >
      <Icon className={`h-4 w-4 ${isObserve ? 'text-emerald-300' : 'text-amber-300'}`} />
      <div className="text-[12px] leading-tight">
        <div className="font-bold uppercase tracking-[0.18em] text-[10.5px]">{label} Mode</div>
        <div className="opacity-80">
          {isObserve
            ? 'Click any word in the DM narration to inspect it.'
            : 'Click any word — you\'ll tell the DM what you\'re looking for.'}
        </div>
      </div>
      <button
        onClick={clearMode}
        className="ml-1 p-0.5 rounded-full hover:bg-white/10 transition-colors"
        aria-label="Cancel target mode (Esc)"
        data-testid="target-mode-cancel-btn"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
};

export const SearchTargetModal = ({ open, target, onClose, onSubmit }) => {
  const [query, setQuery] = useState('');
  useEffect(() => { if (open) setQuery(''); }, [open]);

  if (!open) return null;

  const submit = () => {
    const q = query.trim();
    if (!q) return;
    onSubmit(q);
  };

  return (
    <div
      className="fixed inset-0 z-[160] bg-stone-950/70 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
      data-testid="search-target-modal-overlay"
      role="dialog"
      aria-modal="true"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-xl border-2 border-amber-400/70 bg-gradient-to-br from-stone-950 via-stone-900 to-amber-950/30 shadow-[0_20px_60px_rgba(0,0,0,0.7)] overflow-hidden animate-in fade-in zoom-in-95 duration-200"
        data-testid="search-target-modal"
      >
        <div className="flex items-center gap-2.5 px-4 py-3 border-b border-amber-400/30 bg-stone-900">
          <Search className="h-5 w-5 text-amber-300" />
          <div className="flex-1 min-w-0">
            <div className="text-[10px] uppercase tracking-[0.2em] text-amber-400 font-bold leading-none">
              Investigation Target
            </div>
            <div className="text-amber-50 font-bold text-base leading-tight font-serif truncate mt-0.5">
              {target}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-stone-400 hover:text-amber-100 p-1 rounded-full hover:bg-white/10 transition-colors"
            aria-label="Close (Esc)"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="px-4 py-4 space-y-2">
          <label className="block text-[12px] uppercase tracking-wider font-bold text-amber-200">
            What are you looking for?
          </label>
          <Textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit();
            }}
            placeholder={`e.g. "hidden compartment", "maker's mark", "anything that smells off about it"`}
            className="bg-stone-950 border-amber-500/40 text-amber-50 placeholder:text-amber-200/40 min-h-[90px] font-serif"
            autoFocus
            data-testid="search-target-input"
          />
          <p className="text-[11px] text-amber-300/70 italic">
            The DM will narrate what your search turns up — be specific to get specific clues.
          </p>
        </div>
        <div className="px-4 py-3 border-t border-amber-400/20 bg-stone-950/80 flex justify-end gap-2">
          <Button size="sm" variant="ghost" onClick={onClose}
            className="h-9 text-amber-200/70 hover:text-amber-100">
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={submit}
            disabled={!query.trim()}
            className="h-9 bg-amber-600 hover:bg-amber-500 text-stone-950 font-bold border border-amber-300"
            data-testid="search-target-submit-btn"
          >
            <Wand2 className="h-4 w-4 mr-1" /> Search
          </Button>
        </div>
      </div>
    </div>
  );
};
