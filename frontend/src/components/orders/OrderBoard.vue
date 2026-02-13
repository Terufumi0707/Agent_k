<template>
  <div class="order-board">
    <aside class="order-list-column">
      <div class="view-switcher" role="tablist" aria-label="order views">
        <button
          type="button"
          class="view-switcher-button"
          :class="{ active: activeView === 'timeline' }"
          @click="activeView = 'timeline'"
        >
          依頼一覧
        </button>
        <button
          type="button"
          class="view-switcher-button"
          :class="{ active: activeView === 'status' }"
          @click="activeView = 'status'"
        >
          ステータス一覧
        </button>
      </div>

      <section v-if="activeView === 'timeline'" class="panel">
        <h2 class="panel-title">依頼一覧（時系列）</h2>
        <p v-if="ordersLoading" class="panel-message">Loading...</p>
        <p v-else-if="ordersError" class="panel-error">{{ ordersError }}</p>
        <p v-else-if="orders.length === 0" class="panel-message">No orders found.</p>
        <div v-else class="order-list">
          <OrderCard
            v-for="order in orders"
            :key="order.id"
            :order="order"
            :is-selected="selectedOrderId === order.id"
            @select="selectOrder"
          />
        </div>
      </section>

      <section v-else class="status-list">
        <StatusSection
          v-for="status in statuses"
          :key="status"
          :status="status"
          :orders="ordersByStatus[status] ?? []"
          :loading="statusLoading"
          :error="statusError"
          :selected-order-id="selectedOrderId"
          @select-order="selectOrder"
        />
      </section>
    </aside>

    <main class="order-detail">
      <h2 class="order-detail-title">会話履歴</h2>
      <p v-if="!selectedOrderId" class="order-detail-text">依頼を選択してください。</p>
      <p v-else-if="messagesLoading" class="order-detail-text">Loading...</p>
      <p v-else-if="messagesError" class="order-detail-error">{{ messagesError }}</p>
      <MessageTimeline v-else :messages="messages" />
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import OrderCard from "./OrderCard.vue";
import StatusSection from "./StatusSection.vue";
import MessageTimeline from "./MessageTimeline.vue";

const statuses = ["DELIVERY", "COORDINATE", "BACKYARD"];
const activeView = ref("timeline");
const selectedOrderId = ref(null);

const orders = ref([]);
const ordersLoading = ref(false);
const ordersError = ref("");

const statusLoading = ref(false);
const statusError = ref("");
const ordersByStatus = ref({
  DELIVERY: [],
  COORDINATE: [],
  BACKYARD: []
});

const messages = ref([]);
const messagesLoading = ref(false);
const messagesError = ref("");

const backendBaseUrl = import.meta.env.VITE_BACKEND_BASE_URL
  ? import.meta.env.VITE_BACKEND_BASE_URL.replace(/\/$/, "")
  : "";

const buildApiUrl = (path) => (backendBaseUrl ? `${backendBaseUrl}/api${path}` : `/api${path}`);

const parseTime = (value) => new Date(value).getTime() || 0;

const sortByUpdatedAtDesc = (items) => [...items].sort((a, b) => parseTime(b.updated_at) - parseTime(a.updated_at));

const sortByCreatedAtAsc = (items) => [...items].sort((a, b) => parseTime(a.created_at) - parseTime(b.created_at));

const fetchOrders = async () => {
  try {
    ordersLoading.value = true;
    ordersError.value = "";
    const response = await fetch(buildApiUrl("/v1/orders?sort=updated_at_desc&limit=100&offset=0"));
    if (!response.ok) {
      throw new Error(`Failed to fetch orders: ${response.status}`);
    }
    const data = await response.json();
    orders.value = sortByUpdatedAtDesc(data);
  } catch (err) {
    ordersError.value = err instanceof Error ? err.message : "An unexpected error occurred.";
  } finally {
    ordersLoading.value = false;
  }
};

const fetchStatusGroups = async () => {
  try {
    statusLoading.value = true;
    statusError.value = "";
    const response = await fetch(buildApiUrl("/v1/orders/status-groups?limit=100&offset=0"));
    if (!response.ok) {
      throw new Error(`Failed to fetch status groups: ${response.status}`);
    }
    const groups = await response.json();
    const merged = {
      DELIVERY: [],
      COORDINATE: [],
      BACKYARD: []
    };
    for (const group of groups) {
      if (merged[group.status]) {
        merged[group.status] = sortByUpdatedAtDesc(group.orders ?? []);
      }
    }
    ordersByStatus.value = merged;
  } catch (err) {
    statusError.value = err instanceof Error ? err.message : "An unexpected error occurred.";
  } finally {
    statusLoading.value = false;
  }
};

const fetchMessages = async (orderId) => {
  try {
    messagesLoading.value = true;
    messagesError.value = "";
    const response = await fetch(buildApiUrl(`/v1/orders/${orderId}/messages?limit=200&offset=0`));
    if (!response.ok) {
      throw new Error(`Failed to fetch messages: ${response.status}`);
    }
    const data = await response.json();
    messages.value = sortByCreatedAtAsc(data);
  } catch (err) {
    messagesError.value = err instanceof Error ? err.message : "An unexpected error occurred.";
  } finally {
    messagesLoading.value = false;
  }
};

const selectOrder = (orderId) => {
  selectedOrderId.value = orderId;
  fetchMessages(orderId);
};

onMounted(() => {
  fetchOrders();
  fetchStatusGroups();
});
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

.order-list-column {
  display: grid;
  gap: 12px;
}

.view-switcher {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.view-switcher-button {
  border: 1px solid #d0dbfa;
  border-radius: 10px;
  background: #fff;
  padding: 10px 12px;
  color: #2f4270;
  font-weight: 700;
  cursor: pointer;
}

.view-switcher-button.active {
  border-color: #3152ff;
  color: #1f35ab;
  background: #edf1ff;
}

.panel {
  border: 1px solid #d3defa;
  border-radius: 14px;
  background: linear-gradient(160deg, #ffffff 0%, #f6f8ff 100%);
  padding: 16px;
}

.panel-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 800;
  color: #1c2d67;
}

.panel-message,
.order-detail-text {
  margin: 0;
  font-size: 14px;
  color: #566588;
}

.panel-error,
.order-detail-error {
  margin: 0;
  font-size: 14px;
  color: #c62828;
}

.order-list,
.status-list {
  display: grid;
  gap: 8px;
}

.order-detail {
  border: 1px solid #d3defa;
  border-radius: 14px;
  background: #ffffff;
  padding: 24px;
  box-shadow: 0 10px 24px rgba(12, 39, 244, 0.07);
}

.order-detail-title {
  margin: 0 0 16px;
  font-size: 18px;
  color: #19295e;
}

@media (min-width: 960px) {
  .order-board {
    grid-template-columns: 380px 1fr;
  }
}
</style>
