<script setup>
import { onMounted } from "vue";
import { useAuth0 } from "@auth0/auth0-vue";

const { isAuthenticated, loginWithRedirect, isLoading } = useAuth0();

const login = () => {
  loginWithRedirect({
    appState: {
      target: "/"
    }
  });
};

onMounted(() => {
  if (!isLoading.value && !isAuthenticated.value) {
    login();
  }
});
</script>

<template>
  <main class="auth-container">
    <h1>ログイン</h1>
    <p>Auth0 Universal Login に遷移します。</p>
    <button type="button" class="auth-button" @click="login">ログインする</button>
  </main>
</template>
