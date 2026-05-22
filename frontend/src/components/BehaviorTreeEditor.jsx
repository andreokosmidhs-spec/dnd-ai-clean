/**
 * BehaviorTreeEditor.jsx
 *
 * Full-page admin panel for editing D&D 5e enemy behavior trees.
 * Route: /behavior-trees (standalone page) or via Battle Config button in CombatScreen.
 */
import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL || "";

// ─── Color palette per node type ──────────────────────────────────────────────
const NODE_COLORS = {
  selector: { border: "#f97316", bg: "#431407", label: "Selector (OR)" },
  sequence: { border: "#3b82f6", bg: "#1e3a5f", label: "Sequence (AND)" },
  condition: { border: "#22c55e", bg: "#14532d", label: "Condition" },
  action: { border: "#a855f7", bg: "#3b0764", label: "Action" },
  not: { border: "#ef4444", bg: "#450a0a", label: "NOT" },
};

const NODE_TYPES = Object.keys(NODE_COLORS);

// ─── Utility: deep clone ──────────────────────────────────────────────────────
function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

// ─── Default blank nodes ──────────────────────────────────────────────────────
function blankNode(type = "action") {
  if (type === "selector" || type === "sequence")
    return { type, children: [] };
  if (type === "not")
    return { type, child: { type: "condition", check: "hp_below", value: 0.5 } };
  if (type === "condition")
    return { type: "condition", check: "hp_below", value: 0.5 };
  // action
  return { type: "action", action: "attack_melee", damage_die: "1d6+2", damage_type: "slashing", label: "Attack" };
}

// ─── Recursive node path setter ───────────────────────────────────────────────
function setAtPath(root, path, updater) {
  if (path.length === 0) return updater(root);
  const [head, ...tail] = path;
  const r = clone(root);
  if (head === "child") {
    r.child = setAtPath(r.child, tail, updater);
  } else if (typeof head === "number") {
    r.children = r.children.map((c, i) =>
      i === head ? setAtPath(c, tail, updater) : c
    );
  }
  return r;
}

function deleteAtPath(root, path) {
  if (path.length === 0) return null;
  const [head, ...tail] = path;
  const r = clone(root);
  if (head === "child" && tail.length === 0) {
    r.child = blankNode("condition");
    return r;
  }
  if (typeof head === "number" && tail.length === 0) {
    r.children = r.children.filter((_, i) => i !== head);
    return r;
  }
  if (head === "child") {
    r.child = deleteAtPath(r.child, tail);
    return r;
  }
  r.children = r.children.map((c, i) =>
    i === head ? deleteAtPath(c, tail) : c
  );
  return r;
}

// ─── Condition param controls ─────────────────────────────────────────────────
function ConditionControls({ node, conditions, onChange }) {
  const cond = conditions.find((c) => c.id === node.check) || {};
  return (
    <div className="flex flex-col gap-1 mt-1">
      <select
        className="bg-slate-800 border border-slate-600 text-slate-200 text-xs rounded px-2 py-1"
        value={node.check || ""}
        onChange={(e) => onChange({ ...node, check: e.target.value, value: undefined })}
      >
        {conditions.map((c) => (
          <option key={c.id} value={c.id}>{c.label}</option>
        ))}
      </select>
      {cond.has_value && (
        <input
          className="bg-slate-800 border border-slate-600 text-slate-200 text-xs rounded px-2 py-1"
          type={cond.value_type === "int" ? "number" : "text"}
          step={cond.value_type === "float" ? "0.05" : "1"}
          placeholder={`value (${cond.value_type})`}
          value={node.value !== undefined ? node.value : ""}
          onChange={(e) => {
            const raw = e.target.value;
            const val = cond.value_type === "float" ? parseFloat(raw) :
              cond.value_type === "int" ? parseInt(raw, 10) : raw;
            onChange({ ...node, value: isNaN(val) ? raw : val });
          }}
        />
      )}
      {cond.description && (
        <p className="text-slate-500 text-[10px] italic">{cond.description}</p>
      )}
    </div>
  );
}

