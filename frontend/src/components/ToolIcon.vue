<script setup>
import ICONS from '../tools/icons'

defineProps({
  name: { type: String, required: true },
})
</script>

<template>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path v-for="(d, i) in ICONS[name] || []" :key="i" :d="d" />
  </svg>
</template>
