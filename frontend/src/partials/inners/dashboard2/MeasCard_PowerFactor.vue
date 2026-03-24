<template>
  <div v-if="hasData" class="card-wrap">
    <div class="card-header">
      <h3 class="card-title">역률 · 유효전력</h3>
      <span class="card-channel">
        {{ channel === 'Main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>

    <div class="card-body">
      <div class="pf-power-grid">
        <!-- 역률 반원 게이지 -->
        <div class="gauge-area">
          <span class="gauge-label">{{ t('dashboard.pq.powerfactor') }}</span>
          <div class="gauge-wrap">
            <svg :width="gaugeSize" :height="gaugeSize * 0.55" :viewBox="`0 0 ${gaugeSize} ${gaugeSize * 0.55}`">
              <!-- background arc -->
              <path :d="arcPath" fill="none" stroke="#f1f5f9" stroke-width="10" stroke-linecap="round"
                class="dark:stroke-gray-700" />
              <!-- value arc -->
              <path :d="arcPath" fill="none" :stroke="pfColor" stroke-width="10" stroke-linecap="round"
                :stroke-dasharray="arcLength" :stroke-dashoffset="arcOffset"
                class="transition-all duration-700" />
              <!-- center value -->
              <text :x="gaugeSize / 2" :y="gaugeSize * 0.48" text-anchor="middle"
                :fill="pfColor" font-weight="800" font-size="20" class="tabular-nums">
                {{ pfValue }}%
              </text>
            </svg>
          </div>
          <span class="pf-status" :class="pfStatusClass">{{ pfStatusText }}</span>
        </div>

        <!-- 전력 수치 (P / Q / S) -->
        <div class="power-stack">
          <div class="power-item">
            <span class="power-label">유효전력 (P)</span>
            <div class="power-value">
              {{ data.P4 || 0 }} <span class="power-unit">kW</span>
            </div>
          </div>
          <div class="power-item">
            <span class="power-label">무효전력 (Q)</span>
            <div class="power-value">
              {{ data.Q4 || 0 }} <span class="power-unit">kVar</span>
            </div>
          </div>
          <div class="power-item">
            <span class="power-label">피상전력 (S)</span>
            <div class="power-value">
              {{ data.S4 || 0 }} <span class="power-unit">kVA</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRealtimeStore } from '@/store/realtime'

export default {
  name: 'MeasCard_PowerFactor',
  props: {
    channel: { type: String, required: true },
  },
  setup(props) {
    const { t } = useI18n()
    const store = useRealtimeStore()
    const data = computed(() => {
      const ch = props.channel?.toLowerCase() === 'main' ? 'Main' : 'Sub'
      return store.getChannelData(ch) || {}
    })

    const hasData = computed(() => Object.keys(data.value).length > 0)
    const pfValue = computed(() => {
      const v = data.value.PF4
      return v != null ? parseFloat(v).toFixed(2) : '0.00'
    })

    // Gauge calculations
    const gaugeSize = 140
    const r = gaugeSize * 0.4
    const arcLength = Math.PI * r

    const arcPath = computed(() => {
      const s = gaugeSize
      return `M ${s * 0.1} ${s * 0.5} A ${r} ${r} 0 0 1 ${s * 0.9} ${s * 0.5}`
    })

    const arcOffset = computed(() => {
      const pf = Math.min(Math.max(parseFloat(pfValue.value) || 0, 0), 100)
      return arcLength * (1 - pf / 100)
    })

    const pfColor = computed(() => {
      const v = parseFloat(pfValue.value) || 0
      if (v >= 95) return '#22c55e'
      if (v >= 85) return '#f59e0b'
      return '#ef4444'
    })

    const pfStatusClass = computed(() => {
      const v = parseFloat(pfValue.value) || 0
      if (v >= 95) return 'text-green-500'
      if (v >= 85) return 'text-amber-500'
      return 'text-red-500'
    })

    const pfStatusText = computed(() => {
      const v = parseFloat(pfValue.value) || 0
      if (v >= 95) return '양호'
      if (v >= 85) return '주의'
      return '기준 미달'
    })

    return {
      t, data, hasData, pfValue,
      gaugeSize, arcPath, arcLength, arcOffset, pfColor,
      pfStatusClass, pfStatusText,
    }
  },
}
</script>

<style scoped>
.card-wrap {
  @apply col-span-full sm:col-span-6 xl:col-span-5;
  @apply bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900;
  @apply shadow-lg rounded-xl border border-gray-200/50 dark:border-gray-700/50;
  @apply overflow-hidden;
}
.card-header {
  @apply flex justify-between items-center px-5 pt-4 pb-2;
}
.card-title {
  @apply text-sm font-bold text-gray-700 dark:text-white;
}
.card-channel {
  @apply text-xs text-gray-400 dark:text-gray-500;
}
.card-body {
  @apply px-5 pb-5;
}

/* Grid layout */
.pf-power-grid {
  @apply grid grid-cols-2 gap-4;
}

/* Gauge area */
.gauge-area {
  @apply flex flex-col items-center bg-gray-50 dark:bg-gray-700/50 rounded-xl py-4;
}
.gauge-label {
  @apply text-xs text-gray-400 dark:text-gray-500 mb-1;
}
.gauge-wrap {
  @apply flex justify-center;
}
.pf-status {
  @apply text-xs font-semibold mt-1;
}

/* Power stack */
.power-stack {
  @apply flex flex-col gap-3 justify-center;
}
.power-item {
  @apply bg-gray-50 dark:bg-gray-700/50 rounded-xl px-4 py-3;
}
.power-label {
  @apply text-xs text-gray-400 dark:text-gray-500;
}
.power-value {
  @apply text-xl font-bold text-gray-800 dark:text-white mt-1 tabular-nums;
}
.power-unit {
  @apply text-sm font-medium text-gray-400 dark:text-gray-500;
}
</style>
