import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Login() {
  const [mode, setMode] = useState("login"); // "login" | "register" | "forgot"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password);
      }
      navigate("/menu");
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontFamily: "'Segoe UI', sans-serif",
    }}>
      <div style={{
        background: "rgba(255,255,255,0.05)",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 16,
        padding: "40px 48px",
        width: 380,
        backdropFilter: "blur(12px)",
      }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>⚔️</div>
          <h1 style={{ color: "#e2d9f3", margin: 0, fontSize: 24, fontWeight: 700 }}>
            D&D AI
          </h1>
          <p style={{ color: "#94a3b8", margin: "6px 0 0", fontSize: 14 }}>
            {mode === "login" ? "Welcome back, adventurer" : "Begin your legend"}
          </p>
        </div>

        {/* Mode toggle — only show for login/register, not forgot */}
        {mode !== "forgot" && (
          <div style={{
            display: "flex",
            background: "rgba(0,0,0,0.3)",
            borderRadius: 8,
            padding: 4,
            marginBottom: 24,
          }}>
            {["login", "register"].map((m) => (
              <button key={m} onClick={() => { setMode(m); setError(""); }} style={{
                flex: 1,
                padding: "8px 0",
                borderRadius: 6,
                border: "none",
                cursor: "pointer",
                fontSize: 14,
                fontWeight: 500,
                background: mode === m ? "rgba(139,92,246,0.6)" : "transparent",
                color: mode === m ? "#fff" : "#94a3b8",
                transition: "all 0.2s",
              }}>
                {m === "login" ? "Sign In" : "Register"}
              </button>
            ))}
          </div>
        )}

        {/* Forgot password view */}
        {mode === "forgot" && (
          <div style={{ marginBottom: 24 }}>
            <h2 style={{ color: "#e2d9f3", fontSize: 18, fontWeight: 600, margin: "0 0 8px" }}>
              Reset Password
            </h2>
            <p style={{ color: "#94a3b8", fontSize: 14, lineHeight: 1.6, margin: 0 }}>
              Email us at{" "}
              <a href="mailto:support@rpgforge.app" style={{ color: "#c4b5fd" }}>
                support@rpgforge.app
              </a>{" "}
              with your registered email address and we'll reset your password manually.
            </p>
            <button onClick={() => { setMode("login"); setError(""); }} style={{
              marginTop: 20, background: "none", border: "none",
              color: "#8b5cf6", fontSize: 13, cursor: "pointer",
            }}>
              ← Back to Sign In
            </button>
          </div>
        )}

        {mode !== "forgot" && <form onSubmit={submit}>
          <label style={{ display: "block", marginBottom: 16 }}>
            <span style={{ color: "#94a3b8", fontSize: 13, display: "block", marginBottom: 6 }}>
              Email
            </span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "10px 14px",
                background: "rgba(0,0,0,0.4)",
                border: "1px solid rgba(255,255,255,0.15)",
                borderRadius: 8,
                color: "#e2d9f3",
                fontSize: 14,
                outline: "none",
                boxSizing: "border-box",
              }}
              placeholder="you@example.com"
            />
          </label>

          <label style={{ display: "block", marginBottom: 24 }}>
            <span style={{ color: "#94a3b8", fontSize: 13, display: "block", marginBottom: 6 }}>
              Password
            </span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              style={{
                width: "100%",
                padding: "10px 14px",
                background: "rgba(0,0,0,0.4)",
                border: "1px solid rgba(255,255,255,0.15)",
                borderRadius: 8,
                color: "#e2d9f3",
                fontSize: 14,
                outline: "none",
                boxSizing: "border-box",
              }}
              placeholder="••••••••"
            />
          </label>

          {error && (
            <div style={{
              background: "rgba(239,68,68,0.15)",
              border: "1px solid rgba(239,68,68,0.4)",
              borderRadius: 8,
              padding: "10px 14px",
              color: "#fca5a5",
              fontSize: 13,
              marginBottom: 16,
            }}>
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} style={{
            width: "100%",
            padding: "12px 0",
            background: loading ? "rgba(139,92,246,0.4)" : "rgba(139,92,246,0.8)",
            border: "none",
            borderRadius: 8,
            color: "#fff",
            fontSize: 15,
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
            transition: "all 0.2s",
          }}>
            {loading ? "..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>

          {mode === "login" && (
            <button type="button" onClick={() => { setMode("forgot"); setError(""); }} style={{
              display: "block", width: "100%", marginTop: 12,
              background: "none", border: "none", color: "#64748b",
              fontSize: 13, cursor: "pointer", textAlign: "center",
            }}>
              Forgot password?
            </button>
          )}
        </form>}

        <button onClick={() => navigate("/menu")} style={{
          display: "block",
          margin: "20px auto 0",
          background: "none",
          border: "none",
          color: "#64748b",
          fontSize: 13,
          cursor: "pointer",
          textDecoration: "underline",
        }}>
          Continue without account
        </button>
      </div>
    </div>
  );
}
