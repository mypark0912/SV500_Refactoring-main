<template>
  <div class="thd-rings">
    <div v-for="(item, index) in chartItems" :key="index" class="ring-item">
      <svg class="ring-svg" viewBox="0 0 36 36">
        <circle class="ring-bg" cx="18" cy="18" r="15.5" />
        <circle
          class="ring-fill"
          :class="item.colorClass"
          cx="18" cy="18" r="15.5"
          :stroke-dasharray="`${Math.min(parseFloat(item.value), 100) * 0.9742} 97.42`"
          stroke-dashoffset="0"
        />
      </svg>
      <div class="ring-center">
        <span class="ring-value">{{ item.value }}</span>
        <span class="ring-unit">%</span>
      </div>
      <span class="ring-label">{{ item.label }}</span>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'DualMeasCard_THD_v2',
  props: {
    data: { type: Object, default: () => ({}) },
    pt: { type: Boolean, default: false },
  },
  setup(props) {
    const chartItems = computed(() => {
      const voltageItem = props.pt
        ? { key: 'thdupp total', label: 'THD-Upp', color: 'pink' }
        : { key: 'thdu total', label: 'THD-U', color: 'pink' }
      const items = [
        voltageItem,
        { key: 'thdi total', label: 'THD-I', color: 'indigo' },
        { key: 'tddi total', label: 'TDD-I', color: 'teal' },
      ]
      return items.map(it => ({
        label: it.label,
        value: parseFloat(props.data[it.key] || 0).toFixed(1),
        colorClass: `bar-${it.color}`,
      }))
    })
    return { chartItems }
  },
}
</script>

<style scoped>
.thd-rings {
  @apply flex justify-around items-center gap-2 px-2 py-3;
}
.ring-item {
  @apply flex flex-col items-center gap-1;
  position: relative;
}
.ring-svg {
  width: 52px;
  height: 52px;
  transform: rotate(-90deg);
}
.ring-bg {
  fill: none;
  stroke: #e5e7eb;
  stroke-width: 3;
}
:is(.dark) .ring-bg {
  stroke: #374151;
}
.ring-fill {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 0.7s ease-out;
}
.ring-fill.bar-pink { stroke: #ec4899; }
.ring-fill.bar-indigo { stroke: #6366f1; }
.ring-fill.bar-teal { stroke: #14b8a6; }

.ring-center {
  position: absolute;
  top: 0;
  left: 0;
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1px;
}
.ring-value {
  @apply text-xs font-bold text-gray-800 dark:text-white;
}
.ring-unit {
  @apply text-[9px] font-medium text-gray-500 dark:text-gray-400;
}
.ring-label {
  @apply text-xs font-semibold text-gray-600 dark:text-gray-400;
}
</style>
