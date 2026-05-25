import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../contexts/AuthContext";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "";

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    period: "forever",
    turns: "100 turns/month",
    features: ["100 turns per month", "Full DM narration", "All character classes"],
    color: "#64748b",
    highlight: false,
  },
  {
    id: "basic",
    name: "Adventurer",
    price: "$10",
    period: "/month",
    turns: "600 turns/month",
    features: ["600 turns per month", "Full DM narration", "Story Consistency AI", "Quest tracking"],
    color: "#8b5cf6",
    highlight: true,
  },
  {
    id: "unlimited",
    name: "Legend",
    price: "$35",
    period: "/month",
    turns: "2,400 turns/month",
    features: ["2,400 turns per month", "Everything in Adventurer", "Priority support", "Early access features"],
    color: "#f59e0b",
    highlight: false,
  },
];

export default function Pricing() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState("");

  const handleSelect = async (plan) => {
    if (plan.id === "free") {
      navigate("/");
      return;
    }
    if (!token) {
      navigate("/login");
      return;
    }
    setLoading(plan.id);
    setError("");
    try {
      const res = await axios.post(
        `${BACKEND}/billing/checkout`,
        { plan: plan.id },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      window.location.href = res.data.url;
    } catch (err) {
      setError(err.response?.data?.detail || "Could not start checkout");
      setLoading(null);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      padding: "60px 20px",
      fontFamily: "'Segoe UI', sans-serif",
    }}>
      <button onClick={() => navigate("/")} style={{
        position: "absolute", top: 20, left: 20,
        background: "none", border: "none", color: "#94a3b8",
        cursor: "pointer", fontSize: 14,
      }}>← Back</button>

      <h1 style={{ color: "#e2d9f3", fontSize: 36, fontWeight: 700, margin: "0 0 8px" }}>
        Choose Your Plan
      </h1>
      <p style={{ color: "#94a3b8", fontSize: 16, marginBottom: 48 }}>
        Each turn = one player action + full DM response
      </p>

      {error && (
        <div style={{
          background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.4)",
          borderRadius: 8, padding: "10px 20px", color: "#fca5a5", marginBottom: 24, fontSize: 14,
        }}>
          {error}
        </div>
      )}

      <div style={{ display: "flex", gap: 24, flexWrap: "wrap", justifyContent: "center" }}>
        {PLANS.map((plan) => {
          const isCurrent = user?.plan === plan.id;
          return (
            <div key={plan.id} style={{
              width: 280,
              background: plan.highlight
                ? "rgba(139,92,246,0.12)"
                : "rgba(255,255,255,0.04)",
              border: `1px solid ${plan.highlight ? "rgba(139,92,246,0.5)" : "rgba(255,255,255,0.1)"}`,
              borderRadius: 16,
              padding: 28,
              position: "relative",
              boxShadow: plan.highlight ? "0 0 40px rgba(139,92,246,0.15)" : "none",
            }}>
              {plan.highlight && (
                <div style={{
                  position: "absolute", top: -12, left: "50%", transform: "translateX(-50%)",
                  background: "#8b5cf6", color: "#fff", padding: "4px 16px",
                  borderRadius: 20, fontSize: 12, fontWeight: 600,
                }}>
                  Most Popular
                </div>
              )}

              <div style={{ color: plan.color, fontSize: 13, fontWeight: 600, marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>
                {plan.name}
              </div>

              <div style={{ display: "flex", alignItems: "flex-end", gap: 4, marginBottom: 4 }}>
                <span style={{ color: "#e2d9f3", fontSize: 40, fontWeight: 700 }}>{plan.price}</span>
                <span style={{ color: "#64748b", fontSize: 14, paddingBottom: 8 }}>{plan.period}</span>
              </div>

              <div style={{ color: "#94a3b8", fontSize: 13, marginBottom: 24 }}>{plan.turns}</div>

              <ul style={{ listStyle: "none", padding: 0, margin: "0 0 28px", display: "flex", flexDirection: "column", gap: 10 }}>
                {plan.features.map((f) => (
                  <li key={f} style={{ color: "#cbd5e1", fontSize: 14, display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ color: plan.color }}>✓</span> {f}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleSelect(plan)}
                disabled={isCurrent || loading === plan.id}
                style={{
                  width: "100%",
                  padding: "12px 0",
                  borderRadius: 8,
                  border: isCurrent ? `1px solid ${plan.color}` : "none",
                  background: isCurrent
                    ? "transparent"
                    : plan.highlight
                      ? "#8b5cf6"
                      : "rgba(255,255,255,0.1)",
                  color: isCurrent ? plan.color : "#fff",
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: isCurrent ? "default" : "pointer",
                  opacity: loading && loading !== plan.id ? 0.5 : 1,
                }}
              >
                {isCurrent ? "Current Plan" : loading === plan.id ? "Loading..." : plan.id === "free" ? "Get Started" : "Upgrade"}
              </button>
            </div>
          );
        })}
      </div>

      {user && (
        <button onClick={async () => {
          try {
            const res = await axios.post(`${BACKEND}/billing/portal`, {}, {
              headers: { Authorization: `Bearer ${token}` },
            });
            window.location.href = res.data.url;
          } catch {
            setError("Could not open billing portal");
          }
        }} style={{
          marginTop: 40, background: "none", border: "1px solid rgba(255,255,255,0.15)",
          color: "#94a3b8", padding: "10px 24px", borderRadius: 8, cursor: "pointer", fontSize: 14,
        }}>
          Manage Subscription
        </button>
      )}
    </div>
  );
}