// ─── Action param controls ────────────────────────────────────────────────────
function ActionControls({ node, actions, onChange }) {
  const actionDef = actions.find((a) => a.id === node.action) || { params: [] };

  function field(name, type, defaultVal) {
    const val = node[name] !== undefined ? node[name] : defaultVal;
    if (type === "bool") {
      return (
        <label key={name} className="flex items-center gap-1 text-xs text-slate-300">
          <input
            type="checkbox"
            checked={!!val}
            onChange={(e) => onChange({ ...node, [name]: e.target.checked })}
            className="accent-violet-500"
          />
          {name}
        </label>
      );
    }
    if (type === "list") {
      // Attacks list: render as textarea with JSON
      return (
        <div key={name} className="flex flex-col gap-0.5">
          <span className="text-[10px] text-slate-400">{name} (JSON array)</span>
          <textarea
            className="bg-slate-800 border border-slate-600 text-slate-200 text-[10px] rounded px-2 py-1 font-mono h-20 resize-y"
            value={
              val
                ? JSON.stringify(val, null, 2)
                : "[]"
            }
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                onChange({ ...node, [name]: parsed });
              } catch (_) {}
            }}
          />
        </div>
      );
    }
    return (
      <div key={name} className="flex flex-col gap-0.5">
        <span className="text-[10px] text-slate-400">{name}</span>
        <input
          className="bg-slate-800 border border-slate-600 text-slate-200 text-xs rounded px-2 py-1"
          type={type === "int" ? "number" : "text"}
          value={val ?? ""}
          onChange={(e) => {
            const v = type === "int" ? parseInt(e.target.value, 10) : e.target.value;
            onChange({ ...node, [name]: isNaN(v) ? e.target.value : v });
          }}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1 mt-1">
      <select
        className="bg-slate-800 border border-slate-600 text-slate-200 text-xs rounded px-2 py-1"
        value={node.action || ""}
        onChange={(e) => {
          const newDef = actions.find((a) => a.id === e.target.value) || { params: [] };
          const newNode = { type: "action", action: e.target.value };
          newDef.params.forEach((p) => { newNode[p.name] = p.default; });
          onChange(newNode);
        }}
      >
        {actions.map((a) => (
          <option key={a.id} value={a.id}>{a.label}</option>
        ))}
      </select>
      {actionDef.params.map((p) => field(p.name, p.type, p.default))}
      {actionDef.description && (
        <p className="text-slate-500 text-[10px] italic">{actionDef.description}</p>
      )}
    </div>
  );
}

