<template>
  <div class="minutes-source-input">
    <label class="minutes-input-label" for="minutes-source-text">テキスト入力</label>
    <textarea
      id="minutes-source-text"
      :value="sourceText"
      class="chat-input chat-input-textarea"
      placeholder="会議メモや文字起こしを入力してください"
      rows="4"
      @input="$emit('update:sourceText', $event.target.value)"
    ></textarea>
    <label class="minutes-input-label" for="minutes-audio-file">音声アップロード</label>
    <input id="minutes-audio-file" type="file" accept="audio/*" class="minutes-audio-input" @change="$emit('audio-change', $event)" />
    <p v-if="audioFileName" class="minutes-audio-filename">{{ audioFileName }}</p>
    <button type="button" class="send-button minutes-generate-button" :disabled="!canGenerate || isSending" @click="$emit('generate')">
      議事録を生成する
    </button>
  </div>
</template>

<script setup>
defineProps({
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
  }
});

defineEmits(["update:sourceText", "audio-change", "generate"]);
</script>
