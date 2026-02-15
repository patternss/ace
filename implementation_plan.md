# ACE - Implementation Plan

**Version**: 0.1.0-draft
**Last Updated**: 2026-02-12
**Reference**: [General Specifications](./general_specifications.md)

---

## Overview

This plan follows the principle: **each phase produces something usable**. Phase 0 is a chatbot. Phase 1 is a chatbot that knows you. Phase 2 is an assistant that does things. Phase 3 is a voice assistant. Phase 4 is ACE.

The MVP (Phase 0) is deliberately minimal: a text-based assistant running in a browser, talking to a lightweight server, which talks to an LLM. Everything else is layered on top.

---

## Phase 0: MVP — Text Chat

**Goal**: A working text conversation between a user in a browser and an LLM, routed through a coordination server.

**What this validates**:
- Client ↔ server WebSocket communication
- The orchestration loop (input → LLM → response)
- LLM provider abstraction (start with one, prove the interface)
- The basic project structure and development workflow

### Tech Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Server** | Python + FastAPI | Best LLM SDK ecosystem (Anthropic, OpenAI, Google all have first-class Python SDKs). FastAPI has native WebSocket support, async, and is lightweight enough for a Pi. |
| **Client** | Svelte | Compiles to minimal JS (small bundles, ideal for Pi-served static files). Built-in reactivity for streaming responses and real-time state. Built-in transitions/animations for face states and view switching. Simple component model that scales from text chat to full UI. |
| **Communication** | WebSocket | As specified. Bidirectional, real-time. |
| **First LLM provider** | Google (Gemini) | Pick one to start. The abstraction layer means swapping is cheap later. Google has a generous free tier and a first-class Python SDK. |
| **Configuration** | `.env` file + `config.yaml` | API keys in `.env` (never committed). Server settings in YAML. Simple, no database needed yet. |

### Tasks

#### 0.1 Project Setup
- [ ] Initialize repository structure
- [ ] Set up Python project (pyproject.toml, virtual env, dependencies)
- [ ] Set up Svelte project (`npm create svelte@latest`, TypeScript enabled)
- [ ] Basic dev tooling: linter, formatter, .gitignore, Vite dev server
- [ ] README with setup instructions

**Repository Structure** (initial):
```
ace/
├── server/
│   ├── main.py              # FastAPI entrypoint
│   ├── config.py             # Configuration loading
│   ├── session_manager.py    # Orchestration loop
│   ├── llm/
│   │   ├── router.py         # LLM abstraction interface
│   │   └── adapters/
│   │       └── gemini.py     # First adapter
│   └── requirements.txt
├── client/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── stores/
│   │   │   │   └── connection.ts    # WebSocket state store
│   │   │   ├── components/
│   │   │   │   ├── Chat.svelte      # Message list + input
│   │   │   │   └── MessageBubble.svelte
│   │   │   └── websocket.ts         # WebSocket client module
│   │   ├── routes/
│   │   │   └── +page.svelte         # Main page
│   │   └── app.html
│   ├── package.json
│   ├── svelte.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── config.yaml               # Server configuration
├── .env.example              # API key template
└── README.md
```

#### 0.2 WebSocket Server
- [ ] FastAPI app with WebSocket endpoint (`/ws`)
- [ ] Connection lifecycle: accept, receive messages, send messages, disconnect
- [ ] Message format: JSON with `type` and `payload` (matching the draft protocol)
- [ ] Basic error handling (malformed messages, disconnections)

#### 0.3 LLM Router + First Adapter
- [ ] Define the LLM interface: `chat(messages) → response`, `stream(messages) → chunks`
- [ ] Implement Google Gemini adapter using the official SDK (`google-genai`)
- [ ] Router that loads the configured adapter
- [ ] Streaming support from day 1 (stream partial responses to the client)

