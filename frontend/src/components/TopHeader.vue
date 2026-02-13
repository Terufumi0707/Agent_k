<template>
  <header class="top-header">
    <div class="top-header-left">
      <p class="top-header-title">日程変更エージェント</p>
    </div>

    <div class="top-header-right">
      <div class="auth-user-info">
        <p class="auth-user-name">{{ authDisplayName }}</p>
        <p class="auth-user-meta" v-if="authDisplayEmail">{{ authDisplayEmail }}</p>
        <p class="auth-user-meta" v-else-if="authDisplaySub">{{ authDisplaySub }}</p>
      </div>
      <button type="button" class="top-header-logout-button" @click="$emit('logout')">ログアウト</button>
    </div>
  </header>
</template>

<script setup>
defineProps({
  authDisplayName: {
    type: String,
    default: ""
  },
  authDisplayEmail: {
    type: String,
    default: ""
  },
  authDisplaySub: {
    type: String,
    default: ""
  }
});

defineEmits(["logout"]);
</script>
