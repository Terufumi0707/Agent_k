<template>
  <div class="progress-panel">
    <p class="progress-title">進捗</p>
    <p v-if="isSending && !currentPhase" class="progress-current">
      処理を開始しています...
    </p>
    <p v-if="currentPhase" class="progress-current">{{ currentPhase }}</p>
    <ul v-if="progressLogs.length" class="progress-list">
      <li v-for="(log, index) in progressLogs" :key="index">
        <span class="progress-phase">{{ log.phaseLabel }}</span>
        <span class="progress-detail">{{ log.detail }}</span>
      </li>
    </ul>
    <p v-if="streamError" class="progress-error">{{ streamError }}</p>
  </div>
</template>

<script setup>
defineProps({
  progressLogs: {
    type: Array,
    default: () => []
  },
  currentPhase: {
    type: String,
    default: ""
  },
  streamError: {
    type: String,
    default: ""
  },
  isSending: {
    type: Boolean,
    default: false
  }
});
</script>
