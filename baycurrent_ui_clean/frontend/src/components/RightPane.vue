<template>
  <aside class="card">
    <div class="section-title">
      <h3>アウトプット</h3>
    </div>
    <p class="section-caption">最新の生成結果</p>

    <div class="card" style="padding: 1rem; background: #f7f9ff;">
      <p v-if="lastOutput" v-html="formatMessage(lastOutput)"></p>
      <p v-else class="section-caption">（ここに最新の応答や生成結果が表示されます）</p>
    </div>

    <hr />

    <div class="section-title">
      <h3>エージェントログ（直近）</h3>
    </div>
    <p class="section-caption">直近 3 件の会話を確認できます</p>

    <div class="card" style="padding: 1rem; background: #f7f9ff;">
      <div v-for="(message, index) in recentMessages" :key="index" style="margin-bottom: 0.75rem;">
        <strong>{{ message.role === "assistant" ? "AI" : "あなた" }}</strong>
        <p class="section-caption" v-html="formatMessage(message.content)"></p>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { storeToRefs } from "pinia";
import { useChatStore } from "../stores/chat";

const chatStore = useChatStore();
const { lastOutput, recentMessages } = storeToRefs(chatStore);

function formatMessage(text) {
  return text.replace(/\n/g, "<br />");
}
</script>