// ─── Recursive Node Card ──────────────────────────────────────────────────────
function NodeCard({ node, path, conditions, actions, onUpdate, onDelete, depth = 0 }) {
  if (!node) return null;
  const colors = NODE_COLORS[node.type] || NODE_COLORS.action;
  const indent = Math.min(depth, 6) * 12;

  function handleTypeChange(newType) {
    onUpdate(path, () => blankNode(newType));
  }

  function handleUpdate(updater) {
    onUpdate(path, updater);
  }

  function handleChildUpdate(childPath, updater) {
    onUpdate([...path, ...childPath], updater);
  }

  function addChild() {
    onUpdate(path, (n) => ({
      ...n,
      children: [...(n.children || []), blankNode("action")],
    }));
  }

  return (
    <div
      style={{ marginLeft: indent, borderColor: colors.border }}
      className="border rounded-lg p-2 mb-1.5 text-xs"
      data-testid={`node-${node.type}`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-1">
        <span
          className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
          style={{ background: colors.bg, color: colors.border, border: `1px solid ${colors.border}40` }}
        >
          {colors.label}
        </span>
        {node.label && (
          <span className="text-slate-300 text-[11px] italic truncate max-w-[120px]">{node.label}</span>
        )}
        <div className="ml-auto flex items-center gap-1">
          {/* Change type */}
          <select
            className="bg-slate-900 border border-slate-700 text-slate-400 text-[10px] rounded px-1 py-0.5"
            value={node.type}
            onChange={(e) => handleTypeChange(e.target.value)}
          >
            {NODE_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          {/* Delete */}
          {depth > 0 && (
            <button
              onClick={() => onDelete(path)}
              className="text-red-500 hover:text-red-300 font-bold text-sm leading-none w-5 h-5 flex items-center justify-center rounded hover:bg-red-900/30"
              title="Delete node"
            >
              x
            </button>
          )}
        </div>
      </div>

      {/* Condition body */}
      {node.type === "condition" && (
        <ConditionControls
          node={node}
          conditions={conditions}
          onChange={(updated) => handleUpdate(() => updated)}
        />
      )}

      {/* Action body */}
      {node.type === "action" && (
        <ActionControls
          node={node}
          actions={actions}
          onChange={(updated) => handleUpdate(() => updated)}
        />
      )}

      {/* NOT child */}
      {node.type === "not" && node.child && (
        <div className="mt-1 pl-1 border-l border-red-800/60">
          <NodeCard
            node={node.child}
            path={["child"]}
            conditions={conditions}
            actions={actions}
            onUpdate={(childPath, updater) => handleChildUpdate(childPath, updater)}
            onDelete={(childPath) => onUpdate([...path, ...childPath], () => blankNode("condition"))}
            depth={depth + 1}
          />
        </div>
      )}

      {/* Selector / Sequence children */}
      {(node.type === "selector" || node.type === "sequence") && (
        <div className="mt-1 pl-1 border-l border-slate-700/60">
          {(node.children || []).map((child, i) => (
            <NodeCard
              key={i}
              node={child}
              path={[i]}
              conditions={conditions}
              actions={actions}
              onUpdate={(childPath, updater) => handleChildUpdate([i, ...childPath], updater)}
              onDelete={(childPath) => {
                if (childPath.length === 0) {
                  onUpdate(path, (n) => ({
                    ...n,
                    children: n.children.filter((_, idx) => idx !== i),
                  }));
                } else {
                  onDelete([...path, i, ...childPath]);
                }
              }}
              depth={depth + 1}
            />
          ))}
          <button
            onClick={addChild}
            className="mt-1 text-[10px] px-2 py-0.5 rounded border border-dashed border-slate-600 text-slate-400 hover:border-violet-500 hover:text-violet-400 transition-all"
          >
            + Add Child
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Simulation Panel ─────────────────────────────────────────────────────────
function SimulationPanel({ treeId, onClose }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function run() {
      try {
        const resp = await axios.post(
          `${API}/api/behavior-trees/${treeId}/simulate`,
          { player_hp: 30 }
        );
        setResult(resp.data);
      } catch (e) {
        setError(e.message || "Simulation failed");
      } finally {
        setLoading(false);
      }
    }
    run();
  }, [treeId]);

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-[480px] max-h-[70vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-bold text-lg">3-Round Simulation</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl leading-none">&times;</button>
        </div>
        {loading && <p className="text-slate-400 text-sm">Running simulation...</p>}
        {error && <p className="text-red-400 text-sm">{error}</p>}
        {result && (
          <div className="flex flex-col gap-3">
            <p className="text-slate-400 text-xs">Tree: <span className="text-violet-300">{result.tree_name}</span></p>
            {result.rounds.map((r) => (
              <div key={r.round} className="bg-slate-800/60 rounded-lg p-3 border border-slate-700/60">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-violet-400 font-bold text-sm">Round {r.round}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 uppercase">
                    {r.action_type}
                  </span>
                  {r.advantage && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-900 text-green-300">ADV</span>
                  )}
                </div>
                {r.damage_die && (
                  <p className="text-slate-300 text-xs">
                    Damage: <span className="text-amber-300">{r.damage_die}</span>
                    {r.damage_type && <span className="text-slate-400"> ({r.damage_type})</span>}
                  </p>
                )}
                {r.narration_hint && (
                  <p className="text-slate-400 text-[11px] italic mt-1">{r.narration_hint}</p>
                )}
                {r.abilities_used && r.abilities_used.length > 0 && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {r.abilities_used.map((ab) => (
                      <span key={ab} className="text-[9px] px-1.5 py-0.5 rounded-full bg-violet-900/60 text-violet-300 border border-violet-700/40">
                        {ab}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function BehaviorTreeEditor({ onBack }) {
  const [trees, setTrees] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [editingTree, setEditingTree] = useState(null); // {id, name, description, node}
  const [meta, setMeta] = useState({ conditions: [], actions: [] });
  const [saving, setSaving] = useState(false);
  const [showSim, setShowSim] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  // Load tree list and meta on mount
  useEffect(() => {
    async function load() {
      try {
        const [treeResp, metaResp] = await Promise.all([
          axios.get(`${API}/api/behavior-trees`),
          axios.get(`${API}/api/behavior-trees/meta`),
        ]);
        setTrees(treeResp.data || []);
        setMeta(metaResp.data || { conditions: [], actions: [] });
      } catch (e) {
        console.error("Failed to load behavior trees:", e);
      }
    }
    load();
  }, []);

  // Load a specific tree for editing
  const selectTree = useCallback(async (treeId) => {
    try {
      const resp = await axios.get(`${API}/api/behavior-trees/${treeId}`);
      setEditingTree(clone(resp.data));
      setSelectedId(treeId);
    } catch (e) {
      console.error("Failed to load tree:", treeId, e);
    }
  }, []);

  // Update node at path
  const handleNodeUpdate = useCallback((path, updater) => {
    setEditingTree((prev) => {
      if (!prev) return prev;
      const newNode = setAtPath(prev.node, path, updater);
      return { ...prev, node: newNode };
    });
  }, []);

  // Delete node at path
  const handleNodeDelete = useCallback((path) => {
    setEditingTree((prev) => {
      if (!prev) return prev;
      const newNode = deleteAtPath(prev.node, path);
      return { ...prev, node: newNode };
    });
  }, []);

  // Save tree
  async function handleSave() {
    if (!editingTree) return;
    setSaving(true);
    setSaveMsg(null);
    try {
      await axios.put(`${API}/api/behavior-trees/${editingTree.id}`, editingTree);
      setSaveMsg({ ok: true, text: "Saved successfully." });
      // Refresh list
      const resp = await axios.get(`${API}/api/behavior-trees`);
      setTrees(resp.data || []);
    } catch (e) {
      setSaveMsg({ ok: false, text: e.message || "Save failed." });
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMsg(null), 3000);
    }
  }

  // Reset to default
  async function handleReset() {
    if (!selectedId) return;
    if (!window.confirm(`Reset '${selectedId}' to default? This deletes any custom version.`)) return;
    try {
      await axios.delete(`${API}/api/behavior-trees/${selectedId}`);
      await selectTree(selectedId);
      setSaveMsg({ ok: true, text: "Reset to default." });
      setTimeout(() => setSaveMsg(null), 2000);
    } catch (e) {
      setSaveMsg({ ok: false, text: "Reset failed: " + e.message });
    }
  }

  // New tree
  function handleNewTree() {
    const id = `custom_${Date.now()}`;
    const newTree = {
      id,
      name: "New Tree",
      description: "Custom behavior tree",
      node: {
        type: "selector",
        children: [
          {
            type: "sequence",
            children: [
              { type: "condition", check: "in_melee_range" },
              { type: "action", action: "attack_melee", damage_die: "1d6+2", damage_type: "slashing", label: "Attack" },
            ],
          },
          { type: "action", action: "move_toward_player" },
        ],
      },
    };
    setEditingTree(newTree);
    setSelectedId(id);
  }

  const filteredTrees = trees.filter((t) =>
    !searchQuery ||
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-200">
      {/* Top Bar */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-3">
          {onBack && (
            <button
              onClick={onBack}
              className="text-xs text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 px-2 py-1 rounded transition-all"
            >
              Back
            </button>
          )}
          <h1 className="text-white font-bold text-base">Behavior Tree Editor</h1>
          <span className="text-slate-500 text-xs">D&D 5e Enemy AI</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleNewTree}
            className="text-xs px-3 py-1 rounded border border-violet-700 text-violet-300 hover:bg-violet-900/40 transition-all"
          >
            + New Tree
          </button>
          {editingTree && (
            <>
              <button
                onClick={() => setShowSim(true)}
                className="text-xs px-3 py-1 rounded border border-amber-700 text-amber-300 hover:bg-amber-900/40 transition-all"
              >
                Simulate
              </button>
              <button
                onClick={handleReset}
                className="text-xs px-3 py-1 rounded border border-slate-600 text-slate-400 hover:border-red-600 hover:text-red-400 transition-all"
              >
                Reset to Default
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="text-xs px-3 py-1 rounded bg-violet-700 hover:bg-violet-600 text-white font-semibold transition-all disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save"}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Save message */}
      {saveMsg && (
        <div className={`flex-shrink-0 px-4 py-1 text-xs ${saveMsg.ok ? "bg-green-900/40 text-green-300" : "bg-red-900/40 text-red-300"}`}>
          {saveMsg.text}
        </div>
      )}

      {/* Body */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Sidebar: tree list */}
        <div className="flex-shrink-0 w-56 bg-slate-900/80 border-r border-slate-800 flex flex-col">
          <div className="p-2 border-b border-slate-800">
            <input
              type="text"
              placeholder="Search trees..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-violet-600"
            />
          </div>
          <div className="flex-1 overflow-y-auto py-1">
            {filteredTrees.map((tree) => (
              <button
                key={tree.id}
                onClick={() => selectTree(tree.id)}
                className={`w-full text-left px-3 py-2 text-xs transition-all border-l-2 ${
                  selectedId === tree.id
                    ? "bg-violet-900/40 border-violet-500 text-violet-200"
                    : "border-transparent text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                <div className="font-medium truncate">{tree.name}</div>
                <div className="text-[10px] text-slate-500 truncate">{tree.id}</div>
                {tree.is_custom && (
                  <span className="inline-block mt-0.5 text-[9px] px-1 py-0 rounded bg-violet-900/60 text-violet-400 border border-violet-700/40">
                    custom
                  </span>
                )}
              </button>
            ))}
            {filteredTrees.length === 0 && (
              <p className="text-slate-600 text-xs p-3">No trees found.</p>
            )}
          </div>
        </div>

        {/* Main editor panel */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {!editingTree ? (
            <div className="flex-1 flex items-center justify-center text-slate-600 text-sm">
              Select a tree from the sidebar to edit it
            </div>
          ) : (
            <>
              {/* Tree metadata */}
              <div className="flex-shrink-0 p-3 bg-slate-900/40 border-b border-slate-800 flex gap-3 items-start">
                <div className="flex flex-col gap-1">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">ID</span>
                  <input
                    className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 w-40"
                    value={editingTree.id}
                    onChange={(e) => setEditingTree((prev) => ({ ...prev, id: e.target.value }))}
                  />
                </div>
                <div className="flex flex-col gap-1 flex-1">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">Name</span>
                  <input
                    className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 w-full"
                    value={editingTree.name || ""}
                    onChange={(e) => setEditingTree((prev) => ({ ...prev, name: e.target.value }))}
                  />
                </div>
                <div className="flex flex-col gap-1 flex-1">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">Description</span>
                  <input
                    className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-400 w-full"
                    value={editingTree.description || ""}
                    onChange={(e) => setEditingTree((prev) => ({ ...prev, description: e.target.value }))}
                  />
                </div>
              </div>

              {/* Legend */}
              <div className="flex-shrink-0 px-3 py-1.5 bg-slate-950/50 border-b border-slate-800/50 flex gap-3 flex-wrap">
                {Object.entries(NODE_COLORS).map(([type, c]) => (
                  <div key={type} className="flex items-center gap-1">
                    <div className="w-2.5 h-2.5 rounded-sm border" style={{ borderColor: c.border, background: c.bg }} />
                    <span className="text-[10px] text-slate-500">{c.label}</span>
                  </div>
                ))}
              </div>

              {/* Node tree */}
              <div className="flex-1 overflow-y-auto p-3">
                {editingTree.node ? (
                  <NodeCard
                    node={editingTree.node}
                    path={[]}
                    conditions={meta.conditions}
                    actions={meta.actions}
                    onUpdate={(path, updater) => {
                      if (path.length === 0) {
                        setEditingTree((prev) => ({ ...prev, node: updater(prev.node) }));
                      } else {
                        handleNodeUpdate(path, updater);
                      }
                    }}
                    onDelete={(path) => {
                      if (path.length === 0) return; // don't delete root
                      handleNodeDelete(path);
                    }}
                    depth={0}
                  />
                ) : (
                  <p className="text-slate-500 text-xs">No node. Click New Tree to start.</p>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Simulation modal */}
      {showSim && selectedId && (
        <SimulationPanel
          treeId={selectedId}
          onClose={() => setShowSim(false)}
        />
      )}
    </div>
  );
}
