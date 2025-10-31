import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { sendChatMessage } from "../services/api";

export const useChatStore = defineStore("chat", () => {
  const messages = ref([
    {
      role: "assistant",
      content: "こんにちは。BayCurrentエージェントです。どの案件から進めますか？"
    }
  ]);
  const lastOutput = ref("");
  const workflowPath = ref([]);
  const workflowClassification = ref("other");
  const loading = ref(false);
  const error = ref(null);

  const recentMessages = computed(() => messages.value.slice(-3));

  async function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || loading.value) {
      return;
    }

    messages.value.push({ role: "user", content: trimmed });
    loading.value = true;
    error.value = null;

    try {
      const result = await sendChatMessage(trimmed);
      messages.value.push({ role: "assistant", content: result.reply });
      lastOutput.value = result.reply;
      workflowPath.value = result.path;
      workflowClassification.value = result.classification;
    } catch (err) {
      error.value = "応答の取得中に問題が発生しました。しばらくしてから再度お試しください。";
    } finally {
      loading.value = false;
    }
  }

  return {
    messages,
    lastOutput,
    workflowPath,
    workflowClassification,
    recentMessages,
    loading,
    error,
    sendMessage
  };
});
