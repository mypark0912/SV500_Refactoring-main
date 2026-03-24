<template>
  <div v-if="hasData" class="card-wrap">
    <div class="card-header">
      <h3 class="card-title">{{ t('dashboard.meter.frequency') }}</h3>
      <span class="card-channel">
        {{ channel === 'Main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>
    <div class="card-body">
      <div class="freq-content">
        <span class="freq-label">주파수</span>
        <div class="freq-value">
          <span class="status-dot" :class="freqStatusClass"></span>
          {{ currentFreq }} <span class="freq-unit">Hz</span>
        </div>
        <span class="freq-status" :class="freqStatusTextClass">{{ freqStatusText }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRealtimeStore } from '@/store/realtime'

export default {
  name: 'MeasCard_Frequency',
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
    const currentFreq = computed(() => data.value.Freq || 0)

    const freqStatusClass = computed(() => {
      const v = currentFreq.value
      if (v < 59.5 || v > 60.5) return 'dot-danger'
      if (v < 59.8 || v > 60.2) return 'dot-warn'
      return 'dot-good'
    })

    const freqStatusText = computed(() => {
      const v = currentFreq.value
      if (v < 59.5 || v > 60.5) return '이상'
      if (v < 59.8 || v > 60.2) return '주의'
      return '안정'
    })

    const freqStatusTextClass = computed(() => {
      const v = currentFreq.value
      if (v < 59.5 || v > 60.5) return 'text-red-500'
      if (v < 59.8 || v > 60.2) return 'text-amber-500'
      return 'text-green-500'
    })

    return { t, hasData, currentFreq, freqStatusClass, freqStatusText, freqStatusTextClass }
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
  @apply w-1 h-4 rounded-full bg-emerald-500 inline-block flex-shrink-0;
}
.card-channel {
  @apply text-gray-500 dark:text-gray-500;
  font-size: 10px;
}
.card-body {
  @apply px-4 py-3;
}
.freq-content {
  @apply flex flex-col items-center justify-center py-1;
}
.freq-label {
  @apply text-sm text-gray-600 dark:text-gray-400 mb-1;
}
.freq-value {
  @apply text-3xl font-extrabold text-gray-800 dark:text-white tabular-nums flex items-center gap-2;
}
.freq-unit {
  @apply text-base font-medium text-gray-600 dark:text-gray-400;
}
.status-dot {
  @apply w-2 h-2 rounded-full flex-shrink-0;
}
.dot-good { @apply bg-green-500; }
.dot-warn { @apply bg-amber-500; }
.dot-danger { @apply bg-red-500; }
.freq-status {
  @apply text-sm font-semibold mt-1;
}
</style>
