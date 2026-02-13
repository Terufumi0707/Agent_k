<template>
  <button
    type="button"
    class="order-card"
    :class="{ 'order-card-selected': isSelected }"
    @click="$emit('select', order.id)"
  >
    <p class="order-card-label">ID</p>
    <p class="order-card-value">{{ order.id }}</p>
    <p class="order-card-label">Session ID</p>
    <p class="order-card-session">{{ order.session_id }}</p>
  </button>
</template>

<script setup>
defineProps({
  order: {
    type: Object,
    required: true
  },
  isSelected: {
    type: Boolean,
    default: false
  }
});

defineEmits(["select"]);
</script>

<style scoped>
.order-card {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: #ffffff;
  padding: 12px;
  text-align: left;
  cursor: pointer;
}

.order-card:hover {
  border-color: #9ca3af;
  background: #f9fafb;
}

.order-card-selected {
  border-color: #2563eb;
  background: #eff6ff;
  box-shadow: 0 0 0 1px #2563eb;
}

.order-card-label {
  margin: 0;
  color: #6b7280;
  font-size: 12px;
}

.order-card-value {
  margin: 2px 0 10px;
  color: #111827;
  font-weight: 600;
  word-break: break-all;
}

.order-card-session {
  margin: 2px 0 0;
  color: #374151;
  font-size: 14px;
  word-break: break-all;
}
</style>
