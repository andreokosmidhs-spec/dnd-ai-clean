/**
 * GameEscapeMenu — small in-game pause menu, opens on ESC.
 * Three top-level options: Continue · Settings · Main Menu.
 * Settings opens an inline panel for the font-size preset (3 options).
 *
 * Visual style stays in line with the rest of the dark/amber Adventure-Log
 * aesthetic — solid stone-950 backdrop, amber border, large readable text.
 */
import React, { useEffect, useState, useCallback } from 'react';
import { Button } from './ui/button';
import { Play, Settings as SettingsIcon, Home, ChevronLeft, X, Type } from 'lucide-react';
import { useFontSize } from '../contexts/FontSizeContext';

const GameEscapeMenu = ({ open, onClose, onMainMenu }) => {
  const [view, setView] = useState('root');  // 'root' | 'settings'
  const { preset, setPreset, presets, order } = useFontSize();

  // Reset to root view whenever the menu re-opens.
  useEffect(() => {
    if (open) setView('root');
  }, [open]);

  const handleContinue = useCallback(() => {
    onClose && onClose();
  }, [onClose]);

  const handleMainMenu = useCallback(() => {
    if (typeof window !== 'undefined') {
      const ok = window.confirm(
        'Return to the main menu? Your current campaign is auto-saved on the server, so you can resume it later.'
      );
      if (!ok) return;
    }
    onClose && onClose();
    onMainMenu && onMainMenu();
  }, [onClose, onMainMenu]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[120] bg-stone-950/85 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={handleContinue}
      data-testid="game-escape-menu-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Pause menu"
    >
      <div
        className="relative w-full max-w-md rounded-xl border-2 border-amber-500/70 bg-stone-950 shadow-[0_0_60px_rgba(245,158,11,0.35)] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        data-testid="game-escape-menu-panel"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-amber-500/30 bg-stone-900">
          <div className="flex items-center gap-3">
            {view === 'settings' && (
              <button
                onClick={() => setView('root')}
                className="text-amber-200 hover:text-amber-50 transition-colors"
                aria-label="Back"
                data-testid="escape-menu-back-btn"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
            )}
            <div>
              <div className="text-[11px] uppercase tracking-[0.2em] text-amber-400 font-bold">
                {view === 'settings' ? 'Settings' : 'Paused'}
              </div>
              <div className="text-amber-50 font-bold text-lg">
                {view === 'settings' ? 'Reading Comfort' : 'Game Menu'}
              </div>
            </div>
          </div>
          <button
            onClick={handleContinue}
            className="text-stone-400 hover:text-amber-100 transition-colors"
            aria-label="Close menu"
            data-testid="escape-menu-close-btn"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5">
          {view === 'root' ? (
            <div className="flex flex-col gap-3" data-testid="escape-menu-root">
              <Button
                onClick={handleContinue}
                className="h-14 text-base font-bold bg-emerald-600 hover:bg-emerald-500 text-stone-950 border border-emerald-300 justify-start gap-3"
                data-testid="escape-menu-continue-btn"
              >
                <Play className="h-5 w-5" />
                <div className="flex flex-col items-start leading-tight">
                  <span>Continue</span>
                  <span className="text-[11px] font-normal opacity-80">Resume the adventure</span>
                </div>
              </Button>

              <Button
                onClick={() => setView('settings')}
                className="h-14 text-base font-bold bg-stone-800 hover:bg-stone-700 text-amber-50 border border-amber-500/40 justify-start gap-3"
                data-testid="escape-menu-settings-btn"
              >
                <SettingsIcon className="h-5 w-5 text-amber-300" />
                <div className="flex flex-col items-start leading-tight">
                  <span>Settings</span>
                  <span className="text-[11px] font-normal text-amber-200/80">
                    Font size · {presets[preset]?.label}
                  </span>
                </div>
              </Button>

              <Button
                onClick={handleMainMenu}
                className="h-14 text-base font-bold bg-stone-800 hover:bg-rose-900 text-amber-50 border border-rose-500/40 justify-start gap-3"
                data-testid="escape-menu-main-menu-btn"
              >
                <Home className="h-5 w-5 text-rose-300" />
                <div className="flex flex-col items-start leading-tight">
                  <span>Go Back to Main Menu</span>
                  <span className="text-[11px] font-normal text-rose-200/80">
                    Saves automatically — resume anytime
                  </span>
                </div>
              </Button>
            </div>
          ) : (
            <div className="flex flex-col gap-3" data-testid="escape-menu-settings">
              <div className="text-amber-100/85 text-sm leading-relaxed mb-1">
                <Type className="h-4 w-4 inline-block mr-1.5 -mt-0.5 text-amber-300" />
                Pick the size that's easiest on your eyes. Applies across the
                whole game — narration, cards, menus.
              </div>

              {order.map((key) => {
                const cfg = presets[key];
                const active = preset === key;
                return (
                  <button
                    key={key}
                    onClick={() => setPreset(key)}
                    className={`relative rounded-lg border-2 px-4 py-3 text-left transition-all
                      ${active
                        ? 'border-emerald-400 bg-emerald-950/50 shadow-[0_0_20px_rgba(16,185,129,0.3)]'
                        : 'border-stone-700 bg-stone-900 hover:border-amber-500/50 hover:bg-stone-800'}`}
                    data-testid={`escape-menu-fontsize-${key}`}
                    aria-pressed={active}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className={`font-bold ${active ? 'text-emerald-100' : 'text-amber-50'}`}>
                          {cfg.label}
                        </div>
                        <div
                          className={`italic font-serif mt-1 ${active ? 'text-emerald-200/90' : 'text-amber-100/80'}`}
                          // Independent preview — uses literal pixel sizes so the
                          // sample reflects the chosen preset regardless of the
                          // current root scale.
                          style={{ fontSize: `${14 * cfg.scale}px`, lineHeight: 1.5 }}
                        >
                          The wooden sign hangs at eye level, ink still wet…
                        </div>
                      </div>
                      <div className={`shrink-0 ml-3 w-8 h-8 rounded-full flex items-center justify-center font-bold border-2
                        ${active
                          ? 'border-emerald-300 bg-emerald-500 text-stone-950'
                          : 'border-stone-600 bg-stone-800 text-amber-200'}`}
                      >
                        {Math.round(cfg.scale * 100)}
                      </div>
                    </div>
                  </button>
                );
              })}

              <div className="text-[11px] text-stone-400 italic mt-1">
                Saved automatically. Press <kbd className="px-1 rounded bg-stone-800 border border-stone-600 text-stone-200 not-italic">Esc</kbd> to close.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GameEscapeMenu;
