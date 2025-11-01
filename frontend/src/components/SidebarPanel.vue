<template>
  <aside class="card">
    <div class="section-title">
      <h3>ワークスペース</h3>
      <span class="badge">LangGraph</span>
    </div>
    <button class="new-workspace" type="button" @click="handleCreateWorkspace" :disabled="workspaceLoading">
      {{ workspaceLoading ? "処理中..." : "新規ワークスペース" }}
    </button>
    <p v-if="workspaceError" class="error-text">{{ workspaceError }}</p>
    <div v-if="workspaceLoading && workspaces.length === 0" class="loading-placeholder">
      ワークスペースを読み込んでいます...
    </div>
    <div v-if="runningWorkspaces.length > 0" class="workspace-scroll">
      <ul class="workspace-list">
        <li
          v-for="workspace in runningWorkspaces"
          :key="workspace.id"
          :class="['workspace-item', { active: workspace.id === activeWorkspaceId }]"
        >
          <div class="workspace-row">
            <button type="button" class="workspace-button" @click="selectWorkspace(workspace.id)">
              <div class="workspace-header">
                <span class="workspace-title">{{ workspace.title }}</span>
                <span class="status" :class="workspace.status">
                  {{ workspace.status === "running" ? "実行中" : "実行完了" }}
                </span>
              </div>
              <p class="workspace-summary">
                {{ workspace.summary || "エージェント入力の要約がまだありません" }}
              </p>
            </button>
            <button
              type="button"
              class="delete-button"
              :disabled="workspaceLoading"
              @click.stop="handleDeleteWorkspace(workspace.id)"
            >
              削除
            </button>
          </div>
        </li>
      </ul>
    </div>
    <div v-else class="empty-workspaces">
      実行中のワークスペースはありません。新規作成して開始してください。
    </div>

    <hr />

    <div class="section-title">
      <h3>タスク状況</h3>
    </div>
    <p class="section-caption">LangGraph のワークフロー進行状況</p>

    <WorkflowProgress />
  </aside>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { storeToRefs } from "pinia";
import WorkflowProgress from "./WorkflowProgress.vue";
import { useWorkspaceStore } from "../stores/workspace";
import { useChatStore } from "../stores/chat";

const workspaceStore = useWorkspaceStore();
const chatStore = useChatStore();
const { workspaces, activeWorkspaceId, loading: workspaceLoading, error: workspaceError } =
  storeToRefs(workspaceStore);

const runningWorkspaces = computed(() =>
  workspaces.value.filter((workspace) => workspace.status !== "completed")
);

onMounted(() => {
  workspaceStore.loadWorkspaces();
});

async function handleCreateWorkspace() {
  try {
    await workspaceStore.createWorkspace();
    chatStore.resetSession();
  } catch (err) {
    // error message handled by store state
  }
}

function selectWorkspace(id) {
  workspaceStore.setActiveWorkspace(id);
  chatStore.resetSession();
}

async function handleDeleteWorkspace(id) {
  try {
    const wasActive = id === activeWorkspaceId.value;
    await workspaceStore.deleteWorkspace(id);
    if (wasActive) {
      chatStore.resetSession();
    }
  } catch (err) {
    // error handled via store state
  }
}
</script>

<style scoped>
.new-workspace {
  width: 100%;
  margin: 0.75rem 0 1rem 0;
  padding: 0.6rem 0.9rem;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #1f4fa3, #4369c6);
  color: #ffffff;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
  box-shadow: 0 14px 28px rgba(31, 79, 163, 0.2);
}

.new-workspace:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.new-workspace:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 34px rgba(31, 79, 163, 0.28);
}

.new-workspace:focus-visible {
  outline: 3px solid rgba(255, 255, 255, 0.6);
  outline-offset: 2px;
}

.workspace-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.workspace-item {
  border-radius: 14px;
  background: #f7f9ff;
  border: 1px solid rgba(212, 223, 245, 0.8);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.workspace-item.active {
  background: #ecf2ff;
  border-color: #b8c9f3;
  box-shadow: 0 8px 20px rgba(67, 105, 198, 0.15);
}

.workspace-row {
  display: flex;
  align-items: stretch;
  gap: 0.4rem;
}

.workspace-button {
  flex: 1 1 auto;
  background: transparent;
  border: none;
  text-align: left;
  padding: 0.85rem 1rem;
  cursor: pointer;
  border-radius: 14px;
}

.workspace-button:hover {
  background: rgba(236, 242, 255, 0.6);
}

.workspace-button:focus-visible {
  outline: 3px solid rgba(42, 108, 198, 0.35);
  outline-offset: 2px;
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.workspace-title {
  font-weight: 600;
  color: #1f3d6d;
}

.status {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 8px;
  background: #d9e4ff;
  color: #1f3d6d;
}

.status.completed {
  background: #e4f7e8;
  color: #1f6d3d;
}

.workspace-summary {
  margin: 0;
  color: #4b587a;
  font-size: 0.85rem;
  line-height: 1.4;
}

.delete-button {
  flex: 0 0 auto;
  margin: 0.5rem 0.4rem 0.5rem 0;
  padding: 0.4rem 0.85rem;
  border: none;
  border-radius: 10px;
  background: rgba(255, 105, 97, 0.12);
  color: #c0392b;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  height: fit-content;
  align-self: flex-start;
}

.delete-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-placeholder {
  padding: 0.85rem 1rem;
  border-radius: 12px;
  background: #f0f4ff;
  color: #4b587a;
  font-size: 0.85rem;
}

.error-text {
  color: #c0392b;
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
}

.empty-workspaces {
  padding: 0.85rem 1rem;
  border-radius: 12px;
  background: #f0f4ff;
  color: #4b587a;
  font-size: 0.85rem;
  text-align: center;
}
</style>
