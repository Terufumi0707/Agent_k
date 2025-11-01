<template>
  <div class="workspace-layout">
    <SidebarPanel class="layout-sidebar" />
    <ChatArea class="layout-chat" />
    <RightPane class="layout-right" />
  </div>
</template>

<script setup>
import SidebarPanel from "../components/SidebarPanel.vue";
import ChatArea from "../components/ChatArea.vue";
import RightPane from "../components/RightPane.vue";
</script>
