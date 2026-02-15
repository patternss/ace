# ACE — Project Story

<!--
  HOW TO WRITE THIS FILE:

  This is a narrative log of the project's evolution. Write in broad strokes:
  - What was added and why it matters (not every file, but every meaningful step)
  - Key decisions and the reasoning behind them
  - How one phase led to the next
  - What was learned or discovered along the way
  - what was forsaken or changed and why

  Keep it readable — someone new to the project should be able to read this
  and understand how ACE came to be, what shape it has, and why.

  Don't duplicate specs or plans. This is the "why and how it happened" story,
  not the "what it should be" spec. Update it as each meaningful milestone lands.
-->

---

## The Beginning — Specs and a Vision (2026-02-12)

ACE started as an idea: a personal AI assistant that doesn't live in a chat window but *inhabits a screen*. An animated face that talks to you, shows you things, and controls the display. Think less "chatbot" and more "companion that occupies a monitor."

The first work was all on paper. A general specification laid out the full vision — the animated face, voice interaction, memory system, tool use, device handoff, and a modular architecture where every component is replaceable. An implementation plan broke that vision into six phases, each producing something usable: text chat first, then memory, tools, voice, the face, and finally polish.

Two key principles were established early: **modularity first** (every component loosely coupled, replaceable, independently testable) and **iterative development** (build the simplest working version, then enhance).

## Phase 0.1 — Project Scaffolding (2026-02-15)

Before writing any real logic, the project needed a skeleton. The goal was simple: set up the repo so that both the server and client can run, and every developer tool is in place.

**The server** is Python with FastAPI. We chose `pyproject.toml` as the single source of truth for dependencies and tool config — the modern Python standard, replacing the older `requirements.txt` approach. FastAPI was picked for its native WebSocket support, async capabilities, and the fact that every major LLM provider has a first-class Python SDK. The server is intentionally lightweight — it's meant to run on something as modest as a Raspberry Pi. For now it has just a `/health` endpoint to prove it starts.

**The client** is Svelte with TypeScript, built using Vite. We chose plain Svelte over SvelteKit — SvelteKit adds file-based routing and server-side rendering, neither of which a single-page app needs. Vite handles the dev server (with instant hot reloads) and the production build (compiling everything into static files that FastAPI will serve). The Vite config includes a proxy so that during development, WebSocket and API calls from the browser get forwarded to the FastAPI backend automatically.

**Dev tooling** was set up from day one: Ruff for Python (linting + formatting in one tool), ESLint + Prettier for the TypeScript/Svelte side. A root `.gitignore` covers both ecosystems. The philosophy: catch mistakes early, enforce consistency without thinking about it.

**Placeholder stubs** were created for every module in the planned architecture — the session manager, LLM router, Gemini adapter, WebSocket client, Svelte stores and components. Each stub is just a docstring explaining the module's future responsibility. No dead code, but the file tree is navigable and communicates intent.

At the end of this phase: the server starts and responds to health checks, the client builds and passes all lint/type checks, and the project structure is ready for real code. Nothing works end-to-end yet — that's Phase 0.2.
