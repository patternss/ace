/**
 * Reactive chat state (Svelte 5 runes).
 *
 * Singleton `chatState` owns the message list, connection status, streaming flag,
 * and history-loaded flag. No sessions — one continuous memory stream.
 *
 * On connect: sends history.request to load recent messages from the server's
 * SQLite database. Input is disabled until history is loaded.
 *
 * Usage:
 *   import { chatState } from '../stores/connection.svelte';
 *
 *   chatState.connect();                   // open WebSocket
 *   chatState.sendMessage("Hello");        // send user message
 *   chatState.messages                     // ChatMessage[] (reactive)
 *   chatState.connectionState              // 'connected' | 'disconnected' | 'reconnecting'
 *   chatState.isStreaming                  // true while assistant chunks arrive
 *   chatState.historyLoaded               // true after history.response received
 *   chatState.disconnect();                // close WebSocket
 */

import {
  ChatSocket,
  type ConnectionState,
  type IncomingMessage,
} from "../websocket";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

function createChatState() {
  // eslint-disable-next-line prefer-const -- $state must use let for reactivity
  let messages = $state<ChatMessage[]>([]);
  let connectionState = $state<ConnectionState>("disconnected");
  let isStreaming = $state(false);
  let historyLoaded = $state(false);

  const socket = new ChatSocket({
    onMessage: handleMessage,
    onStateChange: (state) => {
      connectionState = state;
      if (state === "connected") {
        // Request history on every (re)connect
        historyLoaded = false;
        socket.send({ type: "history.request" });
      } else if (state === "disconnected" || state === "reconnecting") {
        isStreaming = false;
      }
    },
  });

  function handleMessage(msg: IncomingMessage) {
    if (msg.type === "history.response") {
      // Replace messages with history from server
      messages = msg.payload.messages.map((m) => ({
        id: crypto.randomUUID(),
        role: m.role as "user" | "assistant",
        content: m.content,
      }));
      historyLoaded = true;
    } else if (msg.type === "assistant.response.text") {
      const { text, isPartial } = msg.payload;

      if (isPartial) {
        isStreaming = true;
        const last = messages[messages.length - 1];
        if (last?.role === "assistant" && isStreaming) {
          // Append chunk to existing assistant message
          messages[messages.length - 1] = {
            ...last,
            content: last.content + text,
          };
        } else {
          // First chunk — create new assistant message
          messages.push({
            id: crypto.randomUUID(),
            role: "assistant",
            content: text,
          });
        }
      } else {
        // Final complete message — replace assistant message content
        isStreaming = false;
        const last = messages[messages.length - 1];
        if (last?.role === "assistant") {
          messages[messages.length - 1] = { ...last, content: text };
        } else {
          messages.push({
            id: crypto.randomUUID(),
            role: "assistant",
            content: text,
          });
        }
      }
    } else if (msg.type === "error") {
      console.error(
        `Server error [${msg.payload.code}]: ${msg.payload.message}`,
      );
    }
    // connection.pong — ignored (no heartbeat timer)
  }

  return {
    get messages() {
      return messages;
    },
    get connectionState() {
      return connectionState;
    },
    get isStreaming() {
      return isStreaming;
    },
    get historyLoaded() {
      return historyLoaded;
    },

    connect() {
      socket.connect();
    },
    disconnect() {
      socket.disconnect();
    },

    sendMessage(text: string) {
      messages.push({ id: crypto.randomUUID(), role: "user", content: text });
      socket.send({
        type: "user.input.text",
        payload: { text },
      });
    },
  };
}

export const chatState = createChatState();
