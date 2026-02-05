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
            <div class="message-bubble" v-if="message.mode === 'text'">{{ message.text }}</div>

            <div class="message-bubble formatted-result" v-else>
              <section class="result-section">
                <h3>識別子情報</h3>
                <ul class="result-list">
                  <li v-for="item in message.formatted.identifiers" :key="item.label">
                    <span class="label">{{ item.label }}：</span>
                    <span>{{ item.value }}</span>
                    <span v-if="item.needsAttention" class="attention">※要確認</span>
                    <p v-if="item.evidence" class="evidence">判断根拠：{{ item.evidence }}</p>
                    <p v-if="item.needsAttention" class="confidence">信頼度：{{ item.confidenceLabel }}</p>
                  </li>
                </ul>
              </section>

              <section class="result-section">
                <h3>工事種別ごとの情報</h3>
                <div v-if="message.formatted.constructionTypes.length" class="construction-list">
                  <article
                    v-for="(constructionType, blockIndex) in message.formatted.constructionTypes"
                    :key="`type-${blockIndex}`"
                    class="construction-card"
                  >
                    <p><span class="label">工事種別：</span>{{ constructionType.normalizedName }}</p>
                    <p v-if="constructionType.originalExpression">
                      <span class="label">原文表現：</span>{{ constructionType.originalExpression }}
                    </p>
                    <ul class="result-list">
                      <li v-for="schedule in constructionType.schedules" :key="schedule.priority">
                        <span class="label">{{ schedule.priorityLabel }}：</span>
                        <span>{{ schedule.date }}</span>
                        <span>　</span>
                        <span>{{ schedule.timeSlot }}</span>
                        <span v-if="schedule.needsAttention" class="attention">※要確認</span>
                        <p v-if="schedule.evidence" class="evidence">判断根拠：{{ schedule.evidence }}</p>
                        <p v-if="schedule.needsAttention" class="confidence">信頼度：{{ schedule.confidenceLabel }}</p>
                      </li>
                    </ul>
                  </article>
                </div>
                <p v-else class="empty-text">工事種別情報はありません。</p>
              </section>
            </div>
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
        <button class="send-button" :disabled="!canSend || isSending" @click="sendMessage">送信</button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";

const PRIORITY_LABELS = {
  1: "第一希望",
  2: "第二希望",
  3: "第三希望",
  4: "第四希望",
  5: "第五希望"
};

const inputText = ref("");
const messages = ref([]);
const isSending = ref(false);

const canSend = computed(() => inputText.value.trim().length > 0);

const backendBaseUrl = import.meta.env.VITE_BACKEND_BASE_URL
  ? import.meta.env.VITE_BACKEND_BASE_URL.replace(/\/$/, "")
  : "";

const createEntryUrl = backendBaseUrl ? `${backendBaseUrl}/api/create_entry` : "/api/create_entry";

const getConfidenceLabel = (confidence) => {
  if (typeof confidence !== "number") {
    return "低";
  }

  if (confidence === 1.0) {
    return "確定";
  }

  if (confidence >= 0.8) {
    return "高";
  }

  if (confidence >= 0.6) {
    return "中";
  }

  return "低";
};

const formatIdentifier = (label, item) => {
  const isObject = item && typeof item === "object";
  const confidence = isObject ? item.confidence : undefined;
  const needsAttention = typeof confidence === "number" && confidence < 0.8;

  return {
    label,
    value: isObject && item.value !== null && item.value !== undefined ? item.value : "未記載",
    needsAttention,
    confidenceLabel: getConfidenceLabel(confidence),
    evidence: needsAttention && isObject && item.evidence ? item.evidence : ""
  };
};

const formatSchedule = (schedule) => {
  const isObject = schedule && typeof schedule === "object";
  const confidence = isObject ? schedule.confidence : undefined;
  const needsAttention = typeof confidence === "number" && confidence < 0.8;

  return {
    priority: isObject ? schedule.priority : undefined,
    priorityLabel: PRIORITY_LABELS[isObject ? schedule.priority : undefined] ?? "希望日程",
    date: isObject && schedule.date !== null && schedule.date !== undefined ? schedule.date : "未指定",
    timeSlot:
      isObject && schedule.time_slot !== null && schedule.time_slot !== undefined
        ? schedule.time_slot
        : "未指定",
    needsAttention,
    confidenceLabel: getConfidenceLabel(confidence),
    evidence: needsAttention && isObject && schedule.evidence ? schedule.evidence : ""
  };
};

const formatConstructionType = (item) => {
  const isObject = item && typeof item === "object";
  const preferredDates =
    isObject && Array.isArray(item.preferred_dates) ? item.preferred_dates.map(formatSchedule) : [];

  preferredDates.sort((a, b) => {
    if (typeof a.priority !== "number") {
      return 1;
    }

    if (typeof b.priority !== "number") {
      return -1;
    }

    return a.priority - b.priority;
  });

  return {
    normalizedName:
      isObject && item.normalized_type !== null && item.normalized_type !== undefined
        ? item.normalized_type
        : "未記載",
    originalExpression:
      isObject && item.original_expression !== null && item.original_expression !== undefined
        ? item.original_expression
        : "",
    schedules: preferredDates
  };
};

const formatAgentResult = (json) => {
  const identifiers = json && typeof json === "object" ? json.identifiers : undefined;
  const constructionTypes = json && typeof json === "object" ? json.construction_types : undefined;

  return {
    identifiers: [
      formatIdentifier("N番号", identifiers && identifiers.n_number),
      formatIdentifier("WebエントリID", identifiers && identifiers.web_entry_id)
    ],
    constructionTypes: Array.isArray(constructionTypes)
      ? constructionTypes.map(formatConstructionType)
      : []
  };
};

const parseAgentResult = (value) => {
  if (typeof value !== "string") {
    return null;
  }

  try {
    const parsed = JSON.parse(value);
    if (!parsed || typeof parsed !== "object") {
      return null;
    }

    return formatAgentResult(parsed);
  } catch {
    return null;
  }
};

const sendMessage = async () => {
  const userText = inputText.value.trim();
  if (!userText || isSending.value) {
    return;
  }

  messages.value.push({ role: "user", mode: "text", text: userText });
  inputText.value = "";
  isSending.value = true;

  try {
    const response = await fetch(createEntryUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ prompt: userText })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    const formatted = parseAgentResult(data.result ?? "");

    if (formatted) {
      messages.value.push({ role: "ai", mode: "formatted", formatted });
    } else {
      messages.value.push({ role: "ai", mode: "text", text: data.result ?? "" });
    }
  } catch (error) {
    console.error("create_entry request failed:", error);
    messages.value.push({ role: "ai", mode: "text", text: "エラーが発生しました。時間をおいて再度お試しください。" });
  } finally {
    isSending.value = false;
  }
};
</script>
