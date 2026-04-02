import { createRouter, createWebHistory } from "vue-router";
import ChatPage from "../components/ChatPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "proposal",
      component: ChatPage
    }
  ]
});

export default router;
