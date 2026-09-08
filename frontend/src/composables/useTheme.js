import { ref, watchEffect } from 'vue'

const KEY = 'workshop-theme'
const theme = ref(null)

function apply(value) {
  document.documentElement.dataset.theme = value
}

export function useTheme() {
  if (theme.value === null) {
    const saved = localStorage.getItem(KEY)
    theme.value = saved === 'light' || saved === 'dark' ? saved : 'dark'
    watchEffect(() => {
      apply(theme.value)
      localStorage.setItem(KEY, theme.value)
    })
  }

  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  return { theme, toggle }
}
