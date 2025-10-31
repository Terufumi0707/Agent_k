<template>
  <div class="app-shell">
    <header class="card" style="margin: 1.5rem;">
      <h1 style="margin: 0 0 0.25rem 0;">BayCurrent AIエージェント</h1>
      <p class="section-caption">業務エージェントとの対話とワークフローの状況を確認できます</p>
    </header>
    <main class="app-content">
      <SidebarPanel />
      <ChatArea />
      <RightPane />
    </main>
  </div>
</template>

<script setup>
import SidebarPanel from "./components/SidebarPanel.vue";
import ChatArea from "./components/ChatArea.vue";
import RightPane from "./components/RightPane.vue";
</script>
