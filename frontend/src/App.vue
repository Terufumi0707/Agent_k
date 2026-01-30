<template>
  <div>
    <h1>日程変更の受付AIエージェント（初期フェーズ）</h1>

    <div class="card">
      <h2>自然言語で入力</h2>
      <p class="helper">
        A番号またはエントリID、工事種別、変更希望日を自然な文章で入力してください。
        例:「A-12345 工事種別: メイン回線_開通 希望日: 2026-02-10」
      </p>
      <textarea
        v-model="message"
        rows="5"
        placeholder="例: ENT-001 工事種別: バックアップ回線_撤去 希望日: 2026-02-12"
      ></textarea>
      <div class="form-row">
        <label>
          <span>変更前オーダー情報を取得</span>
          <input v-model="fetchCurrentOrder" type="checkbox" />
        </label>
      </div>

      <div class="form-row">
        <button type="button" :disabled="isSubmitting" @click="submit">
          {{ sessionId ? "追加入力を送信" : "受付を開始" }}
        </button>
        <button class="secondary" type="button" @click="resetForm">リセット</button>
      </div>

      <div v-if="status" class="status-box">
        <strong>ステータス:</strong> {{ status }}
        <p v-if="messageText">{{ messageText }}</p>
      </div>

      <div v-if="questions.length" class="notice">
        <strong>追加で必要な情報</strong>
        <p>以下の項目を自然文で教えてください。</p>
        <ul class="questions">
          <li v-for="(question, index) in questions" :key="index">{{ question }}</li>
        </ul>
      </div>

      <div v-if="orderInfo" class="order-info">
        <div>
          <strong>主回線 A番号</strong>
          <p>{{ orderInfo.main_a_number }}</p>
        </div>
        <div>
          <strong>バックアップ A番号</strong>
          <p>{{ orderInfo.backup_a_number || "-" }}</p>
        </div>
        <div>
          <strong>主回線 工事種別</strong>
          <p>{{ orderInfo.main_work_types.join(" / ") }}</p>
        </div>
        <div>
          <strong>主回線 工事日</strong>
          <p>{{ orderInfo.main_work_date || "-" }}</p>
        </div>
        <div>
          <strong>バックアップ 工事種別</strong>
          <p>{{ orderInfo.backup_work_types.join(" / ") }}</p>
        </div>
        <div>
          <strong>バックアップ 工事日</strong>
          <p>{{ orderInfo.backup_work_date || "-" }}</p>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>セッション情報</h2>
      <p>session_id: {{ sessionId || "未発行" }}</p>
      <p>不足項目: {{ missingFields.join(", ") || "なし" }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

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
    messageText.value = "通信に失敗しました";
  } finally {
    isSubmitting.value = false;
  }
};
</script>
