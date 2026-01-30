<template>
  <div class="app-shell">
    <header class="agent-header">
      <div>
        <p class="system-label">DM業務高度化PJ</p>
        <h1>日程変更エージェント</h1>
      </div>
      <div class="header-status">
        <span class="status-pill">AIと協働する運用モード</span>
      </div>
    </header>

    <main class="layout-grid">
      <section class="panel agent-chat-panel">
        <div class="panel-header">
          <div>
            <h2>対話パネル</h2>
            <p class="subtle">AIの理解・解釈・提案を構造化して確認できます。</p>
          </div>
          <div class="confidence-indicator" :data-confidence="confidenceLevel">
            <span>確信度</span>
            <strong>{{ confidenceLabel }}</strong>
          </div>
        </div>

        <div class="ai-state">
          <div v-for="(stage, index) in aiStages" :key="stage" class="ai-stage" :data-active="index <= activeStage">
            <span class="stage-dot"></span>
            <span>{{ stage }}</span>
          </div>
        </div>

        <div class="nonblocking-feedback">
          <span class="pulse"></span>
          <p>{{ feedbackMessage }}</p>
        </div>

        <div class="chat-stream">
          <div v-for="(item, index) in sentMessages" :key="`user-${index}`" class="chat-card user">
            <div class="card-label">あなたの依頼</div>
            <p>{{ item }}</p>
          </div>

          <div v-if="hasResponse" class="chat-card ai">
            <div class="card-label">AIの解釈</div>
            <p>{{ interpretationText }}</p>
            <div v-if="questions.length" class="info-badges">
              <span v-for="(question, index) in questions" :key="index" class="badge">{{ question }}</span>
            </div>
          </div>

          <div v-if="hasResponse" class="chat-card ai">
            <div class="card-label">AIからの提案</div>
            <p>{{ proposalText }}</p>
          </div>
        </div>

        <div class="input-panel">
          <label class="input-label" for="message">依頼内容</label>
          <p class="input-hint">
            例: A番号: AB1234567890 工事種別: 端末工事 希望日: 2026-02-10
          </p>
          <textarea
            id="message"
            v-model="message"
            rows="4"
            placeholder="A番号: AB1234567890 工事種別: 端末工事 希望日: 2026-02-10"
          ></textarea>
          <div class="form-row">
            <button type="button" :disabled="!canSubmit" @click="submit">
              {{ isSubmitting ? "送信中..." : "依頼内容を送信" }}
            </button>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";

const backendBaseUrl = (() => {
  const envUrl = import.meta.env.VITE_BACKEND_BASE_URL;
  if (envUrl) return envUrl;
  if (import.meta.env.DEV) {
    return "";
  }
  return window.location.origin;
})();

const message = ref("");
const sentMessages = ref([]);
const sessionId = ref("");
const status = ref("");
const messageText = ref("");
const questions = ref([]);
const missingFields = ref([]);
const isSubmitting = ref(false);
const canSubmit = computed(() => message.value.trim().length > 0 && !isSubmitting.value);

const aiStages = ["理解", "推論", "判断", "提案"];

const normalizedStatus = computed(() => (status.value || "").toLowerCase());

const activeStage = computed(() => {
  if (normalizedStatus.value.includes("propos")) return 3;
  if (normalizedStatus.value.includes("decid")) return 2;
  if (normalizedStatus.value.includes("reason")) return 1;
  if (sessionId.value) return 0;
  return 0;
});

const confidenceLevel = computed(() => {
  if (questions.value.length > 2 || missingFields.value.length > 2) return "low";
  if (questions.value.length || missingFields.value.length) return "medium";
  if (status.value === "error") return "low";
  return "high";
});

const confidenceLabel = computed(() => {
  if (confidenceLevel.value === "low") return "低";
  if (confidenceLevel.value === "medium") return "中";
  return "高";
});

const hasResponse = computed(() => Boolean(messageText.value || questions.value.length || sessionId.value));

const feedbackMessage = computed(() => {
  if (isSubmitting.value) return "AIが最新の内容を整理しています…";
  if (questions.value.length) return "AIが不明点を整理し、確認の準備をしています。";
  if (sessionId.value) return "AIが提案を磨く準備ができています。";
  return "AIが依頼内容の入力を待っています。";
});

const interpretationText = computed(() => {
  if (messageText.value) return `AIは次のように解釈しました: ${messageText.value}`;
  return "AIは意図・主要要素・曖昧さを要約して提示します。";
});

const proposalText = computed(() => {
  if (questions.value.length) {
    return "AI: 追加で教えてほしい内容があります。上の確認事項を共有いただけると、確定案に進めます。";
  }
  if (sessionId.value) {
    return "AI: 受領しました。内容を整理して提案を作成します。";
  }
  return "AI: 依頼内容を入力いただければ、次の行動案をまとめてご案内します。";
});

const submit = async () => {
  if (!canSubmit.value) return;
  isSubmitting.value = true;
  const userMessage = message.value.trim();
  sentMessages.value.push(userMessage);
  try {
    const endpoint = sessionId.value ? "/intake/next" : "/intake/start";
    const payload = {
      message: userMessage
    };
    if (sessionId.value) {
      payload.session_id = sessionId.value;
    }
    const response = await fetch(`${backendBaseUrl}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });
    const contentType = response.headers.get("content-type") || "";
    const rawText = await response.text();
    let data = {};
    if (contentType.includes("application/json") && rawText) {
      try {
        data = JSON.parse(rawText);
      } catch (parseError) {
        status.value = "error";
        messageText.value = "サーバーの応答形式が不正です。管理者に確認してください。";
        questions.value = [];
        missingFields.value = [];
        return;
      }
    }
    if (!response.ok) {
      status.value = "error";
      messageText.value =
        data.message || data.detail || `サーバー応答エラーが発生しました (${response.status})。`;
      questions.value = [];
      missingFields.value = [];
      return;
    }
    sessionId.value = data.session_id;
    status.value = data.status;
    messageText.value = data.message;
    questions.value = data.questions || [];
    missingFields.value = data.missing_fields || [];
    message.value = "";
  } catch (error) {
    status.value = "error";
    messageText.value = "通信が不安定なため、もう一度状況を教えてください。";
  } finally {
    isSubmitting.value = false;
  }
};
</script>
