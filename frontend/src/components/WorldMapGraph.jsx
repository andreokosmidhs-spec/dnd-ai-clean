import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Compass, MapPin, Trees, Sun, Mountain, Snowflake, Waves, Droplet, Flame, Building, Sparkle, Moon, Wind, Loader2, Check, X, Scroll, Users } from 'lucide-react';
import { toast } from 'sonner';
import { eventTypeMeta } from '../utils/eventTypes';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const BIOME_STYLES = {
  forest:    { fill: '#047857', stroke: '#10b981', icon: Trees,     label: 'Forest' },
  plains:    { fill: '#a16207', stroke: '#eab308', icon: Wind,      label: 'Plains' },
  desert:    { fill: '#c2410c', stroke: '#f59e0b', icon: Sun,       label: 'Desert' },
  mountain:  { fill: '#44403c', stroke: '#a8a29e', icon: Mountain,  label: 'Mountain' },
  swamp:     { fill: '#115e59', stroke: '#14b8a6', icon: Droplet,   label: 'Swamp' },
  coast:     { fill: '#155e75', stroke: '#0ea5e9', icon: Waves,     label: 'Coast' },
  tundra:    { fill: '#1d4ed8', stroke: '#7dd3fc', icon: Snowflake, label: 'Tundra' },
  underdark: { fill: '#6b21a8', stroke: '#c084fc', icon: Mountain,  label: 'Underdark' },
  volcanic:  { fill: '#9a3412', stroke: '#f97316', icon: Flame,     label: 'Volcanic' },
  urban:     { fill: '#334155', stroke: '#94a3b8', icon: Building,  label: 'Urban' },
  fey:       { fill: '#9d174d', stroke: '#f472b6', icon: Sparkle,   label: 'Feywild' },
  shadow:    { fill: '#27272a', stroke: '#a1a1aa', icon: Moon,      label: 'Shadowfell' },
};

const biomeStyle = (key) => BIOME_STYLES[key] || BIOME_STYLES.plains;

const diffChip = {
  easy:   'bg-emerald-500/20 text-emerald-300 border-emerald-400/40',
  medium: 'bg-amber-500/20 text-amber-300 border-amber-400/40',
  hard:   'bg-red-500/20 text-red-300 border-red-400/40',
};

/**
 * Node-graph world map.
 * Renders regions as biome-colored SVG nodes laid out on normalized 0..1 coords.
 * Clicking a region opens its event deck (quest hooks). Accepting an event
 * converts it into an active quest card via the backend.
 */
