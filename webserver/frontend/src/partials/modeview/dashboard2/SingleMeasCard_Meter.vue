<template v-if="hasData">
  <div class="card-wrap">
    <!-- 헤더 -->
    <div class="card-header">
      <h3 class="card-title meter-accent-blue">{{ t('dashboard.meter.singletitle') }}</h3>
      <span class="card-channel">
        {{ channel == 'main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>

    <div class="card-body">
      <!-- 주요 지표 요약 -->
      <div class="summary-row">
        <!-- 평균 전압 -->
        <div v-if="realtimeData.DashPT == 0" class="summary-item">
          <span class="summary-label">{{ t('dashboard.meter.avgvoltage') }}</span>
          <div class="summary-value">{{ realtimeData?.U4 || 0 }} <span class="summary-unit">V</span></div>
        </div>
        <div v-else class="summary-item">
          <span class="summary-label">{{ t('dashboard.meter.avgvoltage') }}</span>
          <div class="summary-value">{{ realtimeData?.Upp4 || 0 }} <span class="summary-unit">V</span></div>
        </div>

        <!-- 총 전류 -->
        <div class="summary-item">
          <span class="summary-label">{{ t('dashboard.meter.totcurrent') }}</span>
          <div class="summary-value">{{ realtimeData?.I4 || 0 }} <span class="summary-unit">A</span></div>
        </div>

        <!-- 주파수 -->
        <div class="summary-item">
          <span class="summary-label">{{ t('dashboard.meter.frequency') }}</span>
          <div class="summary-value">{{ realtimeData?.Freq || 0 }} <span class="summary-unit">Hz</span></div>
        </div>
      </div>

      <!-- 상세 측정값 -->
      <div class="detail-grid">
        <!-- 전압 상세 -->
        <div class="detail-block">
          <span class="detail-block-title">{{ t('dashboard.meter.voltage') }}</span>
          <div v-if="realtimeData.DashPT == 0" class="phase-section">
            <div class="phase-row">
              <span class="phase-label">L1</span>
              <span class="phase-value" :class="getVoltageClass(realtimeData?.U1)">
                {{ realtimeData?.U1 || 0 }} <span class="phase-unit">V</span>
              </span>
            </div>
            <div class="phase-row">
              <span class="phase-label">L2</span>
              <span class="phase-value" :class="getVoltageClass(realtimeData?.U2)">
                {{ realtimeData?.U2 || 0 }} <span class="phase-unit">V</span>
              </span>
            </div>
            <div class="phase-row">
              <span class="phase-label">L3</span>
              <span class="phase-value" :class="getVoltageClass(realtimeData?.U3)">
                {{ realtimeData?.U3 || 0 }} <span class="phase-unit">V</span>
              </span>
            </div>
          </div>
          <div v-else class="phase-section">
            <div class="phase-row">
              <span class="phase-label">L1</span>
              <span class="phase-value" :class="getVoltageClass(realtimeData?.Upp1)">
                {{ realtimeData?.Upp1 || 0 }} <span class="phase-unit">V</span>
              </span>
            </div>
            <div class="phase-row">
              <span class="phase-label">L2</span>
              <span class="phase-value" :class="getVoltageClass(realtimeData?.Upp2)">
                {{ realtimeData?.Upp2 || 0 }} <span class="phase-unit">V</span>
              </span>
            </div>
            <div class="phase-row">
              <span class="phase-label">L3</span>
              <span class="phase-value" :class="getVoltageClass(realtimeData?.Upp3)">
                {{ realtimeData?.Upp3 || 0 }} <span class="phase-unit">V</span>
              </span>
            </div>
          </div>
        </div>

        <!-- 전류 상세 -->
        <div class="detail-block">
          <span class="detail-block-title">{{ t('dashboard.meter.current') }}</span>
          <div class="phase-section">
            <div class="phase-row">
              <span class="phase-label">L1</span>
              <span class="phase-value" :class="getCurrentClass(realtimeData?.I1)">
                {{ realtimeData?.I1 || 0 }} <span class="phase-unit">A</span>
              </span>
            </div>
            <div class="phase-row">
              <span class="phase-label">L2</span>
              <span class="phase-value" :class="getCurrentClass(realtimeData?.I2)">
                {{ realtimeData?.I2 || 0 }} <span class="phase-unit">A</span>
              </span>
            </div>
            <div class="phase-row">
              <span class="phase-label">L3</span>
              <span class="phase-value" :class="getCurrentClass(realtimeData?.I3)">
                {{ realtimeData?.I3 || 0 }} <span class="phase-unit">A</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { watch, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRealtimeStore } from '@/store/realtime'
export default {
  name: 'SingleMeasCard_Meter',
  props: {
    channel: String,
    data: Object,
  },
  setup(props) {
    const { t } = useI18n()
    const channel = ref(props.channel)
   // const data2 = ref({})
    const store = useRealtimeStore()
    const realtimeData = computed(() => {
      // 'main' → 'Main' 변환 (Store의 getter가 'Main'/'Sub'를 기대)
      const channelName = props.channel?.toLowerCase() === 'main' ? 'Main' : 'Sub'
     // console.log('useRealtimeStore',channelName,store.getChannelData(channelName))
      return store.getChannelData(channelName) || {}
    })

    // 데이터 존재 확인
    const hasData = computed(() => {
      return Object.keys(realtimeData.value).length > 0
    })
    // 전압 상태 클래스 - 다크모드 개선
    const getVoltageClass = (value) => {
      if (!value) return 'text-gray-500 dark:text-gray-400'
      if (value < 200 || value > 240) return 'text-red-600 dark:text-red-400 font-bold'
      if (value < 210 || value > 230) return 'text-orange-500 dark:text-orange-400 font-semibold'
      return 'text-green-600 dark:text-green-400 font-medium'
    }

    // 전류 상태 클래스 - 다크모드 개선
    const getCurrentClass = (value) => {
      if (!value) return 'text-gray-500 dark:text-gray-400'
      if (value > 100) return 'text-red-600 dark:text-red-400 font-bold'
      if (value > 80) return 'text-orange-500 dark:text-orange-400 font-semibold'
      if (value > 60) return 'text-yellow-600 dark:text-yellow-400 font-semibold'
      return 'text-green-600 dark:text-green-400 font-medium'
    }

    // 역률 상태 클래스 - 다크모드 개선
    const getPowerFactorClass = (value) => {
      if (!value) return 'text-gray-500 dark:text-gray-400'
      if (value < 80) return 'text-red-600 dark:text-red-400 font-bold'
      if (value < 90) return 'text-orange-500 dark:text-orange-400 font-semibold'
      if (value < 95) return 'text-yellow-600 dark:text-yellow-400 font-semibold'
      return 'text-green-600 dark:text-green-400 font-medium'
    }

    // props.data 감시
    // watch(
    //   () => props.data,
    //   (newData) => {
    //     if (newData && Object.keys(newData).length > 0) {
    //       data2.value = newData
    //     }
    //   },
    //   { immediate: true }
    // )

    return {
      channel,
      //data2,
      t,
      getVoltageClass,
      getCurrentClass,
      getPowerFactorClass,
      realtimeData,
      hasData,
    }
  },
}
</script>

<style scoped>
.card-wrap {
  @apply col-span-full sm:col-span-6 xl:col-span-4;
  @apply bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900;
  @apply shadow-lg rounded-xl border border-gray-200/50 dark:border-gray-700/50;
  @apply overflow-hidden flex flex-col;
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
  @apply px-4 py-3 flex-1 flex flex-col;
}

/* Summary row */
.summary-row {
  @apply grid grid-cols-3 gap-3 mb-3 pb-3 border-b border-gray-100 dark:border-gray-700;
}
.summary-item {
  @apply flex flex-col items-center text-center;
}
.summary-label {
  @apply text-sm text-gray-600 dark:text-gray-400 mb-1;
}
.summary-value {
  @apply text-2xl font-extrabold text-gray-800 dark:text-white tabular-nums flex items-center justify-center gap-1.5;
}
.summary-unit {
  @apply text-sm font-medium text-gray-600 dark:text-gray-400;
}

/* Detail grid */
.detail-grid {
  @apply grid grid-cols-2 gap-3 flex-1;
}
.detail-block {
  @apply bg-gray-50 dark:bg-gray-700/50 rounded-lg overflow-hidden;
}
.detail-block-title {
  @apply block text-sm font-bold text-gray-700 dark:text-white px-3 py-1.5;
  @apply bg-gray-100 dark:bg-gray-600 border-b border-gray-200 dark:border-gray-500;
}
.phase-section {
  @apply px-3 py-2 space-y-1;
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
