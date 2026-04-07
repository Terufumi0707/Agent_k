<template>
  <div class="proposal-page">
    <TopHeader />

    <form class="proposal-form" @submit.prevent="submitProposal">
      <label v-for="field in fields" :key="field.key" class="field">
        <span>{{ field.label }}</span>
        <textarea
          v-if="field.multiline"
          v-model="form[field.key]"
          :placeholder="field.placeholder"
          rows="3"
          required
        />
        <input
          v-else
          v-model="form[field.key]"
          :placeholder="field.placeholder"
          required
        />
      </label>

      <button type="submit" :disabled="loading">
        {{ loading ? "実行中..." : "提案書を作成" }}
      </button>
    </form>

    <section class="result-panel">
      <p v-if="loading">ローディング中です。提案書作成フローを実行しています...</p>
      <p v-else-if="error" class="error">{{ error }}</p>
      <pre v-else-if="result">{{ JSON.stringify(result, null, 2) }}</pre>
      <p v-else>まだ結果はありません。</p>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import TopHeader from "./TopHeader.vue";

const form = reactive({
  theme: "",
  target_company: "",
  background: "",
  issues: "",
  goal: "",
  additional_requirements: ""
});

const fields = [
  { key: "theme", label: "テーマ", placeholder: "例: 提案活動の標準化", multiline: false },
  { key: "target_company", label: "提案先", placeholder: "例: 株式会社サンプル", multiline: false },
  { key: "background", label: "背景", placeholder: "背景を入力", multiline: true },
  { key: "issues", label: "課題", placeholder: "課題を入力", multiline: true },
  { key: "goal", label: "ゴール", placeholder: "到達したい状態を入力", multiline: true },
  { key: "additional_requirements", label: "補足条件", placeholder: "制約や補足条件を入力", multiline: true }
];

const loading = ref(false);
const error = ref("");
const result = ref(null);

const apiBasePath = (import.meta.env.VITE_API_BASE_PATH || "/api").replace(/\/$/, "");

const endpoint = `${apiBasePath}/minutes/jobs`;

const submitProposal = async () => {
  loading.value = true;
  error.value = "";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        input_type: "transcript",
        transcript: [
          form.theme,
          form.target_company,
          form.background,
          form.issues,
          form.goal,
          form.additional_requirements
        ]
          .filter(Boolean)
          .join("\n")
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    result.value = await response.json();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "不明なエラーが発生しました";
  } finally {
    loading.value = false;
  }
};
</script>
