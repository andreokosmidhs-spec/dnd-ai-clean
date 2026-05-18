/**
 * PressureDashboard.jsx
 * Living Campaign Pressure Engine — visual DM dashboard
 *
 * Shows: regional pressure axes, active hooks, leads, antagonist phase,
 * cleansing events, and the narrative tick trigger.
 */

import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL + "/api/pressure";

// ─── colour helpers ───────────────────────────────────────────────
const LABEL_COLOURS = {
  CALM:     { bg: "#0d2d1a", text: "#34d399", border: "#065f46" },
  LOW:      { bg: "#1a2a0d", text: "#86efac", border: "#166534" },
  MODERATE: { bg: "#2d1f00", text: "#fbbf24", border: "#92400e" },
  HIGH:     { bg: "#2d0d0d", text: "#f87171", border: "#991b1b" },
  CRITICAL: { bg: "#1a0000", text: "#ff4444", border: "#7f1d1d" },
};

const AXIS_COLOURS = {
  crime:               "#f87171",
  war:                 "#dc2626",
  scarcity:            "#fbbf24",
  corruption:          "#a78bfa",
  cult_activity:       "#c084fc",
  magical_instability: "#60a5fa",
  social_unrest:       "#fb923c",
};

const PHASE_LABELS = {
  act1_shadow:       { label: "ACT I — Shadow",       colour: "#64748b" },
  act2_pressure:     { label: "ACT II — Pressure",     colour: "#fbbf24" },
  act3_confrontation:{ label: "ACT III — Confrontation",colour: "#f87171" },
  act4_resolution:   { label: "ACT IV — Resolution",   colour: "#34d399" },
};

const LEAD_STATUS_STYLE = {
  active:      { bg: "#0d2a1a", text: "#34d399", border: "#065f46" },
  ignored:     { bg: "#1e1e1e", text: "#64748b", border: "#374151" },
  resolved:    { bg: "#0d1f2d", text: "#60a5fa", border: "#1e3a5f" },
  abandoned:   { bg: "#1a1000", text: "#92400e", border: "#92400e" },
  sealed:      { bg: "#1a0d2d", text: "#7c3aed", border: "#4c1d95" },
  transformed: { bg: "#1a2d0d", text: "#84cc16", border: "#365314" },
};


// ─── sub-components ───────────────────────────────────────────────

function PressureBar({ axis, value }) {
  const colour = AXIS_COLOURS[axis] || "#94a3b8";
  const pct = Math.round(value * 100);
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
        <span style={{ fontSize: 11, color: "#94a3b8", textTransform: "capitalize", letterSpacing: 1 }}>
          {axis.replace(/_/g, " ")}
        </span>
        <span style={{ fontSize: 11, color: colour, fontFamily: "monospace" }}>{pct}%</span>
      </div>
      <div style={{ height: 6, background: "#1e293b", borderRadius: 3, overflow: "hidden" }}>
        <div style={{
          height: "100%",
          width: `${pct}%`,
          background: `linear-gradient(90deg, ${colour}99, ${colour})`,
          borderRadius: 3,
          transition: "width 0.6s ease",
          boxShadow: pct > 60 ? `0 0 8px ${colour}88` : "none",
        }} />
      </div>
    </div>
  );
}

