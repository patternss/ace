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

## Phase 0.2 — WebSocket Server (2026-02-15)

With the skeleton in place, the next step was communication. The browser needs to talk to the server in real time — not HTTP request-response, but a persistent bidirectional channel. That's what WebSockets are for.

**The message protocol** was formalized in a new `protocol.md` document. Every message is JSON with a `type` field and a `payload`. The spec had drafted 17 message types; Phase 0.2 implements just the five needed for text chat: `user.input.text`, `assistant.response.text`, `connection.ping`/`pong`, and `error`. The rest are documented as "defined, not yet implemented" so nothing is forgotten.

**Pydantic models** (`server/protocol.py`) give each message type a typed Python representation. A `CamelModel` base class handles the naming convention mismatch — Python uses `snake_case` (`session_id`) but the JSON wire format uses `camelCase` (`sessionId`). The `parse_incoming()` function takes raw JSON, checks the `type` field, and returns the right typed model.

**The WebSocket handler** (`server/connection.py`) is deliberately thin. A `ConnectionManager` tracks who's connected and knows how to send messages. The `websocket_endpoint()` function accepts connections, loops receiving messages, and dispatches them. For now, `handle_message()` just echoes user text back — the real LLM call comes in Phase 0.4. But the full round-trip works: send JSON, receive JSON, errors are handled gracefully.

**Configuration** (`server/config.py`) was also implemented — frozen dataclasses that load `config.yaml` and `.env`, with a cached `get_config()` accessor.

A security review prompted the addition of a **Security Hardening Checklist** to the implementation plan. Items like WebSocket authentication, TLS, rate limiting, and error message sanitization are deliberately omitted now (local-only, single-user) but tracked with the phase where they become relevant. The goal: never forget a security concern just because it's not urgent yet.

## Phase 0.3 — LLM Router + Ollama Adapter (2026-02-15)

Now the server needed a brain. The LLM router is the abstraction that lets the rest of the system talk to any language model without knowing which one.

**A key decision was made here: start with Ollama instead of Gemini.** The original plan said Gemini, but during implementation it made more sense to use a local model — free, no API key management, no cloud dependency during development. The router abstraction means swapping to Gemini or Claude later is just writing a new adapter and changing one line in `config.yaml`.

**The interface** (`server/llm/router.py`) is built on `typing.Protocol` — a structural typing approach where adapters don't inherit from a base class, they just have the right methods. The interface has two async methods: `chat(messages) → str` for complete responses, and `stream(messages) → AsyncGenerator[str]` for streaming. A `Message` frozen dataclass (`role` + `content`) is the standard format — adapters convert to provider-specific formats internally.

**The Ollama adapter** (`server/llm/adapters/ollama.py`) is straightforward. Ollama's message format happens to match our standard format almost exactly (both use "user" and "assistant" as roles), so the conversion is trivial. The adapter uses the `ollama` SDK's `AsyncClient` for both chat and streaming.

**Config was updated** to make `api_key` and `host` optional fields — Ollama doesn't need an API key, and defaults to `localhost:11434`. The Gemini adapter stub remains for Phase 6.

At the end of this phase: the router can be called with a list of messages and get a response from a local Ollama model, both as a complete response and as a stream of chunks. The WebSocket handler still echoes — Phase 0.4 will wire the router into the orchestration loop and make it all work end-to-end.

## Phase 0.4 — The Orchestration Loop (2026-02-15)

This is where ACE stopped being a skeleton and started being a conversational assistant. The goal: wire the LLM router (Phase 0.3) into the WebSocket handler (Phase 0.2) so that when a user sends a message, they get a real streamed response from the language model.

**The session manager** (`server/session_manager.py`) replaced its stub with two responsibilities: conversation history and LLM orchestration. History is a simple in-memory dict mapping session IDs to message lists — no persistence yet (that's Phase 1). The key function, `handle_user_message()`, is an async generator: it appends the user message to history, streams from the LLM router, yields each chunk, and after the stream completes, appends the full assistant response to history.

A deliberate design choice: **the session manager has zero WebSocket awareness**. It takes a session ID and text in, yields string chunks out. The connection layer decides how to wrap those chunks in protocol messages. This keeps transport and logic cleanly separated — the session manager is equally usable from a WebSocket handler, an HTTP endpoint, or a test harness.

**The connection handler** (`server/connection.py`) got its echo logic replaced. Now when a `user.input.text` arrives, the handler iterates over the session manager's stream: each chunk is sent as an `assistant.response.text` with `isPartial: true`, and after the stream ends, a final message with `isPartial: false` carries the full assembled response. LLM errors are caught and sent as `ErrorMessage` with a new `LLM_ERROR` code — the connection stays alive so the user can try again.

**The model was switched to `qwen3:14b`** from `qwen3-vl:30b` for faster responses during development, and **the server port was changed to 8888** to avoid conflicts with other services commonly running on 8000.

Testing confirmed all three pillars work: streaming responses arrive chunk-by-chunk, conversation context is preserved across messages on the same session, and ping/pong still works alongside the new orchestration. The server is now a functioning chat backend — the next step (Phase 0.5) is the browser UI to talk to it.

## Phase 0.5 — The Svelte Client (2026-02-15)

With the server streaming real LLM responses, the final piece of Phase 0 was giving users a way to actually talk to it. This phase replaced the Vite boilerplate with a working chat interface.

**The architecture splits into two layers.** `websocket.ts` is a plain TypeScript `ChatSocket` class — no Svelte dependency, just callbacks for messages and state changes. It handles connecting to `/ws`, sending JSON, and auto-reconnecting with exponential backoff (1s → 2s → 4s → 30s max). On top of that, `connection.svelte.ts` wraps the socket in Svelte 5 runes (`$state`, `$derived`) to make everything reactive. The `.svelte.ts` extension is required because runes only work in files the Svelte compiler processes — a plain `.ts` file can't use `$state()`.

**The store owns all chat state**: a reactive `messages` array, `connectionState` (connected/disconnected/reconnecting), and an `isStreaming` flag. Streaming logic handles the server's partial/complete protocol: `isPartial: true` chunks get appended to the current assistant message, and the final `isPartial: false` message replaces the content with the complete text. The session ID is an ephemeral `crypto.randomUUID()` — new on every page refresh, with persistence deferred to Phase 1.

**Two components make up the UI.** `Chat.svelte` is the full-screen layout: a header with "ACE" and a connection status dot (green/orange/red), a scrollable message list with auto-scroll, and a text input with send button. Input disables when disconnected; send disables while streaming. `MessageBubble.svelte` renders individual messages — user messages right-aligned in blue, assistant messages left-aligned in dark gray. Content uses `{message.content}` (not `{@html}`), so everything is auto-escaped with no XSS risk.

**The global CSS was stripped down** from Vite's demo theme to a minimal dark theme — just enough for the chat to look clean. The old `Counter.svelte` boilerplate and the plain `connection.ts` stub were deleted.

At the end of this phase: ACE is a working text chat app. Open the browser, type a message, watch the assistant's response stream in chunk by chunk. Send another message and the assistant has full conversation context. Stop the server and the status dot turns red; restart it and the client auto-reconnects. Phase 0 is complete — everything from here is enhancement.
