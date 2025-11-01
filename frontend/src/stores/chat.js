import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { suggestWorkflow, submitWorkflowSelection } from "../services/api";
import { useWorkspaceStore } from "./workspace";

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
  const pendingWorkflow = ref(null);
  const pendingPrompt = ref("");
  const suggestionMessage = ref("");
  const workspaceStore = useWorkspaceStore();

  const recentMessages = computed(() => messages.value.slice(-3));

  async function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || loading.value) {
      return;
    }

    messages.value.push({ role: "user", content: trimmed });
    await workspaceStore.updateSummaryWithAgentInput(trimmed);
    loading.value = true;
    error.value = null;

    try {
      const result = await suggestWorkflow(trimmed);
      messages.value.push({ role: "assistant", content: result.message });
      pendingWorkflow.value = result.candidate;
      pendingPrompt.value = trimmed;
      suggestionMessage.value = result.message;
      workflowPath.value = [];
      workflowClassification.value = "other";
    } catch (err) {
      error.value = "応答の取得中に問題が発生しました。しばらくしてから再度お試しください。";
    } finally {
      loading.value = false;
    }
  }

  async function executeWorkflowSelection(decision, userMessage) {
    if (!pendingWorkflow.value || !pendingPrompt.value || loading.value) {
      return;
    }

    if (userMessage) {
      messages.value.push({ role: "user", content: userMessage });
      await workspaceStore.updateSummaryWithAgentInput(userMessage);
    }

    loading.value = true;
    error.value = null;

    try {
      const result = await submitWorkflowSelection({
        message: pendingPrompt.value,
        workflow_id: pendingWorkflow.value.id,
        decision
      });

      messages.value.push({ role: "assistant", content: result.reply });
      lastOutput.value = result.reply;
      workflowPath.value = result.path;
      workflowClassification.value = result.classification;
      pendingWorkflow.value = null;
      pendingPrompt.value = "";
      suggestionMessage.value = "";
      await workspaceStore.markActiveWorkspaceCompleted();
    } catch (err) {
      error.value = "ワークフローの実行に失敗しました。時間を置いて再度お試しください。";
    } finally {
      loading.value = false;
    }
  }

  async function acceptSuggestedWorkflow() {
    if (!pendingWorkflow.value) {
      return;
    }

    const userMessage =
      pendingWorkflow.value.id === "schedule_change"
        ? "このワークフローで実行してください。"
        : "その他の対応で進めてください。";

    await executeWorkflowSelection("accept", userMessage);
  }

  async function declineSuggestedWorkflow() {
    if (!pendingWorkflow.value) {
      return;
    }

    await executeWorkflowSelection("decline", "別の選択肢を検討したいです。");
  }

  function resetSession() {
    messages.value = [
      {
        role: "assistant",
        content: "こんにちは。BayCurrentエージェントです。どの案件から進めますか？"
      }
    ];
    lastOutput.value = "";
    workflowPath.value = [];
    workflowClassification.value = "other";
    loading.value = false;
    error.value = null;
    pendingWorkflow.value = null;
    pendingPrompt.value = "";
    suggestionMessage.value = "";
  }

  return {
    messages,
    lastOutput,
    workflowPath,
    workflowClassification,
    recentMessages,
    loading,
    error,
    pendingWorkflow,
    suggestionMessage,
    sendMessage,
    acceptSuggestedWorkflow,
    declineSuggestedWorkflow,
    resetSession
  };
});
