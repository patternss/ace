<!--
  Chat component.

  Full-screen chat UI: header with connection indicator, scrollable message list,
  and text input. Connects WebSocket on mount, disconnects on destroy.
-->
<script lang="ts">
  import { chatState } from "../stores/connection.svelte";
  import MessageBubble from "./MessageBubble.svelte";

  let inputText = $state("");
  let messagesEnd: HTMLDivElement;

  // Connect on mount, disconnect on destroy
  $effect(() => {
    chatState.connect();
    return () => chatState.disconnect();
  });

  // Auto-scroll to bottom when messages change
  $effect(() => {
    // eslint-disable-next-line @typescript-eslint/no-unused-expressions -- reactive dependency
    chatState.messages.length;
    messagesEnd?.scrollIntoView({ behavior: "smooth" });
  });

  function send() {
    const text = inputText.trim();
    if (!text) return;
    chatState.sendMessage(text);
    inputText = "";
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  const statusColor = $derived(
    chatState.connectionState === "connected"
      ? "#22c55e"
      : chatState.connectionState === "reconnecting"
        ? "#f59e0b"
        : "#ef4444",
  );

  const inputDisabled = $derived(chatState.connectionState !== "connected");
  const sendDisabled = $derived(inputDisabled || chatState.isStreaming);
</script>

<div class="chat">
  <header>
    <h1>ACE</h1>
    <span class="status-dot" style="background:{statusColor}"></span>
  </header>

  <div class="messages">
    {#each chatState.messages as message (message.id)}
      <MessageBubble {message} />
    {/each}
    <div bind:this={messagesEnd}></div>
  </div>

  <form class="input-bar" onsubmit={(e) => { e.preventDefault(); send(); }}>
    <input
      type="text"
      placeholder={inputDisabled ? "Disconnected..." : "Type a message..."}
      bind:value={inputText}
      onkeydown={handleKeydown}
      disabled={inputDisabled}
    />
    <button type="submit" disabled={sendDisabled}>Send</button>
  </form>
</div>

<style>
  .chat {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 48rem;
    margin: 0 auto;
  }
  header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #333;
  }
  header h1 {
    font-size: 1.25rem;
    margin: 0;
  }
  .status-dot {
    width: 0.6rem;
    height: 0.6rem;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .input-bar {
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-top: 1px solid #333;
  }
  .input-bar input {
    flex: 1;
    padding: 0.5rem 0.75rem;
    border-radius: 0.5rem;
    border: 1px solid #444;
    background: #1a1a1a;
    color: inherit;
    font-size: 1rem;
    font-family: inherit;
  }
  .input-bar input:disabled {
    opacity: 0.5;
  }
  .input-bar input:focus {
    outline: none;
    border-color: #2563eb;
  }
  .input-bar button {
    padding: 0.5rem 1.25rem;
    border-radius: 0.5rem;
    border: none;
    background: #2563eb;
    color: #fff;
    font-size: 1rem;
    cursor: pointer;
  }
  .input-bar button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
