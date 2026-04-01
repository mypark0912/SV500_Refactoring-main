<template v-if="hasData">
  <div class="card-wrap">
    <!-- 헤더 -->
    <div class="card-header">
      <h3 class="card-title meter-accent-orange">{{ t('dashboard.pq.singletitle') }}</h3>
      <span class="card-channel">
        {{ channel == 'Main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>

    <!-- 불평형률 & 역률 & 고조파 통합 섹션 -->
    <div class="card-body">
      <!-- 불평형률 + 역률 수평 배치 -->
      <div class="horizontal-group">
        <!-- 불평형률 -->
        <div class="data-subsection flex-1">
          <h3 class="subsection-title">{{ t('dashboard.pq.unbalance') }}</h3>
          <div class="unbalance-vertical">
            <!-- 전압 불평형 -->
            <div class="compact-item">
              <div class="compact-header">
                <span class="compact-label">{{ t('dashboard.meter.voltage') }}</span>
                <span class="compact-value" :class="getUnbalanceClass(data2.Ubal1)">
                  {{ data2.Ubal1?.toFixed(1) || 0 }}%
                </span>
              </div>
              <div class="mini-progress">
                <div
                  class="mini-fill bg-violet-400"
                  :style="{ width: Math.min(data2.Ubal1 || 0, 100) + '%' }"
                ></div>
              </div>
            </div>

            <!-- 전류 불평형 -->
            <div class="compact-item">
              <div class="compact-header">
                <span class="compact-label">{{ t('dashboard.meter.current') }}</span>
                <span class="compact-value" :class="getUnbalanceClass(data2.Ibal1)">
                  {{ data2.Ibal1?.toFixed(1) || 0 }}%
                </span>
              </div>
              <div class="mini-progress">
                <div
                  class="mini-fill bg-sky-400"
                  :style="{ width: Math.min(data2.Ibal1 || 0, 100) + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 역률 게이지 -->
        <div class="data-subsection flex-1">
          <h3 class="subsection-title">{{ t('dashboard.pq.powerfactor') }}</h3>
          <div class="gauge-wrapper">
            <div class="gauge">
              <div class="gauge-body" :style="{ '--pf': Math.min((data2.PF4 || 0) / 100, 1) }">
                <div class="gauge-cover">
                  <span class="gauge-value" :class="getPFClass(data2.PF4)">
                    {{ data2.PF4?.toFixed(2) || '0.00' }}<span class="gauge-unit">%</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 고조파 -->
      <div class="data-subsection">
        <h3 class="subsection-title">{{ t('dashboard.pq.THD') }}</h3>

        <!-- CSS 바 차트 -->
        <div class="css-bar-chart">
          <div class="chart-bars">
            <div
              v-for="(item, index) in chartItems"
              :key="index"
              class="bar-item"
            >
              <!-- 바 컨테이너 -->
              <div class="bar-container">
                <div
                  class="bar-fill"
                  :class="item.colorClass"
                  :style="{ height: item.height + '%' }"
                >
                  <!-- 값 라벨 -->
                  <div class="bar-label">{{ item.value }}%</div>
                </div>
              </div>

              <!-- 하단 라벨 -->
              <div class="bar-name">{{ item.label }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { watch, ref, computed, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRealtimeStore } from '@/store/realtime'
import axios from "axios";
export default {
  name: 'SingleMeasCard_PQ',
  props: {
    channel: String,
    asset: String,
    isInv : Boolean,
  },
  // emits: ['data-change'],
  setup(props) {
    const { t } = useI18n()
    const channel = computed(() => props.channel)
    const asset = computed(() => props.asset)
    const isInverter = computed(() => props.isInv)
    const store = useRealtimeStore()
    const data2 = computed(() => {
      // 'main' → 'Main' 변환 (Store의 getter가 'Main'/'Sub'를 기대)
      const channelName = channel.value?.toLowerCase() === 'main' ? 'Main' : 'Sub'
      return store.getChannelData(channelName) || {}
    })
    const chartData = ref([]);
    const pollTimer = ref(null);

    const getTHD = async () => {
      try {
        const response = await axios.get(`/api/getRealTimeTHD/${asset.value}`)
        if (response.data.success) {
          chartData.value = response.data.data;
        }
      } catch (err) {
        console.error(`❌ ${channel.value} 채널 실패:`, err)
      }
    }

    // 데이터 존재 확인
    const hasData = computed(() => {
      if (isInverter.value) {
        return chartData.value.length > 0
      }
      return Object.keys(data2.value).length > 0
    })
    // 고조파 차트 데이터 설정
    const dataKeys = ['thdu total', 'thdi total', 'tddi total']
    const labels = ['THD-U', 'THD-I', 'TDD-I']
    const colors = ['pink', 'indigo', 'teal']

    // 차트 아이템 계산
    const chartItems = computed(() => {
      if (isInverter.value) {
        // API 데이터 사용 (getRealTimeTHD)
        const values = chartData.value.map(item => parseFloat(item.Value || 0))
        const maxValue = Math.max(...values, 10)

        return chartData.value.map((item, index) => {
          const value = parseFloat(item.Value || 0).toFixed(1)
          const height = (parseFloat(item.Value || 0) / maxValue) * 100
          return {
            label: labels[index],
            value,
            height: Math.max(height, 5),
            colorClass: `bar-${colors[index % colors.length]}`
          }
        })
      } else {
        // 기존 store 데이터 사용
        const values = dataKeys.map(key => parseFloat(data2.value[key] || 0))
        const maxValue = Math.max(...values, 10)

        return labels.map((label, index) => {
          const value = values[index].toFixed(1)
          const height = (values[index] / maxValue) * 100
          return {
            label,
            value,
            height: Math.max(height, 5),
            colorClass: `bar-${colors[index]}`
          }
        })
      }
    })

    // 불평형률 상태 클래스 - 다크모드 개선
    const getUnbalanceClass = (value) => {
      if (!value) return 'text-gray-500 dark:text-gray-400'
      if (value >= 3) return 'text-red-600 dark:text-red-400 font-bold'
      if (value >= 2) return 'text-orange-500 dark:text-orange-400 font-semibold'
      if (value >= 1) return 'text-yellow-600 dark:text-yellow-400 font-semibold'
      return 'text-green-600 dark:text-green-400 font-medium'
    }

    // 역률 상태 클래스
    const getPFClass = (value) => {
      if (!value) return 'text-gray-500 dark:text-gray-400'
      if (value >= 0.95) return 'text-green-600 dark:text-green-400'
      if (value >= 0.9) return 'text-yellow-600 dark:text-yellow-400'
      return 'text-red-600 dark:text-red-400'
    }

    // props.data 감시
    const startPolling = () => {
      stopPolling()
      getTHD() // 즉시 1회 호출
      pollTimer.value = setInterval(getTHD, 5 * 60 * 1000) // 5분
    }

    const stopPolling = () => {
      if (pollTimer.value) {
        clearInterval(pollTimer.value)
        pollTimer.value = null
      }
    }

    // chartItems computed는 이전과 동일 ...

    watch(
      () => props.asset,
      () => {
        if (isInverter.value) {
          startPolling()
        } else {
          stopPolling()
          chartData.value = []
        }
      },
      { immediate: true, deep: true }
    )

    onBeforeUnmount(() => {
      stopPolling()
    })

    return {
      channel,
      data2,
      t,
      getUnbalanceClass,
      getPFClass,
      chartItems,
      hasData,
      asset,
      chartData,
      isInverter,
    }
  },
}
</script>

<style scoped>
/* ── dashboard2 card shell ── */
.card-wrap {
  @apply col-span-full sm:col-span-6 xl:col-span-3;
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
.meter-accent-orange::before {
  @apply bg-orange-500;
}
.card-channel {
  @apply text-gray-500 dark:text-gray-500;
  font-size: 10px;
}
.card-body {
  @apply px-4 py-3;
}

/* ── layout ── */
.horizontal-group {
  @apply flex gap-4;
}

.data-subsection {
  @apply space-y-2;
}

.subsection-title {
  @apply text-sm font-semibold text-gray-700 dark:text-white;
  @apply flex items-center gap-2;
}

.subsection-title::before {
  content: '';
  @apply w-2 h-2 bg-orange-500 rounded-full;
}

.unbalance-vertical {
  @apply space-y-5;
}

/* ── 역률 게이지 ── */
.gauge-wrapper {
  @apply flex flex-col items-center;
}

.gauge {
  width: 100%;
  max-width: 120px;
  position: relative;
}

.gauge-body {
  --pf: 0;
  width: 100%;
  padding-bottom: 50%;
  position: relative;
  overflow: hidden;
}

.gauge-body::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 200%;
  border-radius: 50%;
  box-sizing: border-box;
  background: conic-gradient(
    from 0.75turn,
    #10b981 calc(var(--pf) * 0.5turn),
    #e5e7eb calc(var(--pf) * 0.5turn),
    #e5e7eb 0.5turn,
    transparent 0.5turn
  );
}

:is(.dark) .gauge-body::before {
  background: conic-gradient(
    from 0.75turn,
    #34d399 calc(var(--pf) * 0.5turn),
    #374151 calc(var(--pf) * 0.5turn),
    #374151 0.5turn,
    transparent 0.5turn
  );
}

.gauge-cover {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 70%;
  padding-bottom: 35%;
  background: white;
  border-radius: 100% 100% 0 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

:is(.dark) .gauge-cover {
  background: #1f2937;
}

.gauge-value {
  position: absolute;
  bottom: 2px;
  @apply text-sm font-bold;
}

.gauge-unit {
  @apply text-xs font-medium ml-0.5;
}

/* ── 불평형률 compact items ── */
.compact-item {
  @apply space-y-1;
}

.compact-header {
  @apply flex justify-between items-center;
}

.compact-label {
  @apply text-sm font-medium text-gray-600 dark:text-gray-300;
}

.compact-value {
  @apply text-sm font-bold;
}

.mini-progress {
  @apply w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden;
}

.mini-fill {
  @apply h-full rounded-full transition-all duration-500 ease-out;
}

/* ── CSS 바 차트 스타일 ── */
.css-bar-chart {
  @apply w-full p-4 pt-8;
}

.chart-bars {
  @apply flex justify-around items-end gap-4 h-24;
  @apply relative;
}

.bar-item {
  @apply flex-1 flex flex-col items-center;
  @apply max-w-[60px];
}

.bar-container {
  @apply relative w-full h-16 flex items-end justify-center;
}

.bar-fill {
  @apply w-full rounded-t transition-all duration-700 ease-out;
  @apply relative flex items-start justify-center;
  @apply min-h-[8px];
}

.bar-label {
  @apply text-xs font-bold;
  @apply absolute bottom-full left-1/2 transform -translate-x-1/2;
  @apply text-center whitespace-nowrap;
  @apply text-gray-800 dark:text-white;
  @apply mb-1;
}

.bar-name {
  @apply text-xs font-semibold text-gray-700 dark:text-white;
  @apply mt-2 text-center;
}

/* 바 색상 */
.bar-pink {
  @apply bg-gradient-to-t from-pink-500 to-pink-400;
  @apply dark:from-pink-400 dark:to-pink-300;
}

.bar-indigo {
  @apply bg-gradient-to-t from-indigo-500 to-indigo-400;
  @apply dark:from-indigo-400 dark:to-indigo-300;
}

.bar-teal {
  @apply bg-gradient-to-t from-teal-500 to-teal-400;
  @apply dark:from-teal-400 dark:to-teal-300;
}

/* 반응형 개선 */
@media (max-width: 640px) {
  .unbalance-vertical {
    @apply space-y-4;
  }

  .card-body {
    @apply space-y-3;
  }

  .chart-bars {
    @apply gap-2 h-20;
  }

  .bar-container {
    @apply h-12;
  }

  .bar-label {
    @apply text-xs;
  }

  .bar-name {
    @apply text-xs;
  }
}

/* 다크모드 개선 */
.mini-fill.bg-violet-400 {
  @apply dark:bg-violet-300;
}

.mini-fill.bg-sky-400 {
  @apply dark:bg-sky-300;
}
</style>
