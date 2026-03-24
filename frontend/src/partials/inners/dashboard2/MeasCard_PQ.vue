<template>
  <div v-if="hasData" class="card-wrap">
    <div class="card-header">
      <h3 class="card-title">불평형률 · 고조파 왜곡률</h3>
      <span class="card-channel">
        {{ channel === 'Main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>

    <div class="card-body">
      <div class="pq-grid">
        <!-- 불평형률 -->
        <div class="pq-section">
          <span class="section-label">전압/전류 불평형률</span>
          <div class="unbalance-bars">
            <!-- 전압 불평형 -->
            <div class="ubal-row">
              <span class="ubal-label">전압</span>
              <div class="ubal-track">
                <div class="ubal-fill bg-violet-400 dark:bg-violet-300"
                  :style="{ width: Math.min((ubalVoltage / 5) * 100, 100) + '%' }"></div>
                <div class="ubal-threshold" :style="{ left: '60%' }"></div>
              </div>
              <div class="ubal-value-wrap">
                <span class="ubal-dot" :class="getUnbalanceStatusClass(ubalVoltage)"></span>
                <span class="ubal-value">{{ ubalVoltage.toFixed(1) }}%</span>
              </div>
            </div>
            <!-- 전류 불평형 -->
            <div class="ubal-row">
              <span class="ubal-label">전류</span>
              <div class="ubal-track">
                <div class="ubal-fill bg-sky-400 dark:bg-sky-300"
                  :style="{ width: Math.min((ubalCurrent / 5) * 100, 100) + '%' }"></div>
                <div class="ubal-threshold" :style="{ left: '60%' }"></div>
              </div>
              <div class="ubal-value-wrap">
                <span class="ubal-dot" :class="getUnbalanceStatusClass(ubalCurrent)"></span>
                <span class="ubal-value">{{ ubalCurrent.toFixed(1) }}%</span>
              </div>
            </div>
          </div>
          <div class="threshold-legend">
            <span class="threshold-line"></span>
            <span class="threshold-text">허용 기준 (3%)</span>
          </div>
        </div>

        <!-- 고조파 왜곡률 (THD bar chart) -->
        <div class="pq-section">
          <span class="section-label">고조파 왜곡률</span>
          <div class="thd-chart">
            <div v-for="item in thdItems" :key="item.label" class="thd-bar-item">
              <span class="thd-bar-value">{{ item.value }}%</span>
              <div class="thd-bar-track">
                <div class="thd-bar-fill" :style="{ height: item.heightPct + '%', backgroundColor: item.color }"></div>
              </div>
              <span class="thd-bar-label">{{ item.label }}</span>
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
  name: 'MeasCard_PQ',
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

    const ubalVoltage = computed(() => parseFloat(data.value.Ubal1) || 0)
    const ubalCurrent = computed(() => parseFloat(data.value.Ibal1) || 0)

    const thdItems = computed(() => {
      const items = [
        { label: 'THD-U', key: 'thdu total', color: '#f87171' },
        { label: 'THD-I', key: 'thdi total', color: '#60a5fa' },
        { label: 'TDD-I', key: 'tddi total', color: '#2dd4bf' },
      ]
      const values = items.map(it => parseFloat(data.value[it.key]) || 0)
      const maxVal = Math.max(...values, 10)
      return items.map((it, i) => ({
        label: it.label,
        value: values[i].toFixed(1),
        color: it.color,
        heightPct: Math.max((values[i] / maxVal) * 100, 5),
      }))
    })

    const getUnbalanceStatusClass = (value) => {
      if (value >= 3) return 'dot-danger'
      if (value >= 2) return 'dot-warn'
      if (value >= 1) return 'dot-caution'
      return 'dot-good'
    }

    return { t, data, hasData, ubalVoltage, ubalCurrent, thdItems, getUnbalanceStatusClass }
  },
}
</script>

<style scoped>
.card-wrap {
  @apply col-span-full sm:col-span-6 xl:col-span-7;
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

/* PQ Grid */
.pq-grid {
  @apply grid grid-cols-2 gap-5;
}
.pq-section {
  @apply space-y-3;
}
.section-label {
  @apply text-xs font-medium text-gray-500 dark:text-gray-400 block;
}

/* Unbalance Bars */
.unbalance-bars {
  @apply space-y-3;
}
.ubal-row {
  @apply flex items-center gap-2;
}
.ubal-label {
  @apply text-xs text-gray-500 dark:text-gray-400 w-6;
}
.ubal-track {
  @apply flex-1 h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-visible relative;
}
.ubal-fill {
  @apply h-full rounded-full transition-all duration-500;
}
.ubal-threshold {
  @apply absolute top-0 h-full w-0.5 bg-red-300 dark:bg-red-400 rounded;
  opacity: 0.5;
}
.ubal-value-wrap {
  @apply flex items-center gap-1.5 w-16 justify-end;
}
.ubal-dot {
  @apply w-1.5 h-1.5 rounded-full flex-shrink-0;
}
.dot-good { @apply bg-green-500; }
.dot-caution { @apply bg-yellow-500; }
.dot-warn { @apply bg-amber-500; }
.dot-danger { @apply bg-red-500; }
.ubal-value {
  @apply text-xs font-semibold text-gray-600 dark:text-gray-300 tabular-nums;
}

/* Threshold legend */
.threshold-legend {
  @apply flex items-center gap-1.5 text-xs text-gray-300 dark:text-gray-600;
}
.threshold-line {
  @apply w-0.5 h-2.5 bg-red-300 dark:bg-red-400 rounded;
  opacity: 0.6;
}
.threshold-text {
  @apply text-xs;
}

/* THD Bar Chart */
.thd-chart {
  @apply flex items-end justify-center gap-4;
  height: 120px;
}
.thd-bar-item {
  @apply flex flex-col items-center gap-1 flex-1;
  max-width: 48px;
}
.thd-bar-value {
  @apply text-xs font-bold text-gray-600 dark:text-gray-300 tabular-nums;
}
.thd-bar-track {
  @apply w-full flex items-end;
  height: 80px;
}
.thd-bar-fill {
  @apply w-full rounded-t-lg transition-all duration-500;
  min-height: 4px;
}
.thd-bar-label {
  @apply text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap;
  font-size: 10px;
}
</style>
