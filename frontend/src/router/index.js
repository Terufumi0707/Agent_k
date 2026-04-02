import { createRouter, createWebHistory } from "vue-router";
import ChatPage from "../components/ChatPage.vue";
import OrderBoard from "../components/orders/OrderBoard.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "chat",
      component: ChatPage
    },
    {
      path: "/orders",
      name: "orders",
      component: OrderBoard
    }
  ]
});

export default router;