const WorldMapGraph = ({ campaignId, onQuestAccepted }) => {
  const [graph, setGraph] = useState({ regions: [], edges: [], current_region_id: null });
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [busyRegion, setBusyRegion] = useState(null);
  const [busyEvent, setBusyEvent] = useState(null);

  const fetchGraph = useCallback(async () => {
    if (!campaignId) return;
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/campaigns/${campaignId}/world/graph`);
      if (!res.ok) throw new Error('Failed to load map');
      const data = await res.json();
      setGraph(data.graph || { regions: [], edges: [], current_region_id: null });
      // Pre-select the current region on first load only (if nothing is selected yet)
      setSelectedId((prev) => prev || data.graph?.current_region_id || null);
    } catch (e) {
      toast.error('Could not load the campaign map.');
    } finally {
      setLoading(false);
    }
  }, [campaignId]);

  useEffect(() => { fetchGraph(); /* initial load */ }, [fetchGraph]);

  const selectedRegion = useMemo(
    () => graph.regions.find((r) => r.id === selectedId) || null,
    [graph.regions, selectedId]
  );

  const handleVisit = async (regionId) => {
    if (!campaignId || !regionId) return;
    setBusyRegion(regionId);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/world/regions/${regionId}/visit`,
        { method: 'POST' }
      );
      if (!res.ok) throw new Error();
      const data = await res.json();
      setGraph((g) => ({
        ...g,
        regions: g.regions.map((r) => (r.id === regionId ? data.region : r)),
        current_region_id: data.current_region_id,
      }));
      toast.success(`Traveled to ${data.region?.name || 'the region'}.`);
    } catch {
      toast.error('Could not reach that region.');
    } finally {
      setBusyRegion(null);
    }
  };

  const handleAccept = async (eventId) => {
    if (!campaignId || !eventId) return;
    setBusyEvent(eventId);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/world/events/${eventId}/accept`,
        { method: 'POST' }
      );
      if (!res.ok) throw new Error();
      const data = await res.json();
      // Update local graph
      setGraph((g) => ({
        ...g,
        regions: g.regions.map((r) => ({
          ...r,
          events: (r.events || []).map((e) =>
            e.id === eventId ? { ...e, status: 'accepted', quest_id: data.quest?.quest_id } : e
          ),
        })),
      }));
      toast.success(`Quest accepted: ${data.quest?.name}`);
      // Broadcast a DM arrival beat to the Adventure Log so the hook lands as
      // narrative (a courier / rumor / bell), not just a silent card.
      // Two delivery paths — the Adventure Log may or may not be mounted:
      //   1) If mounted (same-tab): the window event appends immediately.
      //   2) If unmounted (we're on the World Map tab): queue it in localStorage
      //      keyed by sessionId, and the log will drain the queue on next mount.
      if (data.arrival_beat) {
        const beat = {
          text: data.arrival_beat,
          quest: data.quest,
          eventTitle: data.event?.title,
          source: 'map-event',
          timestamp: Date.now(),
        };
        window.dispatchEvent(new CustomEvent('rpg:dm-beat', { detail: beat }));
        try {
          const sid = localStorage.getItem('game-state-session-id');
          if (sid) {
            const key = `dm-pending-beats-${sid}`;
            const queue = JSON.parse(localStorage.getItem(key) || '[]');
            queue.push(beat);
            localStorage.setItem(key, JSON.stringify(queue.slice(-20)));
          }
        } catch {
          // ignore storage errors
        }
      }
      if (onQuestAccepted) onQuestAccepted(data.quest);
    } catch {
      toast.error('Could not accept this lead.');
    } finally {
      setBusyEvent(null);
    }
  };

  const handleDismiss = async (eventId) => {
    if (!campaignId || !eventId) return;
    setBusyEvent(eventId);
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/campaigns/${campaignId}/world/events/${eventId}/dismiss`,
        { method: 'POST' }
      );
      if (!res.ok) throw new Error();
      setGraph((g) => ({
        ...g,
        regions: g.regions.map((r) => ({
          ...r,
          events: (r.events || []).map((e) =>
            e.id === eventId ? { ...e, status: 'dismissed' } : e
          ),
        })),
      }));
    } catch {
      toast.error('Could not dismiss this rumor.');
    } finally {
      setBusyEvent(null);
    }
  };

  // --- rendering helpers ---

  // Use a 100x100 viewBox so positions (0..1) become 0..100
  const nodeRadius = 4.4;  // svg units

  if (!campaignId) {
    return (
      <Card className="h-full bg-black/90 border-amber-600/30 flex items-center justify-center">
        <CardContent className="text-amber-300/80 text-sm p-6">
          Start a campaign to see the map.
        </CardContent>
      </Card>
    );
  }

  const regions = graph.regions || [];
  const edges = graph.edges || [];
  const regionById = Object.fromEntries(regions.map((r) => [r.id, r]));
  const currentId = graph.current_region_id;

  return (
    <Card
      className="h-full bg-black/90 border-amber-600/30 backdrop-blur-sm flex flex-col"
      data-testid="world-map-graph"
    >
      <CardHeader className="pb-2">
        <CardTitle className="text-amber-400 text-lg flex items-center gap-2">
          <Compass className="h-5 w-5" />
          Campaign Map
          {loading && <Loader2 className="h-4 w-4 animate-spin ml-2" />}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col lg:flex-row gap-4 overflow-hidden">
        {/* MAP */}
        <div className="flex-1 min-h-[340px] lg:min-h-0 relative rounded-lg border border-amber-700/20 bg-gradient-to-br from-stone-900 via-black to-stone-900 overflow-hidden">
          {/* Decorative parchment grain */}
          <div className="absolute inset-0 opacity-10 pointer-events-none"
               style={{ backgroundImage: 'radial-gradient(circle at 10% 20%, #f59e0b 0%, transparent 50%), radial-gradient(circle at 80% 70%, #9a3412 0%, transparent 50%)' }} />

          <svg
            viewBox="0 0 100 100"
            preserveAspectRatio="xMidYMid meet"
            className="absolute inset-0 w-full h-full"
            data-testid="world-map-svg"
          >
            {/* Edges */}
            {edges.map((e, i) => {
              const a = regionById[e.from];
              const b = regionById[e.to];
              if (!a || !b) return null;
              return (
                <line
                  key={`edge-${i}`}
                  x1={a.x * 100} y1={a.y * 100}
                  x2={b.x * 100} y2={b.y * 100}
                  stroke="#b45309"
                  strokeWidth="0.35"
                  strokeDasharray="1.2 1.2"
                  opacity="0.55"
                />
              );
            })}

            {/* Nodes */}
            {regions.map((r) => {
              const style = biomeStyle(r.biome);
              const isCurrent = r.id === currentId;
              const isSelected = r.id === selectedId;
              const availEvents = (r.events || []).filter((e) => e.status === 'available').length;
              return (
                <g
                  key={r.id}
                  transform={`translate(${r.x * 100}, ${r.y * 100})`}
                  onClick={() => setSelectedId(r.id)}
                  className="cursor-pointer"
                  data-testid={`region-node-${r.id}`}
                >
                  {isCurrent && (
                    <circle r={nodeRadius + 2.2} fill="none" stroke="#fbbf24"
                            strokeWidth="0.5" opacity="0.9">
                      <animate attributeName="r"
                               values={`${nodeRadius + 1.6};${nodeRadius + 2.6};${nodeRadius + 1.6}`}
                               dur="2.4s" repeatCount="indefinite" />
                    </circle>
                  )}
                  <circle
                    r={nodeRadius}
                    fill={style.fill}
                    stroke={isSelected ? '#fde68a' : style.stroke}
                    strokeWidth={isSelected ? 0.8 : 0.5}
                    opacity={r.visited ? 1 : 0.72}
                  />
                  {/* Small hint-count / event-count pip */}
                  {availEvents > 0 && (
                    <g transform={`translate(${nodeRadius - 0.6}, ${-nodeRadius + 0.6})`}>
                      <circle r="1.6" fill="#fbbf24" stroke="#000" strokeWidth="0.15" />
                      <text
                        x="0" y="0.55"
                        fontSize="1.8"
                        fill="#000"
                        textAnchor="middle"
                        fontWeight="700"
                        style={{ pointerEvents: 'none' }}
                      >
                        {availEvents}
                      </text>
                    </g>
                  )}
                  <text
                    x="0"
                    y={nodeRadius + 3.2}
                    textAnchor="middle"
                    fontSize="2.6"
                    fill="#fef3c7"
                    style={{ pointerEvents: 'none', fontFamily: 'Georgia, serif' }}
                  >
                    {r.name}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Legend */}
          <div className="absolute bottom-2 left-2 flex flex-wrap gap-1.5 max-w-[60%] pointer-events-none">
            {[...new Set(regions.map((r) => r.biome))].slice(0, 6).map((b) => {
              const st = biomeStyle(b);
              const Icon = st.icon;
              return (
                <div
                  key={b}
                  className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] text-amber-100/80 bg-black/50 border border-amber-700/30"
                >
                  <Icon className="h-3 w-3" style={{ color: st.stroke }} />
                  {st.label}
                </div>
              );
            })}
          </div>
        </div>

        {/* SIDE PANEL: region detail + event deck */}
        <div className="w-full lg:w-[340px] shrink-0 flex flex-col">
          {selectedRegion ? (
            <RegionPanel
              region={selectedRegion}
              isCurrent={selectedRegion.id === currentId}
              onVisit={() => handleVisit(selectedRegion.id)}
              onAccept={handleAccept}
              onDismiss={handleDismiss}
              busyRegion={busyRegion}
              busyEvent={busyEvent}
            />
          ) : (
            <div className="text-amber-200/60 text-sm italic p-3 border border-amber-700/20 rounded-lg bg-black/40">
              Tap a region on the map to see its rumors and leads.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const RegionPanel = ({ region, isCurrent, onVisit, onAccept, onDismiss, busyRegion, busyEvent }) => {
  const st = biomeStyle(region.biome);
  const Icon = st.icon;
  const visited = region.visited || region.hydrated;
  const availableEvents = (region.events || []).filter((e) => e.status !== 'dismissed');

  return (
    <div
      className="flex flex-col h-full rounded-lg border border-amber-700/30 bg-black/60 overflow-hidden"
      data-testid="region-panel"
    >
      <div
        className="p-3 text-white"
        style={{ background: `linear-gradient(135deg, ${st.fill}, #1c1917)` }}
      >
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4" style={{ color: st.stroke }} />
          <h3 className="font-semibold text-base truncate" data-testid="region-name">
            {region.name}
          </h3>
          {isCurrent && (
            <Badge className="ml-auto text-[10px] bg-amber-500 text-black">You are here</Badge>
          )}
        </div>
        <div className="mt-1 flex items-center gap-2">
          <Badge variant="outline" className="text-[10px] text-amber-100/90 border-amber-200/40">
            {st.label}
          </Badge>
          {region.is_starting && (
            <Badge variant="outline" className="text-[10px] text-amber-100/90 border-amber-200/40">
              Starter
            </Badge>
          )}
        </div>
        <p className="mt-2 text-xs text-amber-50/85 leading-snug">
          {region.description}
        </p>

        {/* Region presence — factions + dominant races driving the event deck */}
        {(region.present_factions?.length > 0 || region.dominant_races?.length > 0) && (
          <div className="mt-2 flex flex-wrap gap-1.5" data-testid="region-presence">
            {(region.present_factions || []).slice(0, 3).map((f, i) => (
              <Badge
                key={`f-${i}`}
                variant="outline"
                className="text-[10px] text-purple-100/95 border-purple-300/40 bg-purple-900/25"
                title={(f.archetypes || []).join(' / ')}
              >
                <Users className="h-2.5 w-2.5 mr-1" />
                {f.name}
              </Badge>
            ))}
            {(region.dominant_races || []).slice(0, 3).map((r, i) => (
              <Badge
                key={`r-${i}`}
                variant="outline"
                className="text-[10px] text-emerald-100/95 border-emerald-300/40 bg-emerald-900/25"
              >
                {r.charAt(0).toUpperCase() + r.slice(1)}
              </Badge>
            ))}
          </div>
        )}
      </div>

      <ScrollArea className="flex-1 min-h-0 p-3">
        {!visited && (
          <div className="space-y-2">
            <div className="text-xs text-amber-300/90 font-semibold flex items-center gap-1.5">
              <Compass className="h-3.5 w-3.5" /> Rumors
            </div>
            <ul className="space-y-1.5">
              {(region.hints || []).map((h, i) => (
                <li
                  key={i}
                  className="text-xs text-amber-100/70 italic border-l-2 border-amber-600/50 pl-2"
                >
                  {h}
                </li>
              ))}
            </ul>
            <Button
              size="sm"
              className="mt-3 w-full bg-amber-600 hover:bg-amber-500 text-black"
              onClick={onVisit}
              disabled={busyRegion === region.id}
              data-testid="region-visit-btn"
            >
              {busyRegion === region.id ? (
                <><Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> Traveling…</>
              ) : (
                <>Travel Here</>
              )}
            </Button>
          </div>
        )}

        {visited && (
          <div className="space-y-2">
            <div className="text-xs text-amber-300/90 font-semibold flex items-center gap-1.5">
              <Scroll className="h-3.5 w-3.5" /> Event Deck
            </div>
            {availableEvents.length === 0 && (
              <div className="text-xs text-amber-100/50 italic">
                No leads to pursue here right now.
              </div>
            )}
            {availableEvents.map((ev) => (
              <EventCard
                key={ev.id}
                event={ev}
                onAccept={() => onAccept(ev.id)}
                onDismiss={() => onDismiss(ev.id)}
                busy={busyEvent === ev.id}
              />
            ))}
            {!isCurrent && (
              <Button
                size="sm"
                variant="outline"
                className="mt-2 w-full border-amber-600/40 text-amber-200 hover:bg-amber-700/20"
                onClick={onVisit}
                disabled={busyRegion === region.id}
                data-testid="region-travel-btn"
              >
                {busyRegion === region.id ? (
                  <><Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> Traveling…</>
                ) : (
                  <><MapPin className="h-3.5 w-3.5 mr-1" /> Travel Here</>
                )}
              </Button>
            )}
          </div>
        )}
      </ScrollArea>
    </div>
  );
};

const EventCard = ({ event, onAccept, onDismiss, busy }) => {
  const accepted = event.status === 'accepted';
  const diffClass = diffChip[event.difficulty] || diffChip.medium;
  const meta = eventTypeMeta(event.type);
  const reasons = event.drafted_because || [];

  return (
    <div
      className={`rounded-md p-2.5 bg-stone-950/70 ${meta.borderClass} ${meta.ringClass} ${
        accepted ? 'opacity-90' : ''
      }`}
      data-testid={`event-card-${event.id}`}
      data-event-type={event.type}
    >
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <Badge
              className={`text-[10px] ${meta.chipBg} ${meta.chipText} border-0 px-1.5 py-0 leading-tight`}
              data-testid={`event-type-${event.type}`}
              title={meta.label}
            >
              <span className="mr-1" aria-hidden="true">{meta.icon}</span>
              {meta.label}
            </Badge>
            <Badge className={`text-[10px] ${diffClass}`}>{event.difficulty}</Badge>
            {accepted && (
              <Badge className="text-[10px] bg-emerald-500 text-black">Quest active</Badge>
            )}
          </div>
          <h4 className={`mt-1.5 text-sm font-semibold truncate ${meta.accent}`}>
            {event.title}
          </h4>
          <p className="text-[11.5px] text-amber-100/80 mt-1 leading-snug">
            {event.description}
          </p>
          {reasons.length > 0 && (
            <p
              className="mt-1.5 text-[10px] italic text-stone-300/70"
              data-testid="event-drafted-because"
              title="Why this card was drafted for this region"
            >
              <span className="opacity-70">Drafted because:</span> {reasons.join(' · ')}
            </p>
          )}
        </div>
      </div>
      {!accepted && (
        <div className="flex gap-1.5 mt-2">
          <Button
            size="sm"
            className="flex-1 h-7 bg-emerald-600 hover:bg-emerald-500 text-black text-xs"
            onClick={onAccept}
            disabled={busy}
            data-testid={`event-accept-${event.id}`}
          >
            {busy ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <><Check className="h-3 w-3 mr-1" /> Accept</>
            )}
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 border-amber-700/50 text-amber-200 hover:bg-amber-700/20 text-xs"
            onClick={onDismiss}
            disabled={busy}
            data-testid={`event-dismiss-${event.id}`}
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      )}
    </div>
  );
};

export default WorldMapGraph;
