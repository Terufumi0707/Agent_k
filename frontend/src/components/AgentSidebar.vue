<template>
  <aside class="left-sidebar" :class="{ collapsed }">
    <div class="sidebar-top">
      <button
        type="button"
        class="sidebar-toggle-button"
        @click="$emit('toggle')"
      >
        {{ collapsed ? "＞" : "＜" }}
      </button>
    </div>

    <div v-if="!collapsed" class="sidebar-bottom">
      <section class="sidebar-section">
        <p class="agent-menu-title">エージェント</p>
        <ul class="agent-menu-list">
          <li>
            <button
              type="button"
              class="agent-menu-button agent-menu-button-active"
            >
              議事録作成
            </button>
          </li>
        </ul>
      </section>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
});

defineEmits(["toggle"]);
</script>
