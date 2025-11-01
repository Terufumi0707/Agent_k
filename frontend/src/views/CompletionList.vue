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
  padding: 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 820px;
  margin: 0 auto;
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
  padding: 1.1rem 1.25rem;
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(245, 248, 255, 0.95), rgba(255, 255, 255, 0.95));
  border: 1px solid rgba(212, 223, 245, 0.8);
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
  gap: 0.75rem;
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

.actions .primary:focus-visible {
  outline: 3px solid rgba(31, 79, 163, 0.35);
  outline-offset: 2px;
}

@media (max-width: 600px) {
  .completion-page {
    padding: 1.25rem;
  }

  .completed-item .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }

  .actions {
    justify-content: center;
  }

  .actions .primary {
    width: 100%;
  }
}
</style>
