import React, { useState, useCallback } from 'react';
import { Scroll, X, Loader2, BookOpen } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function SessionRecapModal({ campaignId, characterName, onClose }) {
  const [recap, setRecap]     = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState(null);
  const [view, setView]       = useState('current'); // 'current' | 'history'

  const generateRecap = useCallback(async () => {
    if (!campaignId) return;
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/session-recap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character_name: characterName || 'Adventurer' }),
      });
      const data = await res.json();
      setRecap(data.recap || 'No events recorded yet.');
    } catch (e) {
      setRecap('Could not generate recap — try again after your next adventure.');
    } finally {
      setLoading(false);
    }
  }, [campaignId, characterName]);

  const loadHistory = useCallback(async () => {
    if (history) { setView('history'); return; }
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/session-recaps`);
      const data = await res.json();
      setHistory(data.recaps || []);
      setView('history');
    } catch {
      setHistory([]);
      setView('history');
    } finally {
      setLoading(false);
    }
  }, [campaignId, history]);

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9998,
    }}>
      <div style={{
        background: 'linear-gradient(160deg,#0f0c1a 0%,#1a1325 100%)',
        border: '1.5px solid rgba(180,130,60,0.35)',
        borderRadius: 12, width: 520, maxWidth: '95vw', maxHeight: '85vh',
        display: 'flex', flexDirection: 'column',
        boxShadow: '0 8px 40px rgba(0,0,0,0.8)',
      }}>
        {/* Header */}
        <div style={{
          padding: '14px 18px', borderBottom: '1px solid rgba(255,255,255,0.07)',
          display: 'flex', alignItems: 'center', gap: 10,
        }}>
          <Scroll size={18} color="#c89b3c" />
          <span style={{ color: '#e8dfc8', fontWeight: 700, fontSize: 16, flex: 1 }}>
            Adventure Journal
          </span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => setView('current')}
              style={{
                fontSize: 12, padding: '3px 10px', borderRadius: 5, cursor: 'pointer',
                background: view === 'current' ? 'rgba(200,155,60,0.2)' : 'transparent',
                border: `1px solid ${view === 'current' ? '#c89b3c' : 'transparent'}`,
                color: view === 'current' ? '#c89b3c' : '#6b7280',
              }}
            >This Session</button>
            <button
              onClick={loadHistory}
              style={{
                fontSize: 12, padding: '3px 10px', borderRadius: 5, cursor: 'pointer',
                background: view === 'history' ? 'rgba(200,155,60,0.2)' : 'transparent',
                border: `1px solid ${view === 'history' ? '#c89b3c' : 'transparent'}`,
                color: view === 'history' ? '#c89b3c' : '#6b7280',
              }}
            >Past Sessions</button>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280' }}>
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
          {view === 'current' ? (
            <>
              {!recap && !loading && (
                <div style={{ textAlign: 'center', padding: '32px 0' }}>
                  <BookOpen size={36} color="#3a2a50" style={{ margin: '0 auto 14px' }} />
                  <p style={{ color: '#6b7280', fontSize: 14, marginBottom: 18 }}>
                    Chronicle this session's events into your adventure journal.
                  </p>
                  <button
                    onClick={generateRecap}
                    style={{
                      background: 'linear-gradient(135deg,#2a1a40,#3a2060)',
                      border: '1px solid #5a3080', borderRadius: 8,
                      color: '#c090ff', padding: '10px 24px', cursor: 'pointer',
                      fontSize: 14, fontWeight: 600,
                    }}
                  >
                    ✦ Write Journal Entry
                  </button>
                </div>
              )}
              {loading && (
                <div style={{ textAlign: 'center', padding: '32px 0', color: '#6b7280' }}>
                  <Loader2 size={24} style={{ margin: '0 auto 12px', animation: 'spin 1s linear infinite' }} />
                  <p style={{ fontSize: 13 }}>The chronicler writes…</p>
                </div>
              )}
              {recap && !loading && (
                <div>
                  <p style={{
                    color: '#d4c9a8', fontSize: 14, lineHeight: 1.8,
                    fontFamily: 'Georgia, serif', fontStyle: 'italic',
                    borderLeft: '3px solid rgba(200,155,60,0.4)',
                    paddingLeft: 16,
                  }}>
                    {recap}
                  </p>
                  <button
                    onClick={generateRecap}
                    style={{
                      marginTop: 16, background: 'transparent',
                      border: '1px solid #3a3050', borderRadius: 6,
                      color: '#6b7280', padding: '6px 14px', cursor: 'pointer', fontSize: 12,
                    }}
                  >
                    Rewrite
                  </button>
                </div>
              )}
            </>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {loading && <p style={{ color: '#6b7280', textAlign: 'center', fontSize: 13 }}>Loading…</p>}
              {history && history.length === 0 && (
                <p style={{ color: '#6b7280', textAlign: 'center', fontSize: 13 }}>No past sessions recorded yet.</p>
              )}
              {history && history.slice().reverse().map((entry, i) => (
                <div key={i} style={{
                  borderLeft: '2px solid rgba(200,155,60,0.3)',
                  paddingLeft: 14,
                }}>
                  <div style={{ color: '#6b7280', fontSize: 11, marginBottom: 6 }}>
                    {new Date(entry.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                  </div>
                  <p style={{ color: '#c4b5a0', fontSize: 13, lineHeight: 1.7, fontFamily: 'Georgia, serif', fontStyle: 'italic' }}>
                    {entry.recap}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
