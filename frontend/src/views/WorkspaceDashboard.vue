<template>
  <div class="workspace-layout">
    <SidebarPanel class="layout-sidebar" />
    <ChatArea class="layout-chat" />
    <RightPane class="layout-right" />
  </div>
</template>

<script setup>
import { watch } from "vue";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";
import SidebarPanel from "../components/SidebarPanel.vue";
import ChatArea from "../components/ChatArea.vue";
import RightPane from "../components/RightPane.vue";
import { useWorkspaceStore } from "../stores/workspace";

const workspaceStore = useWorkspaceStore();
const { activeWorkspace } = storeToRefs(workspaceStore);
const router = useRouter();

watch(
  () => ({
    id: activeWorkspace.value?.id,
    status: activeWorkspace.value?.status
  }),
  (current, previous) => {
    if (
      current?.id &&
      previous?.id === current.id &&
      previous.status !== "completed" &&
      current.status === "completed"
    ) {
      router.push({ name: "completed-workspaces" });
    }
  }
);
</script>
