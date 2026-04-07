<template>
  <footer class="chat-input-area">
    <label class="chat-input-label" for="minutes-instruction">修正指示を入力してください</label>
    <textarea
      id="minutes-instruction"
      ref="textareaRef"
      :value="inputText"
      class="chat-input chat-input-textarea"
      :placeholder="placeholderText"
      rows="3"
      @input="handleInput"
      @keydown.enter.exact.prevent="$emit('send')"
    ></textarea>
    <button class="send-button" :disabled="!canSend || isSending" @click="$emit('send')">送信</button>
  </footer>
</template>

<script setup>
import { ref } from "vue";

const textareaRef = ref(null);

const emit = defineEmits(["update:input-text", "send", "resize"]);

defineProps({
  inputText: {
    type: String,
    default: ""
  },
  placeholderText: {
    type: String,
    default: ""
  },
  canSend: {
    type: Boolean,
    default: false
  },
  isSending: {
    type: Boolean,
    default: false
  }
});

const handleInput = (event) => {
  emit("update:input-text", event.target.value);
  emit("resize", textareaRef.value);
};

defineExpose({
  textareaRef
});
</script>
