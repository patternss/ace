# ACE WebSocket Protocol

All client-server communication uses WebSocket with JSON messages.

## Envelope Format

Every message is a JSON object with a `type` field. Most messages also have a `payload` field.

```json
{
  "type": "<message_type>",
  "payload": { ... }
}
```

## Design: No Sessions

ACE has no session concept. There is one continuous memory stream per server — like a person, not a chatbot. The client connects, requests recent history, and continues the conversation. Refreshing the page or reconnecting restores the same history.

## Message Types

### Client → Server

| Type | Payload | Status |
|------|---------|--------|
| `user.input.text` | `{ text }` | Implemented (Phase 0.2, updated 1.1) |
| `history.request` | _(none)_ | Implemented (Phase 1.1) |
| `user.input.audio` | `{ transcript?, audioChunk? }` | Defined |
| `client.state.update` | `{ deviceId, capabilities, activeView }` | Defined |
| `session.handoff.request` | `{ targetDeviceId }` | Defined |
| `tool.result` | `{ toolCallId, result, error? }` | Defined |

### Server → Client

| Type | Payload | Status |
|------|---------|--------|
| `assistant.response.text` | `{ text, isPartial }` | Implemented (Phase 0.2, updated 1.1) |
| `history.response` | `{ messages: [{ role, content }, ...] }` | Implemented (Phase 1.1) |
| `assistant.response.audio` | `{ audioChunk, format }` | Defined |
| `assistant.action.display` | `{ contentType, contentUrl, layout }` | Defined |
| `assistant.action.annotate` | `{ action, target, style }` | Defined |
| `assistant.action.tab` | `{ action: open\|close\|focus, url? }` | Defined |
| `tool.request` | `{ toolCallId, toolName, parameters }` | Defined |
| `face.state` | `{ state: idle\|listening\|thinking\|speaking\|presenting }` | Defined |
| `session.handoff.execute` | `{ sessionId, action: acquire\|release }` | Defined |

### Bidirectional

| Type | Payload | Status |
|------|---------|--------|
| `connection.ping` | _(none)_ | Implemented (Phase 0.2) |
| `connection.pong` | _(none)_ | Implemented (Phase 0.2) |
| `error` | `{ code, message, context? }` | Implemented (Phase 0.2) |

## History Flow

On connect (or reconnect), the client sends `history.request`. The server responds with `history.response` containing recent messages from the SQLite database. The client populates the message list and enables input.

```
Client                          Server
  │                               │
  │──── history.request ────────►│
  │                               │  (load recent messages from DB)
  │◄─── history.response ────────│
  │     { messages: [...] }       │
```

## Field Naming

Wire format uses **camelCase** (`isPartial`). The Python server uses snake_case internally and converts automatically via Pydantic aliases.

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_MESSAGE` | Malformed JSON or unknown message type |
| `INVALID_PAYLOAD` | Message type recognized but payload validation failed |
| `LLM_ERROR` | LLM provider returned an error or is unreachable |

## Implementation

Pydantic models for implemented message types live in `server/protocol.py`. New message types are added there as they are implemented in each phase.

---

*This is a living document. Updated as message types are implemented.*
