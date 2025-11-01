import { createRouter, createWebHistory } from "vue-router";
import WorkspaceDashboard from "../views/WorkspaceDashboard.vue";
import CompletionList from "../views/CompletionList.vue";

const routes = [
  {
    path: "/",
    name: "workspace-dashboard",
    component: WorkspaceDashboard
  },
  {
    path: "/completed",
    name: "completed-workspaces",
    component: CompletionList
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
