import React from "react";
import { useNavigate } from "react-router-dom";

export default function NotFound() {
  const navigate = useNavigate();
  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      fontFamily: "'Segoe UI', sans-serif", textAlign: "center", padding: 24,
    }}>
      <div style={{ fontSize: 64, marginBottom: 16 }}>🗺️</div>
      <h1 style={{ color: "#e2d9f3", fontSize: 28, fontWeight: 700, margin: "0 0 8px" }}>
        Lost in the Dungeon
      </h1>
      <p style={{ color: "#94a3b8", fontSize: 16, maxWidth: 360, margin: "0 0 32px" }}>
        This path doesn't exist in our realm. The ancient maps show no route here.
      </p>
      <button onClick={() => navigate("/")} style={{
        background: "rgba(139,92,246,0.7)", border: "none", borderRadius: 8,
        color: "#fff", padding: "12px 28px", fontSize: 15, fontWeight: 600, cursor: "pointer",
      }}>
        Return to Safety
      </button>
    </div>
  );
}
