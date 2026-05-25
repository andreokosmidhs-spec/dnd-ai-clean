import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function UsageBanner() {
  const { user, usage } = useAuth();
  const navigate = useNavigate();

  if (!user || !usage) return null;

  const { turns_used, turns_limit, turns_remaining, plan } = usage;
  const pct = turns_limit > 0 ? (turns_used / turns_limit) * 100 : 0;
  const critical = pct >= 90;
  const warning = pct >= 70;

  const barColor = critical ? "#ef4444" : warning ? "#f59e0b" : "#8b5cf6";

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 12,
      padding: "6px 14px",
      background: critical
        ? "rgba(239,68,68,0.1)"
        : "rgba(0,0,0,0.3)",
      border: `1px solid ${critical ? "rgba(239,68,68,0.3)" : "rgba(255,255,255,0.08)"}`,
      borderRadius: 8,
      fontSize: 12,
    }}>
      <div style={{ color: "#94a3b8", whiteSpace: "nowrap" }}>
        {turns_remaining} turns left
      </div>

      <div style={{
        flex: 1,
        height: 4,
        background: "rgba(255,255,255,0.1)",
        borderRadius: 2,
        minWidth: 60,
        maxWidth: 100,
      }}>
        <div style={{
          height: "100%",
          width: `${Math.min(100, pct)}%`,
          background: barColor,
          borderRadius: 2,
          transition: "width 0.3s",
        }} />
      </div>

      {(critical || plan === "free") && (
        <button
          onClick={() => navigate("/pricing")}
          style={{
            background: critical ? "#ef4444" : "rgba(139,92,246,0.7)",
            border: "none",
            borderRadius: 4,
            color: "#fff",
            padding: "3px 10px",
            fontSize: 11,
            fontWeight: 600,
            cursor: "pointer",
            whiteSpace: "nowrap",
          }}
        >
          {critical ? "Upgrade now" : "Upgrade"}
        </button>
      )}
    </div>
  );
}
