<!--
  MessageBubble component.

  Renders a single chat message. User messages align right (blue),
  assistant messages align left (dark gray). Content is plain text (auto-escaped).

  Props: { message: ChatMessage }
-->
<script lang="ts">
  import type { ChatMessage } from "../stores/connection.svelte";

  let { message }: { message: ChatMessage } = $props();
</script>

<div class="bubble-row" class:user={message.role === "user"}>
  <div
    class="bubble"
    class:bubble-user={message.role === "user"}
    class:bubble-assistant={message.role === "assistant"}
  >
    {message.content}
  </div>
</div>

<style>
  .bubble-row {
    display: flex;
  }
  .bubble-row.user {
    justify-content: flex-end;
  }
  .bubble {
    max-width: 75%;
    padding: 0.6rem 1rem;
    border-radius: 1rem;
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.4;
  }
  .bubble-user {
    background: #2563eb;
    color: #fff;
    border-bottom-right-radius: 0.25rem;
  }
  .bubble-assistant {
    background: #374151;
    color: #e5e7eb;
    border-bottom-left-radius: 0.25rem;
  }
</style>
