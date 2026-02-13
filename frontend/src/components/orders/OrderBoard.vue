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
  background: linear-gradient(150deg, #f4f7ff 0%, #eff4ff 100%);
}

.status-column {
  display: grid;
  gap: 16px;
}

.order-detail {
  border: 1px solid #d3defa;
  border-radius: 14px;
  background: #ffffff;
  padding: 24px;
  box-shadow: 0 10px 24px rgba(12, 39, 244, 0.07);
}

.order-detail-title {
  margin: 0 0 8px;
  font-size: 18px;
  color: #19295e;
}

.order-detail-text {
  margin: 0;
  font-size: 14px;
  color: #4f6084;
}

@media (min-width: 960px) {
  .order-board {
    grid-template-columns: 380px 1fr;
  }
}
</style>
