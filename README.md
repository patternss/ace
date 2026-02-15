# ACE — Animated Companion Entity

A personal AI assistant with an animated face.

## Prerequisites

- Python 3.12+
- Node.js 20+

## Setup

### Server

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Client

```bash
cd client
npm install
```

### Configuration

1. Copy `.env.example` to `.env` and add your API keys
2. Edit `config.yaml` for server settings

## Development

Start both processes (two terminals):

```bash
# Terminal 1: Server (run from project root)
source server/.venv/bin/activate
uvicorn server.main:app --reload --port 8888

# Terminal 2: Client dev server
cd client
npm run dev
```

The Vite dev server (http://localhost:5173) proxies `/ws` to the FastAPI server (http://localhost:8888).

## Production

Build the client and run the server — no Vite dev server needed:

```bash
# Build the Svelte client to static files
cd client
npm run build

# Start the server (serves the built client at /)
cd ..
source server/.venv/bin/activate
uvicorn server.main:app --port 8888
```

Open http://localhost:8888 — FastAPI serves the chat UI and handles WebSocket connections.

## Linting & Formatting

```bash
# Python (from server/)
ruff check .
ruff format .

# JS/TS/Svelte (from client/)
npm run lint
npm run format
```
