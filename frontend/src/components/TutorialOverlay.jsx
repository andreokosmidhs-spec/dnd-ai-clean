import React, { useEffect } from "react";
import { useTutorial } from "../contexts/TutorialContext";

const STEPS = [
  {
    icon: "⚔️",
    title: "Welcome, Adventurer",
    subtitle: "D&D AI — Your Personal Dungeon Master",
    body: "This is a full D&D 5e adventure powered by AI. The Dungeon Master describes your world, responds to your choices, and enforces the rules — you just play.",
    tips: [
      "No DM experience needed — the AI handles everything",
      "Your choices genuinely shape the story",
      "All standard D&D 5e rules are in play",
    ],
    color: "#f59e0b",
  },
  {
    icon: "💬",
    title: "The Core Loop",
    subtitle: "Type anything. The DM responds.",
    body: "The text box at the bottom is your only control. Type what your character does or says — as simple or detailed as you like. The DM narrates what happens next.",
    tips: [
      '"I look around the tavern for anyone suspicious"',
      '"I draw my sword and attack the guard"',
      '"I try to pick the lock on the door"',
      "Be specific — more detail gives better results",
    ],
    color: "#8b5cf6",
    highlight: "text input",
  },
  {
    icon: "🎲",
    title: "Ability Checks",
    subtitle: "Roll dice when the DM asks",
    body: "When your action needs a skill check, a roll card appears. It shows the skill, your modifier, and the Difficulty Class (DC) you need to beat.",
    tips: [
      "Your modifier comes from your ability scores",
      "Roll 20 (d20) + modifier vs DC",
      "Advantage = roll twice, take higher",
      "Disadvantage = roll twice, take lower",
      "Natural 20 is always a critical success",
    ],
    color: "#10b981",
    example: {
      label: "Example check",
      content: "Perception DC 14  |  Your modifier: +3  |  You need a 11 or higher",
    },
  },
  {
    icon: "🃏",
    title: "Your Character Deck",
    subtitle: "Cards are your abilities, spells, and gear",
    body: "Every ability, spell, and special item your character has is a card. Click a card to use it — the DM handles the mechanics. Cards recharge on rest.",
    tips: [
      "Spell cards track your spell slots automatically",
      "Weapon cards resolve attack rolls",
      "Per-day abilities (like Second Wind) recharge on Long Rest",
      "You earn new cards from quests and level-ups",
    ],
    color: "#6366f1",
  },
  {
    icon: "🗡️",
    title: "Combat",
    subtitle: "Initiative, actions, and the battlefield grid",
    body: "When combat starts the screen switches to the Battlefield. You see a lane grid (Melee → Far range), initiative order on the right, and your HP/AC at the bottom.",
    tips: [
      "Melee ≤5ft · Close ≤30ft · Medium ≤60ft · Far 60ft+",
      "Each round: type your action in the text box",
      "You get one Action, one Bonus Action, and movement",
      "Spells and weapons are in your card deck",
      "Enemies have HP bars — watch them deplete",
    ],
    color: "#ef4444",
  },
  {
    icon: "📜",
    title: "Quests & the Campaign Log",
    subtitle: "Track objectives, knowledge, and NPCs",
    body: "Quests are assigned through the story — the DM will mention them naturally. Open the Quest Log (top bar) to see your active objectives. The Campaign Log tracks every NPC, location, and rumor you've encountered.",
    tips: [
      "Complete objectives for XP and card rewards",
      "Multi-step investigations unfold over several scenes",
      "Click entity names in narration to inspect them",
      "The Campaign Log is your in-game encyclopedia",
    ],
    color: "#f97316",
  },
  {
    icon: "💤",
    title: "Rest & Recovery",
    subtitle: "Two types of rest — use them wisely",
    body: "Type 'I take a short rest' or 'I make camp for the night' at any time outside combat. Rest recovers HP and recharges your abilities.",
    tips: [
      "Short Rest: roll hit dice to recover HP (2 per long rest)",
      "Long Rest: fully restore HP, spell slots, and all per-day cards",
      "You can't rest during combat",
      "Long Rest takes 8 in-game hours — the world moves on",
    ],
    color: "#64748b",
    example: {
      label: "Try it",
      content: 'Type "I take a short rest and tend to my wounds"',
    },
  },
];

