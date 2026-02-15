/**
 * Reactive chat state (Svelte 5 runes).
 *
 * Singleton `chatState` owns the message list, connection status, and streaming flag.
 * Components read reactive properties; mutations go through methods.
 *
 * Usage:
 *   import { chatState } from '../stores/connection.svelte';
 *
 *   chatState.connect();                   // open WebSocket
 *   chatState.sendMessage("Hello");        // send user message
 *   chatState.messages                     // ChatMessage[] (reactive)
 *   chatState.connectionState              // 'connected' | 'disconnected' | 'reconnecting'
 *   chatState.isStreaming                  // true while assistant chunks arrive
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

const sessionId = crypto.randomUUID();

function createChatState() {
  // eslint-disable-next-line prefer-const -- $state must use let for reactivity
  let messages = $state<ChatMessage[]>([]);
  let connectionState = $state<ConnectionState>("disconnected");
  let isStreaming = $state(false);

  const socket = new ChatSocket({
    onMessage: handleMessage,
    onStateChange: (state) => {
      connectionState = state;
      if (state === "disconnected" || state === "reconnecting") {
        isStreaming = false;
      }
    },
  });

  function handleMessage(msg: IncomingMessage) {
    if (msg.type === "assistant.response.text") {
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
        payload: { text, sessionId },
      });
    },
  };
}

export const chatState = createChatState();
