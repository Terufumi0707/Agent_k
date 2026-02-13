import { createRouter, createWebHistory } from "vue-router";
import { authGuard } from "@auth0/auth0-vue";
import ChatPage from "../components/ChatPage.vue";
import LoginView from "../views/LoginView.vue";

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
      path: "/login",
      name: "login",
      component: LoginView
    }
  ]
});

export default router;
