<template>
  <aside class="card">
    <div class="section-title">
      <h3>ワークスペース</h3>
      <span class="badge">LangGraph</span>
    </div>
    <details class="task-group" open>
      <summary>【進行中】A社提案準備</summary>
      <ul>
        <li>提案シナリオ作成（進行中）</li>
        <li>課題整理（待機）</li>
      </ul>
    </details>
    <details class="task-group">
      <summary>【完了】A社アポイント準備</summary>
      <ul>
        <li>議事体裁作成</li>
        <li>ターゲット課題整理</li>
      </ul>
    </details>
    <details class="task-group">
      <summary>【未着手】B社見積対応</summary>
      <ul>
        <li>案件概要ヒアリング</li>
        <li>構成提案作成</li>
      </ul>
    </details>

    <hr />

    <div class="section-title">
      <h3>タスク状況</h3>
    </div>
    <p class="section-caption">LangGraph のワークフロー進行状況</p>

    <WorkflowProgress />
  </aside>
</template>

<script setup>
import WorkflowProgress from "./WorkflowProgress.vue";
</script>

<style scoped>
ul {
  margin: 0.5rem 0 0 1.5rem;
  padding: 0;
  color: #4b587a;
  font-size: 0.9rem;
}

details {
  margin-bottom: 0.75rem;
  background: #f7f9ff;
  border-radius: 12px;
  padding: 0.6rem 0.85rem;
}

details[open] {
  background: #ecf2ff;
}

summary {
  cursor: pointer;
  font-weight: 600;
}
</style>
