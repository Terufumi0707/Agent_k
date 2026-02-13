import { createRouter, createWebHistory } from "vue-router";
import { authGuard } from "@auth0/auth0-vue";
import ChatPage from "../components/ChatPage.vue";
import OrderBoard from "../components/orders/OrderBoard.vue";

const auth0Domain = import.meta.env.VITE_AUTH0_DOMAIN;
const auth0ClientId = import.meta.env.VITE_AUTH0_CLIENT_ID;
const hasAuth0Config =
  Boolean(auth0Domain) &&
  Boolean(auth0ClientId) &&
  auth0Domain !== "your-tenant.us.auth0.com" &&
  auth0ClientId !== "your-client-id";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "chat",
      component: ChatPage,
      beforeEnter: hasAuth0Config ? authGuard : undefined
    },
    {
      path: "/orders",
      name: "orders",
      component: OrderBoard
    }
  ]
});

export default router;
