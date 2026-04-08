<template>
  <div class="minutes-review-block">
    <div class="minutes-display-area">
      <p class="minutes-display-title">議事録</p>
      <pre class="minutes-display-text">{{ displayedMinutes }}</pre>
      <div class="minutes-display-actions">
        <button
          type="button"
          class="candidate-button candidate-button-primary"
          :disabled="!minuteCandidates.length"
          @click="$emit('adopt', minuteCandidates[0])"
        >
          採用
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  displayedMinutes: {
    type: String,
    default: ""
  },
  minuteCandidates: {
    type: Array,
    default: () => []
  }
});

defineEmits(["adopt"]);
</script>
