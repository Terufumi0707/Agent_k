<template>
  <button
    type="button"
    class="order-card"
    :class="{ 'order-card-selected': isSelected }"
    @click="$emit('select', order.id)"
  >
    <p class="order-card-label">ID</p>
    <p class="order-card-value">{{ order.id }}</p>
    <p class="order-card-label">Status</p>
    <p class="order-card-session">{{ order.current_status }}</p>
    <p class="order-card-label">Updated</p>
    <p class="order-card-session">{{ formatDate(order.updated_at) }}</p>
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

const formatDate = (value) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("ja-JP", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
};
</script>

<style scoped>
.order-card {
  width: 100%;
  border: 1px solid #d0dbfa;
  border-radius: 12px;
  background: #ffffff;
  padding: 12px;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.order-card:hover {
  border-color: #7f9af9;
  background: #f8faff;
  transform: translateY(-1px);
  box-shadow: 0 8px 14px rgba(12, 39, 244, 0.08);
}

.order-card-selected {
  border-color: #3152ff;
  background: #edf1ff;
  box-shadow: 0 0 0 1px #3152ff;
}

.order-card-label {
  margin: 0;
  color: #5f6f92;
  font-size: 12px;
}

.order-card-value {
  margin: 2px 0 10px;
  color: #152140;
  font-weight: 700;
  word-break: break-all;
}

.order-card-session {
  margin: 2px 0 10px;
  color: #33456f;
  font-size: 14px;
  word-break: break-all;
}
</style>
