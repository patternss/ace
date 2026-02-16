/**
 * WebSocket transport layer (plain TypeScript, no Svelte dependency).
 *
 * `ChatSocket` manages a WebSocket connection to the server:
 * - connect / disconnect lifecycle
 * - send JSON messages
 * - receive parsed JSON via callback
 * - auto-reconnect with exponential backoff (1s → 30s max)
 *
 * Usage:
 *   const socket = new ChatSocket({
 *     onMessage: (msg) => console.log(msg),
 *     onStateChange: (state) => console.log(state),
 *   });
 *   socket.connect();
 *   socket.send({ type: "user.input.text", payload: { text: "hi" } });
 *   socket.disconnect();
 */

// --- Protocol types (mirrors server/protocol.py, camelCase wire format) ---

export type ConnectionState = "connected" | "disconnected" | "reconnecting";

export interface TextInputPayload {
  text: string;
}

export interface UserInputText {
  type: "user.input.text";
  payload: TextInputPayload;
}

export interface HistoryRequestMessage {
  type: "history.request";
}

export interface TextResponsePayload {
  text: string;
  isPartial: boolean;
}

export interface AssistantResponseText {
  type: "assistant.response.text";
  payload: TextResponsePayload;
}

export interface HistoryMessageItem {
  role: string;
  content: string;
}

export interface HistoryResponsePayload {
  messages: HistoryMessageItem[];
}

export interface HistoryResponseMessage {
  type: "history.response";
  payload: HistoryResponsePayload;
}

export interface ErrorPayload {
  code: string;
  message: string;
  context?: string;
}

export interface ErrorMessage {
  type: "error";
  payload: ErrorPayload;
}

export interface ConnectionPong {
  type: "connection.pong";
}

export type OutgoingMessage = UserInputText | HistoryRequestMessage;
export type IncomingMessage =
  | AssistantResponseText
  | HistoryResponseMessage
  | ErrorMessage
  | ConnectionPong;

// --- ChatSocket ---

export interface ChatSocketOptions {
  onMessage: (msg: IncomingMessage) => void;
  onStateChange: (state: ConnectionState) => void;
}

const BACKOFF_BASE_MS = 1000;
const BACKOFF_MAX_MS = 30000;

export class ChatSocket {
  private ws: WebSocket | null = null;
  private options: ChatSocketOptions;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempt = 0;
  private shouldReconnect = false;

  constructor(options: ChatSocketOptions) {
    this.options = options;
  }

  /** Open connection to the server's /ws endpoint. */
  connect(): void {
    this.shouldReconnect = true;
    this.createSocket();
  }

  /** Send a JSON message. Silently drops if not connected. */
  send(msg: OutgoingMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  /** Close connection and stop auto-reconnect. */
  disconnect(): void {
    this.shouldReconnect = false;
    this.clearReconnectTimer();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.options.onStateChange("disconnected");
  }

  private createSocket(): void {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${location.host}/ws`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempt = 0;
      this.options.onStateChange("connected");
    };

    this.ws.onmessage = (event) => {
      try {
        const msg: IncomingMessage = JSON.parse(event.data);
        this.options.onMessage(msg);
      } catch {
        console.error("Failed to parse WebSocket message:", event.data);
      }
    };

    this.ws.onclose = () => {
      this.ws = null;
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      } else {
        this.options.onStateChange("disconnected");
      }
    };

    this.ws.onerror = () => {
      // onclose fires after onerror, so reconnect is handled there
    };
  }

  private scheduleReconnect(): void {
    this.options.onStateChange("reconnecting");
    const delay = Math.min(
      BACKOFF_BASE_MS * 2 ** this.reconnectAttempt,
      BACKOFF_MAX_MS,
    );
    this.reconnectAttempt++;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.createSocket();
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}
