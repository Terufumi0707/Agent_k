<template>
  <div class="minutes-review-block">
    <div class="minutes-display-area">
      <p class="minutes-display-title">議事録</p>
      <pre class="minutes-display-text">{{ displayedMinutes }}</pre>
    </div>
    <div class="minutes-candidates">
      <p class="minutes-candidates-title">議事録候補</p>
      <ul class="minutes-candidates-list">
        <li v-for="candidate in minuteCandidates" :key="candidate.id" class="minutes-candidate-card">
          <p class="minutes-candidate-text">{{ candidate.text }}</p>
          <div class="minutes-candidate-actions">
            <button type="button" class="candidate-button candidate-button-primary" @click="$emit('adopt', candidate)">
              採用
            </button>
            <button type="button" class="candidate-button" @click="$emit('edit', candidate)">
              修正
            </button>
          </div>
        </li>
      </ul>
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

defineEmits(["adopt", "edit"]);
</script>
