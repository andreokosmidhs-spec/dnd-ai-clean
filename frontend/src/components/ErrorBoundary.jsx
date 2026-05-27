import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{
          minHeight: "100vh",
          background: "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
          display: "flex", flexDirection: "column", alignItems: "center",
          justifyContent: "center", fontFamily: "'Segoe UI', sans-serif",
          textAlign: "center", padding: 24,
        }}>
          <div style={{ fontSize: 56, marginBottom: 16 }}>⚠️</div>
          <h1 style={{ color: "#e2d9f3", fontSize: 24, fontWeight: 700, margin: "0 0 8px" }}>
            Something went wrong
          </h1>
          <p style={{ color: "#94a3b8", fontSize: 14, maxWidth: 400, margin: "0 0 8px" }}>
            {this.state.error?.message || "An unexpected error occurred."}
          </p>
          <p style={{ color: "#475569", fontSize: 13, margin: "0 0 28px" }}>
            Your progress is auto-saved. Refreshing will restore your session.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              background: "rgba(139,92,246,0.7)", border: "none", borderRadius: 8,
              color: "#fff", padding: "11px 28px", fontSize: 14, fontWeight: 600,
              cursor: "pointer", marginRight: 12,
            }}
          >
            Reload Page
          </button>
          <button
            onClick={() => { this.setState({ error: null }); window.location.hash = "/"; }}
            style={{
              background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.15)",
              borderRadius: 8, color: "#94a3b8", padding: "11px 28px", fontSize: 14,
              cursor: "pointer",
            }}
          >
            Go to Main Menu
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
