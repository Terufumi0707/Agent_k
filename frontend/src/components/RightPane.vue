<template>
  <aside class="card">
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

    <div v-if="pendingWorkflow" class="info-block info-warning">
      <p class="section-caption info-caption">提案中のワークフロー</p>
      <strong class="info-title">{{ pendingWorkflow.label }}</strong>
      <p class="section-caption info-description">
        {{ pendingWorkflow.description }}
      </p>
    </div>

    <hr />

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
import { storeToRefs } from "pinia";
import { useChatStore } from "../stores/chat";

const chatStore = useChatStore();
const { lastOutput, recentMessages, pendingWorkflow } = storeToRefs(chatStore);

function formatMessage(text) {
  return text.replace(/\n/g, "<br />");
}
</script>
