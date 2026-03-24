<template>
  <div v-if="hasData" class="card-wrap">
    <div class="card-header">
      <h3 class="card-title">{{ t('dashboard.meter.current') }}</h3>
      <span class="card-channel">
        {{ channel === 'Main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>
    <div class="card-body">
      <!-- 평균 전류 (가운데 정렬) -->
      <div class="avg-section">
        <span class="avg-label">{{ t('dashboard.meter.totcurrent') }}</span>
        <div class="avg-value">
          <span class="status-dot" :class="currentStatusClass"></span>
          {{ data.I4 || 0 }} <span class="avg-unit">A</span>
        </div>
      </div>
      <!-- 상별 전류 (아래) -->
      <div class="phase-section">
        <div v-for="item in phaseItems" :key="item.label" class="phase-row">
          <span class="phase-label">{{ item.label }}</span>
          <span class="phase-value" :class="item.statusClass">{{ item.value }} <span class="phase-unit">A</span></span>
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

    const getCurrentStatusClass = (v) => {
      if (!v) return 'text-gray-400'
      if (v > 100) return 'text-red-500 dark:text-red-400'
      if (v > 80) return 'text-amber-500 dark:text-amber-400'
      if (v > 60) return 'text-yellow-500 dark:text-yellow-400'
      return 'text-green-600 dark:text-green-400'
    }

    const phaseItems = computed(() => {
      const phases = [
        { label: 'L1', value: data.value.I1 || 0 },
        { label: 'L2', value: data.value.I2 || 0 },
        { label: 'L3', value: data.value.I3 || 0 },
      ]
      return phases.map(p => ({ ...p, statusClass: getCurrentStatusClass(p.value) }))
    })

    const currentStatusClass = computed(() => {
      const v = data.value.I4 || 0
      if (v > 100) return 'dot-danger'
      if (v > 80) return 'dot-warn'
      return 'dot-good'
    })

    return { t, data, hasData, phaseItems, currentStatusClass }
  },
}
</script>

<style scoped>
.card-wrap {
  @apply col-span-full sm:col-span-6 xl:col-span-2;
  @apply bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900;
  @apply shadow-lg rounded-xl border border-gray-200/50 dark:border-gray-700/50;
  @apply overflow-hidden;
}
.card-header {
  @apply flex justify-between items-center px-4 py-2.5;
}
.card-title {
  @apply text-base font-bold text-gray-800 dark:text-white flex items-center gap-2;
}
.card-title::before {
  content: '';
  @apply w-1 h-4 rounded-full bg-amber-500 inline-block flex-shrink-0;
}
.card-channel {
  @apply text-gray-500 dark:text-gray-500;
  font-size: 10px;
}
.card-body {
  @apply px-4 py-3;
}
/* 평균 (가운데 정렬) */
.avg-section {
  @apply flex flex-col items-center text-center mb-2;
}
.avg-label {
  @apply text-sm text-gray-600 dark:text-gray-400 mb-1;
}
.avg-value {
  @apply text-3xl font-extrabold text-gray-800 dark:text-white tabular-nums flex items-center justify-center gap-1.5;
}
.avg-unit {
  @apply text-base font-medium text-gray-600 dark:text-gray-400;
}
.status-dot {
  @apply w-2 h-2 rounded-full flex-shrink-0;
}
.dot-good { @apply bg-green-500; }
.dot-warn { @apply bg-amber-500; }
.dot-danger { @apply bg-red-500; }

/* 상별 (아래) */
.phase-section {
  @apply border-t border-gray-100 dark:border-gray-700 pt-3 mt-1 space-y-1;
}
.phase-row {
  @apply flex justify-between items-center;
}
.phase-label {
  @apply text-sm font-semibold text-gray-600 dark:text-gray-400;
}
.phase-value {
  @apply text-base font-bold tabular-nums;
}
.phase-unit {
  @apply text-sm font-medium text-gray-600 dark:text-gray-400;
}
</style>
