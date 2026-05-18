#!/bin/bash
set -euo pipefail

# Only run in remote Claude Code environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo '{"async": true, "asyncTimeout": 300000}'

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/home/user/dnd-ai-clean}"

echo "🎲 Setting up D&D AI game environment..."

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd "$PROJECT_DIR/frontend"
yarn install --frozen-lockfile --silent

# Start React dev server in background on port 3000
echo "🚀 Starting React dev server on port 3000..."
BROWSER=none PORT=3000 yarn start > /tmp/react-dev.log 2>&1 &
echo "✅ Dev server starting (PID $!)"

# Install backend dependencies (best-effort — some private packages may be unavailable)
echo "📦 Installing backend dependencies..."
cd "$PROJECT_DIR/backend"
pip install -r requirements.txt -q 2>/dev/null || echo "⚠️  Some backend packages unavailable (private deps) — skipping"

echo "✅ Environment ready!"
