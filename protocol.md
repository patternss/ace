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

## Message Types

### Client → Server

| Type | Payload | Status |
|------|---------|--------|
| `user.input.text` | `{ text, sessionId }` | Implemented (Phase 0.2) |
| `user.input.audio` | `{ transcript?, audioChunk?, sessionId }` | Defined |
| `client.state.update` | `{ deviceId, capabilities, activeView }` | Defined |
| `session.handoff.request` | `{ targetDeviceId }` | Defined |
| `tool.result` | `{ toolCallId, result, error? }` | Defined |

### Server → Client

| Type | Payload | Status |
|------|---------|--------|
| `assistant.response.text` | `{ text, isPartial, sessionId }` | Implemented (Phase 0.2) |
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

## Field Naming

Wire format uses **camelCase** (`sessionId`, `isPartial`). The Python server uses snake_case internally and converts automatically via Pydantic aliases.

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
