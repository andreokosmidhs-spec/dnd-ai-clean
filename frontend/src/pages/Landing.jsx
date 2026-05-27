import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const FEATURES = [
  {
    icon: "🎭",
    title: "Living AI Dungeon Master",
    desc: "A full Claude-powered DM that remembers your choices, enforces D&D 5e rules, and crafts stories around your decisions.",
  },
  {
    icon: "⚔️",
    title: "Real D&D 5e Mechanics",
    desc: "Spell slots, hit dice, ability checks, short & long rests, conditions — all tracked automatically so you can focus on roleplaying.",
  },
  {
    icon: "🖼️",
    title: "AI Scene Images",
    desc: "Every dramatic moment comes to life with an AI-generated scene illustration. Available on paid plans.",
  },
  {
    icon: "🗺️",
    title: "Persistent World",
    desc: "Your campaign world evolves between sessions. NPCs remember you, quests develop, and consequences carry forward.",
  },
  {
    icon: "🎙️",
    title: "Narrator Voices & Tones",
    desc: "Choose your DM's style — Balanced, Heroic, Gritty, Dark, or Comedic — and hear narration read aloud via browser TTS.",
  },
  {
    icon: "📖",
    title: "Session Recaps",
    desc: "Auto-generated adventure journal entries after every session so you never lose the thread of your story.",
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(160deg, #0a0818 0%, #1a0f3a 40%, #0f1a2e 100%)",
      fontFamily: "'Segoe UI', sans-serif",
      color: "#e2d9f3",
    }}>

      {/* Nav */}
      <nav className="landing-nav" style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        position: "sticky", top: 0, zIndex: 10,
        background: "rgba(10,8,24,0.85)", backdropFilter: "blur(12px)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 24 }}>⚔️</span>
          <span style={{ fontSize: 20, fontWeight: 700, color: "#f59e0b" }}>RPG Forge</span>
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <button className="landing-nav-hide-mobile" onClick={() => navigate("/pricing")} style={{
            background: "none", border: "none", color: "#94a3b8",
            fontSize: 14, cursor: "pointer", padding: "6px 12px",
          }}>
            Pricing
          </button>
          {user ? (
            <button className="landing-nav-cta" onClick={() => navigate("/menu")} style={{
              background: "rgba(139,92,246,0.8)", border: "none",
              borderRadius: 8, color: "#fff", fontSize: 14,
              fontWeight: 600, padding: "8px 20px", cursor: "pointer",
            }}>
              Open Game
            </button>
          ) : (
            <>
              <button className="landing-nav-hide-mobile" onClick={() => navigate("/login")} style={{
                background: "none", border: "1px solid rgba(255,255,255,0.15)",
                borderRadius: 8, color: "#94a3b8", fontSize: 14,
                padding: "8px 20px", cursor: "pointer",
              }}>
                Sign In
              </button>
              <button className="landing-nav-cta" onClick={() => navigate("/menu")} style={{
                background: "rgba(139,92,246,0.8)", border: "none",
                borderRadius: 8, color: "#fff", fontSize: 14,
                fontWeight: 600, padding: "8px 20px", cursor: "pointer",
              }}>
                Play Free
              </button>
            </>
          )}
        </div>
      </nav>

      {/* Hero */}
      <section className="landing-hero" style={{
        display: "flex", flexDirection: "column", alignItems: "center",
        textAlign: "center",
      }}>
        <div style={{
          display: "inline-block", background: "rgba(139,92,246,0.15)",
          border: "1px solid rgba(139,92,246,0.3)", borderRadius: 20,
          padding: "6px 16px", fontSize: 13, color: "#c4b5fd",
          marginBottom: 28, letterSpacing: 0.5,
        }}>
          Powered by Claude AI · D&D 5e Rules Engine
        </div>

        <h1 style={{
          fontSize: "clamp(40px, 7vw, 72px)", fontWeight: 800,
          margin: "0 0 20px", lineHeight: 1.1,
          background: "linear-gradient(135deg, #f59e0b, #fbbf24, #e2d9f3)",
          WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
        }}>
          Your AI Dungeon Master<br />Awaits
        </h1>

        <p style={{
          fontSize: "clamp(16px, 2.5vw, 20px)", color: "#94a3b8",
          maxWidth: 560, margin: "0 0 48px", lineHeight: 1.6,
        }}>
          A fully rules-accurate D&amp;D 5e text RPG with a living AI DM that remembers
          your story, reacts to your choices, and never runs out of adventure.
        </p>

        <div className="landing-cta-row">
          <button onClick={() => navigate("/menu")} style={{
            padding: "16px 40px", background: "linear-gradient(135deg, #8b5cf6, #7c3aed)",
            border: "none", borderRadius: 12, color: "#fff",
            fontSize: 17, fontWeight: 700, cursor: "pointer",
            boxShadow: "0 0 32px rgba(139,92,246,0.4)",
          }}>
            Play Free — No Download
          </button>
          <button onClick={() => navigate("/pricing")} style={{
            padding: "16px 40px", background: "transparent",
            border: "1px solid rgba(255,255,255,0.2)", borderRadius: 12,
            color: "#e2d9f3", fontSize: 17, cursor: "pointer",
          }}>
            See Plans
          </button>
        </div>

        <p style={{ color: "#475569", fontSize: 13, marginTop: 20 }}>
          100 free turns/month · No credit card required
        </p>
      </section>

      {/* Features */}
      <section style={{ padding: "60px 24px 80px", maxWidth: 1100, margin: "0 auto" }}>
        <h2 style={{
          textAlign: "center", fontSize: 32, fontWeight: 700,
          margin: "0 0 12px", color: "#e2d9f3",
        }}>
          Everything a tabletop session needs
        </h2>
        <p style={{ textAlign: "center", color: "#64748b", marginBottom: 52, fontSize: 16 }}>
          No prep, no scheduling, no missing players — just adventure.
        </p>

        <div className="landing-features-grid" style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: 24,
        }}>
          {FEATURES.map((f) => (
            <div key={f.title} style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 16, padding: "28px 24px",
            }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>{f.icon}</div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#e2d9f3" }}>{f.title}</div>
              <div style={{ fontSize: 14, color: "#64748b", lineHeight: 1.6 }}>{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Banner */}
      <section style={{
        background: "rgba(139,92,246,0.08)", borderTop: "1px solid rgba(139,92,246,0.2)",
        borderBottom: "1px solid rgba(139,92,246,0.2)", padding: "60px 24px",
        textAlign: "center",
      }}>
        <h2 style={{ fontSize: 32, fontWeight: 700, margin: "0 0 12px" }}>
          Ready to roll for initiative?
        </h2>
        <p style={{ color: "#94a3b8", marginBottom: 32, fontSize: 16 }}>
          Start your first campaign in under 2 minutes.
        </p>
        <button onClick={() => navigate("/menu")} style={{
          padding: "16px 48px", background: "linear-gradient(135deg, #8b5cf6, #7c3aed)",
          border: "none", borderRadius: 12, color: "#fff",
          fontSize: 17, fontWeight: 700, cursor: "pointer",
          boxShadow: "0 0 32px rgba(139,92,246,0.35)",
        }}>
          Start for Free
        </button>
      </section>

      {/* Footer */}
      <footer className="landing-footer" style={{
        display: "flex",
        justifyContent: "space-between", alignItems: "center",
        borderTop: "1px solid rgba(255,255,255,0.06)",
        color: "#475569", fontSize: 13,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span>⚔️</span>
          <span>RPG Forge &copy; {new Date().getFullYear()}</span>
        </div>
        <div className="landing-footer-links" style={{ display: "flex", gap: 24 }}>
          <button onClick={() => navigate("/tos")} style={{
            background: "none", border: "none", color: "#475569",
            fontSize: 13, cursor: "pointer", textDecoration: "underline",
          }}>
            Terms of Service
          </button>
          <button onClick={() => navigate("/privacy")} style={{
            background: "none", border: "none", color: "#475569",
            fontSize: 13, cursor: "pointer", textDecoration: "underline",
          }}>
            Privacy Policy
          </button>
          <button onClick={() => navigate("/pricing")} style={{
            background: "none", border: "none", color: "#475569",
            fontSize: 13, cursor: "pointer", textDecoration: "underline",
          }}>
            Pricing
          </button>
        </div>
      </footer>
    </div>
  );
}
