<template>
  <div v-if="hasData" class="card-wrap">
    <div class="card-header">
      <h3 class="card-title">{{ t('dashboard.meter.frequency') }}</h3>
      <span class="card-channel">
        {{ channel === 'Main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>

    <div class="card-body">
      <!-- 주파수 Big Number -->
      <div class="big-number">
        <span class="status-dot" :class="freqStatusClass"></span>
        <div>
          <div class="big-value">
            {{ currentFreq }} <span class="big-unit">Hz</span>
          </div>
          <span class="big-label" :class="freqStatusTextClass">{{ freqStatusText }}</span>
        </div>
      </div>

      <!-- 미니 트렌드 차트 (최근 이력) -->
      <div class="trend-area">
        <span class="trend-label">최근 추이</span>
        <div class="trend-chart" ref="chartContainer">
          <svg v-if="freqHistory.length >= 2" :width="chartW" :height="chartH" class="overflow-visible">
            <defs>
              <linearGradient :id="'fg-' + channel" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" :stop-color="trendColor" stop-opacity="0.18" />
                <stop offset="100%" :stop-color="trendColor" stop-opacity="0.02" />
              </linearGradient>
            </defs>
            <polygon :points="areaPoints" :fill="`url(#fg-${channel})`" />
            <polyline :points="linePoints" fill="none" :stroke="trendColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
            <!-- latest dot -->
            <circle :cx="lastPt[0]" :cy="lastPt[1]" r="3.5" fill="white" :stroke="trendColor" stroke-width="2" />
          </svg>
        </div>
        <div class="trend-axis">
          <span>-{{ freqHistory.length }}min</span>
          <span>now</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
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

    // 주파수 이력 (최근 60개, 1분 간격 push)
    const freqHistory = ref([])
    const MAX_HISTORY = 60

    const pushHistory = () => {
      const v = currentFreq.value
      if (v > 0) {
        freqHistory.value.push(v)
        if (freqHistory.value.length > MAX_HISTORY) freqHistory.value.shift()
      }
    }

    // 최초 1회 + 1분 간격 수집
    pushHistory()
    const timer = setInterval(pushHistory, 60000)
    onBeforeUnmount(() => clearInterval(timer))

    // 데이터 변경 시에도 수집
    watch(currentFreq, () => {
      // 실시간 store 가 바뀔 때마다 최신값 갱신 (마지막 값만 교체)
      if (freqHistory.value.length > 0) {
        freqHistory.value[freqHistory.value.length - 1] = currentFreq.value
      }
    })

    // 차트 사이즈
    const chartW = 260
    const chartH = 60

    const trendColor = computed(() => {
      const v = currentFreq.value
      if (v < 59.5 || v > 60.5) return '#ef4444'
      if (v < 59.8 || v > 60.2) return '#f59e0b'
      return '#22c55e'
    })

    const linePoints = computed(() => {
      const d = freqHistory.value
      if (d.length < 2) return ''
      const max = Math.max(...d) + 0.05
      const min = Math.min(...d) - 0.05
      const range = max - min || 0.1
      return d.map((v, i) => {
        const x = (i / (d.length - 1)) * chartW
        const y = chartH - ((v - min) / range) * (chartH - 4) - 2
        return `${x},${y}`
      }).join(' ')
    })

    const areaPoints = computed(() => {
      if (!linePoints.value) return ''
      return `0,${chartH} ${linePoints.value} ${chartW},${chartH}`
    })

    const lastPt = computed(() => {
      const d = freqHistory.value
      if (d.length < 2) return [0, 0]
      const max = Math.max(...d) + 0.05
      const min = Math.min(...d) - 0.05
      const range = max - min || 0.1
      const last = d[d.length - 1]
      return [chartW, chartH - ((last - min) / range) * (chartH - 4) - 2]
    })

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

    return {
      t, hasData, currentFreq, freqHistory,
      chartW, chartH, trendColor,
      linePoints, areaPoints, lastPt,
      freqStatusClass, freqStatusText, freqStatusTextClass,
    }
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
  @apply text-xs font-medium;
}

/* Trend */
.trend-area {
  @apply bg-gray-50 dark:bg-gray-700/50 rounded-xl p-3;
}
.trend-label {
  @apply text-xs text-gray-400 dark:text-gray-500 block mb-2;
}
.trend-chart {
  @apply w-full;
}
.trend-axis {
  @apply flex justify-between mt-1 text-xs text-gray-300 dark:text-gray-600;
}
</style>
