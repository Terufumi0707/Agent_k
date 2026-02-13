<template>
  <div class="chat-page" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <aside class="left-sidebar" :class="{ collapsed: isSidebarCollapsed }">
      <div class="sidebar-top">
        <button
          type="button"
          class="sidebar-toggle-button"
          @click="isSidebarCollapsed = !isSidebarCollapsed"
        >
          {{ isSidebarCollapsed ? "＞" : "＜" }}
        </button>
      </div>

      <div v-if="!isSidebarCollapsed" class="sidebar-bottom">
        <section class="sidebar-section">
          <button type="button" class="section-toggle" @click="statusListCollapsed = !statusListCollapsed">
            <span class="history-title">ステータス一覧</span>
            <span class="section-toggle-icon">{{ statusListCollapsed ? "＋" : "－" }}</span>
          </button>

          <template v-if="!statusListCollapsed">
            <p v-if="ordersLoading" class="history-status">読み込み中...</p>
            <p v-else-if="ordersError" class="history-error">{{ ordersError }}</p>

            <template v-else>
              <div
                v-for="status in orderStatuses"
                :key="status"
                class="order-group"
              >
                <button
                  type="button"
                  class="order-group-toggle"
                  @click="toggleStatusSection(status)"
                >
                  <span class="order-group-title">{{ status }}</span>
                  <span class="order-group-icon">{{ isStatusCollapsed(status) ? "＋" : "－" }}</span>
                </button>

                <template v-if="!isStatusCollapsed(status)">
                  <ul class="history-list">
                    <li
                      v-for="order in ordersByStatus[status]"
                      :key="order.id"
                      class="order-item"
                    >
                      <button
                        type="button"
                        class="order-item-button"
                        :class="{ 'order-item-button-active': activeOrderId === order.id }"
                        @click="openOrderExecution(order)"
                      >
                        <p class="order-item-id">{{ order.id }}</p>
                        <p class="order-item-session">session: {{ order.session_id }}</p>
                      </button>
                    </li>
                  </ul>
                  <p v-if="ordersByStatus[status].length === 0" class="history-status">
                    該当オーダーはありません。
                  </p>
                </template>
              </div>
            </template>
          </template>
        </section>

        <section class="sidebar-section">
          <button type="button" class="section-toggle" @click="historySectionCollapsed = !historySectionCollapsed">
            <span class="history-title">依頼一覧</span>
            <span class="section-toggle-icon">{{ historySectionCollapsed ? "＋" : "－" }}</span>
          </button>

          <template v-if="!historySectionCollapsed">
            <div
              v-for="month in requestMonths"
              :key="month"
              class="order-group"
            >
              <button
                type="button"
                class="order-group-toggle"
                @click="toggleRequestMonthSection(month)"
              >
                <span class="order-group-title">{{ month }}</span>
                <span class="order-group-icon">{{ isRequestMonthCollapsed(month) ? "＋" : "－" }}</span>
              </button>

              <template v-if="!isRequestMonthCollapsed(month)">
                <ul class="history-list">
                  <li
                    v-for="request in requestsByMonth[month]"
                    :key="request.id"
                    class="order-item"
                  >
                    <button
                      type="button"
                      class="order-item-button"
                      :class="{ 'order-item-button-active': activeOrderId === request.id }"
                      @click="openRequestExecution(request)"
                    >
                      <p class="order-item-id">{{ request.id }}</p>
                      <p class="order-item-session">{{ request.summary }}</p>
                    </button>
                  </li>
                </ul>
              </template>
            </div>
          </template>
        </section>
      </div>
    </aside>

    <div class="chat-content">
      <TopHeader
        :auth-display-name="authDisplayName"
        :auth-display-email="authDisplayEmail"
        :auth-display-sub="authDisplaySub"
        @logout="handleLogout"
      />

      <main class="chat-main">
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
            <div class="message-bubble" :class="{ 'greeting-bubble': message.isGreeting }">
              <span v-if="message.role === 'ai'" class="ai-icon" aria-hidden="true">🤖</span>
              <span class="message-text">{{ message.text }}</span>
            </div>
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
import { useRoute, useRouter } from "vue-router";
import { useOptionalAuth } from "../auth";
import TopHeader from "./TopHeader.vue";

const { user, logout } = useOptionalAuth();
const router = useRouter();
const route = useRoute();

const inputText = ref("");
const inputRef = ref(null);
const greetingMessage = `日程変更依頼のメール、もしくは変更対象の確認したいオーダーをN番号かWebエントリIDで教えてください。`;

const messages = ref([{ role: "ai", text: greetingMessage, isGreeting: true }]);
const isSending = ref(false);
const progressLogs = ref([]);
const currentPhase = ref("");
const streamError = ref("");
const sessionId = ref(null);
const ordersLoading = ref(false);
const ordersError = ref("");
const orderStatuses = ["DELIVERY", "COORDINATE", "BACKYARD"];
const statusListCollapsed = ref(true);
const statusSectionCollapsed = ref({
  DELIVERY: true,
  COORDINATE: true,
  BACKYARD: true
});
const isSidebarCollapsed = ref(false);
const ordersByStatus = ref({
  DELIVERY: [],
  COORDINATE: [],
  BACKYARD: []
});
const activeOrderId = ref(null);

const placeholderText =
  "指示してください";

