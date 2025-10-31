<template>
  <div class="workflow-timeline">
    <template v-for="(node, index) in orderedNodes" :key="node.name">
      <div
        class="workflow-step"
        :class="{
          visited: isVisited(node.name),
          active: activeNode === node.name
        }"
      >
        <div class="node">{{ node.short }}</div>
        <div class="label">
          <strong>{{ node.label }}</strong>
          <span>{{ node.description }}</span>
        </div>
      </div>
      <div v-if="index < orderedNodes.length - 1" class="workflow-connector"></div>
    </template>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { storeToRefs } from "pinia";
import { useChatStore } from "../stores/chat";

const chatStore = useChatStore();
const { workflowPath, workflowClassification } = storeToRefs(chatStore);

const orderedNodes = [
  { name: "START", label: "Start", short: "S", description: "ワークフロー開始" },
  { name: "classify_intent", label: "意図判定", short: "1", description: "リクエスト分類" },
  { name: "call_schedule_api", label: "API 呼び出し", short: "2", description: "スケジュール調整" },
  { name: "END", label: "End", short: "E", description: "完了" }
];

const visitedSequence = computed(() => {
  const path = ["START", ...workflowPath.value];
  if (workflowClassification.value === "schedule_change" || workflowPath.value.length > 0) {
    path.push("END");
  }
  return path;
});

const visitedSet = computed(() => new Set(visitedSequence.value));

const activeNode = computed(() => {
  if (workflowPath.value.length === 0) {
    return "START";
  }
  return workflowPath.value[workflowPath.value.length - 1];
});

function isVisited(nodeName) {
  return visitedSet.value.has(nodeName);
}
</script>
