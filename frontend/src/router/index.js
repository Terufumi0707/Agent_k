// Vue Router本体と履歴モードを読み込み
import { createRouter, createWebHistory } from "vue-router";
// 各ルートで表示する画面コンポーネント
import WorkspaceDashboard from "../views/WorkspaceDashboard.vue";
import CompletionList from "../views/CompletionList.vue";

// アプリで利用するルート定義
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
  // ヒストリーモードを指定し、ルート設定を適用
  history: createWebHistory(),
  routes
});

export default router;
