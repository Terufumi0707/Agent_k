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
        <button type="button" class="new-request-button" @click="startNewRequest">
          ＋ 新しい依頼へ
        </button>

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
                  <span class="order-group-title">{{ statusLabels[status] ?? status }}</span>
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
                        <p class="order-item-summary">{{ order.summary || "要約なし" }}</p>
                        <p class="order-item-meta">更新日: {{ formatCreatedAt(order.updated_at) }}</p>
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
                      <p class="order-item-summary">{{ request.summary || "要約なし" }}</p>
                      <p class="order-item-meta">作成日: {{ formatCreatedAt(request.created_at) }}</p>
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
              <span class="progress-phase">{{ log.phaseLabel }}</span>
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
const statusLabels = {
  DELIVERY: "デリバリー",
  COORDINATE: "コーディネート",
  BACKYARD: "バックヤード"
};
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
const messageFetchRequestId = ref(0);

const placeholderText =
  "指示してください";

const requestsByMonth = ref({});
const requestMonths = computed(() => Object.keys(requestsByMonth.value));
const requestMonthCollapsed = ref({});
const historySectionCollapsed = ref(true);

const phaseLabels = {
  PHASE1_SESSION_READY: "1. 受付",
  PHASE2_INTENT_CLASSIFY: "2. ご要望の理解",
  PHASE0_EXTRACT: "3. 情報整理",
  PHASE0_JUDGE: "4. 内容確認",
  PHASE0_FORMAT: "5. 文面作成",
  PHASE1_SAVE: "6. 保存",
  PHASE3_CHANGE_PREVIEW: "3. 変更プレビュー作成",
  PHASE_QUERY_STATUS: "3. オーダー照会"
};

const getPhaseLabel = (phase) => phaseLabels[phase] ?? "処理中";

const canSend = computed(() => inputText.value.trim().length > 0);
const authDisplayName = computed(
  () => user.value?.name || user.value?.nickname || "認証済みユーザー"
);
const authDisplayEmail = computed(() => user.value?.email || "");
const authDisplaySub = computed(() => user.value?.sub || "");

const formatMonthLabel = (value) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "不明";
  }
  return `${date.getFullYear()}年${date.getMonth() + 1}月`;
};

const formatCreatedAt = (value) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "不明";
  }

  return new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
};

const buildRequestsByMonth = (orders) => {
  const grouped = {};
  for (const order of orders) {
    const month = formatMonthLabel(order.updated_at);
    if (!grouped[month]) {
      grouped[month] = [];
    }
    grouped[month].push(order);
  }
  return grouped;
};

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
  if (request.session_id) {
    nextQuery.session_id = request.session_id;
  }
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

const startNewRequest = async () => {
  messageFetchRequestId.value += 1;
  activeOrderId.value = null;
  sessionId.value = null;
  inputText.value = "";
  progressLogs.value = [];
  currentPhase.value = "";
  streamError.value = "";
  messages.value = [{ role: "ai", text: greetingMessage, isGreeting: true }];

  await router.push({ name: "chat", query: {} });
  await nextTick();
  resizeTextarea();
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
    const monthly = buildRequestsByMonth(orders);
    requestsByMonth.value = monthly;
    const monthState = {};
    requestMonths.value.forEach((month, index) => {
      monthState[month] = index !== 0;
    });
    requestMonthCollapsed.value = monthState;
    return orders;
  } catch (error) {
    console.error("orders request failed:", error);
    ordersError.value = "オーダー一覧の取得に失敗しました。";
    return [];
  } finally {
    ordersLoading.value = false;
  }
};

const refreshOrdersAfterCompletion = async () => {
  const latestOrders = await fetchOrders();
  if (!sessionId.value || !Array.isArray(latestOrders) || latestOrders.length === 0) {
    return;
  }

  const matchedOrder = latestOrders.find((order) => order.session_id === sessionId.value);
  if (!matchedOrder) {
    return;
  }

  activeOrderId.value = matchedOrder.id;
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
  const requestId = messageFetchRequestId.value + 1;
  messageFetchRequestId.value = requestId;

  try {
    const response = await fetchWithRelativeFallback(
      `${orderMessagesBaseUrl}/${orderId}/messages?limit=200&offset=0`,
      `/api/v1/orders/${orderId}/messages?limit=200&offset=0`
    );
    if (!response.ok) {
      throw new Error(`会話履歴の取得に失敗しました (${response.status})`);
    }
    const historyMessages = await response.json();
    if (requestId !== messageFetchRequestId.value) {
      return;
    }
    messages.value = historyMessages.map(mapHistoryMessage);
  } catch (error) {
    if (requestId !== messageFetchRequestId.value) {
      return;
    }
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
      const phase = payload.phase ?? "";
      const detail = payload.detail ?? "";
      const phaseLabel = getPhaseLabel(phase);
      currentPhase.value = detail ? `${phaseLabel}: ${detail}` : phaseLabel;
      progressLogs.value.push({
        phase,
        phaseLabel,
        detail
      });
    } else if (eventType === "done") {
      sessionId.value = payload.session_id ?? sessionId.value;
      messages.value.push({ role: "ai", text: payload.message ?? "" });
      currentPhase.value = "完了しました。";
      void refreshOrdersAfterCompletion();
    } else if (eventType === "error") {
      streamError.value = payload.error ?? "ストリーミングでエラーが発生しました。";
      messages.value.push({
        role: "ai",
        text: "エラーが発生しました。時間をおいて再度お試しください。"
      });
    }
  };

  const requestCreateEntry = async () => {
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
    currentPhase.value = "完了しました。";
    await refreshOrdersAfterCompletion();
  };

  try {
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
      streamError.value = "ストリーミングの接続に失敗したため通常応答へフォールバックします。";
      await requestCreateEntry();
    }
  } catch (error) {
    console.error("create_entry request failed:", error);
    messages.value.push({
      role: "ai",
      text: "エラーが発生しました。時間をおいて再度お試しください。"
    });
  }

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
