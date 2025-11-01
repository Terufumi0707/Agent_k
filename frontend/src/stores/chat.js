import { computed, ref, watch } from "vue";
import { defineStore, storeToRefs } from "pinia";
import { suggestWorkflow, submitWorkflowSelection } from "../services/api";
import { DEFAULT_GREETING_MESSAGE } from "../constants/chat";
import { useWorkspaceStore } from "./workspace";

function createChatEntry(role, content, timestamp) {
  return {
    role,
    content,
    timestamp: timestamp ? new Date(timestamp).toISOString() : new Date().toISOString()
  };
}

function getDefaultConversation() {
  return [createChatEntry("assistant", DEFAULT_GREETING_MESSAGE)];
}

export const useChatStore = defineStore("chat", () => {
  const messages = ref(getDefaultConversation());
  const lastOutput = ref("");
  const workflowPath = ref([]);
  const workflowClassification = ref("other");
  const loading = ref(false);
  const error = ref(null);
  const pendingWorkflow = ref(null);
  const pendingPrompt = ref("");
  const suggestionMessage = ref("");

  const workspaceStore = useWorkspaceStore();
  const { activeWorkspaceId, workspaces } = storeToRefs(workspaceStore);

  let currentWorkspaceId = null;

  function findActiveWorkspace() {
    return workspaces.value.find((workspace) => workspace.id === activeWorkspaceId.value) || null;
  }

  function syncMessagesFromWorkspace(workspace) {
    if (workspace?.transcript?.length) {
      messages.value = workspace.transcript.map((entry) => ({ ...entry }));
      const lastAssistant = [...workspace.transcript]
        .reverse()
        .find((entry) => entry.role === "assistant");
      lastOutput.value = lastAssistant?.content ?? "";
    } else if (workspace) {
      messages.value = getDefaultConversation();
      lastOutput.value = "";
    } else {
      messages.value = getDefaultConversation();
      lastOutput.value = "";
    }
  }

  function resetWorkflowState() {
    workflowPath.value = [];
    workflowClassification.value = "other";
    pendingWorkflow.value = null;
    pendingPrompt.value = "";
    suggestionMessage.value = "";
    loading.value = false;
    error.value = null;
  }

  function syncActiveWorkspace(forceReset = false) {
    const workspace = findActiveWorkspace();
    syncMessagesFromWorkspace(workspace);
    if (forceReset || currentWorkspaceId !== workspace?.id) {
      resetWorkflowState();
      currentWorkspaceId = workspace?.id ?? null;
    }
  }

  watch(
    [activeWorkspaceId, workspaces],
    () => {
      syncActiveWorkspace();
    },
    { immediate: true, deep: true }
  );

  const recentMessages = computed(() => messages.value.slice(-3));

  async function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || loading.value) {
      return;
    }

    const workspace = findActiveWorkspace();
    if (!workspace) {
      error.value = "ワークスペースが選択されていません。";
      return;
    }

    const userMessage = createChatEntry("user", trimmed);
    messages.value.push(userMessage);
    await workspaceStore.appendMessageToActiveWorkspace(userMessage);
    await workspaceStore.updateSummaryWithAgentInput(trimmed);
    loading.value = true;
    error.value = null;

    try {
      const result = await suggestWorkflow(trimmed);
      const assistantMessage = createChatEntry("assistant", result.message);
      messages.value.push(assistantMessage);
      await workspaceStore.appendMessageToActiveWorkspace(assistantMessage);
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

    const workspace = findActiveWorkspace();
    if (!workspace) {
      error.value = "ワークスペースが選択されていません。";
      return;
    }

    if (userMessage) {
      const userEntry = createChatEntry("user", userMessage);
      messages.value.push(userEntry);
      await workspaceStore.appendMessageToActiveWorkspace(userEntry);
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

      const assistantMessage = createChatEntry("assistant", result.reply);
      messages.value.push(assistantMessage);
      await workspaceStore.appendMessageToActiveWorkspace(assistantMessage);
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
    syncActiveWorkspace(true);
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
