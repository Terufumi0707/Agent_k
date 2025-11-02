<template>
  <section class="card chat-container">
    <!-- チャットエリアのタイトルと説明 -->
    <div class="section-title">
      <h3>BayCurrentエージェントとのチャット</h3>
    </div>
    <p class="section-caption">最新の会話が下部に表示されます</p>

    <!-- 送受信したメッセージの一覧。スクロール表示される -->
    <div class="chat-log" ref="chatLog" aria-live="polite">
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="chat-bubble"
        :class="message.role"
      >
        <span v-html="formatMessage(message.content)"></span>
      </div>
    </div>

    <!-- AIからワークフローの提案があった場合に表示するブロック -->
    <div v-if="pendingWorkflow" class="workflow-suggestion info-block info-surface">
      <p class="section-caption suggestion-label">
        提案されたワークフロー候補
      </p>
      <h4 class="suggestion-title">{{ pendingWorkflow.label }}</h4>
      <p class="section-caption suggestion-description">
        {{ pendingWorkflow.description }}
      </p>
      <div class="suggestion-actions">
        <button
          type="button"
          class="primary"
          @click="handleAccept"
          :disabled="loading"
        >
          このワークフローで実行する
        </button>
        <button
          type="button"
          class="secondary"
          @click="handleDecline"
          :disabled="loading"
        >
          別の選択肢を選ぶ
        </button>
      </div>
    </div>

    <!-- タスク完了時の案内メッセージ -->
    <div
      v-if="completionPromptVisible"
      class="completion-prompt info-block info-surface"
      role="status"
    >
      <p class="section-caption prompt-label">タスクが完了しました</p>
      <h4 class="prompt-title">{{ completionPromptMessage }}</h4>
      <div class="prompt-actions">
        <button type="button" class="primary" @click="handleNavigateToCompletion">
          実行完了一覧へ移動
        </button>
        <button type="button" class="secondary" @click="handleStayOnWorkspace">
          このまま画面にとどまる
        </button>
      </div>
    </div>

    <!-- エラーメッセージの表示領域 -->
    <div v-if="error" class="error-banner" role="alert">{{ error }}</div>

    <!-- ユーザーからメッセージを送信するフォーム -->
    <form class="message-form" @submit.prevent="handleSubmit">
      <label class="section-caption message-hint" for="messageInput">
        メッセージを入力後、送信ボタンを押してください
      </label>
      <textarea
        id="messageInput"
        v-model="draft"
        placeholder="こちらにメッセージを入力してください"
        :disabled="loading || !!pendingWorkflow || !activeWorkspace"
      ></textarea>
      <button
        type="submit"
        :disabled="draft.trim().length === 0 || loading || !!pendingWorkflow || !activeWorkspace"
      >
        {{ loading ? "送信中..." : "送信" }}
      </button>
    </form>
  </section>
</template>

<script setup>
// Vue本体から必要な関数を読み込み
import { nextTick, onMounted, ref } from "vue";
// Piniaのstoreをreactiveに参照するための関数
import { storeToRefs } from "pinia";
// 完了画面へ遷移するためにルーターを利用
import { useRouter } from "vue-router";
// チャット関連の定数とストアを読み込み
import { COMPLETION_PROMPT_MESSAGE, useChatStore } from "../stores/chat";
// ワークスペースの状態管理を扱うストア
import { useWorkspaceStore } from "../stores/workspace";

// チャットとワークスペースのストアを初期化
const chatStore = useChatStore();
const workspaceStore = useWorkspaceStore();
const router = useRouter();
// ストアのリアクティブな値を取得
const { activeWorkspace } = storeToRefs(workspaceStore);
const { messages, loading, error, pendingWorkflow, completionPromptVisible } =
  storeToRefs(chatStore);
// 入力中のメッセージを保持
const draft = ref("");
// チャットログDOMを参照してスクロール制御に使う
const chatLog = ref(null);
// 完了案内の文言を定数から利用
const completionPromptMessage = COMPLETION_PROMPT_MESSAGE;

// 改行コードをHTMLの改行タグに置き換えるヘルパー
function formatMessage(text) {
  return text.replace(/\n/g, "<br />");
}

