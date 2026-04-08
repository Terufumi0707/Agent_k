<template>
  <section class="minutes-workspace">
    <p class="minutes-guide-message">会議の音声ファイルまたはテキストを入力して、議事録を生成してください。</p>
    <div class="minutes-status">
      <span class="minutes-status-label">ステータス</span>
      <span class="status-chip" :class="`status-chip-${workflowStatus.toLowerCase()}`">{{ workflowStatus }}</span>
    </div>

    <MinutesInputPanel
      v-if="workflowStatus === statusCreated"
      :source-text="sourceText"
      :audio-file-name="audioFileName"
      :can-generate="canGenerate"
      :is-sending="isSending"
      @update:source-text="$emit('update:source-text', $event)"
      @audio-change="$emit('audio-change', $event)"
      @generate="$emit('generate')"
    />

    <div v-else-if="workflowStatus === statusDrafting" class="minutes-loading">
      <p class="minutes-loading-text">議事録を作成中です...</p>
    </div>

    <MinutesCandidatesPanel
      v-else
      :displayed-minutes="displayedMinutes"
      :minute-candidates="minuteCandidates"
      @adopt="$emit('adopt', $event)"
    />
  </section>
</template>

<script setup>
import MinutesCandidatesPanel from "./MinutesCandidatesPanel.vue";
import MinutesInputPanel from "./MinutesInputPanel.vue";

defineProps({
  workflowStatus: {
    type: String,
    required: true
  },
  statusCreated: {
    type: String,
    required: true
  },
  statusDrafting: {
    type: String,
    required: true
  },
  sourceText: {
    type: String,
    default: ""
  },
  audioFileName: {
    type: String,
    default: ""
  },
  canGenerate: {
    type: Boolean,
    default: false
  },
  isSending: {
    type: Boolean,
    default: false
  },
  displayedMinutes: {
    type: String,
    default: ""
  },
  minuteCandidates: {
    type: Array,
    default: () => []
  }
});

defineEmits(["update:source-text", "audio-change", "generate", "adopt"]);
</script>
