import { computed, ref } from "vue";
import { defineStore } from "pinia";
import {
  createWorkspaceRecord,
  deleteWorkspaceRecord,
  fetchWorkspaces,
  updateWorkspaceRecord
} from "../services/workspaces";
import { DEFAULT_GREETING_MESSAGE } from "../constants/chat";

function buildSummary(text) {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (!normalized) {
    return "";
  }
  if (normalized.length <= 60) {
    return normalized;
  }
  return `${normalized.slice(0, 57)}...`;
}

function getDefaultTitle(count) {
  return `ワークスペース #${String(count + 1).padStart(2, "0")}`;
}

function createTranscriptEntry(role, content, timestamp) {
  return {
    role,
    content,
    timestamp: timestamp ? new Date(timestamp).toISOString() : new Date().toISOString()
  };
}

function ensureTranscript(record) {
  if (Array.isArray(record.transcript) && record.transcript.length > 0) {
    return record.transcript;
  }
  return [createTranscriptEntry("assistant", DEFAULT_GREETING_MESSAGE, record.lastUpdatedAt)];
}

export const useWorkspaceStore = defineStore("workspace", () => {
  const workspaces = ref([]);
  const activeWorkspaceId = ref(null);
  const loading = ref(false);
  const error = ref(null);

  const activeWorkspace = computed(() =>
    workspaces.value.find((workspace) => workspace.id === activeWorkspaceId.value) || null
  );

  function ensureActiveWorkspaceSelection() {
    const current = workspaces.value.find(
      (workspace) => workspace.id === activeWorkspaceId.value && workspace.status !== "completed"
    );
    if (current) {
      activeWorkspaceId.value = current.id;
      return;
    }
    const candidate = workspaces.value.find((workspace) => workspace.status !== "completed");
    activeWorkspaceId.value = candidate?.id ?? null;
  }

  function setActiveWorkspace(id) {
    const target = workspaces.value.find(
      (workspace) => workspace.id === id && workspace.status !== "completed"
    );
    if (target) {
      activeWorkspaceId.value = target.id;
    } else {
      ensureActiveWorkspaceSelection();
    }
  }

  function updateWorkspaceState(updated) {
    const hydrated = {
      ...updated,
      transcript: ensureTranscript(updated)
    };
    const index = workspaces.value.findIndex((workspace) => workspace.id === hydrated.id);
    if (index === -1) {
      workspaces.value = [...workspaces.value, hydrated];
    } else {
      const next = [...workspaces.value];
      next.splice(index, 1, hydrated);
      workspaces.value = next;
    }
    ensureActiveWorkspaceSelection();
  }

  async function loadWorkspaces() {
    loading.value = true;
    error.value = null;
    try {
      const records = await fetchWorkspaces();
      workspaces.value = records.map((record) => ({
        ...record,
        transcript: ensureTranscript(record)
      }));
      ensureActiveWorkspaceSelection();
    } catch (err) {
      error.value = "ワークスペースの取得に失敗しました。";
    } finally {
      loading.value = false;
    }
  }

  async function createWorkspace() {
    loading.value = true;
    error.value = null;
    try {
      const record = await createWorkspaceRecord({
        title: getDefaultTitle(workspaces.value.length)
      });
      updateWorkspaceState(record);
      activeWorkspaceId.value = record.id;
      return record;
    } catch (err) {
      error.value = "ワークスペースの作成に失敗しました。";
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function updateSummaryWithAgentInput(text) {
    if (!text) {
      return;
    }
    const workspace = activeWorkspace.value;
    if (!workspace) {
      return;
    }

    const summary = buildSummary(text);
    const updated = await updateWorkspaceRecord(workspace.id, {
      summary,
      status: "running"
    });
    updateWorkspaceState(updated);
  }

  async function markActiveWorkspaceCompleted() {
    const workspace = activeWorkspace.value;
    if (!workspace) {
      return;
    }
    if (workspace.status === "completed") {
      return;
    }

    const updated = await updateWorkspaceRecord(workspace.id, {
      status: "completed"
    });
    updateWorkspaceState(updated);
    ensureActiveWorkspaceSelection();
    return updated;
  }

  async function deleteWorkspace(id) {
    loading.value = true;
    error.value = null;

    try {
      await deleteWorkspaceRecord(id);
      workspaces.value = workspaces.value.filter((workspace) => workspace.id !== id);
      ensureActiveWorkspaceSelection();
    } catch (err) {
      error.value = "ワークスペースの削除に失敗しました。";
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function appendMessageToActiveWorkspace(message) {
    const workspace = activeWorkspace.value;
    if (!workspace) {
      return;
    }

    const transcript = [
      ...ensureTranscript(workspace),
      createTranscriptEntry(message.role, message.content, message.timestamp)
    ];

    const updated = await updateWorkspaceRecord(workspace.id, {
      transcript
    });
    updateWorkspaceState(updated);
    return updated;
  }

  return {
    workspaces,
    activeWorkspaceId,
    activeWorkspace,
    loading,
    error,
    loadWorkspaces,
    createWorkspace,
    setActiveWorkspace,
    updateSummaryWithAgentInput,
    markActiveWorkspaceCompleted,
    deleteWorkspace,
    appendMessageToActiveWorkspace
  };
});
