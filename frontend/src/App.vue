<template>
  <div class="chat-page">
    <aside class="left-sidebar">
      <div class="sidebar-top">
        <h1 class="sidebar-title">日程変更エージェント</h1>
        <button type="button" class="feature-link">別機能へ遷移</button>
      </div>

      <div class="sidebar-bottom">
        <p class="history-title">過去のチャット履歴（mock）</p>
        <ul class="history-list">
          <li>2026/04/01 工事日程の確認</li>
          <li>2026/03/30 N番号の問い合わせ</li>
          <li>2026/03/29 変更工事種別の相談</li>
        </ul>
      </div>
    </aside>

    <div class="chat-content">
      <main class="chat-main">
        <p class="welcome-message">
          お手伝いできることはありますか？<br />
          WebエントリIDもしくはN番号、変更工事種別、変更工事日程を教えてください。
        </p>

        <div class="messages" v-if="messages.length">
          <div
            v-for="(message, index) in messages"
            :key="index"
            class="message-row"
            :class="message.role"
          >
            <div class="message-bubble">{{ message.text }}</div>
          </div>
        </div>
      </main>

      <footer class="chat-input-area">
        <input
          v-model="inputText"
          class="chat-input"
          type="text"
          placeholder="質問してみましょう"
          @keydown.enter="sendMessage"
        />
        <button class="send-button" :disabled="!canSend" @click="sendMessage">送信</button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";

const inputText = ref("");
const messages = ref([]);

const canSend = computed(() => inputText.value.trim().length > 0);

const sendMessage = () => {
  const userText = inputText.value.trim();
  if (!userText) {
    return;
  }

  messages.value.push({ role: "user", text: userText });
  messages.value.push({ role: "ai", text: "入力を受け付けました" });
  inputText.value = "";
};
</script>
