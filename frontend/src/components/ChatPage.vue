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
          <li v-for="(item, index) in visibleHistoryItems" :key="`${item}-${index}`">
            {{ item }}
          </li>
        </ul>
        <button
          v-if="shouldShowHistoryToggle"
          type="button"
          class="history-toggle"
          @click="toggleHistory"
        >
          {{ historyToggleLabel }}
        </button>
      </div>
    </aside>

    <div class="chat-content">
      <header class="auth-header">
        <div class="auth-user-info">
          <p class="auth-user-name">{{ authDisplayName }}</p>
          <p class="auth-user-meta" v-if="authDisplayEmail">{{ authDisplayEmail }}</p>
          <p class="auth-user-meta" v-else-if="authDisplaySub">{{ authDisplaySub }}</p>
        </div>
        <button type="button" class="logout-button" @click="handleLogout">ログアウト</button>
      </header>

      <main class="chat-main">
        <p class="welcome-message">
          お手伝いできることはありますか？<br />
          WebエントリIDもしくはN番号、変更工事種別、変更工事日程を教えてください。
        </p>

        <div
          v-if="progressLogs.length || currentPhase || streamError || isSending"
          class="progress-panel"
        >
          <p class="progress-title">進捗</p>
          <p v-if="isSending && !currentPhase" class="progress-current">
            処理を開始しています...
          </p>
          <p v-if="currentPhase" class="progress-current">{{ currentPhase }}</p>
          <ul v-if="progressLogs.length" class="progress-list">
            <li v-for="(log, index) in progressLogs" :key="index">
              <span class="progress-phase">{{ log.phase }}</span>
              <span class="progress-detail">{{ log.detail }}</span>
            </li>
          </ul>
          <p v-if="streamError" class="progress-error">{{ streamError }}</p>
        </div>

        <div class="messages" v-if="messages.length">
          <div
            v-for="(message, index) in messages"
            :key="index"
            class="message-row"
            :class="message.role"
          >
            <pre class="message-bubble">{{ message.text }}</pre>
          </div>
        </div>
      </main>

      <footer class="chat-input-area">
        <textarea
          ref="inputRef"
          v-model="inputText"
          class="chat-input chat-input-textarea"
          :placeholder="placeholderText"
          rows="3"
          @input="handleInput"
          @keydown.enter.exact.prevent="sendMessage"
        ></textarea>
        <button class="send-button" :disabled="!canSend || isSending" @click="sendMessage">送信</button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useAuth0 } from "@auth0/auth0-vue";

const { user, logout } = useAuth0();

const inputText = ref("");
const inputRef = ref(null);
const messages = ref([]);
const isSending = ref(false);
const progressLogs = ref([]);
const currentPhase = ref("");
const streamError = ref("");
const sessionId = ref(null);

const placeholderText =
  "指示してください";

const historyItems = ref([
  "2026/04/01 工事日程の確認",
  "2026/03/30 N番号の問い合わせ",
  "2026/03/29 変更工事種別の相談",
  "2026/03/28 工事希望日の再調整",
  "2026/03/27 連絡先の更新",
  "2026/03/26 工事内容の補足共有",
  "2026/03/25 現地調査日程の確認",
  "2026/03/24 契約内容の再確認",
  "2026/03/23 施工担当者の変更相談",
  "2026/03/22 書類提出期限の確認",
  "2026/03/21 工事時間帯の相談",
  "2026/03/20 追加工事の可否確認"
]);
const historyCollapsed = ref(true);
const historyLimit = 10;

const canSend = computed(() => inputText.value.trim().length > 0);
const shouldShowHistoryToggle = computed(
  () => historyItems.value.length > historyLimit
);
const visibleHistoryItems = computed(() => {
  if (!shouldShowHistoryToggle.value || !historyCollapsed.value) {
    return historyItems.value;
  }
  return historyItems.value.slice(0, historyLimit);
});
const historyToggleLabel = computed(() =>
  historyCollapsed.value ? "履歴をもっと見る" : "履歴を閉じる"
);
const authDisplayName = computed(
  () => user.value?.name || user.value?.nickname || "認証済みユーザー"
);
const authDisplayEmail = computed(() => user.value?.email || "");
const authDisplaySub = computed(() => user.value?.sub || "");

