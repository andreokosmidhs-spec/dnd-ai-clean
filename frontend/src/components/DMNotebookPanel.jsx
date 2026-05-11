/**
 * DMNotebookPanel — the "DM Notebook" pause-menu surface. Lists every
 * lesson the DM has accumulated about this player, grouped by type. The
 * player can toggle each on/off, edit text, bump weight, or delete bad
 * lessons. Manual lesson entry is supported via the inline form at the
 * bottom of each group.
 *
 * Data model (server-side, see backend/services/dm_lessons.py):
 *   type: "rule_correction" | "dc_calibration" | "style_preference" | "taboo"
 *   weight: 1..5  (★ stars in the UI)
 *   trigger_keywords: short tags
 *   apply_count + last_applied_at — usage stats
 */
import React, { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Switch } from './ui/switch';
import {
  X, BookOpen, Plus, Trash2, Sparkles, ShieldAlert, Gavel, Wand2, Loader2,
  Pencil, Check,
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const GROUPS = [
  {
    key: 'rule_correction',
    title: 'Rules the DM Now Applies',
    hint: 'Skill checks the DM had missed and the player corrected.',
    icon: Gavel,
    accent: 'amber',
  },
  {
    key: 'dc_calibration',
    title: 'DC Calibrations',
    hint: 'When the difficulty number was wrong for this player.',
    icon: ShieldAlert,
    accent: 'rose',
  },
  {
    key: 'taboo',
    title: 'Avoid (player disliked)',
    hint: 'Patterns the DM should stop using.',
    icon: ShieldAlert,
    accent: 'rose',
  },
  {
    key: 'style_preference',
    title: 'Style the player loves',
    hint: 'Beats the DM nailed. Keep doing more of this.',
    icon: Sparkles,
    accent: 'emerald',
  },
];

const ACCENTS = {
  amber:   { border: 'border-amber-500/40',  bg: 'bg-amber-950/30',  text: 'text-amber-50',  chip: 'border-amber-400/50 text-amber-200' },
  emerald: { border: 'border-emerald-500/40',bg: 'bg-emerald-950/30',text: 'text-emerald-50',chip: 'border-emerald-400/50 text-emerald-200' },
  rose:    { border: 'border-rose-500/40',   bg: 'bg-rose-950/30',   text: 'text-rose-50',   chip: 'border-rose-400/50 text-rose-200' },
};

const Stars = ({ weight }) => {
  const n = Math.max(1, Math.min(5, Number(weight) || 1));
  return (
    <span className="text-amber-300 tracking-tight text-xs select-none" aria-label={`Weight ${n}/5`}>
      {'★'.repeat(n)}<span className="text-stone-600">{'★'.repeat(5 - n)}</span>
    </span>
  );
};

const LessonRow = ({ lesson, accent, onPatch, onDelete }) => {
  const a = ACCENTS[accent] || ACCENTS.amber;
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(lesson.text);
  const [busy, setBusy] = useState(false);

  const saveText = async () => {
    if (!text.trim() || text === lesson.text) {
      setEditing(false);
      setText(lesson.text);
      return;
    }
    setBusy(true);
    await onPatch({ text });
    setBusy(false);
    setEditing(false);
  };

  return (
    <div
      className={`rounded-lg border-2 ${a.border} ${lesson.enabled ? a.bg : 'bg-stone-900/40 opacity-60'} p-3`}
      data-testid={`dm-lesson-${lesson.id}`}
    >
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          {!editing ? (
            <p className={`${a.text} text-sm leading-relaxed italic font-serif`}>
              {lesson.text}
            </p>
          ) : (
            <Textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              autoFocus
              className="bg-stone-900 border-stone-700 text-amber-50 text-sm min-h-[70px]"
              data-testid={`dm-lesson-edit-${lesson.id}`}
            />
          )}
          {(lesson.trigger_keywords && lesson.trigger_keywords.length > 0) && (
            <div className="flex flex-wrap gap-1 mt-2">
              {lesson.trigger_keywords.slice(0, 6).map((k, i) => (
                <span
                  key={i}
                  className={`text-[10px] px-1.5 py-0.5 rounded border ${a.chip} bg-stone-950/50`}
                >
                  {k}
                </span>
              ))}
            </div>
          )}
          <div className="flex items-center justify-between mt-2 gap-2 flex-wrap">
            <div className="flex items-center gap-3 text-[10.5px] text-stone-400">
              <Stars weight={lesson.weight} />
              <span className="italic">applied {lesson.apply_count || 0}×</span>
              <span className="capitalize opacity-70">via {lesson.source}</span>
            </div>
            <div className="flex items-center gap-1">
              {/* Weight up/down */}
              <button
                onClick={() => onPatch({ weight: Math.max(1, (lesson.weight || 3) - 1) })}
                className="text-[10px] text-stone-400 hover:text-amber-200 px-1.5 py-0.5 rounded border border-stone-700 hover:border-amber-500/40"
                title="Lower weight"
                data-testid={`dm-lesson-weight-down-${lesson.id}`}
              >
                −
              </button>
              <button
                onClick={() => onPatch({ weight: Math.min(5, (lesson.weight || 3) + 1) })}
                className="text-[10px] text-stone-400 hover:text-amber-200 px-1.5 py-0.5 rounded border border-stone-700 hover:border-amber-500/40"
                title="Raise weight"
                data-testid={`dm-lesson-weight-up-${lesson.id}`}
              >
                +
              </button>
              {!editing ? (
                <button
                  onClick={() => { setText(lesson.text); setEditing(true); }}
                  className="text-stone-400 hover:text-amber-200 p-1 rounded border border-stone-700 hover:border-amber-500/40"
                  title="Edit text"
                  data-testid={`dm-lesson-edit-btn-${lesson.id}`}
                >
                  <Pencil className="h-3 w-3" />
                </button>
              ) : (
                <button
                  onClick={saveText}
                  disabled={busy}
                  className="text-emerald-300 hover:text-emerald-100 p-1 rounded border border-emerald-500/40"
                  title="Save"
                  data-testid={`dm-lesson-save-btn-${lesson.id}`}
                >
                  {busy ? <Loader2 className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
                </button>
              )}
              <button
                onClick={onDelete}
                className="text-stone-400 hover:text-rose-300 p-1 rounded border border-stone-700 hover:border-rose-500/40"
                title="Delete lesson"
                data-testid={`dm-lesson-delete-${lesson.id}`}
              >
                <Trash2 className="h-3 w-3" />
              </button>
              <div className="ml-1 flex items-center gap-1 pl-2 border-l border-stone-700">
                <Switch
                  checked={!!lesson.enabled}
                  onCheckedChange={(v) => onPatch({ enabled: v })}
                  data-testid={`dm-lesson-toggle-${lesson.id}`}
                />
                <span className="text-[10px] text-stone-400">{lesson.enabled ? 'on' : 'off'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const AddLessonInline = ({ groupKey, campaignId, characterId, onCreated }) => {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!text.trim()) {
      toast.error('Write the lesson first.');
      return;
    }
    setBusy(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/dm-lessons`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: groupKey,
          text: text.trim(),
          character_id: characterId || null,
        }),
      });
      if (!res.ok) throw new Error(`Create failed: ${res.status}`);
      const data = await res.json();
      onCreated(data.lesson);
      setText('');
      setOpen(false);
      toast.success('Lesson added.');
    } catch (e) {
      toast.error(e.message || 'Could not save lesson');
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="w-full text-[11px] text-stone-400 hover:text-amber-200 border-2 border-dashed border-stone-700 hover:border-amber-500/40 rounded-lg py-2 transition-colors flex items-center justify-center gap-1"
        data-testid={`dm-lesson-add-${groupKey}`}
      >
        <Plus className="h-3 w-3" /> Add a lesson manually
      </button>
    );
  }

  return (
    <div className="rounded-lg border-2 border-amber-500/40 bg-stone-900 p-3 space-y-2">
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="e.g. 'When NPCs are armed, describe their hand drifting toward the weapon before the player speaks.'"
        className="bg-stone-950 border-stone-700 text-amber-50 text-sm min-h-[80px]"
        data-testid={`dm-lesson-add-input-${groupKey}`}
      />
      <div className="flex justify-end gap-2">
        <Button
          size="sm" variant="ghost"
          onClick={() => { setText(''); setOpen(false); }}
          disabled={busy}
        >
          Cancel
        </Button>
        <Button
          size="sm"
          onClick={submit}
          disabled={busy}
          className="bg-amber-600 hover:bg-amber-500 text-stone-950 font-bold border border-amber-300"
          data-testid={`dm-lesson-add-submit-${groupKey}`}
        >
          {busy ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <Wand2 className="h-3 w-3 mr-1" />}
          Save lesson
        </Button>
      </div>
    </div>
  );
};

const DMNotebookPanel = ({ open, onClose, campaignId, characterId }) => {
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchLessons = useCallback(async () => {
    if (!campaignId) return;
    setLoading(true);
    try {
      const qs = characterId ? `?character_id=${characterId}` : '';
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/dm-lessons${qs}`);
      if (!res.ok) throw new Error(`Load failed: ${res.status}`);
      const data = await res.json();
      setLessons(data.lessons || []);
    } catch (e) {
      toast.error(e.message || 'Could not load lessons');
    } finally {
      setLoading(false);
    }
  }, [campaignId, characterId]);

  useEffect(() => {
    if (open) fetchLessons();
  }, [open, fetchLessons]);

  const patch = async (id, updates) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/dm-lessons/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (!res.ok) throw new Error(`Patch failed: ${res.status}`);
      const data = await res.json();
      setLessons((prev) => prev.map((l) => (l.id === id ? data.lesson : l)));
    } catch (e) {
      toast.error(e.message || 'Could not update lesson');
    }
  };

  const del = async (id) => {
    if (!window.confirm('Delete this lesson? The DM will stop applying it.')) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/dm-lessons/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
      setLessons((prev) => prev.filter((l) => l.id !== id));
      toast.success('Lesson removed.');
    } catch (e) {
      toast.error(e.message || 'Could not delete');
    }
  };

  if (!open) return null;

  const lessonsByType = lessons.reduce((acc, l) => {
    (acc[l.type] = acc[l.type] || []).push(l);
    return acc;
  }, {});

  return (
    <div
      className="fixed inset-0 z-[130] bg-stone-950/85 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
      data-testid="dm-notebook-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="DM Notebook"
    >
      <div
        className="relative w-full max-w-3xl max-h-[90vh] rounded-xl border-2 border-amber-500/70 bg-stone-950 shadow-[0_0_60px_rgba(245,158,11,0.35)] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
        data-testid="dm-notebook-panel"
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-amber-500/30 bg-stone-900">
          <div className="flex items-center gap-3">
            <BookOpen className="h-6 w-6 text-amber-300" />
            <div>
              <div className="text-[11px] uppercase tracking-[0.2em] text-amber-400 font-bold">
                Persistent Memory
              </div>
              <div className="text-amber-50 font-bold text-lg">DM Notebook</div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-stone-400 hover:text-amber-100 transition-colors"
            aria-label="Close notebook"
            data-testid="dm-notebook-close-btn"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="px-5 py-3 border-b border-amber-500/20 bg-stone-900/50">
          <p className="text-amber-100/80 text-xs leading-relaxed italic">
            Every time you flag a missed check, tap 👍 on a great beat, or 👎
            on a bad one, the DM distills it into a lesson here. The DM applies
            these every turn — toggle any off if it's hurting more than helping.
          </p>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
          {loading ? (
            <div className="text-stone-400 text-center py-8" data-testid="dm-notebook-loading">
              <Loader2 className="h-5 w-5 inline-block animate-spin mr-2" />
              Loading lessons…
            </div>
          ) : (
            GROUPS.map((g) => {
              const items = lessonsByType[g.key] || [];
              const Icon = g.icon;
              const accent = ACCENTS[g.accent];
              return (
                <section key={g.key} data-testid={`dm-notebook-group-${g.key}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className={`h-4 w-4 ${accent.text.replace('-50', '-300')}`} />
                    <h3 className={`font-bold text-sm ${accent.text}`}>{g.title}</h3>
                    <span className="text-[10.5px] text-stone-500 italic">— {g.hint}</span>
                    <span className="ml-auto text-[10.5px] text-stone-400">
                      {items.length} {items.length === 1 ? 'lesson' : 'lessons'}
                    </span>
                  </div>
                  <div className="space-y-2">
                    {items.length === 0 && (
                      <div className="text-stone-500 text-xs italic px-3 py-2 rounded border border-dashed border-stone-700">
                        (none yet)
                      </div>
                    )}
                    {items.map((lesson) => (
                      <LessonRow
                        key={lesson.id}
                        lesson={lesson}
                        accent={g.accent}
                        onPatch={(updates) => patch(lesson.id, updates)}
                        onDelete={() => del(lesson.id)}
                      />
                    ))}
                    <AddLessonInline
                      groupKey={g.key}
                      campaignId={campaignId}
                      characterId={characterId}
                      onCreated={(lesson) => setLessons((prev) => [lesson, ...prev])}
                    />
                  </div>
                </section>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default DMNotebookPanel;
