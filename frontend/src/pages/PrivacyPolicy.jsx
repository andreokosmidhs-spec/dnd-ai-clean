import React from "react";
import { useNavigate } from "react-router-dom";

const SECTION = ({ title, children }) => (
  <div style={{ marginBottom: 32 }}>
    <h2 style={{ color: "#e2d9f3", fontSize: 18, fontWeight: 600, marginBottom: 10 }}>{title}</h2>
    <div style={{ color: "#94a3b8", fontSize: 14, lineHeight: 1.8 }}>{children}</div>
  </div>
);

export default function PrivacyPolicy() {
  const navigate = useNavigate();

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
      fontFamily: "'Segoe UI', sans-serif",
      padding: "60px 24px",
    }}>
      <div style={{ maxWidth: 720, margin: "0 auto" }}>
        <button onClick={() => navigate(-1)} style={{
          background: "none", border: "none", color: "#64748b",
          fontSize: 14, cursor: "pointer", marginBottom: 32,
        }}>
          ← Back
        </button>

        <h1 style={{ color: "#e2d9f3", fontSize: 32, fontWeight: 700, marginBottom: 8 }}>
          Privacy Policy
        </h1>
        <p style={{ color: "#64748b", fontSize: 14, marginBottom: 48 }}>
          Last updated: {new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
        </p>

        <SECTION title="1. Information We Collect">
          <p><strong style={{ color: "#e2d9f3" }}>Account data:</strong> Email address and hashed
          password when you register.</p>
          <p style={{ marginTop: 10 }}><strong style={{ color: "#e2d9f3" }}>Game data:</strong> Your
          character sheets, campaign progress, and session history stored to enable save/load and
          the AI DM's memory of your story.</p>
          <p style={{ marginTop: 10 }}><strong style={{ color: "#e2d9f3" }}>Usage data:</strong> Turn
          counts and billing plan information to enforce subscription limits.</p>
        </SECTION>

        <SECTION title="2. How We Use Your Information">
          <p>We use collected data to:</p>
          <ul style={{ paddingLeft: 20, marginTop: 8 }}>
            <li>Provide and operate the game service</li>
            <li>Give the AI DM context about your campaign history</li>
            <li>Process subscription payments via Stripe</li>
            <li>Enforce fair-use turn limits per plan</li>
            <li>Respond to support requests</li>
          </ul>
          <p style={{ marginTop: 10 }}>We do not sell your personal data to third parties.</p>
        </SECTION>

        <SECTION title="3. AI Processing">
          Your in-game actions and campaign context are sent to Anthropic's Claude API to generate
          DM narration. This is necessary to operate the Service. Please review Anthropic's privacy
          policy at anthropic.com for details on how they handle API input data.
        </SECTION>

        <SECTION title="4. Data Storage">
          Account and campaign data is stored in a hosted MongoDB database. Payment processing
          is handled by Stripe — we never store full credit card numbers.
        </SECTION>

        <SECTION title="5. Cookies and Local Storage">
          We use browser localStorage to keep you signed in between sessions and to save your
          preferences (narrator tone, TTS settings). We do not use third-party tracking cookies.
        </SECTION>

        <SECTION title="6. Data Retention">
          Your account and campaign data is retained for as long as your account is active. You
          may request deletion of your account and all associated data by emailing
          support@rpgforge.app.
        </SECTION>

        <SECTION title="7. Children's Privacy">
          The Service is not directed to children under 13. We do not knowingly collect personal
          information from children under 13.
        </SECTION>

        <SECTION title="8. Your Rights">
          Depending on your location, you may have rights to access, correct, or delete your
          personal data. Contact support@rpgforge.app to exercise these rights.
        </SECTION>

        <SECTION title="9. Changes to This Policy">
          We may update this Privacy Policy periodically. We will notify registered users of
          material changes by email.
        </SECTION>

        <SECTION title="10. Contact">
          For privacy questions or data requests, contact us at support@rpgforge.app.
        </SECTION>
      </div>
    </div>
  );
}
