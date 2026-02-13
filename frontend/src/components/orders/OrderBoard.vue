<template>
  <div class="order-board">
    <aside class="status-column">
      <StatusSection
        v-for="status in statuses"
        :key="status"
        :status="status"
        :selected-order-id="selectedOrderId"
        @select-order="selectedOrderId = $event"
      />
    </aside>

    <main class="order-detail">
      <h2 class="order-detail-title">Order Detail</h2>
      <p class="order-detail-text">
        {{ selectedOrderId ? `Selected order id: ${selectedOrderId}` : "詳細表示エリア（プレースホルダー）" }}
      </p>
    </main>
  </div>
</template>

<script setup>
import { ref } from "vue";
import StatusSection from "./StatusSection.vue";

const statuses = ["DELIVERY", "COORDINATE", "BACKYARD"];
const selectedOrderId = ref(null);
</script>

<style scoped>
.order-board {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  padding: 16px;
  background: #f3f4f6;
}

.status-column {
  display: grid;
  gap: 16px;
}

.order-detail {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  padding: 24px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.order-detail-title {
  margin: 0 0 8px;
  font-size: 18px;
  color: #111827;
}

.order-detail-text {
  margin: 0;
  font-size: 14px;
  color: #4b5563;
}

@media (min-width: 960px) {
  .order-board {
    grid-template-columns: 380px 1fr;
  }
}
</style>
