<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useAuth0 } from "@auth0/auth0-vue";

const AUTO_REDIRECT_SECONDS = 3;

const { isAuthenticated, loginWithRedirect, isLoading } = useAuth0();
const secondsLeft = ref(AUTO_REDIRECT_SECONDS);
const isRedirecting = ref(false);
const isAutoRedirectEnabled = ref(true);
let countdownTimer = null;

const statusLabel = computed(() => {
  if (isRedirecting.value) {
    return "Auth0へ移動しています...";
  }
  if (!isAutoRedirectEnabled.value) {
    return "自動遷移は停止中です。ボタンからログインできます。";
  }
  return `${secondsLeft.value}秒後にAuth0 Universal Loginへ遷移します。`;
});

const startLogin = async () => {
  if (isRedirecting.value || isLoading.value) {
    return;
  }

  isRedirecting.value = true;
  await loginWithRedirect({
    appState: {
      target: "/"
    }
  });
};

const stopAutoRedirect = () => {
  isAutoRedirectEnabled.value = false;
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
};

onMounted(() => {
  if (isAuthenticated.value) {
    return;
  }

  countdownTimer = setInterval(() => {
    if (!isAutoRedirectEnabled.value || isRedirecting.value) {
      return;
    }

    if (secondsLeft.value <= 1) {
      clearInterval(countdownTimer);
      countdownTimer = null;
      startLogin();
      return;
    }

    secondsLeft.value -= 1;
  }, 1000);
});

onBeforeUnmount(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
  }
});
</script>

<template>
  <main class="auth-container">
    <h1>ログイン</h1>
    <p>Auth0 Universal Loginへ移動する前の確認画面です。</p>
    <p class="auth-note">{{ statusLabel }}</p>
    <div class="auth-actions">
      <button type="button" class="auth-button" :disabled="isRedirecting" @click="startLogin">
        Auth0でログイン
      </button>
      <button
        v-if="isAutoRedirectEnabled && !isRedirecting"
        type="button"
        class="auth-button auth-button-secondary"
        @click="stopAutoRedirect"
      >
        自動遷移を停止
      </button>
    </div>
  </main>
</template>