const toggleHistory = () => {
  historyCollapsed.value = !historyCollapsed.value;
};

const handleLogout = () => {
  logout({
    logoutParams: {
      returnTo: window.location.origin
    }
  });
};

const backendBaseUrl = import.meta.env.VITE_BACKEND_BASE_URL
  ? import.meta.env.VITE_BACKEND_BASE_URL.replace(/\/$/, "")
  : "";

const createEntryStreamUrl = backendBaseUrl
  ? `${backendBaseUrl}/api/create_entry/stream`
  : "/api/create_entry/stream";
const createEntryUrl = backendBaseUrl
  ? `${backendBaseUrl}/api/create_entry`
  : "/api/create_entry";

const resizeTextarea = () => {
  const textarea = inputRef.value;
  if (!textarea) {
    return;
  }

  const maxHeight = 200;
  textarea.style.height = "auto";
  const nextHeight = Math.min(textarea.scrollHeight, maxHeight);
  textarea.style.height = `${nextHeight}px`;
  textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
};

const handleInput = () => {
  resizeTextarea();
};

const sendMessage = async () => {
  const userText = inputText.value.trim();
  if (!userText || isSending.value) {
    return;
  }

  progressLogs.value = [];
  currentPhase.value = "";
  streamError.value = "";

  messages.value.push({ role: "user", text: userText });
  inputText.value = "";
  isSending.value = true;
  await nextTick();
  resizeTextarea();

  const handleSseEvent = (eventBlock) => {
    const lines = eventBlock.split(/\r?\n/);
    let eventType = "message";
    let dataPayload = null;

    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventType = line.replace("event:", "").trim();
      } else if (line.startsWith("data:")) {
        dataPayload = line.replace("data:", "").trim();
      }
    }

    if (!dataPayload) {
      return;
    }

    let payload = null;
    try {
      payload = JSON.parse(dataPayload);
    } catch (error) {
      console.error("SSE payload parse failed:", error);
      return;
    }

    if (eventType === "phase") {
      currentPhase.value = payload.detail ?? payload.phase ?? "";
      progressLogs.value.push({
        phase: payload.phase ?? "",
        detail: payload.detail ?? ""
      });
    } else if (eventType === "done") {
      sessionId.value = payload.session_id ?? sessionId.value;
    } else if (eventType === "error") {
      streamError.value = payload.error ?? "ストリーミングでエラーが発生しました。";
      messages.value.push({
        role: "ai",
        text: "エラーが発生しました。時間をおいて再度お試しください。"
      });
    }
  };

  const streamPromise = (async () => {
    try {
      const response = await fetch(createEntryStreamUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ prompt: userText, session_id: sessionId.value })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      if (!response.body) {
        throw new Error("ReadableStream is not supported in this environment.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split(/\r?\n\r?\n/);
        buffer = events.pop() ?? "";
        for (const eventBlock of events) {
          if (eventBlock.trim()) {
            handleSseEvent(eventBlock.trim());
          }
        }
      }

      if (buffer.trim()) {
        handleSseEvent(buffer.trim());
      }
    } catch (error) {
      console.error("create_entry stream request failed:", error);
      streamError.value = "ストリーミングの接続に失敗しました。";
    }
  })();

  const resultPromise = (async () => {
    try {
      const response = await fetch(createEntryUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ prompt: userText, session_id: sessionId.value })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      sessionId.value = data.session_id ?? sessionId.value;
      messages.value.push({ role: "ai", text: data.result ?? "" });
    } catch (error) {
      console.error("create_entry request failed:", error);
      messages.value.push({
        role: "ai",
        text: "エラーが発生しました。時間をおいて再度お試しください。"
      });
    }
  })();

  await Promise.allSettled([streamPromise, resultPromise]);
  isSending.value = false;
};

onMounted(() => {
  resizeTextarea();
});

watch(inputText, () => {
  nextTick(() => {
    resizeTextarea();
  });
});
</script>
