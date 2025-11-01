<template>
  <section class="card chat-container">
    <div class="section-title">
      <h3>BayCurrentエージェントとのチャット</h3>
    </div>
    <p class="section-caption">最新の会話が下部に表示されます</p>

    <div class="chat-log" ref="chatLog" aria-live="polite">
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="chat-bubble"
        :class="message.role"
      >
        <span v-html="formatMessage(message.content)"></span>
      </div>
    </div>

    <div v-if="pendingWorkflow" class="workflow-suggestion info-block info-surface">
      <p class="section-caption suggestion-label">
        提案されたワークフロー候補
      </p>
      <h4 class="suggestion-title">{{ pendingWorkflow.label }}</h4>
      <p class="section-caption suggestion-description">
        {{ pendingWorkflow.description }}
      </p>
      <div class="suggestion-actions">
        <button
          type="button"
          class="primary"
          @click="handleAccept"
          :disabled="loading"
        >
          このワークフローで実行する
        </button>
        <button
          type="button"
          class="secondary"
          @click="handleDecline"
          :disabled="loading"
        >
          別の選択肢を選ぶ
        </button>
      </div>
    </div>

    <div v-if="error" class="error-banner" role="alert">{{ error }}</div>

    <form class="message-form" @submit.prevent="handleSubmit">
      <label class="section-caption message-hint" for="messageInput">
        メッセージを入力後、送信ボタンを押してください
      </label>
      <textarea
        id="messageInput"
        v-model="draft"
        placeholder="こちらにメッセージを入力してください"
        :disabled="loading || !!pendingWorkflow || !activeWorkspace"
      ></textarea>
      <button
        type="submit"
        :disabled="draft.trim().length === 0 || loading || !!pendingWorkflow || !activeWorkspace"
      >
        {{ loading ? "送信中..." : "送信" }}
      </button>
    </form>
  </section>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";
import { storeToRefs } from "pinia";
import { useChatStore } from "../stores/chat";
import { useWorkspaceStore } from "../stores/workspace";

const chatStore = useChatStore();
const workspaceStore = useWorkspaceStore();
const { activeWorkspace } = storeToRefs(workspaceStore);
const { messages, loading, error, pendingWorkflow } = storeToRefs(chatStore);
const draft = ref("");
const chatLog = ref(null);

function formatMessage(text) {
  return text.replace(/\n/g, "<br />");
}

async function handleSubmit() {
  if (
    draft.value.trim().length === 0 ||
    loading.value ||
    pendingWorkflow.value ||
    !activeWorkspace.value
  ) {
    return;
  }

  const current = draft.value;
  draft.value = "";
  await chatStore.sendMessage(current);
  await nextTick();
  if (chatLog.value) {
    chatLog.value.scrollTop = chatLog.value.scrollHeight;
  }
}

async function handleAccept() {
  if (!activeWorkspace.value) {
    return;
  }

  await chatStore.acceptSuggestedWorkflow();
  await nextTick();
  if (chatLog.value) {
    chatLog.value.scrollTop = chatLog.value.scrollHeight;
  }
}

async function handleDecline() {
  if (!activeWorkspace.value) {
    return;
  }

  await chatStore.declineSuggestedWorkflow();
  await nextTick();
  if (chatLog.value) {
    chatLog.value.scrollTop = chatLog.value.scrollHeight;
  }
}

onMounted(() => {
  if (chatLog.value) {
    chatLog.value.scrollTop = chatLog.value.scrollHeight;
  }
});
</script>

<style scoped>
.workflow-suggestion {
  margin-top: 0.5rem;
}

.suggestion-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.suggestion-actions button {
  border: none;
  border-radius: 12px;
  padding: 0.65rem 1.25rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.2s ease;
}

.suggestion-actions button.primary {
  background: #1f4fa3;
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(31, 79, 163, 0.2);
}

.suggestion-actions button.secondary {
  background: #e8efff;
  color: #1f3d6d;
}

.suggestion-actions button:focus-visible {
  outline: 3px solid rgba(31, 79, 163, 0.25);
  outline-offset: 2px;
}

.suggestion-actions button:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(31, 79, 163, 0.24);
}

.suggestion-actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
