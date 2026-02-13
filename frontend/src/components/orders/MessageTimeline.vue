<template>
  <div>
    <p v-if="messages.length === 0" class="empty">No messages.</p>
    <div v-else class="timeline">
      <article
        v-for="message in messages"
        :key="message.id"
        class="message"
        :class="`message-${message.role}`"
      >
        <header class="message-header">
          <span class="role">{{ message.role }}</span>
          <time class="time">{{ formatDate(message.created_at) }}</time>
          <span v-if="message.metadata?.status_event" class="status-badge">ステータス変更</span>
        </header>
        <p class="content">{{ message.content }}</p>
        <p
          v-if="message.metadata?.status_event"
          class="status-detail"
        >
          {{ message.metadata?.order_status_before || "-" }} -> {{ message.metadata?.order_status_after || "-" }}
        </p>
      </article>
    </div>
  </div>
</template>

<script setup>
defineProps({
  messages: {
    type: Array,
    default: () => []
  }
});

const formatDate = (value) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
};
</script>

<style scoped>
.empty {
  margin: 0;
  color: #566588;
}

.timeline {
  display: grid;
  gap: 10px;
}

.message {
  border: 1px solid #d0dbfa;
  border-radius: 12px;
  padding: 10px 12px;
  max-width: 78%;
  background: #f9fbff;
}

.message-user {
  margin-left: auto;
  background: #edf2ff;
}

.message-assistant {
  margin-right: auto;
}

.message-system {
  margin: 0 auto;
  background: #fff6e5;
  border-color: #f3d29d;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.role {
  font-size: 12px;
  font-weight: 700;
  color: #33456f;
  text-transform: uppercase;
}

.time {
  font-size: 12px;
  color: #6679a4;
}

.content {
  margin: 6px 0 0;
  white-space: pre-wrap;
  color: #1b2c57;
}

.status-badge {
  display: inline-block;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  color: #7d4d00;
  background: #ffe6b8;
}

.status-detail {
  margin: 8px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: #7d4d00;
}
</style>