const requestsByMonth = {
  "2026年4月": [
    { id: "N-202604-001", summary: "日程変更依頼メールの確認" },
    { id: "WE-202604-014", summary: "変更対象オーダーの内容確認" }
  ],
  "2026年3月": [
    { id: "N-202603-122", summary: "工事希望日の再調整" },
    { id: "WE-202603-089", summary: "変更工事種別の問い合わせ" },
    { id: "N-202603-076", summary: "連絡先更新依頼" }
  ]
};
const requestMonths = Object.keys(requestsByMonth);
const requestMonthCollapsed = ref({
  "2026年4月": false,
  "2026年3月": true
});
const historySectionCollapsed = ref(true);

const canSend = computed(() => inputText.value.trim().length > 0);
const authDisplayName = computed(
  () => user.value?.name || user.value?.nickname || "認証済みユーザー"
);
const authDisplayEmail = computed(() => user.value?.email || "");
const authDisplaySub = computed(() => user.value?.sub || "");

const isRequestMonthCollapsed = (month) => Boolean(requestMonthCollapsed.value[month]);

const toggleRequestMonthSection = (month) => {
  requestMonthCollapsed.value = {
    ...requestMonthCollapsed.value,
    [month]: !isRequestMonthCollapsed(month)
  };
};

const isStatusCollapsed = (status) => Boolean(statusSectionCollapsed.value[status]);

const toggleStatusSection = (status) => {
  statusSectionCollapsed.value = {
    ...statusSectionCollapsed.value,
    [status]: !isStatusCollapsed(status)
  };
};

const openOrderExecution = async (order) => {
  activeOrderId.value = order.id;
  const nextQuery = { ...route.query, order_id: order.id };
  if (order.session_id) {
    nextQuery.session_id = order.session_id;
  }
  await router.push({ name: "chat", query: nextQuery });
  await fetchOrderMessages(order.id);
};

const openRequestExecution = async (request) => {
  activeOrderId.value = request.id;
  const nextQuery = { ...route.query, order_id: request.id };
  await router.push({ name: "chat", query: nextQuery });
  await fetchOrderMessages(request.id);
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
const ordersUrl = backendBaseUrl
  ? `${backendBaseUrl}/api/orders`
  : "/api/orders";
const orderMessagesBaseUrl = backendBaseUrl
  ? `${backendBaseUrl}/api/v1/orders`
  : "/api/v1/orders";

const shouldRetryWithRelativeUrl = (error) => {
  if (!backendBaseUrl) {
    return false;
  }
  return error instanceof TypeError;
};

const fetchWithRelativeFallback = async (primaryUrl, relativeUrl, options) => {
  try {
    return await fetch(primaryUrl, options);
  } catch (error) {
    if (!shouldRetryWithRelativeUrl(error)) {
      throw error;
    }
    console.warn(`Primary API endpoint is unreachable. Falling back to ${relativeUrl}.`, error);
    return fetch(relativeUrl, options);
  }
};

const fetchOrders = async () => {
  ordersLoading.value = true;
  ordersError.value = "";

  try {
    const response = await fetchWithRelativeFallback(ordersUrl, "/api/orders");
    if (!response.ok) {
      throw new Error(`オーダー一覧の取得に失敗しました (${response.status})`);
    }

    const orders = await response.json();
    const groupedOrders = {
      DELIVERY: [],
      COORDINATE: [],
      BACKYARD: []
    };

    for (const order of orders) {
      const status = order.current_status;
      if (status in groupedOrders) {
        groupedOrders[status].push(order);
      }
    }

    for (const status of orderStatuses) {
      groupedOrders[status].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
    }

    ordersByStatus.value = groupedOrders;
  } catch (error) {
    console.error("orders request failed:", error);
    ordersError.value = "オーダー一覧の取得に失敗しました。";
  } finally {
    ordersLoading.value = false;
  }
};

const mapHistoryMessage = (message) => {
  if (message.role === "user") {
    return { role: "user", text: message.content };
  }
  if (message.role === "system") {
    return { role: "ai", text: `[system] ${message.content}` };
  }
  return { role: "ai", text: message.content };
};

const fetchOrderMessages = async (orderId) => {
  try {
    const response = await fetchWithRelativeFallback(
      `${orderMessagesBaseUrl}/${orderId}/messages?limit=200&offset=0`,
      `/api/v1/orders/${orderId}/messages?limit=200&offset=0`
    );
    if (!response.ok) {
      throw new Error(`会話履歴の取得に失敗しました (${response.status})`);
    }
    const historyMessages = await response.json();
    messages.value = historyMessages.map(mapHistoryMessage);
  } catch (error) {
    console.error("order messages request failed:", error);
    messages.value = [{ role: "ai", text: "会話履歴の取得に失敗しました。" }];
  }
};

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
      const response = await fetchWithRelativeFallback(createEntryStreamUrl, "/api/create_entry/stream", {
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
      const response = await fetchWithRelativeFallback(createEntryUrl, "/api/create_entry", {
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
  if (typeof route.query.order_id === "string") {
    activeOrderId.value = route.query.order_id;
  }
  if (typeof route.query.session_id === "string") {
    sessionId.value = route.query.session_id;
  }
  fetchOrders();
  if (activeOrderId.value) {
    fetchOrderMessages(activeOrderId.value);
  }
});

watch(inputText, () => {
  nextTick(() => {
    resizeTextarea();
  });
});
</script>
