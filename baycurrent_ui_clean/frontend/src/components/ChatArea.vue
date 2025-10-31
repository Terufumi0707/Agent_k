<template>
  <section class="card chat-container">
    <div class="section-title">
      <h3>BayCurrentエージェントとのチャット</h3>
    </div>
    <p class="section-caption">最新の会話が下部に表示されます</p>

    <div class="chat-log" ref="chatLog">
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="chat-bubble"
        :class="message.role"
      >
        <span v-html="formatMessage(message.content)"></span>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <form class="message-form" @submit.prevent="handleSubmit">
      <label class="section-caption" for="messageInput">
        Enter キーで送信 / Shift + Enter で改行できます
      </label>
      <textarea
        id="messageInput"
        v-model="draft"
        placeholder="こちらにメッセージを入力してください"
        @keydown.enter.exact.prevent="handleSubmit"
        @keydown.enter.shift.exact.stop
      ></textarea>
      <button type="submit" :disabled="draft.trim().length === 0 || loading">
        {{ loading ? "送信中..." : "送信" }}
      </button>
    </form>
  </section>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";
import { storeToRefs } from "pinia";
import { useChatStore } from "../stores/chat";

const chatStore = useChatStore();
const { messages, loading, error } = storeToRefs(chatStore);
const draft = ref("");
const chatLog = ref(null);

function formatMessage(text) {
  return text.replace(/\n/g, "<br />");
}

async function handleSubmit() {
  if (draft.value.trim().length === 0 || loading.value) {
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

onMounted(() => {
  if (chatLog.value) {
    chatLog.value.scrollTop = chatLog.value.scrollHeight;
  }
});
</script>
