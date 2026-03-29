#!/usr/bin/env bash
# RMTK VN — Local dev server
# Run from project root: ./serve.sh [port]

PORT="${1:-4000}"
JEKYLL="/home/khaitran/.local/share/gem/ruby/3.2.0/bin/jekyll"

# Kill any existing server on the port
lsof -ti:"$PORT" | xargs kill -9 2>/dev/null
sleep 0.5

echo "🚀 Starting RMTK VN at http://127.0.0.1:$PORT"
$JEKYLL serve --port "$PORT" --host 127.0.0.1 --livereload
