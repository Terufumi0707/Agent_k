<template>
  <div class="workspace-layout">
    <!-- 左側にワークスペース一覧を表示 -->
    <SidebarPanel class="layout-sidebar" />
    <!-- 中央にチャット画面を配置 -->
    <ChatArea class="layout-chat" />
    <!-- 右側にアウトプットやログを表示 -->
    <RightPane class="layout-right" />
  </div>
</template>

<script setup>
// 画面を構成する各コンポーネントを読み込み
import SidebarPanel from "../components/SidebarPanel.vue";
import ChatArea from "../components/ChatArea.vue";
import RightPane from "../components/RightPane.vue";
</script>
