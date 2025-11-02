<template>
  <div class="completion-page card">
    <!-- 完了ワークスペースの見出しと説明 -->
    <div class="section-title">
      <h3>実行完了一覧</h3>
    </div>
    <p class="section-caption">完了したワークスペースの履歴です</p>

    <!-- 完了データがない場合のメッセージ -->
    <div v-if="completedWorkspaces.length === 0" class="empty-state">
      実行完了したワークスペースはまだありません。
    </div>

    <!-- 完了済みワークスペースのリスト表示 -->
    <ul v-else class="completed-list">
      <li v-for="workspace in completedWorkspaces" :key="workspace.id" class="completed-item">
        <div class="header">
          <strong class="title">{{ workspace.title }}</strong>
          <span class="timestamp">{{ formatDateTime(workspace.lastUpdatedAt) }}</span>
        </div>
        <p class="summary">{{ workspace.summary || "要約は登録されていません" }}</p>
        <div class="log-actions">
          <button type="button" class="log-toggle" @click="toggleLog(workspace.id)">
            {{ isExpanded(workspace.id) ? "チャットログを閉じる" : "チャットログを表示" }}
          </button>
        </div>
        <div v-if="isExpanded(workspace.id)" class="transcript">
          <div v-if="workspace.transcript?.length" class="transcript-list">
            <div v-for="(entry, index) in workspace.transcript" :key="index" class="transcript-entry">
              <div class="entry-meta">
                <span class="speaker">{{ entry.role === "assistant" ? "AI" : "あなた" }}</span>
                <span class="entry-time">{{ formatDateTime(entry.timestamp) }}</span>
              </div>
              <p class="entry-message" v-html="formatMessage(entry.content)"></p>
            </div>
          </div>
          <p v-else class="transcript-empty">チャットログは登録されていません。</p>
        </div>
      </li>
    </ul>

    <!-- 一覧画面へ戻る操作ボタン -->
    <div class="actions">
      <button type="button" class="primary" @click="router.push({ name: 'workspace-dashboard' })">
        ワークスペース一覧に戻る
      </button>
    </div>
  </div>
</template>

<script setup>
// 完了一覧表示に必要なリアクティブ変数を利用
import { computed, onMounted, ref } from "vue";
// Piniaストアからワークスペース状態を取得
import { storeToRefs } from "pinia";
// 画面遷移に利用するVue Router
import { useRouter } from "vue-router";
import { useWorkspaceStore } from "../stores/workspace";

const workspaceStore = useWorkspaceStore();
const { workspaces } = storeToRefs(workspaceStore);
const router = useRouter();

const expandedLogId = ref(null);

// 初回表示時にデータがなければ取得する
onMounted(() => {
  if (workspaces.value.length === 0) {
    workspaceStore.loadWorkspaces();
  }
});

// 完了済みワークスペースのみを抽出し、更新日時でソート
const completedWorkspaces = computed(() =>
  workspaces.value
    .filter((workspace) => workspace.status === "completed")
    .sort((a, b) => new Date(b.lastUpdatedAt) - new Date(a.lastUpdatedAt))
);

// 展開するログをトグルする
function toggleLog(id) {
  expandedLogId.value = expandedLogId.value === id ? null : id;
}

// 指定IDが展開中かどうかを返す
function isExpanded(id) {
  return expandedLogId.value === id;
}

// 日時文字列をYYYY-MM-DD HH:mm形式で整形
function formatDateTime(timestamp) {
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

// 改行をHTMLに変換して表示に使う
function formatMessage(text) {
  return text.replace(/\n/g, "<br />");
}
</script>

<style scoped>
.completion-page {
  /* 完了一覧カードのレイアウト */
  padding: 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 820px;
  margin: 0 auto;
}

.completed-list {
  /* 完了ワークスペースのリスト */
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.completed-item {
  /* 各完了ワークスペースカード */
  padding: 1.1rem 1.25rem;
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(245, 248, 255, 0.95), rgba(255, 255, 255, 0.95));
  border: 1px solid rgba(212, 223, 245, 0.8);
}

.completed-item .header {
  /* タイトルと更新日時の行 */
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

.log-actions {
  /* ログ表示切り替えボタンの位置調整 */
  margin-top: 0.75rem;
}

.log-toggle {
  border: none;
  background: none;
  color: #1f4fa3;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
}

.log-toggle:focus-visible {
  outline: 3px solid rgba(31, 79, 163, 0.35);
  outline-offset: 3px;
}

.transcript {
  /* チャットログ全体の枠 */
  margin-top: 0.75rem;
  padding: 0.75rem 0.85rem;
  border-radius: 12px;
  background: #f7f9ff;
  border: 1px solid rgba(212, 223, 245, 0.7);
}

.transcript-list {
  /* 各チャットの配列 */
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.transcript-entry {
  /* 1件のチャット内容 */
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.entry-meta {
  /* 発言者と時刻 */
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #7b879c;
}

.speaker {
  font-weight: 600;
  color: #1f3d6d;
}

.entry-message {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.5;
  color: #394563;
}

.transcript-empty {
  margin: 0;
  font-size: 0.85rem;
  color: #4b587a;
}

.empty-state {
  /* 完了データがない場合の案内 */
  padding: 1rem;
  text-align: center;
  color: #4b587a;
  background: #f0f4ff;
  border-radius: 12px;
}

.actions {
  /* 画面下部のボタン行 */
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
    /* モバイル時は余白を調整 */
    padding: 1.25rem;
  }

  .completed-item .header {
    /* スマホでは縦並びにする */
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
