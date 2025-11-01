<template>
  <div class="completion-page card">
    <div class="section-title">
      <h3>実行完了一覧</h3>
    </div>
    <p class="section-caption">完了したワークスペースの履歴です</p>

    <div v-if="completedWorkspaces.length === 0" class="empty-state">
      実行完了したワークスペースはまだありません。
    </div>

    <ul v-else class="completed-list">
      <li v-for="workspace in completedWorkspaces" :key="workspace.id" class="completed-item">
        <div class="header">
          <strong class="title">{{ workspace.title }}</strong>
          <span class="timestamp">{{ formatDate(workspace.lastUpdatedAt) }}</span>
        </div>
        <p class="summary">{{ workspace.summary || "要約は登録されていません" }}</p>
      </li>
    </ul>

    <div class="actions">
      <button type="button" class="primary" @click="router.push({ name: 'workspace-dashboard' })">
        ワークスペース一覧に戻る
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";
import { useWorkspaceStore } from "../stores/workspace";

const workspaceStore = useWorkspaceStore();
const { workspaces } = storeToRefs(workspaceStore);
const router = useRouter();

onMounted(() => {
  if (workspaces.value.length === 0) {
    workspaceStore.loadWorkspaces();
  }
});

const completedWorkspaces = computed(() =>
  workspaces.value
    .filter((workspace) => workspace.status === "completed")
    .sort((a, b) => new Date(b.lastUpdatedAt) - new Date(a.lastUpdatedAt))
);

function formatDate(timestamp) {
  if (!timestamp) {
    return "";
  }
  const date = new Date(timestamp);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(
    date.getDate()
  ).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(
    date.getMinutes()
  ).padStart(2, "0")}`;
}
</script>

<style scoped>
.completion-page {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.completed-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.completed-item {
  padding: 1rem;
  border-radius: 12px;
  background: #f7f9ff;
}

.completed-item .header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.completed-item .title {
  color: #1f3d6d;
}

.completed-item .timestamp {
  font-size: 0.8rem;
  color: #7b879c;
}

.completed-item .summary {
  margin: 0;
  color: #4b587a;
  font-size: 0.9rem;
  line-height: 1.4;
}

.empty-state {
  padding: 1rem;
  text-align: center;
  color: #4b587a;
  background: #f0f4ff;
  border-radius: 12px;
}

.actions {
  margin-top: auto;
  display: flex;
  justify-content: flex-end;
}

.actions .primary {
  border: none;
  border-radius: 12px;
  padding: 0.65rem 1.5rem;
  font-size: 0.95rem;
  background: linear-gradient(135deg, #1f4fa3, #4369c6);
  color: #ffffff;
  cursor: pointer;
}
</style>
