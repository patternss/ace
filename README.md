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

Start both processes:

```bash
# Terminal 1: Server (run from project root)
source server/.venv/bin/activate
uvicorn server.main:app --reload

# Terminal 2: Client
cd client
npm run dev
```

The Vite dev server (default: http://localhost:5173) proxies WebSocket and API requests to the FastAPI server (default: http://localhost:8000).

## Linting & Formatting

```bash
# Python (from server/)
ruff check .
ruff format .

# JS/TS/Svelte (from client/)
npm run lint
npm run format
```
