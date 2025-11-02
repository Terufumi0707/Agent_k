<template>
  <aside class="card">
    <!-- 最新の生成結果を表示するブロック -->
    <div class="section-title">
      <h3>アウトプット</h3>
    </div>
    <p class="section-caption">最新の生成結果</p>

    <div class="info-block info-surface">
      <p v-if="lastOutput" class="info-text" v-html="formatMessage(lastOutput)"></p>
      <p v-else class="section-caption info-placeholder">
        （ここに最新の応答や生成結果が表示されます）
      </p>
    </div>

    <!-- 提案中のワークフローがある場合の概要表示 -->
    <div v-if="pendingWorkflow" class="info-block info-warning">
      <p class="section-caption info-caption">提案中のワークフロー</p>
      <strong class="info-title">{{ pendingWorkflow.label }}</strong>
      <p class="section-caption info-description">
        {{ pendingWorkflow.description }}
      </p>
    </div>

    <hr />

    <!-- 直近の会話ログを3件まで表示 -->
    <div class="section-title">
      <h3>エージェントログ（直近）</h3>
    </div>
    <p class="section-caption">直近 3 件の会話を確認できます</p>

    <div class="info-block info-surface">
      <div v-for="(message, index) in recentMessages" :key="index" class="log-entry">
        <strong class="log-speaker">{{ message.role === "assistant" ? "AI" : "あなた" }}</strong>
        <p class="section-caption log-message" v-html="formatMessage(message.content)"></p>
      </div>
    </div>
  </aside>
</template>

<script setup>
// Piniaのストアから状態を参照する
import { storeToRefs } from "pinia";
// チャットに関する情報を保持しているストア
import { useChatStore } from "../stores/chat";

const chatStore = useChatStore();
const { lastOutput, recentMessages, pendingWorkflow } = storeToRefs(chatStore);

// 改行をHTMLで表示できるように整形する
function formatMessage(text) {
  return text.replace(/\n/g, "<br />");
}
</script>