export default function TutorialOverlay() {
  const { open, step, setStep, closeTutorial } = useTutorial();

  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (e.key === "Escape") closeTutorial(false);
      if (e.key === "ArrowRight" && step < STEPS.length - 1) setStep((s) => s + 1);
      if (e.key === "ArrowLeft" && step > 0) setStep((s) => s - 1);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, step, setStep, closeTutorial]);

  if (!open) return null;

  const current = STEPS[step];
  const isFirst = step === 0;
  const isLast = step === STEPS.length - 1;

  return (
    <div
      style={{
        position: "fixed", inset: 0,
        background: "rgba(0,0,0,0.82)",
        backdropFilter: "blur(4px)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 200, padding: 16,
        fontFamily: "'Segoe UI', system-ui, sans-serif",
      }}
      onClick={() => closeTutorial(false)}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "linear-gradient(145deg, #1c1917, #0f0f1a)",
          border: `1px solid ${current.color}55`,
          borderRadius: 20,
          boxShadow: `0 0 60px ${current.color}22, 0 24px 48px rgba(0,0,0,0.6)`,
          width: "100%",
          maxWidth: 640,
          overflow: "hidden",
          animation: "tutorial-in 0.22s ease-out",
        }}
      >
        <style>{`
          @keyframes tutorial-in {
            from { opacity: 0; transform: translateY(12px) scale(0.97); }
            to   { opacity: 1; transform: translateY(0) scale(1); }
          }
        `}</style>

        {/* Header strip */}
        <div style={{
          background: `linear-gradient(90deg, ${current.color}18, transparent)`,
          borderBottom: `1px solid ${current.color}33`,
          padding: "20px 24px 16px",
          display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{
              width: 56, height: 56, borderRadius: 14,
              background: `${current.color}20`,
              border: `1px solid ${current.color}44`,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 28, flexShrink: 0,
            }}>
              {current.icon}
            </div>
            <div>
              <div style={{
                fontSize: 11, fontWeight: 700, letterSpacing: "0.15em",
                textTransform: "uppercase", color: current.color, marginBottom: 2,
              }}>
                Step {step + 1} of {STEPS.length}
              </div>
              <div style={{ fontSize: 20, fontWeight: 700, color: "#f1f5f9", lineHeight: 1.2 }}>
                {current.title}
              </div>
              <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 2 }}>
                {current.subtitle}
              </div>
            </div>
          </div>
          <button
            onClick={() => closeTutorial(false)}
            style={{
              background: "none", border: "none", color: "#475569",
              cursor: "pointer", fontSize: 20, lineHeight: 1, padding: "4px 8px",
              flexShrink: 0,
            }}
            title="Close"
          >×</button>
        </div>

        {/* Body */}
        <div style={{ padding: "20px 24px" }}>
          <p style={{ color: "#cbd5e1", fontSize: 15, lineHeight: 1.65, margin: "0 0 20px" }}>
            {current.body}
          </p>

          {/* Tips list */}
          <div style={{
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.07)",
            borderRadius: 12, padding: "14px 16px",
            marginBottom: current.example ? 12 : 0,
          }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 10 }}>
              Key Points
            </div>
            <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
              {current.tips.map((tip, i) => (
                <li key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                  <span style={{ color: current.color, flexShrink: 0, marginTop: 1 }}>▸</span>
                  <span style={{ color: "#94a3b8", fontSize: 14, lineHeight: 1.5 }}>{tip}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Example callout */}
          {current.example && (
            <div style={{
              background: `${current.color}0d`,
              border: `1px solid ${current.color}33`,
              borderRadius: 10, padding: "12px 16px",
              display: "flex", gap: 10, alignItems: "flex-start",
            }}>
              <span style={{ fontSize: 16 }}>💡</span>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: current.color, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 4 }}>
                  {current.example.label}
                </div>
                <div style={{ color: "#e2e8f0", fontSize: 14, fontStyle: "italic" }}>
                  {current.example.content}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          borderTop: "1px solid rgba(255,255,255,0.07)",
          padding: "14px 24px",
          display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12,
        }}>
          {/* Step dots */}
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            {STEPS.map((s, i) => (
              <button
                key={i}
                onClick={() => setStep(i)}
                style={{
                  width: i === step ? 20 : 7,
                  height: 7,
                  borderRadius: 4,
                  border: "none",
                  background: i === step ? current.color : "rgba(255,255,255,0.15)",
                  cursor: "pointer",
                  padding: 0,
                  transition: "all 0.2s",
                }}
                aria-label={`Go to step ${i + 1}`}
              />
            ))}
          </div>

          {/* Navigation */}
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {!isFirst && (
              <button
                onClick={() => setStep((s) => s - 1)}
                style={{
                  padding: "8px 16px", borderRadius: 8,
                  background: "rgba(255,255,255,0.06)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  color: "#94a3b8", fontSize: 14, cursor: "pointer",
                }}
              >
                ← Back
              </button>
            )}

            {isFirst && (
              <button
                onClick={() => closeTutorial(true)}
                style={{
                  padding: "8px 16px", borderRadius: 8,
                  background: "none", border: "none",
                  color: "#475569", fontSize: 13, cursor: "pointer",
                }}
              >
                Skip tutorial
              </button>
            )}

            <button
              onClick={() => {
                if (isLast) closeTutorial(true);
                else setStep((s) => s + 1);
              }}
              style={{
                padding: "9px 22px", borderRadius: 8,
                background: current.color,
                border: "none",
                color: "#000", fontSize: 14, fontWeight: 700,
                cursor: "pointer",
                boxShadow: `0 4px 16px ${current.color}44`,
              }}
            >
              {isLast ? "Begin Adventure" : "Next →"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Re-export step count for convenience
export const TUTORIAL_STEP_COUNT = STEPS.length;
