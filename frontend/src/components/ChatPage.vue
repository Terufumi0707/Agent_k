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
          <p class="agent-menu-title">エージェント</p>
          <ul class="agent-menu-list">
            <li>
              <button
                type="button"
                class="agent-menu-button"
                :class="{ 'agent-menu-button-active': selectedAgent === 'minutes' }"
                @click="selectedAgent = 'minutes'"
              >
                議事録作成
              </button>
            </li>
            <li>
              <button
                type="button"
                class="agent-menu-button"
                :class="{ 'agent-menu-button-active': selectedAgent === 'other' }"
                @click="selectedAgent = 'other'"
              >
                その他（仮）
              </button>
            </li>
          </ul>
        </section>
      </div>
    </aside>

    <div class="chat-content">
      <TopHeader />

      <main class="chat-main">
        <section class="minutes-workspace">
          <p class="minutes-guide-message">会議の音声ファイルまたはテキストを入力して、議事録を生成してください。</p>
          <div class="minutes-status">
            <span class="minutes-status-label">ステータス</span>
            <span class="status-chip" :class="`status-chip-${workflowStatus.toLowerCase()}`">{{ workflowStatus }}</span>
          </div>

          <div v-if="workflowStatus === STATUS.CREATED" class="minutes-source-input">
            <label class="minutes-input-label" for="minutes-source-text">テキスト入力</label>
            <textarea
              id="minutes-source-text"
              v-model="sourceText"
              class="chat-input chat-input-textarea"
              placeholder="会議メモや文字起こしを入力してください"
              rows="4"
            ></textarea>
            <label class="minutes-input-label" for="minutes-audio-file">音声アップロード</label>
            <input id="minutes-audio-file" type="file" accept="audio/*" class="minutes-audio-input" @change="handleAudioChange" />
            <p v-if="audioFileName" class="minutes-audio-filename">{{ audioFileName }}</p>
            <button type="button" class="send-button minutes-generate-button" :disabled="!canGenerate || isSending" @click="generateMinutes">
              議事録を生成する
            </button>
          </div>

          <div v-else-if="workflowStatus === STATUS.DRAFTING" class="minutes-loading">
            <p class="minutes-loading-text">議事録を作成中です...</p>
          </div>

          <div v-else class="minutes-review-block">
            <div class="minutes-display-area">
              <p class="minutes-display-title">議事録</p>
              <pre class="minutes-display-text">{{ displayedMinutes }}</pre>
            </div>
            <div class="minutes-candidates">
            <p class="minutes-candidates-title">議事録候補</p>
            <ul class="minutes-candidates-list">
              <li v-for="candidate in minuteCandidates" :key="candidate.id" class="minutes-candidate-card">
                <p class="minutes-candidate-text">{{ candidate.text }}</p>
                <div class="minutes-candidate-actions">
                  <button type="button" class="candidate-button candidate-button-primary" @click="adoptCandidate(candidate)">
                    採用
                  </button>
                  <button type="button" class="candidate-button" @click="editCandidate(candidate)">
                    修正
                  </button>
                </div>
              </li>
            </ul>
          </div>
          </div>
        </section>

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

      </main>

      <footer v-if="workflowStatus === STATUS.WAITING_FOR_REVIEW" class="chat-input-area">
        <label class="chat-input-label" for="minutes-instruction">修正指示を入力してください</label>
        <textarea
          id="minutes-instruction"
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
import TopHeader from "./TopHeader.vue";
const router = useRouter();
const route = useRoute();

const inputText = ref("");
const inputRef = ref(null);
const sourceText = ref("");
const audioFileName = ref("");
const greetingMessage = `日程変更依頼のメール、もしくは変更対象の確認したいオーダーをN番号かWebエントリIDで教えてください。`;

