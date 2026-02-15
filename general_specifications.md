# ACE - General Specifications

**Project Codename**: ACE (Animated Companion Entity)
**Version**: 0.1.0-draft
**Last Updated**: 2026-02-12

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Project Vision](#2-project-vision)
3. [System Architecture](#3-system-architecture)
4. [Core Components](#4-core-components)
5. [Platform Strategy](#5-platform-strategy)
6. [Assistant Roles & Capabilities](#6-assistant-roles--capabilities)
7. [User Interface](#7-user-interface)
8. [Voice & Communication](#8-voice--communication)
9. [Memory & Persistence](#9-memory--persistence)
10. [LLM Integration](#10-llm-integration)
11. [Security & Privacy](#11-security--privacy)
12. [Assistant Customization](#12-assistant-customization)
13. [Future Considerations](#13-future-considerations)

---

## 1. Design Philosophy

### 1.1 Core Principles

#### Modularity First
The system MUST be built as loosely coupled, independent modules that communicate through well-defined interfaces. Each component should be replaceable without affecting others.

**Rationale**: The final form of this project cannot be fully defined upfront. Discovery will happen during development. Modularity enables evolution without rewrites.

**In Practice**:
- Define clear interfaces/contracts between components
- Avoid tight coupling; components should not know implementation details of others
- Use dependency injection where appropriate
- Each module should be independently testable

#### Iterative Development
Build the simplest working version first, then enhance. Resist the urge to over-engineer early.

**In Practice**:
- Start with rough implementations that work
- Optimize only when necessary and measured
- Ship early, learn, iterate
- "Make it work, make it right, make it fast" - in that order

#### Graceful Degradation
The system should remain functional even when some components fail or are unavailable.

**In Practice**:
- If the face renderer fails, fall back to text mode
- If cloud LLM is unavailable, attempt local model
- If voice fails, offer text input
- Always provide a working (if reduced) experience

#### Configuration Over Code
Behavior changes should be possible through configuration rather than code changes where reasonable.

**In Practice**:
- User preferences stored in configuration
- Feature flags for experimental features
- Plugin/skill system for extensibility
- Avoid hardcoded values for anything that might change

#### Local-First, Privacy-Respecting
User data stays on user devices by default. Cloud features are opt-in and transparent.

**In Practice**:
- Data storage is local by default (on the user's coordination server)
- Clear indication when data leaves the device (e.g., LLM API calls)
- User owns and controls their data
- No telemetry without explicit consent
- Note: Full offline operation is not a primary goal. The system is designed to work with cloud LLM providers (Claude, Gemini, etc.) as the default. Users *can* run a local model (e.g., Ollama) for offline/private LLM usage, but this is optional, not mandatory.

### 1.2 Development Guidelines

#### Technology Choices
- **Server**: Python (FastAPI)
- **Client**: Svelte (TypeScript)
- **Selection Criteria**:
  - Widely used and battle-tested
  - Strong ecosystem and community
  - Aligns with modularity goals
  - Safe defaults (type safety where practical)
  - Svelte: compiles to minimal JS (lightweight for Pi-served deployments), built-in reactivity and transitions

#### Code Quality
- Readable code over clever code
- Explicit over implicit
- Document the "why", not just the "what"
- Tests for critical paths, not vanity coverage metrics

#### Dependency Management
- Prefer well-maintained, widely-used libraries
- Minimize dependency count where reasonable
- Pin versions for reproducibility
- Regular security audits of dependencies

---

## 2. Project Vision

### 2.1 What Is ACE?

ACE is a personal AI assistant with a visual presence. Unlike traditional chatbots confined to text boxes, ACE "occupies" a screen - displaying an animated face, speaking with voice, and controlling the display to show content, documents, and media.

### 2.2 Core Concept: Screen Occupation

The assistant doesn't live in a chat window - it **inhabits a display**. This means:

- The assistant's face is the primary interface when idle/conversing
- The assistant can "step aside" to show you content (documents, videos, web pages)
- The assistant can annotate, point to, scroll, and manipulate **its own rendered content** (Phase 1: same-origin only; Phase 3/native: any application)
- The assistant can narrate and explain what it's showing
- The display is the assistant's "body" for that session
- For third-party content (e.g., external websites), the assistant can open and manage tabs but cannot directly annotate or manipulate the content until the native wrapper phase

### 2.3 Assistant Roles

ACE serves three primary roles, plus an extensible Expert role:

| Role | Description | Example Interactions |
|------|-------------|---------------------|
| **Secretary** | Task management, scheduling, reminders, information lookup | "What's on my calendar today?", "Remind me to call John at 3pm" |
| **Colleague/Friend** | Conversation partner, feedback on projects, brainstorming | "What do you think about this design?", "Let's talk through this problem" |
| **Teacher/Trainer** | Learning support, explanations, skill development | "Explain how neural networks work", "Quiz me on Spanish vocabulary" |
| **Expert** ⚠️ | Field-specific expertise requiring specialized skills or outside resources | "Review this contract for red flags", "Analyze this circuit diagram", "Help me debug this kernel module" |

> **⚠️ Note on Expert Role**: This is the last role to be added on the role side of the assistant and requires further design work. Expert personas are envisioned as **add-on features** — modular, domain-specific skill packs that the assistant can adopt when a task demands field-specific expertise (e.g., legal, medical, engineering, finance). The exact mechanism for activating, acquiring, and scoping these expert personas is **not yet defined** and needs more thinking before implementation.

---

## 3. System Architecture

### 3.1 High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     COORDINATION LAYER                          │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐   │
│  │  Session  │ │  Device   │ │  Memory   │ │  LLM Router   │   │
│  │  Manager  │ │  Registry │ │  Manager  │ │  & Abstraction│   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ WebSocket / HTTP
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Client Application                    │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │   │
│  │  │    Face     │ │    Voice    │ │   Presentation  │   │   │
│  │  │  Renderer   │ │   Engine    │ │      Layer      │   │   │
│  │  │             │ │  (TTS/STT)  │ │ (content/annot) │   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │   │
│  │  │   Input     │ │    Tab      │ │     Tools       │   │   │
│  │  │  Handler    │ │  Controller │ │    Interface    │   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Communication

- **Client ↔ Coordination Layer**: WebSocket for real-time bidirectional communication
- **Between Modules**: Event-based messaging with defined message schemas
- **LLM Communication**: Abstracted through router; supports multiple backends

#### Message Protocol (Draft)

All messages are JSON objects with a `type` field and a `payload`. Direction indicates the primary flow; some types may be bidirectional.

**Client → Server**:

| Type | Description | Payload (key fields) |
|------|-------------|---------------------|
| `user.input.text` | User typed a message | `{ text, sessionId }` |
| `user.input.audio` | User voice input (transcribed or raw) | `{ transcript?, audioChunk?, sessionId }` |
| `client.state.update` | Client reports its capabilities or state | `{ deviceId, capabilities, activeView }` |
| `session.handoff.request` | User requests session move to another device | `{ targetDeviceId }` |
| `tool.result` | Result of a client-side tool execution | `{ toolCallId, result, error? }` |

**Server → Client**:

| Type | Description | Payload (key fields) |
|------|-------------|---------------------|
| `assistant.response.text` | Text response (may be streamed) | `{ text, isPartial, sessionId }` |
| `assistant.response.audio` | TTS audio output | `{ audioChunk, format }` |
| `assistant.action.display` | Show content or change view | `{ contentType, contentUrl, layout }` |
| `assistant.action.annotate` | Annotation command (same-origin content) | `{ action, target, style }` |
| `assistant.action.tab` | Tab management command | `{ action: open\|close\|focus, url? }` |
| `tool.request` | Request client to execute a tool | `{ toolCallId, toolName, parameters }` |
| `face.state` | Update face expression/state | `{ state: idle\|listening\|thinking\|speaking\|presenting }` |
| `session.handoff.execute` | Instruction to pick up or release a session | `{ sessionId, action: acquire\|release }` |

**Bidirectional**:

| Type | Description |
|------|-------------|
| `connection.ping` / `connection.pong` | Keepalive |
| `error` | Error with `{ code, message, context? }` |

> **Note**: This is a draft schema. Message types will be refined during implementation. The key principle is that every message is typed, every payload is structured, and the protocol is extensible (new message types can be added without breaking existing ones).

### 3.3 Module Boundaries

Each module exposes:
1. **Interface**: What it does (contract)
2. **Events**: What it emits
3. **Configuration**: What can be customized

Modules do NOT:
- Directly instantiate other modules
- Access other modules' internal state
- Make assumptions about implementation details

---

## 4. Core Components

### 4.1 Coordination Layer (Backend)

**Technology**: Python (FastAPI) or Node.js (to be determined based on prototyping)

**Deployment Model**: The coordination layer runs on the **user's own hardware** — a home server, Raspberry Pi, mini PC, or cloud VPS. It is intentionally lightweight: a WebSocket server, SQLite database, HTTP client for LLM APIs, and an optional vector store. No GPU required. A modern Raspberry Pi (4/5, 4GB+ RAM) is sufficient.

The **client (browser) does the heavy lifting**: rendering the avatar (Canvas/WebGL with GPU access), running TTS/STT (via Web Speech API or WASM-based models), processing audio, and driving the UI. The coordination layer is essentially stateful middleware — it routes messages, manages memory, and proxies LLM calls.

**Network Considerations**:
- **Local network**: Client and server on the same WiFi — simplest setup, zero-config with mDNS
- **Remote access**: Requires port forwarding, a reverse proxy, or a tunnel service (e.g., Tailscale, Cloudflare Tunnel)
- **Cloud-hosted**: User runs the coordination layer on a VPS — accessible from anywhere, but adds hosting cost

#### Session Manager
- Tracks active sessions across devices
- Manages conversation context
- Handles device handoff (see 4.3)
- **Runs the orchestration loop** — the core agentic cycle of the system

**Orchestration Loop**:
```
User Input (text or transcribed voice)
       │
       ▼
┌─────────────────────────────┐
│  1. Gather Context          │
│  - Conversation history     │
│  - Relevant memories        │◄── Memory Manager
│  - Available tools          │◄── Tools Interface (filtered by device, role)
│  - Active role/persona      │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  2. Send to LLM             │◄── LLM Router
│  - Assembled prompt         │
│  - Tool definitions         │
│  - Streaming enabled        │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│  3. Process LLM Response    │
│  ┌────────────────────────┐ │
│  │ Text response?         │─┼──► Return to client (stream to device)
│  │ Tool call request?     │─┼──► Execute tool → feed result back to step 2
│  │ Multiple tool calls?   │─┼──► Execute in parallel → feed results back
│  └────────────────────────┘ │
└─────────────────────────────┘
```

The Session Manager is the **executor**, not the **decider**. It controls what tools are *offered* to the LLM (based on device capabilities, active role, and context), but the LLM decides which tools to *use*. The loop repeats until the LLM produces a final text response.

#### Device Registry
- Tracks connected devices/clients
- Manages device capabilities
- Routes messages to appropriate device

#### Memory Manager
- Short-term: Current conversation context
- Long-term: Persistent facts, preferences, history
- Semantic: Vector-based retrieval for relevant memories

#### LLM Router
- Abstracts LLM provider (OpenAI, Anthropic, Ollama, etc.)
- Handles fallback logic
- Manages rate limiting and costs

### 4.2 Client Layer (Frontend)

**Technology**: Svelte (TypeScript), compiled to static files served by the coordination layer. Potential native wrappers later.

#### Face Renderer
- Displays animated avatar
- Syncs expressions/lip movement with speech
- Initial: Simple 2D animated character (cute animal)
- Future: More sophisticated animation

#### Voice Engine
- **TTS (Text-to-Speech)**: Converts assistant responses to audio
- **STT (Speech-to-Text)**: Converts user speech to text
- **VAD (Voice Activity Detection)**: Detects when user is speaking

#### Presentation Layer
- Displays content (documents, images, video, web pages)
- Annotation system (highlight, underline, pointer)
- Transitions between face view and content view

#### Tab Controller
- Manages browser tabs
- Opens/closes/switches tabs on assistant command
- Reports current tab state to coordination layer

#### Input Handler
- Keyboard input (text mode)
- Microphone input (voice mode)
- Touch/click input

#### Tools Interface
- Exposes available tools to the assistant
- Executes tool calls from LLM
- Returns results to coordination layer

### 4.3 Device Handoff

Device handoff is user-initiated. The user requests that the assistant "move" to another device:

1. User says "Move to the living room screen" (or selects a device from a list)
2. Session Manager checks Device Registry for the target device
3. If the target device is connected and available, Session Manager transfers the active session (conversation context, current state)
4. The target client picks up the session — face appears, conversation continues
5. The source client either goes idle or disconnects

The coordination layer (running on the user's server) holds all session state, so the handoff is a matter of re-pointing which client receives the output stream. Both devices must be connected to the same coordination layer.

---

## 5. Platform Strategy

### 5.1 Phase 1: Web-First

**Approach**: Single Page Application running in modern browsers

**Rationale**:
- Immediate cross-device support (desktop, laptop, phone, tablet)
- No installation required
- Fastest path to working prototype
- Large ecosystem of libraries

**Constraints**:
- Limited OS-level integration
- Browser security sandbox limits some capabilities
- Requires internet for initial load (can use service workers for offline)

**Screen Control Scope**:
- Full control over **same-origin content** — ACE-rendered pages, built-in viewers, iframes hosting ACE's own content. The assistant can annotate, scroll, manipulate, and overlay these freely.
- **Third-party URLs** (Google Sheets, YouTube, etc.) can be opened and managed via basic tab operations (open, close, focus), but the assistant cannot read, annotate, or manipulate their content due to browser Same-Origin Policy.
- Rich interaction with external content is deferred to Phase 3 (native wrappers) rather than pursuing a browser extension intermediate step.

**Browser Support**: Modern evergreen browsers (Chrome, Firefox, Safari, Edge)

### 5.2 Phase 2: Enhanced Web + PWA

**Additions**:
- Progressive Web App for better mobile experience
- Service workers for offline capability
- Push notifications

### 5.3 Phase 3: Native Wrappers (Future)

**Potential Approaches**:
- **Desktop**: Electron or Tauri wrapper around web app
- **Mobile**: Capacitor or React Native

**Benefits**:
- System-level permissions (always-on microphone, notifications)
- Better performance
- OS integration (menu bar, system tray)
- **OS-level screen control**: Full ability to annotate, overlay, and interact with any application's content — not just same-origin pages. This is a key motivator for going native, unlocking the full "screen occupation" vision that the browser sandbox prevents.

---

## 6. Assistant Roles & Capabilities

### 6.1 Core Capabilities

| Capability | Description | Priority |
|------------|-------------|----------|
| Conversation | Natural dialogue with context retention | P0 |
| Screen Control | Display and manipulate content | P0 |
| Voice I/O | Speak and listen | P0 |
| Memory | Remember facts and preferences | P1 |
| Task Management | Reminders, todos, scheduling | P1 |
| Web Browsing | Search and display web content | P1 |
| Document Handling | Open, display, annotate documents | P1 |
| Tool Use | Extensible tool system (see 6.3) | P0 |
| Device Switching | Move between devices (see 4.3) | P2 |

### 6.2 Role-Specific Behaviors

The assistant adapts its behavior based on context:

**Secretary Mode**:
- Concise, action-oriented responses
- Proactive reminders
- Efficient task capture

**Colleague/Friend Mode**:
- Conversational, thoughtful responses
- Asks clarifying questions
- Offers opinions when asked

**Teacher/Trainer Mode**:
- Explanatory, patient responses
- Uses visual aids (screen control)
- Checks understanding, offers practice

**Expert Mode** ⚠️ *(add-on, requires further design)*:
- Activates domain-specific knowledge and specialized skills
- May leverage external tools, APIs, or curated resources particular to the field
- Adopts terminology, reasoning patterns, and standards of the relevant discipline
- Clearly communicates confidence level and the limits of its expertise
- Designed as modular add-ons — users would enable specific expert personas as needed

> **Open Questions for Expert Role**:
> - How are expert personas packaged and distributed? (plugin-like system, marketplace, user-created?)
> - What is the activation mechanism? (explicit user selection, automatic detection from context, or both?)
> - How do expert personas interact with the base roles? (layered on top, or a distinct mode switch?)
> - What guardrails are needed for high-stakes domains (legal, medical) to prevent over-reliance?
> - Should expert personas carry their own memory/knowledge bases, or extend the shared memory system?

### 6.3 Tools & Skills

**Tools** are atomic actions the assistant can invoke — a single, well-defined operation (search the web, send an email, read a file). **Skills** are higher-level, composed behaviors that may chain multiple tools together and carry their own logic (e.g., "research a topic" might combine web search, document reading, and summarization).

#### Built-in Tools

| Tool | Description | Priority | Execution |
|------|-------------|----------|-----------|
| **Web Search** | Search the web and return results | P1 | Server-side |
| **Gmail** (Google API) | Read, send, search emails | P1 | Server-side (OAuth) |
| **Google Drive** (Google API) | Read, create, list files in Drive | P1 | Server-side (OAuth) |
| **Google Calendar** (Google API) | Read, create, modify calendar events | P1 | Server-side (OAuth) |
| **Timer / Alarm** | Set timers, alarms, reminders | P1 | Client-side |
| **Notes / Todo** | Create, read, update notes and task lists | P1 | Server-side (local storage) |
| **Calculator** | Arithmetic and unit conversions | P2 | Client-side |
| **Document Viewer** | Open and display documents (PDF, markdown, text) | P1 | Client-side |
| **Media Player** | Play audio/video content | P2 | Client-side |
| **Weather** | Current weather and forecasts | P2 | Server-side (API) |
| **Image Generation** | Generate images via API (DALL-E, etc.) | P3 | Server-side (API) |

> **Execution column**: "Server-side" tools are executed by the coordination layer. "Client-side" tools are executed by the client (browser) and results are sent back via `tool.result` messages. This distinction matters because client-side tools have access to the display and audio, while server-side tools have access to APIs and persistent storage.

#### Skills (Future)

Skills are composed of tools and logic. Examples:
- **"Research a topic"** — web search → read multiple sources → summarize findings → present on screen
- **"Morning briefing"** — check calendar → check email → check weather → narrate summary
- **"Study session"** — present material → quiz user → track progress → adjust difficulty

The skill system design is deferred to a later phase but the architecture should anticipate it (tools should be composable, results should be structured).

---

## 7. User Interface

### 7.1 Primary Interface: The Face

The animated face is the default view when:
- Assistant is idle
- Assistant is speaking
- Assistant is listening
- No content is being presented

**Initial Implementation**:
- 2D animated character (cute animal aesthetic)
- Basic expressions: neutral, happy, thinking, speaking
- Lightweight rendering (CSS/Canvas/simple WebGL)
- Lip-sync approximation (mouth movement while audio plays)

**Face States**:
| State | Visual Indication |
|-------|-------------------|
| Idle | Neutral expression, subtle idle animation (blinking, breathing) |
| Listening | Attentive expression, possible visual indicator |
| Thinking | Thinking expression, processing indicator |
| Speaking | Animated mouth, appropriate expression |
| Presenting | Face minimized or moved to corner |

### 7.2 Content Presentation Mode

When showing content, the face:
- Shrinks to corner (picture-in-picture style), OR
- Disappears with quick transition back when speaking

**Annotation Capabilities** *(same-origin content only in Phase 1)*:
- Pointer/cursor controlled by assistant
- Highlight regions
- Underline text
- Draw simple shapes (circles, arrows)
- Scroll content

> **Browser Sandbox Note**: These annotation and manipulation capabilities apply only to same-origin content — pages and iframes that ACE itself renders (e.g., built-in document viewers, media players, whiteboards, code viewers). Third-party sites opened in separate tabs are outside ACE's reach due to the Same-Origin Policy. Full cross-application annotation is a Phase 3 (native wrapper) capability.

### 7.3 Tab/Window Model

**Same-Origin Content** (full control):
- Loaded within ACE's own views (iframes, embedded viewers)
- Assistant can annotate, scroll, manipulate, and overlay
- Examples: built-in document viewer, media player, markdown renderer, code viewer

**Third-Party Content** (basic tab management):
- Opened in new browser tabs via `window.open()`
- Assistant can open, close, and focus tabs
- Assistant **cannot** read, annotate, or manipulate content in these tabs
- Still useful: "Let me open that Google Sheet for you", "Switching to YouTube"

**Commands**:
- "Let me show you..." → Opens content in ACE's viewer (same-origin) or new tab (external)
- "As you can see here..." → Points to element *(same-origin content only)*
- "Let me go back..." → Returns to face view
- "Switch to the document I showed earlier" → Tab switch or view switch

---

## 8. Voice & Communication

### 8.1 Voice Modes

Users can configure their preferred interaction mode:

| Mode | Description | Use Case |
|------|-------------|----------|
| **Push-to-Talk** | User holds button/key to speak | Noisy environments, precise control |
| **Wake Word** | Always listening for activation phrase | Hands-free, always ready |
| **Continuous** | Open conversation, VAD-based turn-taking | Natural dialogue sessions |
| **Text Only** | No voice, keyboard input only | Silent environments, preference |

### 8.2 Speech-to-Text (STT)

**Options** (modular - can swap):
- Browser Web Speech API (free, decent quality)
- Whisper (local or API)
- Cloud providers (Google, Azure, Deepgram)

### 8.3 Text-to-Speech (TTS)

**Options** (modular - can swap):
- Browser Web Speech API (free, robotic)
- ElevenLabs (high quality, paid)
- Coqui/XTTS (local, open source)
- Cloud providers (Google, Azure, Amazon Polly)

### 8.4 Voice Characteristics

User can customize:
- Voice selection (from available options)
- Speech rate
- Pitch (if supported)

### 8.5 Responsiveness & Latency

For voice conversations to feel natural, the assistant must minimize the delay between the user finishing their sentence and the assistant beginning to respond. This is a critical UX concern.

**Key latency targets** *(to be refined during prototyping)*:
- **Time to first audio**: The assistant should begin speaking within ~1-2 seconds of the user finishing. This requires streaming LLM responses and starting TTS before the full response is generated.
- **Streaming pipeline**: User speech → STT → LLM (streaming) → TTS (incremental) → audio output. Each stage should begin processing as soon as partial input is available, not wait for the previous stage to fully complete.
- **Face feedback**: While the LLM is generating, the face should immediately transition to a "thinking" state so the user knows they were heard.

### 8.6 Interruption Handling

What happens when the user starts speaking while the assistant is talking? This is a common and unavoidable scenario in voice interactions.

**Intended behavior** *(implementation details TBD)*:
- The assistant should detect user speech (via VAD) and stop or lower its own audio
- The interrupted response may be discarded or paused for resumption
- The system should distinguish between intentional interruption ("stop, I have a question") and background noise

> This is a hard problem with no perfect solution. The spec acknowledges it as a **day-1 UX requirement** rather than a research item. A basic implementation (stop on user speech detected) should ship with Phase 1, with refinements over time.

---

## 9. Memory & Persistence

### 9.1 Memory Layers

#### Working Memory (Session Context)
- Current conversation history
- Temporary task state
- Cleared on session end (configurable)

#### Short-Term Memory
- Recent conversations (last N days)
- Recent tasks and their status
- Searchable, auto-summarized

#### Long-Term Memory
- User profile (name, preferences, important facts)
- Learned information ("User prefers dark mode", "User's dog is named Max")
- Skills and tool configurations

#### Semantic Memory
- Vector embeddings of past interactions
- Enables "remember when we discussed X?" queries
- Retrieved based on relevance, not just recency

### 9.2 Storage

**Local Storage**:
- SQLite for structured data
- File system for documents/media
- Vector store (e.g., ChromaDB, Qdrant) for semantic search

**Sync (Future)**:
- Optional encrypted cloud backup
- Cross-device sync
- User-controlled, transparent

---

## 10. LLM Integration

### 10.1 Abstraction Layer

The system treats LLMs as interchangeable backends:

```
┌─────────────────────────────────────────┐
│            LLM Router                   │
│  ┌─────────────────────────────────┐   │
│  │     Unified Interface           │   │
│  │  - chat(messages) → response    │   │
│  │  - stream(messages) → chunks    │   │
│  └─────────────────────────────────┘   │
│         │           │           │           │       │
│    ┌────┴───┐  ┌────┴───┐  ┌────┴───┐  ┌────┴───┐  │
│    │Anthropic│  │ OpenAI │  │ Gemini │  │ Ollama │  │
│    │ Adapter │  │ Adapter│  │ Adapter│  │ Adapter│  │
│    └────────┘  └────────┘  └────────┘  └────────┘  │
└─────────────────────────────────────────────────────┘
```

### 10.2 Supported Providers

| Provider | Type | Notes |
|----------|------|-------|
| Anthropic (Claude) | Cloud API | High quality, good for complex tasks |
| OpenAI (GPT) | Cloud API | Wide compatibility |
| Google (Gemini) | Cloud API | Strong multimodal capabilities |
| Ollama | Local | Privacy, offline, no API costs |
| Others | Pluggable | Architecture allows adding new providers |

### 10.3 Fallback Logic

1. Try primary configured provider
2. If failure, try secondary provider
3. If all cloud fails, attempt local model
4. If all fails, inform user gracefully

### 10.4 Model Selection

Users can configure:
- Default model for general use
- Model overrides for specific tasks
- Cost/quality tradeoffs

---

## 11. Security & Privacy

### 11.1 Core Principles

- **Local-First**: Data stays on device by default
- **Minimal Collection**: Only store what's necessary
- **User Control**: User can view, export, delete their data
- **Transparency**: Clear indication of what goes where

### 11.2 Data Classification

| Data Type | Storage | Sync | Notes |
|-----------|---------|------|-------|
| Conversation history | Local | Opt-in | Encrypted if synced |
| User preferences | Local | Opt-in | Non-sensitive config |
| API keys | Local only | Never | Stored securely (keychain/encrypted) |
| Voice recordings | Transient | Never | Processed and discarded |
| Documents shown | Local refs | Never | Only paths stored, not content |

### 11.3 API Key Security

- API keys stored in secure system storage where available
- Never logged or transmitted except to respective provider
- User can rotate/revoke at any time

### 11.4 Future: Multi-User Considerations

When adding support for external contacts:
- Explicit allowlisting required
- Separate contexts per external user
- Rate limiting and abuse prevention
- Clear consent flows

---

## 12. Assistant Customization

### 12.1 Personality Configuration

Users can adjust:

| Aspect | Options |
|--------|---------|
| Name | User-defined |
| Appearance | Avatar selection (future: customization) |
| Voice | Selection from available voices |
| Verbosity | Concise ↔ Detailed |
| Formality | Casual ↔ Formal |
| Proactivity | Reactive only ↔ Proactive suggestions |

### 12.2 Behavioral Tuning

- **System Prompt**: Advanced users can customize base prompt
- **Role Emphasis**: Weight toward secretary/friend/teacher
- **Boundaries**: Topics to avoid, preferred interaction patterns

### 12.3 Skills & Tools

Users can:
- Enable/disable built-in tools
- Add custom tools (future)
- Configure tool-specific settings

### 12.4 Presets

Pre-configured combinations for quick setup:
- "Focused Work" - minimal interruptions, task-oriented
- "Learning Session" - teacher mode, detailed explanations
- "Casual Chat" - friendly, conversational

---

## 13. Future Considerations

### 13.1 Planned Enhancements

These are explicitly deferred but captured for future:

- **Native Apps**: Electron/Tauri desktop, mobile apps
- **Cloud Sync**: Encrypted backup and cross-device sync
- **Multi-User**: Other users/assistants can contact yours
- **Advanced Avatar**: 3D rendering, custom characters
- **Proactive Features**: Anticipate needs, surface relevant info
- **Integrations**: Calendar, email, smart home, etc.
- **Plugin System**: Third-party extensions

### 13.2 Research Areas

- Long-term memory management and forgetting
- Multi-modal understanding (images, video)
- Emotional intelligence and rapport building
- Advanced interrupt handling (distinguishing intent, partial response resumption) — basic interruption is covered in section 8.6

### 13.3 Known Limitations (Current Scope)

- Single user only
- Browser-based (no OS-level screen control)
- Internet required for cloud LLMs
- Basic avatar animation

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **ACE** | Project codename (Animated Companion Entity) |
| **Coordination Layer** | Backend services managing state, routing, and LLM communication |
| **Client** | Frontend application running on a device |
| **Screen Occupation** | The concept of assistant "living" on a display |
| **Device Handoff** | Transferring active session from one device to another |
| **Tool** | An atomic, single-purpose action the assistant can invoke (e.g., web search, send email, set timer). Tools have defined inputs and outputs. |
| **Skill** | A higher-level composed behavior that chains multiple tools with its own logic (e.g., "morning briefing" combines calendar + email + weather tools). Skills are future functionality. |
| **Orchestration Loop** | The core agentic cycle: gather context → call LLM → execute tool calls → repeat until final response. Run by the Session Manager. |

---

## Appendix B: Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-10 | Web-first platform strategy | Fastest path to cross-device support |
| 2026-02-10 | Local-first data storage | Privacy, user control, offline capability |
| 2026-02-10 | Python/JS/TS tech stack | Widely used, good ecosystem, team familiarity |
| 2026-02-10 | Simple 2D avatar initially | Avoid premature optimization, iterate based on feedback |
| 2026-02-10 | Browser tab-based screen control | Achievable within browser security model |
| 2026-02-12 | Phase 1 screen control scoped to same-origin content | Browser Same-Origin Policy prevents annotation/manipulation of third-party sites; iframes and ACE-rendered pages provide sufficient capability for initial phase |
| 2026-02-12 | Skip browser extension, go native for cross-app control | Native wrappers (Phase 3) provide OS-level screen control, making a browser extension an unnecessary intermediate step |
| 2026-02-12 | Lightweight coordination layer, heavy client | Coordination layer is stateful middleware (WebSocket + SQLite + API proxy) — runs on a Pi. Browser handles rendering, voice, UI with GPU access |
| 2026-02-12 | Commercial LLMs as primary, local optional | Full offline not a goal. Users can self-host Ollama but Claude/Gemini/etc. are the default path |
| 2026-02-12 | Tool Use promoted to P0 | Tool use is core infrastructure that all roles depend on, not an optional feature |
| 2026-02-12 | Voice interruption is day-1, not research | Basic stop-on-speech is a Phase 1 requirement; advanced handling is research |
| 2026-02-12 | Svelte for client framework | Compiles to minimal JS (Pi-friendly), built-in reactivity and transitions, TypeScript support. Chosen upfront to avoid vanilla-to-framework migration cost. |
| 2026-02-12 | Python + FastAPI for server | First-class LLM SDK support, native WebSocket/async, lightweight enough for Pi |

---

*This is a living document. It will evolve as we learn more during development.*
