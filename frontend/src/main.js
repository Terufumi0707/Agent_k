// Vue本体のアプリ生成関数を読み込み
import { createApp } from "vue";
// 状態管理ライブラリPiniaを使用するための関数を読み込み
import { createPinia } from "pinia";
// アプリのルートコンポーネントを読み込み
import App from "./App.vue";
// 画面遷移を管理するためのルーター設定を読み込み
import router from "./router";
// グローバルスタイルを読み込み
import "./assets/styles.scss";

// ルートコンポーネントからVueアプリを生成
const app = createApp(App);
// アプリ全体でPiniaのストアを使えるようにする
app.use(createPinia());
// ルーターをアプリに組み込む
app.use(router);
// index.html内の#app要素にマウントして表示する
app.mount("#app");
