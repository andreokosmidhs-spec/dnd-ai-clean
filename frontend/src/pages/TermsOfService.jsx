import React from "react";
import { useNavigate } from "react-router-dom";

const SECTION = ({ title, children }) => (
  <div style={{ marginBottom: 32 }}>
    <h2 style={{ color: "#e2d9f3", fontSize: 18, fontWeight: 600, marginBottom: 10 }}>{title}</h2>
    <div style={{ color: "#94a3b8", fontSize: 14, lineHeight: 1.8 }}>{children}</div>
  </div>
);

export default function TermsOfService() {
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
          Terms of Service
        </h1>
        <p style={{ color: "#64748b", fontSize: 14, marginBottom: 48 }}>
          Last updated: {new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
        </p>

        <SECTION title="1. Acceptance of Terms">
          By accessing or using RPG Forge ("the Service"), you agree to be bound by these Terms of
          Service. If you do not agree to these terms, please do not use the Service.
        </SECTION>

        <SECTION title="2. Description of Service">
          RPG Forge is an AI-powered text role-playing game that uses large language models to
          generate narrative content. The Service requires an internet connection and an account to
          access full features.
        </SECTION>

        <SECTION title="3. User Accounts">
          <p>You are responsible for maintaining the confidentiality of your account credentials.
          You agree to provide accurate information when creating an account and to notify us
          immediately of any unauthorized use.</p>
          <p style={{ marginTop: 10 }}>You must be at least 13 years of age to use the Service.</p>
        </SECTION>

        <SECTION title="4. Subscriptions and Payments">
          <p>Paid plans are billed monthly. You may cancel at any time through the billing portal.
          Cancellations take effect at the end of the current billing period — no partial refunds
          are issued for unused portions of a subscription period.</p>
          <p style={{ marginTop: 10 }}>Turn allocations reset on the first day of each calendar month and do not roll over.</p>
        </SECTION>

        <SECTION title="5. AI-Generated Content">
          The Service uses AI to generate narrative content. This content is for entertainment
          purposes only. We do not guarantee the accuracy, appropriateness, or completeness of
          any AI-generated output. You acknowledge that AI-generated content may occasionally be
          unexpected or inconsistent.
        </SECTION>

        <SECTION title="6. Prohibited Conduct">
          You agree not to: (a) attempt to circumvent usage limits or access controls; (b) use the
          Service to generate harmful, abusive, or illegal content; (c) reverse-engineer or scrape
          the Service; (d) share your account credentials with others.
        </SECTION>

        <SECTION title="7. Intellectual Property">
          The RPG Forge platform, including its code, design, and branding, is our property.
          AI-generated story content produced during your sessions is yours to enjoy but may not
          be resold or distributed commercially.
        </SECTION>

        <SECTION title="8. Disclaimer of Warranties">
          The Service is provided "as is" without warranties of any kind. We do not guarantee
          uninterrupted availability or that the AI will always produce the narrative outcome you
          expect.
        </SECTION>

        <SECTION title="9. Limitation of Liability">
          To the maximum extent permitted by law, RPG Forge shall not be liable for any indirect,
          incidental, or consequential damages arising from your use of the Service.
        </SECTION>

        <SECTION title="10. Changes to Terms">
          We may update these Terms from time to time. Continued use of the Service after changes
          constitutes acceptance of the new Terms.
        </SECTION>

        <SECTION title="11. Contact">
          For questions about these Terms, contact us at support@rpgforge.app.
        </SECTION>
      </div>
    </div>
  );
}