#### 0.4 Orchestration Loop (Minimal)
- [ ] Session Manager receives `user.input.text` message
- [ ] Appends to conversation history (in-memory list for now)
- [ ] Sends history to LLM via Router
- [ ] Streams response back to client as `assistant.response.text` (with `isPartial` flag)
- [ ] No tools, no memory persistence — just the conversation loop

#### 0.5 Svelte Client
- [ ] `Chat.svelte` component: message list + text input + send button
- [ ] `MessageBubble.svelte` component: renders a single message (user or assistant)
- [ ] `websocket.ts` module: WebSocket connection, send/receive, auto-reconnect
- [ ] `connection.ts` Svelte store: reactive connection state (connected/disconnected/reconnecting)
- [ ] Send `user.input.text` messages on submit
- [ ] Receive and render `assistant.response.text` messages (handle streaming/partial with reactive updates)
- [ ] Basic styling (readable, clean — nothing fancy)
- [ ] Connection status indicator (reactive, bound to store)

#### 0.6 Configuration & First Run
- [ ] Load API key from `.env`
- [ ] Load server config from `config.yaml` (port, LLM provider, model name)
- [ ] Dev setup: FastAPI server + Vite dev server (with proxy to API for WebSocket)
- [ ] Production build: Svelte compiles to static files, served by FastAPI
- [ ] Startup script or instructions to run server + open client
- [ ] Verify: type a message → see a streamed response from Gemini

### Definition of Done
You can open a browser, type a message, and have a streamed conversation with Gemini through the coordination server. Refreshing the page loses history (no persistence yet). The code is clean, modular, and ready for the next layer.

---

## Phase 1: Memory

**Goal**: The assistant remembers things — within a session (working memory) and across sessions (long-term memory).

**Depends on**: Phase 0 complete

### Tasks

#### 1.1 Working Memory (Conversation Persistence)
- [ ] Store conversation history in SQLite (not just in-memory)
- [ ] Sessions persist across page refreshes
- [ ] Session ID management (create new, resume existing)
- [ ] Configurable context window (last N messages sent to LLM)

#### 1.2 Long-Term Memory
- [ ] SQLite schema for facts/preferences (`key`, `value`, `source`, `timestamp`)
- [ ] Memory Manager module: `store(fact)`, `retrieve(query)`, `forget(key)`
- [ ] Instruct the LLM (via system prompt) to extract and store notable facts
- [ ] Inject relevant long-term memories into the prompt context
- [ ] User can ask "What do you remember about me?" and get a meaningful answer

#### 1.3 Semantic Memory (Basic)
- [ ] Add a vector store (ChromaDB — lightweight, embedded, Python-native)
- [ ] Embed conversation summaries and stored facts
- [ ] On each user message, retrieve top-N relevant memories by similarity
- [ ] Inject retrieved memories into prompt alongside conversation history

#### 1.4 Memory in the Orchestration Loop
- [ ] Update the Session Manager: before calling the LLM, query the Memory Manager
- [ ] After LLM response, check for facts to store (either via LLM extraction or explicit user instruction)
- [ ] Conversation summaries generated periodically (e.g., every N turns) for long-term storage

### Definition of Done
You can close the browser, come back tomorrow, and the assistant knows your name, your preferences, and can reference past conversations. "Remember that I prefer dark mode" works. "What did we talk about yesterday?" returns something meaningful.

---

## Phase 2: First Tools

**Goal**: The assistant can take actions — search the web, manage notes, interact with external services.

**Depends on**: Phase 1 complete (memory needed for tool context)

### Tasks

#### 2.1 Tool System Architecture
- [ ] Define the tool interface: `name`, `description`, `parameters` (JSON Schema), `execute(params) → result`
- [ ] Tool registry: register tools at startup, list available tools
- [ ] Update orchestration loop to handle tool calls:
  - LLM returns a tool call → Session Manager executes → result fed back to LLM → loop
  - Support parallel tool calls
