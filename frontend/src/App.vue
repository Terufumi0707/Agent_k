<template>
  <div class="app-shell">
    <header class="agent-header">
      <div>
        <p class="system-label">NDB 内部業務AI</p>
        <h1>日程変更エージェント</h1>
        <p class="tagline">AIが意図を読み取り、状況を整理し、次の一手を一緒に考えます。</p>
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
          <div class="chat-card user">
            <div class="card-label">あなたの依頼</div>
            <p>{{ message || "日程変更の依頼を入力すると、AIが意図を整理してご案内します。" }}</p>
          </div>

          <div class="chat-card ai">
            <div class="card-label">AIの解釈</div>
            <p>{{ interpretationText }}</p>
            <div v-if="questions.length" class="info-badges">
              <span v-for="(question, index) in questions" :key="index" class="badge">{{ question }}</span>
            </div>
          </div>

          <div class="chat-card ai">
            <div class="card-label">AIからの提案</div>
            <p>{{ proposalText }}</p>
            <div class="proposal-actions">
              <button type="button" :disabled="isSubmitting" @click="submit">
                {{ sessionId ? "追加の背景を伝える" : "AIに相談を始める" }}
              </button>
              <button class="secondary" type="button" @click="resetForm">入力をクリア</button>
            </div>
          </div>
        </div>

        <div class="input-panel">
          <label class="input-label" for="message">依頼内容</label>
          <textarea
            id="message"
            v-model="message"
            rows="4"
            placeholder="例: A-12345 工事種別: メイン回線_開通 希望日: 2026-02-10"
          ></textarea>
          <div class="form-row">
            <label class="toggle">
              <input v-model="fetchCurrentOrder" type="checkbox" />
              <span>AIが変更前オーダーの文脈を確認する</span>
            </label>
          </div>
        </div>
      </section>

      <section class="panel stack">
        <details class="panel reasoning-panel">
          <summary>
            <div>
              <h3>AIの思考ステップ</h3>
              <p class="subtle">要約を表示し、必要に応じて詳細を確認できます。</p>
            </div>
            <span class="summary-chip">{{ reasoningSummary }}</span>
          </summary>
          <div class="reasoning-steps">
            <div v-for="(step, index) in reasoningSteps" :key="step.title" class="reasoning-step">
              <div class="step-index">0{{ index + 1 }}</div>
              <div>
                <strong>{{ step.title }}</strong>
                <p>{{ step.description }}</p>
              </div>
            </div>
          </div>
        </details>

        <div class="panel decision-panel">
          <div class="panel-header">
            <div>
              <h3>判断サマリー</h3>
              <p class="subtle">抽出された要素と次の行動を整理しています。</p>
            </div>
            <div class="confidence-indicator" :data-confidence="confidenceLevel">
              <span>確信度</span>
              <strong>{{ confidenceLabel }}</strong>
            </div>
          </div>

          <div class="entity-grid">
            <div>
              <span>主回線 A番号</span>
              <strong>{{ orderInfo?.main_a_number || "未確定" }}</strong>
            </div>
            <div>
              <span>バックアップ A番号</span>
              <strong>{{ orderInfo?.backup_a_number || "未確定" }}</strong>
            </div>
            <div>
              <span>主回線 工事種別</span>
              <strong>{{ orderInfo?.main_work_types?.join(" / ") || "未確定" }}</strong>
            </div>
            <div>
              <span>主回線 工事日</span>
              <strong>{{ orderInfo?.main_work_date || "未確定" }}</strong>
            </div>
            <div>
              <span>バックアップ 工事種別</span>
              <strong>{{ orderInfo?.backup_work_types?.join(" / ") || "未確定" }}</strong>
            </div>
            <div>
              <span>バックアップ 工事日</span>
              <strong>{{ orderInfo?.backup_work_date || "未確定" }}</strong>
            </div>
          </div>

          <div class="next-action">
            <p>{{ nextActionText }}</p>
          </div>
        </div>

        <div class="panel session-panel">
          <h3>セッション状況</h3>
          <div class="session-row">
            <span>session_id</span>
            <strong>{{ sessionId || "未発行" }}</strong>
          </div>
          <div class="session-row">
            <span>不足項目</span>
            <strong>{{ missingFields.join(", ") || "なし" }}</strong>
          </div>
          <div v-if="status" class="status-box">
            <p><strong>最新ステータス:</strong> {{ status }}</p>
            <p v-if="messageText">{{ messageText }}</p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";

const backendBaseUrl = import.meta.env.VITE_BACKEND_BASE_URL || "http://localhost:8000";

const message = ref("");
const fetchCurrentOrder = ref(false);
const sessionId = ref("");
const status = ref("");
const messageText = ref("");
const questions = ref([]);
const missingFields = ref([]);
const orderInfo = ref(null);
const isSubmitting = ref(false);

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
  if (orderInfo.value) {
    return "AI: 必要な要素を整理できました。次は確定に向けた確認をご一緒します。";
  }
  return "AI: 依頼内容を入力いただければ、次の行動案をまとめてご案内します。";
});

const reasoningSummary = computed(() => {
  if (questions.value.length) return "確認事項あり";
  if (orderInfo.value) return "主要要素を抽出済み";
  return "依頼待ち";
});

const reasoningSteps = computed(() => [
  {
    title: "理解",
    description: message.value
      ? "AIが依頼の目的と希望日程を捉えています。"
      : "AIが依頼内容の入力を待っています。"
  },
  {
    title: "推論",
    description: "AIが工事種別と日程の整合性を静かに確認しています。"
  },
  {
    title: "判断",
    description: questions.value.length
      ? "AIが不足要素の確認を優先しています。"
      : "AIが最適な日程変更案を選定しています。"
  },
  {
    title: "提案",
    description: "AIが次に進むための提案を整えています。"
  }
]);

const nextActionText = computed(() => {
  if (status.value === "error") {
    return "AI: 接続状況の確認が必要です。再度状況を共有いただけると助かります。";
  }
  if (questions.value.length) {
    return "AI: 不明点を確認できると、日程変更案を確定できます。";
  }
  if (sessionId.value) {
    return "AI: このまま確定に進む準備が整っています。必要なら追加の背景も教えてください。";
  }
  return "AI: 依頼内容を入力いただければ、次の行動案を提示します。";
});

const resetForm = () => {
  message.value = "";
  fetchCurrentOrder.value = false;
  sessionId.value = "";
  status.value = "";
  messageText.value = "";
  questions.value = [];
  missingFields.value = [];
  orderInfo.value = null;
};

const submit = async () => {
  isSubmitting.value = true;
  try {
    const endpoint = sessionId.value ? "/intake/next" : "/intake/start";
    const payload = {
      message: message.value || null,
      fetch_current_order: fetchCurrentOrder.value
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
    const data = await response.json();
    sessionId.value = data.session_id;
    status.value = data.status;
    messageText.value = data.message;
    questions.value = data.questions || [];
    missingFields.value = data.missing_fields || [];
    orderInfo.value = data.order_info || null;
    message.value = "";
  } catch (error) {
    status.value = "error";
    messageText.value = "通信が不安定なため、もう一度状況を教えてください。";
  } finally {
    isSubmitting.value = false;
  }
};
</script>
