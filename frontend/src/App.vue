<template>
  <div class="app-shell">
    <header class="card app-header">
      <div>
        <h1>BayCurrent AIエージェント</h1>
        <p class="section-caption">業務エージェントとの対話とワークフローの状況を確認できます</p>
      </div>
      <nav class="header-nav">
        <RouterLink to="/" class="nav-link" exact-active-class="active">ワークスペース一覧</RouterLink>
        <RouterLink to="/completed" class="nav-link" exact-active-class="active">実行完了一覧</RouterLink>
      </nav>
    </header>
    <main class="app-main">
      <div class="content-wrapper">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script setup>
import { RouterLink, RouterView } from "vue-router";
</script>

<style scoped>
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

.app-main {
  flex: 1;
  width: 100%;
  padding: 1.5rem;
}

.content-wrapper {
  margin: 0 auto;
  width: 100%;
  max-width: 1280px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.nav-link {
  text-decoration: none;
  padding: 0.5rem 0.9rem;
  border-radius: 999px;
  color: #1f3d6d;
  background: #f0f4ff;
  font-weight: 600;
  transition: background 0.2s ease;
}

.nav-link.active,
.nav-link:hover {
  background: linear-gradient(135deg, #1f4fa3, #4369c6);
  color: #ffffff;
}

@media (max-width: 768px) {
  .app-header {
    margin: 1.25rem 1rem 0;
    padding: 1.25rem;
  }

  .app-main {
    padding: 1.25rem 1rem 2rem;
  }

  .content-wrapper {
    gap: 1.25rem;
  }

  .header-nav {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .nav-link {
    flex: 1 1 calc(50% - 0.5rem);
    text-align: center;
  }
}
</style>
