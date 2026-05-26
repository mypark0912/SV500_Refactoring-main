<template>
  <div class="card-wrap">
    <!-- 헤더 -->
    <div class="card-header">
      <h3 class="card-title meter-accent-blue">{{ t('dashboard.meter.title') }}</h3>
      <span class="card-channel">
        {{ channel?.toLowerCase() === 'main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>

    <!-- 주요 지표 요약 -->
    <div class="card-body">
      <div class="summary-row">
        <div class="summary-item">
          <span class="summary-label">{{ t('dashboard.meter.avgvoltage') }}</span>
          <div class="summary-value">
            <span class="status-dot" :class="getVoltageDotClass(avgVoltage)"></span>
            {{ avgVoltage.toFixed(1) }} <span class="summary-unit">V</span>
          </div>
        </div>
        <div class="summary-item">
          <span class="summary-label">{{ t('dashboard.meter.totcurrent') }}</span>
          <div class="summary-value">
            <span class="status-dot" :class="getCurrentDotClass(data2.I4)"></span>
            {{ (data2.I4 || 0).toFixed(2) }} <span class="summary-unit">A</span>
          </div>
        </div>
        <div class="summary-item">
          <span class="summary-label">{{ t('dashboard.meter.frequency') }}</span>
          <div class="summary-value">
            <span class="status-dot" :class="getFreqDotClass(data2.Freq)"></span>
            {{ (data2.Freq || 0).toFixed(2) }} <span class="summary-unit">Hz</span>
          </div>
        </div>
        <div class="summary-item">
          <span class="summary-label">{{ t('dashboard.pq.powerfactor') }}</span>
          <div class="summary-value">
            <span class="status-dot" :class="getPfDotClass(data2.PF4)"></span>
            {{ (data2.PF4 || 0).toFixed(2) }} <span class="summary-unit">%</span>
          </div>
        </div>
        <div class="summary-item">
          <span class="summary-label">{{ t('dashboard.meter.activepower') }}</span>
          <div class="summary-value">
            {{ (data2.P4 || 0).toFixed(2) }} <span class="summary-unit">kW</span>
          </div>
        </div>
      </div>

      <!-- 상세 정보 3컬럼 -->
      <div class="detail-grid-3col">
        <!-- 전압 / 전류 -->
        <div class="detail-block">
          <span class="detail-block-title">{{ t('dashboard.meter.voltage') }} / {{ t('dashboard.meter.current') }}</span>
          <div class="vi-grid">
            <div class="vi-col">
              <div v-for="(phase, index) in ['L1', 'L2', 'L3']" :key="`v-${phase}`" class="phase-row">
                <span class="phase-label">{{ phase }}</span>
                <span class="phase-value">
                  {{ getPhaseVoltage(index + 1).toFixed(1) }} <span class="phase-unit">V</span>
                </span>
              </div>
            </div>
            <div class="vi-col">
              <div v-for="(phase, index) in ['L1', 'L2', 'L3']" :key="`i-${phase}`" class="phase-row">
                <span class="phase-label">{{ phase }}</span>
                <span class="phase-value">
                  {{ (data2[`I${index + 1}`] || 0).toFixed(2) }} <span class="phase-unit">A</span>
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 불평형률 -->
        <div class="detail-block">
          <span class="detail-block-title">{{ t('dashboard.pq.unbalance') }}</span>
          <div class="phase-section">
            <div class="ubal-item">
              <div class="ubal-info">
                <span class="ubal-type">{{ t('dashboard.pq.voltageunbalance') }}</span>
                <span class="ubal-value" :style="{ color: getUnbalColor(ubalVoltage) }">{{ ubalVoltage.toFixed(1) }}%</span>
              </div>
              <div class="hbar-track">
                <div class="hbar-fill" :style="{ width: Math.min(ubalVoltage, 100) + '%', backgroundColor: getUnbalColor(ubalVoltage) }"></div>
              </div>
            </div>
            <div class="ubal-item">
              <div class="ubal-info">
                <span class="ubal-type">{{ t('dashboard.pq.currentunbalance') }}</span>
                <span class="ubal-value" :style="{ color: getUnbalColor(ubalCurrent) }">{{ ubalCurrent.toFixed(1) }}%</span>
              </div>
              <div class="hbar-track">
                <div class="hbar-fill" :style="{ width: Math.min(ubalCurrent, 100) + '%', backgroundColor: getUnbalColor(ubalCurrent) }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 고조파 -->
        <div class="detail-block">
          <span class="detail-block-title">{{ t('dashboard.pq.THD') }}</span>
          <DualMeasCard_THD_v2 :data="data2" :pt="isPT"/>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSetupStore } from '@/store/setup'
import { useRealtimeStore } from '@/store/realtime'
import DualMeasCard_THD_v2 from './DualMeasCard_THD_v2.vue'

export default {
  name: 'DualMeasCard_Meter_v2',
  components: { DualMeasCard_THD_v2 },
  props: {
    channel: { type: String, required: true },
  },
  setup(props) {
    const { t } = useI18n()
    const setupStore = useSetupStore()
    const store = useRealtimeStore()
    const channel = computed(() => props.channel?.toLowerCase() === 'main' ? 'Main' : 'Sub')

    const data2 = computed(() => store.getChannelData(channel.value) || {})
    const isPT = computed(() => data2.value.DashPT !== 0)
    const avgVoltage = computed(() => isPT.value ? (data2.value.Upp4 || 0) : (data2.value.U4 || 0))

    const unbalMode = computed(() => setupStore.getUnbalance)
    const ubalVoltage = computed(() => parseFloat(unbalMode.value === 0 ? data2.value.Ubal_nema : data2.value.Ubal1) || 0)
    const ubalCurrent = computed(() => parseFloat(unbalMode.value === 0 ? data2.value.Ibal_nema : data2.value.Ibal1) || 0)

    const getPhaseVoltage = (idx) => {
      if (isPT.value) return data2.value[`Upp${idx}`] || 0
      return data2.value[`U${idx}`] || 0
    }

    const getVoltageDotClass = (v) => {
      if (!v) return 'dot-unknown'
      if (v < 200 || v > 240) return 'dot-danger'
      if (v < 210 || v > 230) return 'dot-warn'
      return 'dot-good'
    }
    const getCurrentDotClass = (v) => {
      if (!v) return 'dot-unknown'
      if (v > 100) return 'dot-danger'
      if (v > 80) return 'dot-warn'
      return 'dot-good'
    }
    const getFreqDotClass = (v) => {
      if (!v) return 'dot-unknown'
      if (v < 59.5 || v > 60.5) return 'dot-danger'
      if (v < 59.8 || v > 60.2) return 'dot-warn'
      return 'dot-good'
    }
    const getPfDotClass = (v) => {
      if (!v) return 'dot-unknown'
      if (v < 85) return 'dot-danger'
      if (v < 95) return 'dot-warn'
      return 'dot-good'
    }
    const getUnbalColor = (v) => {
      if (v >= 3) return '#ef4444'
      if (v >= 2) return '#f59e0b'
      if (v >= 1) return '#eab308'
      return '#22c55e'
    }

    return {
      t, data2, avgVoltage, channel, isPT,
      ubalVoltage, ubalCurrent,
      getPhaseVoltage,
      getVoltageDotClass, getCurrentDotClass, getFreqDotClass, getPfDotClass,
      getUnbalColor,
    }
  },
}
</script>

<style scoped>
.card-wrap {
  @apply col-span-full sm:col-span-6 xl:col-span-6;
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
  @apply w-1 h-4 rounded-full inline-block flex-shrink-0;
}
.meter-accent-blue::before {
  @apply bg-blue-500;
}
.card-channel {
  @apply text-xs text-gray-500 dark:text-gray-400;
}
.card-body {
  @apply px-4 py-3;
}

/* Summary row - 5 items */
.summary-row {
  @apply grid grid-cols-5 gap-3 mb-4;
}
.summary-item {
  @apply flex flex-col items-center justify-center text-center p-3 rounded-lg;
  @apply bg-gray-50 dark:bg-gray-700/50;
  min-height: 80px;
}
.summary-label {
  @apply text-[13px] text-gray-600 dark:text-gray-400 mb-1.5;
}
.summary-value {
  @apply text-xl font-extrabold text-gray-800 dark:text-white tabular-nums flex items-center justify-center gap-1;
}
.summary-unit {
  @apply text-xs font-medium text-gray-600 dark:text-gray-400;
}

/* Status dot */
.status-dot {
  @apply w-2 h-2 rounded-full flex-shrink-0;
}
.dot-good { @apply bg-green-500; }
.dot-warn { @apply bg-amber-500; }
.dot-danger { @apply bg-red-500; }
.dot-unknown { @apply bg-gray-400; }

/* Detail grid 3-column (equal) */
.detail-grid-3col {
  @apply grid grid-cols-1 lg:grid-cols-3 gap-3;
}
.vi-grid {
  @apply grid grid-cols-2 gap-x-3 px-3 py-2;
}
.vi-col {
  @apply space-y-2;
}
.detail-block {
  @apply bg-gray-50 dark:bg-gray-700/50 rounded-lg overflow-hidden pb-1;
}
.detail-block-title {
  @apply block text-sm font-bold text-gray-700 dark:text-white px-3 py-1.5;
  @apply bg-gray-100 dark:bg-gray-600 border-b border-gray-200 dark:border-gray-500;
}
.phase-section {
  @apply px-3 py-2 space-y-2;
}
.phase-row {
  @apply flex items-center gap-2;
}
.phase-label {
  @apply text-sm font-bold w-6 flex-shrink-0 text-gray-500 dark:text-gray-400;
}
.phase-value {
  @apply text-base font-bold tabular-nums text-green-600 dark:text-green-400;
}
.phase-unit {
  @apply text-xs font-medium text-gray-600 dark:text-gray-400;
}

/* Unbalance */
.ubal-item {
  @apply space-y-1.5;
}
.ubal-info {
  @apply flex justify-between items-center;
}
.ubal-type {
  @apply text-xs text-gray-600 dark:text-gray-400;
}
.ubal-value {
  @apply text-sm font-bold tabular-nums;
}
.hbar-track {
  @apply h-2.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden;
}
.hbar-fill {
  @apply h-full rounded-full transition-all duration-500;
  min-width: 4px;
}

/* Responsive */
@media (max-width: 1024px) {
  .summary-row {
    @apply grid-cols-3;
  }
}
@media (max-width: 640px) {
  .card-wrap {
    @apply col-span-full;
  }
  .summary-row {
    @apply grid-cols-2;
  }
}
</style>