// メッセージ送信処理。送信前に条件をチェックする
async function handleSubmit() {
  if (
    draft.value.trim().length === 0 ||
    loading.value ||
    pendingWorkflow.value ||
    !activeWorkspace.value
  ) {
    return;
  }

  const current = draft.value;
  draft.value = "";
  await chatStore.sendMessage(current);
  await nextTick();
  if (chatLog.value) {
    chatLog.value.scrollTop = chatLog.value.scrollHeight;
  }
}

// 提案されたワークフローを受け入れる処理
async function handleAccept() {
  if (!activeWorkspace.value) {
    return;
  }

  await chatStore.acceptSuggestedWorkflow();
  await nextTick();
  if (chatLog.value) {
    chatLog.value.scrollTop = chatLog.value.scrollHeight;
  }
}

// 提案を断る処理。チャットログを最新に保つ
async function handleDecline() {
  if (!activeWorkspace.value) {
    return;
  }

  await chatStore.declineSuggestedWorkflow();
  await nextTick();
  if (chatLog.value) {
    chatLog.value.scrollTop = chatLog.value.scrollHeight;
  }
}

// 完了一覧画面へ移動する処理
async function handleNavigateToCompletion() {
  await workspaceStore.markActiveWorkspaceCompleted();
  chatStore.dismissCompletionPrompt();
  router.push({ name: "completed-workspaces" });
}

// 完了メッセージを閉じて現在の画面に留まる
function handleStayOnWorkspace() {
  chatStore.dismissCompletionPrompt();
}

// 初回表示時にスクロール位置を一番下にする
onMounted(() => {
  if (chatLog.value) {
    chatLog.value.scrollTop = chatLog.value.scrollHeight;
  }
});
</script>

<style scoped>
/* ワークフロー提案ブロックの余白調整 */
.workflow-suggestion {
  margin-top: 0.5rem;
}

/* 完了案内メッセージの装飾 */
.completion-prompt {
  margin-top: 1rem;
  border: 1px solid rgba(31, 79, 163, 0.18);
  background: linear-gradient(135deg, rgba(31, 79, 163, 0.04), rgba(67, 105, 198, 0.08));
}

/* 完了案内ラベルの強調 */
.prompt-label {
  font-weight: 600;
  color: #1f3d6d;
}

.prompt-title {
  margin: 0.4rem 0 0.75rem 0;
  color: #102449;
  line-height: 1.5;
}

/* 完了案内のボタンを横並びにする */
.prompt-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

/* 完了案内のボタン共通スタイル */
.prompt-actions button {
  border: none;
  border-radius: 12px;
  padding: 0.65rem 1.25rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.2s ease;
}

/* 完了案内のメインボタン */
.prompt-actions button.primary {
  background: #1f4fa3;
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(31, 79, 163, 0.2);
}

/* 完了案内のサブボタン */
.prompt-actions button.secondary {
  background: #e8efff;
  color: #1f3d6d;
}

/* キーボード操作時のフォーカス枠 */
.prompt-actions button:focus-visible {
  outline: 3px solid rgba(31, 79, 163, 0.25);
  outline-offset: 2px;
}

/* ホバー時のアニメーション */
.prompt-actions button:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(31, 79, 163, 0.24);
}

/* 非活性化したボタンの見た目 */
.prompt-actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

/* ワークフロー提案ボタンの並びと見た目 */
.suggestion-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.suggestion-actions button {
  border: none;
  border-radius: 12px;
  padding: 0.65rem 1.25rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.2s ease;
}

/* ワークフロー提案のメインボタン */
.suggestion-actions button.primary {
  background: #1f4fa3;
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(31, 79, 163, 0.2);
}

/* ワークフロー提案のサブボタン */
.suggestion-actions button.secondary {
  background: #e8efff;
  color: #1f3d6d;
}

.suggestion-actions button:focus-visible {
  outline: 3px solid rgba(31, 79, 163, 0.25);
  outline-offset: 2px;
}

.suggestion-actions button:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(31, 79, 163, 0.24);
}

.suggestion-actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}
</style>