function RegionCard({ region }) {
  const lc = LABEL_COLOURS[region.pressure_label] || LABEL_COLOURS.LOW;
  return (
    <div style={{
      background: "#111827",
      border: `1px solid ${lc.border}`,
      borderRadius: 10,
      padding: "14px 16px",
      marginBottom: 12,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <span style={{ fontWeight: 700, color: "#f1f5f9", fontSize: 14, letterSpacing: 0.5 }}>{region.name}</span>
        <span style={{
          fontSize: 10, fontWeight: 800, letterSpacing: 1.5,
          padding: "3px 8px", borderRadius: 4,
          background: lc.bg, color: lc.text, border: `1px solid ${lc.border}`,
        }}>
          {region.pressure_label}
        </span>
      </div>
      {Object.entries(region.axes || {}).map(([axis, val]) => (
        <PressureBar key={axis} axis={axis} value={val} />
      ))}
      <div style={{ marginTop: 10, paddingTop: 10, borderTop: "1px solid #1e293b", display: "flex", gap: 12, flexWrap: "wrap" }}>
        {Object.entries(region.derived || {}).map(([k, v]) => (
          <div key={k} style={{ fontSize: 10, color: "#64748b" }}>
            <span style={{ color: "#94a3b8" }}>{k.replace(/_/g, " ")}</span>
            {" "}
            <span style={{ color: "#e2e8f0", fontFamily: "monospace" }}>{Math.round(v * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function HookCard({ hook, onCreateLead }) {
  return (
    <div style={{
      background: "#0f1827",
      border: "1px solid #1e3a5f",
      borderRadius: 8,
      padding: "12px 14px",
      marginBottom: 8,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 11, color: "#60a5fa", fontWeight: 700, letterSpacing: 1, marginBottom: 4 }}>
            {hook.hook_type?.replace(/_/g, " ").toUpperCase()}
          </div>
          <div style={{ fontSize: 13, color: "#e2e8f0", lineHeight: 1.5 }}>{hook.description}</div>
        </div>
        {hook.status === "noticed" && (
          <button
            onClick={() => onCreateLead(hook)}
            style={{
              fontSize: 10, padding: "5px 10px", borderRadius: 5, border: "1px solid #065f46",
              background: "#0d2a1a", color: "#34d399", cursor: "pointer", whiteSpace: "nowrap",
              fontWeight: 700, letterSpacing: 0.5,
            }}
          >
            + LEAD
          </button>
        )}
      </div>
      <div style={{ marginTop: 6, fontSize: 10, color: "#475569" }}>
        Status: <span style={{ color: "#94a3b8" }}>{hook.status}</span>
        {" · "}Importance: <span style={{ color: "#fbbf24", fontFamily: "monospace" }}>{Math.round((hook.importance_score || 0) * 100)}%</span>
      </div>
    </div>
  );
}

function LeadCard({ lead }) {
  const style = LEAD_STATUS_STYLE[lead.status] || LEAD_STATUS_STYLE.active;
  return (
    <div style={{
      background: style.bg,
      border: `1px solid ${style.border}`,
      borderRadius: 8,
      padding: "11px 13px",
      marginBottom: 8,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{lead.title}</span>
        <span style={{
          fontSize: 9, fontWeight: 800, letterSpacing: 1, padding: "2px 6px",
          borderRadius: 3, background: style.bg, color: style.text, border: `1px solid ${style.border}`,
        }}>{lead.status.toUpperCase()}</span>
      </div>
      <div style={{ fontSize: 12, color: "#94a3b8", lineHeight: 1.5 }}>{lead.summary}</div>
      {lead.player_notes && (
        <div style={{ marginTop: 6, fontSize: 11, color: "#64748b", fontStyle: "italic" }}>
          "{lead.player_notes}"
        </div>
      )}
      <div style={{ marginTop: 5, fontSize: 10, color: "#475569" }}>
        Importance: <span style={{ color: "#fbbf24", fontFamily: "monospace" }}>
          {Math.round((lead.importance_score || 0) * 100)}%
        </span>
      </div>
    </div>
  );
}

function AntagonistCard({ ant }) {
  const phase = PHASE_LABELS[ant.act_phase] || PHASE_LABELS.act1_shadow;
  return (
    <div style={{
      background: "#0f0a1a",
      border: `1px solid ${phase.colour}55`,
      borderRadius: 8,
      padding: "12px 14px",
      marginBottom: 8,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: "#e2e8f0" }}>
          {ant.revealed_signature ? ant.name || "???" : "???"}
        </span>
        <span style={{ fontSize: 10, color: phase.colour, fontWeight: 700, letterSpacing: 1 }}>
          {phase.label}
        </span>
      </div>
      <div style={{ marginBottom: 8 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
          <span style={{ fontSize: 11, color: "#64748b" }}>ESCALATION</span>
          <span style={{ fontSize: 11, color: "#f87171", fontFamily: "monospace" }}>
            {Math.round(ant.escalation_level * 100)}%
          </span>
        </div>
        <div style={{ height: 5, background: "#1e293b", borderRadius: 3, overflow: "hidden" }}>
          <div style={{
            height: "100%",
            width: `${ant.escalation_level * 100}%`,
            background: "linear-gradient(90deg, #7f1d1d, #dc2626)",
            borderRadius: 3,
            transition: "width 0.6s ease",
          }} />
        </div>
      </div>
      {ant.reveal_text && (
        <div style={{
          marginTop: 8, padding: "8px 10px", background: "#1a0d0d",
          borderRadius: 5, border: "1px solid #7f1d1d",
          fontSize: 12, color: "#fca5a5", lineHeight: 1.6, fontStyle: "italic",
        }}>
          {ant.reveal_text}
        </div>
      )}
    </div>
  );
}

function CleansingCard({ event }) {
  return (
    <div style={{
      background: "#1a0d00",
      border: "1px solid #92400e",
      borderRadius: 8,
      padding: "12px 14px",
      marginBottom: 8,
    }}>
      <div style={{ fontSize: 12, color: "#fbbf24", fontWeight: 700, marginBottom: 4 }}>
        ⚠️ {event.title}
      </div>
      <div style={{ fontSize: 12, color: "#d97706", lineHeight: 1.5 }}>{event.description}</div>
      {event.warning_signs?.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontSize: 10, color: "#92400e", letterSpacing: 1, marginBottom: 3 }}>WARNING SIGNS</div>
          {event.warning_signs.map((w, i) => (
            <div key={i} style={{ fontSize: 11, color: "#d97706" }}>· {w}</div>
          ))}
        </div>
      )}
      <div style={{ marginTop: 6, fontSize: 10, color: "#78350f" }}>
        Archived leads: {event.archived_lead_ids?.length || 0}
        {" · "}Transformed: {event.transformed_lead_ids?.length || 0}
        {" · "}Intervention: {event.player_intervention_possible ? "✓" : "✗"}
      </div>
    </div>
  );
}


// ─── main dashboard ───────────────────────────────────────────────

export default function PressureDashboard({ campaignId }) {
  const [summary, setSummary] = useState(null);
  const [hooks, setHooks] = useState([]);
  const [leads, setLeads] = useState([]);
  const [antagonists, setAntagonists] = useState([]);
  const [cleansing, setCleansing] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ticking, setTicking] = useState(false);
  const [activeTab, setActiveTab] = useState("regions");
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (!campaignId) return;
    try {
      setError(null);
      const [sumRes, hookRes, leadRes, antRes, cleanRes] = await Promise.all([
        axios.get(`${API}/${campaignId}/summary`),
        axios.get(`${API}/${campaignId}/hooks`),
        axios.get(`${API}/${campaignId}/leads`),
        axios.get(`${API}/${campaignId}/antagonists`),
        axios.get(`${API}/${campaignId}/cleansing`),
      ]);
      setSummary(sumRes.data);
      setHooks(hookRes.data.hooks || []);
      setLeads(leadRes.data.leads || []);
      setAntagonists(antRes.data.antagonists || []);
      setCleansing(cleanRes.data.cleansing_events || []);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to load pressure state.");
    } finally {
      setLoading(false);
    }
  }, [campaignId]);

  useEffect(() => { load(); }, [load]);

  const tick = async (trigger) => {
    setTicking(true);
    try {
      await axios.post(`${API}/tick`, { campaign_id: campaignId, trigger });
      await load();
    } catch (e) {
      setError("Tick failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setTicking(false);
    }
  };

  const noticeHook = async (hookId) => {
    await axios.post(`${API}/${campaignId}/hooks/notice`, { hook_id: hookId, character_id: "player" });
    await load();
  };

  const createLead = async (hook) => {
    await axios.post(`${API}/${campaignId}/leads`, {
      campaign_id: campaignId,
      hook_id: hook.id,
      character_id: "player",
    });
    await load();
  };

  if (!campaignId) return (
    <div style={{ padding: 24, color: "#64748b", fontFamily: "monospace", textAlign: "center" }}>
      No campaign selected.
    </div>
  );

  if (loading) return (
    <div style={{ padding: 24, color: "#60a5fa", fontFamily: "monospace", textAlign: "center" }}>
      Loading pressure state…
    </div>
  );

  const TABS = [
    { id: "regions",    label: "REGIONS",    count: summary?.regions?.length },
    { id: "hooks",      label: "HOOKS",      count: summary?.visible_hooks },
    { id: "leads",      label: "LEADS",      count: summary?.active_leads },
    { id: "antagonist", label: "ANTAGONIST", count: antagonists.length },
    { id: "cleansing",  label: "CLEANSING",  count: summary?.active_cleansing },
  ];

  return (
    <div style={{
      fontFamily: "'Segoe UI', system-ui, sans-serif",
      background: "#090e18",
      minHeight: "100vh",
      color: "#e2e8f0",
    }}>
      {/* Header */}
      <div style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1a0d2e 100%)",
        borderBottom: "1px solid #1e293b",
        padding: "16px 20px",
      }}>
        <div style={{ fontSize: 11, color: "#64748b", letterSpacing: 2, marginBottom: 4 }}>
          LIVING CAMPAIGN
        </div>
        <div style={{ fontSize: 20, fontWeight: 800, color: "#f1f5f9", letterSpacing: 0.5 }}>
          Pressure Engine
        </div>
        {summary && (
          <div style={{ marginTop: 6, fontSize: 11, color: "#475569" }}>
            {summary.active_leads} active leads · {summary.visible_hooks} visible hooks · {summary.active_cleansing} cleansing events
          </div>
        )}
      </div>

      {error && (
        <div style={{
          margin: "12px 16px", padding: "10px 14px", borderRadius: 6,
          background: "#1a0d0d", border: "1px solid #7f1d1d", color: "#fca5a5", fontSize: 12,
        }}>
          {error}
        </div>
      )}

      {/* Tick Controls */}
      <div style={{
        padding: "12px 16px",
        borderBottom: "1px solid #1e293b",
        display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center",
      }}>
        <span style={{ fontSize: 10, color: "#475569", letterSpacing: 1, marginRight: 4 }}>ADVANCE WORLD:</span>
        {["long_rest", "travel", "next_day", "major_quest_completion"].map(t => (
          <button key={t} onClick={() => tick(t)} disabled={ticking} style={{
            fontSize: 10, padding: "5px 10px", borderRadius: 5,
            border: "1px solid #334155",
            background: ticking ? "#0f172a" : "#1e293b",
            color: ticking ? "#475569" : "#94a3b8",
            cursor: ticking ? "not-allowed" : "pointer",
            fontWeight: 600, letterSpacing: 0.5, textTransform: "uppercase",
            transition: "all 0.15s",
          }}>
            {t.replace(/_/g, " ")}
          </button>
        ))}
        {ticking && <span style={{ fontSize: 10, color: "#60a5fa" }}>Ticking…</span>}
      </div>

      {/* Tabs */}
      <div style={{
        display: "flex", borderBottom: "1px solid #1e293b",
        overflowX: "auto",
      }}>
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
            padding: "10px 16px", border: "none", cursor: "pointer",
            background: "transparent",
            borderBottom: activeTab === tab.id ? "2px solid #6366f1" : "2px solid transparent",
            color: activeTab === tab.id ? "#a5b4fc" : "#64748b",
            fontSize: 11, fontWeight: 700, letterSpacing: 1,
            whiteSpace: "nowrap",
            transition: "all 0.15s",
          }}>
            {tab.label}
            {tab.count != null && tab.count > 0 && (
              <span style={{
                marginLeft: 6, background: activeTab === tab.id ? "#4f46e5" : "#1e293b",
                color: activeTab === tab.id ? "#e0e7ff" : "#94a3b8",
                fontSize: 9, padding: "1px 5px", borderRadius: 10, fontWeight: 800,
              }}>{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={{ padding: "14px 16px" }}>

        {activeTab === "regions" && (
          <>
            {summary?.regions?.length === 0 && (
              <div style={{ color: "#64748b", fontSize: 13 }}>No regions found. Initialize the pressure engine first.</div>
            )}
            {(summary?.regions || []).map(r => <RegionCard key={r.id} region={r} />)}
          </>
        )}

        {activeTab === "hooks" && (
          <>
            {hooks.length === 0 && (
              <div style={{ color: "#64748b", fontSize: 13 }}>No hooks yet. Advance the world to generate pressure.</div>
            )}
            {hooks.filter(h => h.status === "visible").map(h => (
              <div key={h.id} style={{ position: "relative" }}>
                <HookCard hook={h} onCreateLead={createLead} />
                <button
                  onClick={() => noticeHook(h.id)}
                  style={{
                    position: "absolute", bottom: 16, right: 12,
                    fontSize: 9, padding: "3px 8px", border: "1px solid #1e3a5f",
                    background: "#0d1f2d", color: "#60a5fa", cursor: "pointer",
                    borderRadius: 4, fontWeight: 700, letterSpacing: 0.5,
                  }}
                >
                  NOTICE
                </button>
              </div>
            ))}
            {hooks.filter(h => h.status !== "visible").length > 0 && (
              <>
                <div style={{ fontSize: 10, color: "#475569", letterSpacing: 1, margin: "12px 0 6px" }}>NOTICED / ACTED ON</div>
                {hooks.filter(h => h.status !== "visible").map(h => (
                  <HookCard key={h.id} hook={h} onCreateLead={createLead} />
                ))}
              </>
            )}
          </>
        )}

        {activeTab === "leads" && (
          <>
            {leads.length === 0 && (
              <div style={{ color: "#64748b", fontSize: 13 }}>No leads yet. Notice a hook to start tracking it.</div>
            )}
            {leads.filter(l => l.status === "active").map(l => <LeadCard key={l.id} lead={l} />)}
            {leads.filter(l => l.status !== "active").length > 0 && (
              <>
                <div style={{ fontSize: 10, color: "#475569", letterSpacing: 1, margin: "12px 0 6px" }}>OTHER LEADS</div>
                {leads.filter(l => l.status !== "active").map(l => <LeadCard key={l.id} lead={l} />)}
              </>
            )}
          </>
        )}

        {activeTab === "antagonist" && (
          <>
            {antagonists.length === 0 && (
              <div style={{ color: "#64748b", fontSize: 13 }}>No antagonist seeded. Add one during campaign initialization.</div>
            )}
            {antagonists.map((a, i) => <AntagonistCard key={i} ant={a} />)}
            <div style={{
              marginTop: 16, padding: "12px 14px",
              background: "#0d0d0d", border: "1px solid #1e293b", borderRadius: 8,
            }}>
              <div style={{ fontSize: 10, color: "#475569", letterSpacing: 1, marginBottom: 8 }}>ACT STRUCTURE</div>
              {Object.entries(PHASE_LABELS).map(([key, val]) => (
                <div key={key} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 5 }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: val.colour }} />
                  <span style={{ fontSize: 12, color: val.colour }}>{val.label}</span>
                </div>
              ))}
            </div>
          </>
        )}

        {activeTab === "cleansing" && (
          <>
            {cleansing.length === 0 && (
              <div style={{ color: "#64748b", fontSize: 13 }}>No active cleansing events. Pressure must rise further.</div>
            )}
            {cleansing.map(e => <CleansingCard key={e.id} event={e} />)}
            <div style={{
              marginTop: 16, padding: "12px 14px",
              background: "#0d0d0d", border: "1px solid #1e293b", borderRadius: 8,
            }}>
              <div style={{ fontSize: 10, color: "#475569", letterSpacing: 1, marginBottom: 6 }}>CLEANSING RULES</div>
              <div style={{ fontSize: 11, color: "#64748b", lineHeight: 1.8 }}>
                · Low-importance stale leads are sealed silently.<br/>
                · High-importance leads always become story events.<br/>
                · Cleansing generates new hooks from the chaos.<br/>
                · Players can intervene if warned in time.
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
