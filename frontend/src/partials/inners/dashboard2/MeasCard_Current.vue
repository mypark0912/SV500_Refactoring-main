<template>
  <div v-if="hasData" class="card-wrap">
    <div class="card-header">
      <h3 class="card-title">{{ t('dashboard.meter.current') }}</h3>
      <span class="card-channel">
        {{ channel === 'Main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>

    <div class="card-body">
      <!-- 평균 전류 Big Number -->
      <div class="big-number">
        <span class="status-dot" :class="currentStatusClass"></span>
        <div>
          <div class="big-value">
            {{ data.I4 || 0 }} <span class="big-unit">A</span>
          </div>
          <span class="big-label">{{ t('dashboard.meter.totcurrent') }}</span>
        </div>
      </div>

      <!-- 상별 전류 바 차트 -->
      <div class="phase-bars">
        <div v-for="(item, idx) in phaseItems" :key="idx" class="phase-row">
          <span class="phase-label">{{ item.label }}</span>
          <div class="bar-track">
            <div class="bar-fill" :style="{ width: item.pct + '%', backgroundColor: item.color }"></div>
            <div class="avg-marker" :style="{ left: avgPct + '%' }"></div>
          </div>
          <span class="phase-value">{{ item.value }} <span class="phase-unit">A</span></span>
        </div>
      </div>
      <div class="legend">
        <span class="legend-line"></span>
        <span class="legend-text">평균</span>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRealtimeStore } from '@/store/realtime'

export default {
  name: 'MeasCard_Current',
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

    // 상별 전류 최대값 기준으로 바 비율 계산
    const maxCurrent = computed(() => {
      const vals = [data.value.I1 || 0, data.value.I2 || 0, data.value.I3 || 0]
      return Math.max(...vals, 1) * 1.5 // 여유 공간
    })

    const phaseItems = computed(() => {
      const max = maxCurrent.value
      const phases = [
        { label: 'L1', value: data.value.I1 || 0 },
        { label: 'L2', value: data.value.I2 || 0 },
        { label: 'L3', value: data.value.I3 || 0 },
      ]
      const colors = ['#3b82f6', '#60a5fa', '#93c5fd']
      return phases.map((p, i) => ({
        ...p,
        pct: Math.min((p.value / max) * 100, 100),
        color: colors[i],
      }))
    })

    const avgPct = computed(() => {
      const avg = data.value.I4 || 0
      return Math.min((avg / maxCurrent.value) * 100, 100)
    })

    const currentStatusClass = computed(() => {
      const v = data.value.I4 || 0
      if (v > 100) return 'dot-danger'
      if (v > 80) return 'dot-warn'
      return 'dot-good'
    })

    return { t, data, hasData, phaseItems, avgPct, currentStatusClass }
  },
}
</script>

<style scoped>
.card-wrap {
  @apply col-span-full sm:col-span-6 xl:col-span-4;
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
.big-number {
  @apply flex items-center gap-3 mb-4;
}
.status-dot {
  @apply w-2.5 h-2.5 rounded-full flex-shrink-0;
}
.dot-good { @apply bg-green-500; }
.dot-warn { @apply bg-amber-500; }
.dot-danger { @apply bg-red-500; }
.big-value {
  @apply text-3xl font-extrabold text-gray-800 dark:text-white tabular-nums;
}
.big-unit {
  @apply text-sm font-medium text-gray-400 dark:text-gray-500;
}
.big-label {
  @apply text-xs text-gray-400 dark:text-gray-500;
}
.phase-bars {
  @apply space-y-2;
}
.phase-row {
  @apply flex items-center gap-2;
}
.phase-label {
  @apply text-xs font-bold text-gray-400 dark:text-gray-500 w-5;
}
.bar-track {
  @apply flex-1 h-4 bg-gray-100 dark:bg-gray-700 rounded-full overflow-visible relative;
}
.bar-fill {
  @apply h-full rounded-full transition-all duration-500;
  opacity: 0.75;
}
.avg-marker {
  @apply absolute top-0 h-full w-0.5 bg-gray-400 dark:bg-gray-500 rounded;
  opacity: 0.5;
}
.phase-value {
  @apply text-xs font-semibold text-gray-600 dark:text-gray-300 w-20 text-right tabular-nums;
}
.phase-unit {
  @apply text-gray-400 dark:text-gray-500;
}
.legend {
  @apply flex items-center gap-1.5 mt-3 text-xs text-gray-300 dark:text-gray-600;
}
.legend-line {
  @apply w-3 h-0.5 bg-gray-400 dark:bg-gray-500 rounded;
}
.legend-text {
  @apply text-xs;
}
</style>
