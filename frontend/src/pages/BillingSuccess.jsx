import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function BillingSuccess() {
  const navigate = useNavigate();
  const { refreshUsage } = useAuth();

  useEffect(() => {
    refreshUsage();
    const t = setTimeout(() => navigate("/menu"), 4000);
    return () => clearTimeout(t);
  }, [navigate, refreshUsage]);

  const plan = new URLSearchParams(window.location.hash.split("?")[1] || "").get("plan") || "plan";

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      fontFamily: "'Segoe UI', sans-serif", textAlign: "center",
    }}>
      <div style={{ fontSize: 64, marginBottom: 16 }}>🎉</div>
      <h1 style={{ color: "#e2d9f3", fontSize: 28, fontWeight: 700, margin: "0 0 8px" }}>
        Welcome to {plan.charAt(0).toUpperCase() + plan.slice(1)}!
      </h1>
      <p style={{ color: "#94a3b8", fontSize: 16 }}>Redirecting to your adventure...</p>
    </div>
  );
}