- [ ] Tool definitions injected into LLM prompt (using provider's native tool/function calling format)

#### 2.2 Web Search Tool
- [ ] Server-side tool: takes a query, returns search results
- [ ] Use a search API (SearXNG self-hosted, or Tavily/Brave Search API)
- [ ] Returns structured results (title, snippet, URL)
- [ ] The assistant can search and summarize findings

#### 2.3 Notes / Todo Tool
- [ ] Server-side tool backed by SQLite
- [ ] Operations: create note, list notes, search notes, update note, delete note
- [ ] Todo support: create task, mark complete, list tasks (with filters)
- [ ] The assistant can manage your notes and tasks through conversation

#### 2.4 Timer / Alarm Tool
- [ ] Client-side tool: set a timer, receive a notification when it fires
- [ ] Server tracks scheduled timers, client executes the notification
- [ ] First client-side tool — validates the `tool.request` / `tool.result` message flow

#### 2.5 Calculator Tool
- [ ] Simple server-side tool: evaluate math expressions safely
- [ ] Useful for the LLM to delegate arithmetic rather than hallucinating numbers

### Definition of Done
You can say "Search for the best Python testing frameworks", "Add 'buy groceries' to my todo list", "Set a timer for 10 minutes", and the assistant does it. The tool system is extensible — adding a new tool means writing one module and registering it.

---

## Phase 3: Voice

**Goal**: Talk to the assistant and hear it respond. Hands-free interaction.

**Depends on**: Phase 2 complete (tools should work before adding voice input)

### Tasks

#### 3.1 Speech-to-Text (STT)
- [ ] Integrate browser Web Speech API as the first STT provider
- [ ] Push-to-talk mode: hold a button to speak, release to send
- [ ] Transcribed text sent as `user.input.text` (same pipeline as typed input)
- [ ] Visual indicator when listening (CSS state change on the page)

#### 3.2 Text-to-Speech (TTS)
- [ ] Integrate browser Web Speech API as the first TTS provider
- [ ] Assistant responses spoken aloud
- [ ] Streaming TTS: start speaking as soon as partial text is available (sentence-level chunking)
- [ ] Option to mute/unmute

#### 3.3 Voice Activity Detection (VAD)
- [ ] Basic VAD for continuous mode (detect when user starts/stops speaking)
- [ ] Enable continuous conversation mode (beyond push-to-talk)
- [ ] Silence detection to determine when user is done speaking

#### 3.4 Interruption Handling (Basic)
- [ ] Detect user speech during assistant playback (via VAD)
- [ ] Stop TTS playback immediately
- [ ] Send new user input to the orchestration loop
- [ ] Mark the interrupted response in conversation history

#### 3.5 Streaming Pipeline Optimization
- [ ] Measure end-to-end latency: user stops speaking → assistant starts speaking
- [ ] Optimize: STT → server → LLM (streaming) → server → TTS (incremental)
- [ ] Target: < 2 seconds to first audio in normal conditions

#### 3.6 Voice Mode UI
- [ ] Mode selector: text-only, push-to-talk, continuous
- [ ] Visual feedback: listening, processing, speaking indicators
- [ ] Settings: voice selection, speech rate (using available Web Speech API options)

#### 3.7 STT/TTS Provider Abstraction
- [ ] Abstract STT behind an interface (same as LLM router pattern)
- [ ] Abstract TTS behind an interface
- [ ] Add at least one alternative: ElevenLabs adapter for TTS (higher quality, paid)
- [ ] Configuration: select provider in config file

### Definition of Done
You can have a spoken conversation with the assistant. Push-to-talk works reliably. Continuous mode works for natural dialogue. Interrupting the assistant works. Latency is acceptable (< 2s). You can switch between text and voice modes.

---

## Phase 4: The Face

**Goal**: The assistant has a visual presence — an animated character that reacts to conversation state.

**Depends on**: Phase 3 complete (face needs to sync with voice)

### Tasks

#### 4.1 Face Design & Assets
- [ ] Design the character (cute animal aesthetic as spec'd)
- [ ] Create sprite sheets or animation assets for each state:
  - Idle (blinking, subtle breathing)
  - Listening (attentive)
  - Thinking (processing)
  - Speaking (mouth movement)
- [ ] Keep assets lightweight (optimize for fast loading)

#### 4.2 Face Renderer
- [ ] Canvas-based renderer (2D, performant, no heavy dependencies)
- [ ] Render the character centered on screen
- [ ] State-driven: renderer receives a state, plays the corresponding animation
- [ ] Smooth transitions between states

#### 4.3 State Synchronization
- [ ] Server sends `face.state` messages tied to the orchestration loop:
  - User starts typing/speaking → `listening`
  - Message sent to LLM → `thinking`
  - Response streaming → `speaking`
  - Idle → `idle`
- [ ] Client face renderer reacts to state messages in real-time

#### 4.4 Lip-Sync Approximation
- [ ] Analyze TTS audio amplitude or phoneme timing
- [ ] Map to mouth-open/mouth-closed frames (basic lip flap)
- [ ] Sync with audio playback timing

#### 4.5 Layout: Face + Chat
- [ ] Default view: face takes center stage, chat is secondary (small text overlay or side panel)
- [ ] Face minimizes when content is being presented (PIP style)
- [ ] Responsive layout (works on different screen sizes)

#### 4.6 Content Presentation Mode
- [ ] Face shrinks to corner when displaying content
- [ ] Content area fills the main view (same-origin content via iframes)
- [ ] Smooth transition between face view and content view
- [ ] "Back to face" action

### Definition of Done
The assistant has a face. It blinks when idle, looks attentive when listening, shows a thinking animation during processing, and moves its mouth when speaking. The face is the primary interface — the text chat is secondary. You can show content and the face moves to a corner. This is the moment it stops feeling like a chatbot and starts feeling like ACE.

---

## Phase 5: Integrations & More Tools

**Goal**: The assistant connects to real services and becomes genuinely productive.

**Depends on**: Phase 2 tool system (can run in parallel with Phase 3/4 in some cases)

### Tasks

#### 5.1 Google OAuth Flow
- [ ] Implement OAuth 2.0 authorization code flow for Google APIs
- [ ] Token storage (encrypted, on the coordination server)
- [ ] Token refresh handling
- [ ] User-facing: "Connect your Google account" flow in the browser

#### 5.2 Gmail Tool
- [ ] Read emails (inbox, search by query)
- [ ] Send emails (compose, reply)
- [ ] Summarize unread emails
- [ ] "What emails did I get today?" / "Send a reply to John saying..."

#### 5.3 Google Drive Tool
- [ ] List files, search by name/content
- [ ] Read document content (Docs, Sheets — via export API)
- [ ] Display documents in ACE's content viewer (same-origin rendered)
- [ ] "Find the budget spreadsheet" / "Show me my recent documents"

#### 5.4 Google Calendar Tool
- [ ] Read events (today, this week, search)
- [ ] Create events
- [ ] Modify/delete events
- [ ] "What's on my calendar today?" / "Schedule a meeting with Lisa at 3pm"

#### 5.5 Weather Tool
- [ ] Server-side tool using a weather API (OpenWeather, WeatherAPI, etc.)
- [ ] Current conditions + forecast
- [ ] Location-based (user preference or explicit query)

#### 5.6 Document Viewer (Enhanced)
- [ ] Client-side tool: render PDF, markdown, plain text in ACE's content area
- [ ] Annotation support (highlight, underline) on rendered documents
- [ ] The assistant can point to specific sections while explaining

### Definition of Done
The assistant can read your email, check your calendar, find files in your Drive, and tell you the weather. These are real, productive actions that make ACE genuinely useful as a secretary/assistant.

---

## Phase 6: Polish & Multi-Device

**Goal**: Roles, presets, device management, and overall polish.

**Depends on**: All previous phases

### Tasks

#### 6.1 Role System
- [ ] Implement role definitions (secretary, colleague/friend, teacher)
- [ ] Each role adjusts: system prompt, verbosity, proactivity, available tool emphasis
- [ ] Role switching: explicit ("Switch to teacher mode") or automatic (based on context)
- [ ] Role persists across sessions (configurable)

#### 6.2 Presets
- [ ] Implement preset system (named configurations)
- [ ] Built-in presets: "Focused Work", "Learning Session", "Casual Chat"
- [ ] User-created presets (save current configuration as a preset)
- [ ] Quick-switch UI

#### 6.3 Device Registry
- [ ] Track connected clients (device ID, capabilities, connection state)
- [ ] Device capability reporting (`client.state.update` messages)
- [ ] UI: show connected devices list

#### 6.4 Device Handoff
- [ ] Implement session transfer between devices
- [ ] User requests handoff via voice command or UI
- [ ] Session state transfers seamlessly (conversation continues on target device)
- [ ] Source device goes idle

#### 6.5 Customization UI
- [ ] Settings page: name, voice, verbosity, formality, proactivity
- [ ] LLM provider selection + API key management
- [ ] Tool enable/disable toggles
- [ ] System prompt editor (advanced)

#### 6.6 Second LLM Provider
- [ ] Add Anthropic (Claude) adapter (validates the abstraction layer works in practice)
- [ ] Add OpenAI adapter
- [ ] Add Ollama adapter (local model support)
- [ ] Fallback logic: primary → secondary → local → error message
- [ ] User can switch providers in settings

### Definition of Done
The assistant has personality modes, connects across multiple devices, and is configurable to the user's preferences. The system feels polished and personal. Adding a new LLM provider or tool is a well-defined, documented process.

---

## Cross-Cutting Concerns

These are not tied to a single phase — they should be addressed continuously.

### Testing Strategy
- **Unit tests**: For each module (LLM adapters, memory manager, tool implementations)
- **Integration tests**: WebSocket communication, orchestration loop with mock LLM
- **Manual testing**: Each phase has a "Definition of Done" that serves as the acceptance test
- **No vanity coverage targets** — test critical paths and edge cases

### Error Handling
- Graceful degradation at every layer (per spec)
- Server errors → meaningful error messages to client (not stack traces)
- LLM failures → retry once, then fallback or inform user
- WebSocket disconnect → client auto-reconnects, session resumes

### Configuration
- All configurable values in `config.yaml` (not hardcoded)
- API keys in `.env` (never committed)
- Feature flags for experimental features (e.g., `enable_voice: true`)

### Documentation
- README updated with each phase
- Setup instructions always current
- Architecture decisions documented in the spec's Decision Log

---

## Phase Dependencies

```
Phase 0 (MVP: Text Chat)
    │
    ▼
Phase 1 (Memory)
    │
    ▼
Phase 2 (First Tools) ──────────────────┐
    │                                     │
    ▼                                     ▼
Phase 3 (Voice)                    Phase 5 (Integrations)
    │                              (can start after 2, parallel with 3/4)
    ▼
Phase 4 (The Face)
    │
    ▼
Phase 6 (Polish & Multi-Device)
```

---

## Open Questions

These don't need answers before starting Phase 0, but should be resolved before the relevant phase.

| Question | Relevant Phase | Notes |
|----------|---------------|-------|
| Which search API for web search tool? | Phase 2 | SearXNG (self-hosted, free) vs. Tavily/Brave (API, paid). Depends on self-hosting appetite. |
| How to handle LLM context window limits? | Phase 1 | Conversation summarization? Sliding window? Needs experimentation. |
| How are expert personas structured? | Phase 6+ | Deferred per spec. Needs design work before implementation. |
| SvelteKit or plain Svelte + Vite? | Phase 0 | SvelteKit adds routing, SSR, and file-based routes. May be overkill for a SPA, but its file structure is clean. Decide during project setup. |

---

*This is a living document. Update it as decisions are made and phases are completed.*
