<template>
  <section class="status-section">
    <h2 class="status-title">{{ status }}</h2>

    <p v-if="loading" class="status-message">Loading...</p>
    <p v-else-if="error" class="status-error">{{ error }}</p>
    <p v-else-if="orders.length === 0" class="status-message">No orders in this status.</p>

    <div v-else class="order-list">
      <OrderCard
        v-for="order in orders"
        :key="order.id"
        :order="order"
        :is-selected="selectedOrderId === order.id"
        @select="emit('select-order', $event)"
      />
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import OrderCard from "./OrderCard.vue";

const props = defineProps({
  status: {
    type: String,
    required: true
  },
  selectedOrderId: {
    type: String,
    default: null
  }
});

const emit = defineEmits(["select-order"]);

const orders = ref([]);
const loading = ref(true);
const error = ref("");

const backendBaseUrl = import.meta.env.VITE_BACKEND_BASE_URL
  ? import.meta.env.VITE_BACKEND_BASE_URL.replace(/\/$/, "")
  : "";

const fetchOrders = async () => {
  try {
    loading.value = true;
    error.value = "";
    const response = await fetch(`${backendBaseUrl}/orders?status=${props.status}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch ${props.status} orders: ${response.status}`);
    }

    orders.value = await response.json();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "An unexpected error occurred.";
  } finally {
    loading.value = false;
  }
};

watch(
  () => props.status,
  () => {
    fetchOrders();
  }
);

onMounted(() => {
  fetchOrders();
});
</script>

<style scoped>
.status-section {
  border: 1px solid #d3defa;
  border-radius: 14px;
  background: linear-gradient(160deg, #ffffff 0%, #f6f8ff 100%);
  padding: 16px;
  box-shadow: 0 8px 20px rgba(12, 39, 244, 0.06);
}

.status-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #1c2d67;
}

.status-message {
  margin: 0;
  font-size: 14px;
  color: #566588;
}

.status-error {
  margin: 0;
  font-size: 14px;
  color: #c62828;
}

.order-list {
  display: grid;
  gap: 8px;
}
</style>
