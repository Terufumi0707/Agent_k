import { computed, ref } from "vue";
import { defineStore } from "pinia";
import {
  createWorkspaceRecord,
  deleteWorkspaceRecord,
  fetchWorkspaces,
  updateWorkspaceRecord
} from "../services/mockWorkspaceDb";

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

export const useWorkspaceStore = defineStore("workspace", () => {
  const workspaces = ref([]);
  const activeWorkspaceId = ref(null);
  const loading = ref(false);
  const error = ref(null);

  const activeWorkspace = computed(() =>
    workspaces.value.find((workspace) => workspace.id === activeWorkspaceId.value) || null
  );

  function setActiveWorkspace(id) {
    activeWorkspaceId.value = id;
  }

  function updateWorkspaceState(updated) {
    const index = workspaces.value.findIndex((workspace) => workspace.id === updated.id);
    if (index === -1) {
      workspaces.value = [...workspaces.value, updated];
    } else {
      const next = [...workspaces.value];
      next.splice(index, 1, updated);
      workspaces.value = next;
    }
    if (!activeWorkspaceId.value) {
      activeWorkspaceId.value = updated.id;
    }
  }

  async function loadWorkspaces() {
    loading.value = true;
    error.value = null;
    try {
      const records = await fetchWorkspaces();
      workspaces.value = records;
      if (!activeWorkspaceId.value && records.length > 0) {
        activeWorkspaceId.value = records[0].id;
      }
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
    return updated;
  }

  async function deleteWorkspace(id) {
    loading.value = true;
    error.value = null;

    try {
      await deleteWorkspaceRecord(id);
      workspaces.value = workspaces.value.filter((workspace) => workspace.id !== id);
      if (activeWorkspaceId.value === id) {
        activeWorkspaceId.value = workspaces.value[0]?.id || null;
      }
    } catch (err) {
      error.value = "ワークスペースの削除に失敗しました。";
      throw err;
    } finally {
      loading.value = false;
    }
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
    deleteWorkspace
  };
});
