<template>
  <div class="app-shell">
    <!-- 画面上部のヘッダー。タイトルとメニューリンクをまとめている -->
    <header class="card app-header">
      <div>
        <h1>BayCurrent AIエージェント</h1>
        <p class="section-caption">業務エージェントとの対話とワークフローの状況を確認できます</p>
      </div>
      <!-- 画面遷移用のナビゲーションリンク -->
      <nav class="header-nav">
        <RouterLink to="/" class="nav-link" exact-active-class="active">ワークスペース一覧</RouterLink>
        <RouterLink to="/completed" class="nav-link" exact-active-class="active">実行完了一覧</RouterLink>
      </nav>
    </header>
    <!-- メインコンテンツエリア。下位ルートのコンポーネントを表示する -->
    <main class="app-main">
      <div class="content-wrapper">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script setup>
// Vue Routerから画面表示に必要なコンポーネントをインポート
import { RouterLink, RouterView } from "vue-router";
</script>

<style scoped>
/* ヘッダー全体のレイアウト調整 */
.app-header {
  margin: 1.5rem 1.5rem 0;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
}

.app-header h1 {
  margin: 0 0 0.25rem 0;
}

/* メインエリアの余白設定 */
.app-main {
  flex: 1;
  width: 100%;
  padding: 1.5rem;
}

/* 中身のコンポーネントを縦方向に整列 */
.content-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

/* ナビゲーション部分の横並び設定 */
.header-nav {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* リンクのベーススタイル */
.nav-link {
  text-decoration: none;
  padding: 0.5rem 0.9rem;
  border-radius: 999px;
  color: #1f3d6d;
  background: #f0f4ff;
  font-weight: 600;
  transition: background 0.2s ease;
}

/* 選択時やホバー時の色変化 */
.nav-link.active,
.nav-link:hover {
  background: linear-gradient(135deg, #1f4fa3, #4369c6);
  color: #ffffff;
}

@media (max-width: 768px) {
  /* スマホ向けにヘッダーの余白を調整 */
  .app-header {
    margin: 1.25rem 1rem 0;
    padding: 1.25rem;
  }

  /* スマホ時はメイン領域の余白を詰める */
  .app-main {
    padding: 1.25rem 1rem 2rem;
  }

  /* コンテンツ同士の隙間を狭める */
  .content-wrapper {
    gap: 1.5rem;
  }

  /* スマホ時はナビゲーションを折り返して表示 */
  .header-nav {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  /* 小さい画面でリンクを均等に配置 */
  .nav-link {
    flex: 1 1 calc(50% - 0.5rem);
    text-align: center;
  }
}
</style>
