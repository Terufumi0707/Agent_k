import { createRouter, createWebHistory } from "vue-router";
import { authGuard } from "@auth0/auth0-vue";
import ChatPage from "../components/ChatPage.vue";
import OrderBoard from "../components/orders/OrderBoard.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "chat",
      component: ChatPage,
      beforeEnter: authGuard
    },
    {
      path: "/orders",
      name: "orders",
      component: OrderBoard
    }
  ]
});

export default router;