const messages = ref([{ role: "ai", text: greetingMessage, isGreeting: true }]);
const isSending = ref(false);
const progressLogs = ref([]);
const currentPhase = ref("");
const streamError = ref("");
const sessionId = ref(null);
const ordersLoading = ref(false);
const ordersError = ref("");
const isSidebarCollapsed = ref(false);
const activeOrderId = ref(null);
const messageFetchRequestId = ref(0);
const selectedAgent = ref("minutes");
const STATUS = {
  CREATED: "CREATED",
  DRAFTING: "DRAFTING",
  WAITING_FOR_REVIEW: "WAITING_FOR_REVIEW"
};
const workflowStatus = ref(STATUS.CREATED);
const adoptedMinutes = ref("");
const minuteCandidates = ref([
  {
    id: 1,
    text: "候補A: プロジェクト進捗を共有し、来週までに課題一覧を更新することを決定。"
  },
  {
    id: 2,
    text: "候補B: 仕様確認を実施し、次回会議で見積の再提示を行う方針で合意。"
  }
]);

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
const canGenerate = computed(() => sourceText.value.trim().length > 0 || Boolean(audioFileName.value));
const latestAiMessage = computed(() =>
  [...messages.value].reverse().find((message) => message.role === "ai" && !message.isGreeting)
);
const displayedMinutes = computed(() => adoptedMinutes.value || latestAiMessage.value?.text || "議事録はまだ生成されていません。");

const adoptCandidate = (candidate) => {
  adoptedMinutes.value = candidate.text;
  workflowStatus.value = STATUS.WAITING_FOR_REVIEW;
};

const editCandidate = (candidate) => {
  inputText.value = `以下の議事録を修正してください:\n${candidate.text}\n修正点: `;
  workflowStatus.value = STATUS.WAITING_FOR_REVIEW;
  nextTick(() => {
    resizeTextarea();
    inputRef.value?.focus();
  });
};

const handleAudioChange = (event) => {
  const file = event.target.files?.[0];
  audioFileName.value = file ? file.name : "";
};

const generateMinutes = () => {
  const trimmedText = sourceText.value.trim();
  const prompt = trimmedText || `音声ファイル: ${audioFileName.value}`;
  sendMessage(prompt);
};
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

const resetProgressState = () => {
  progressLogs.value = [];
  currentPhase.value = "";
  streamError.value = "";
};

const openRequestExecution = async (request) => {
  resetProgressState();
  activeOrderId.value = request.id;
  const nextQuery = { ...route.query, order_id: request.id };
  if (request.session_id) {
    nextQuery.session_id = request.session_id;
  }
  await router.push({ name: "chat", query: nextQuery });
  await fetchOrderMessages(request.id);
};

const startNewRequest = async () => {
  messageFetchRequestId.value += 1;
  activeOrderId.value = null;
  sessionId.value = null;
  inputText.value = "";
  resetProgressState();
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
    const isGreeting = Boolean(message.metadata?.greeting);
    return { role: "ai", text: message.content, isGreeting };
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

const sendMessage = async (promptText = "") => {
  const userText = (promptText || inputText.value).trim();
  if (!userText || isSending.value) {
    return;
  }

  resetProgressState();

  messages.value.push({ role: "user", text: userText });
  workflowStatus.value = STATUS.DRAFTING;
  inputText.value = "";
  isSending.value = true;
  await nextTick();
  resizeTextarea();

  let shouldRefreshOrdersAfterCompletion = false;

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
      if (payload.message) {
        adoptedMinutes.value = payload.message;
      }
      workflowStatus.value = STATUS.WAITING_FOR_REVIEW;
      currentPhase.value = "完了しました。";
      shouldRefreshOrdersAfterCompletion = true;
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
    if (data.result) {
      adoptedMinutes.value = data.result;
    }
    workflowStatus.value = STATUS.WAITING_FOR_REVIEW;
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

      if (shouldRefreshOrdersAfterCompletion) {
        await refreshOrdersAfterCompletion();
      }
    } catch (error) {
      console.error("create_entry stream request failed:", error);
      streamError.value = "ストリーミングの接続に失敗したため通常応答へフォールバックします。";
      await requestCreateEntry();
    }
  } catch (error) {
    console.error("create_entry request failed:", error);
    workflowStatus.value = STATUS.CREATED;
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
    resetProgressState();
    fetchOrderMessages(activeOrderId.value);
  }
});

watch(inputText, () => {
  nextTick(() => {
    resizeTextarea();
  });
});
</script>
