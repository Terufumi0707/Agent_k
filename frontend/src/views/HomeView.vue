<script setup>
import { useAuth0 } from "@auth0/auth0-vue";
import ChatPage from "../components/ChatPage.vue";

const { user, logout } = useAuth0();

const logoutFromAuth0 = () => {
  logout({
    logoutParams: {
      returnTo: `${window.location.origin}/login`
    }
  });
};
</script>

<template>
  <div>
    <header class="auth-header">
      <p class="auth-user">ログイン中: {{ user?.name || user?.email || "Unknown User" }}</p>
      <button type="button" class="auth-button" @click="logoutFromAuth0">ログアウト</button>
    </header>
    <ChatPage />
  </div>
</template>
