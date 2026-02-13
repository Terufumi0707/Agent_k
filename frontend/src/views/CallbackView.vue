<script setup>
import { computed, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuth0 } from "@auth0/auth0-vue";

const router = useRouter();
const { isAuthenticated, isLoading, error } = useAuth0();

const statusMessage = computed(() => {
  if (isLoading.value) {
    return "認証情報を処理中です...";
  }
  if (error.value) {
    return `認証エラー: ${error.value.message}`;
  }
  return "ログイン完了。画面遷移中です...";
});

watch(
  [isLoading, isAuthenticated, error],
  ([loading, authenticated, authError]) => {
    if (loading) {
      return;
    }
    if (authError) {
      return;
    }
    if (authenticated) {
      router.replace("/");
    } else {
      router.replace("/login");
    }
  },
  { immediate: true }
);
</script>

<template>
  <main class="auth-container">
    <h1>コールバック処理</h1>
    <p>{{ statusMessage }}</p>
  </main>
</template>
