<template v-if="hasData">
  <div class="card-wrap">
    <!-- 헤더 -->
    <div class="card-header">
      <h3 class="card-title meter-accent-orange">{{ t('dashboard.pq.singletitle') }}</h3>
      <span class="card-channel">
        {{ channel == 'Main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>

    <div class="card-body">
      <!-- 상단: 불평형률 -->
      <div class="data-subsection">
        <h3 class="subsection-title">{{ t('dashboard.pq.unbalance') }}</h3>
        <div class="unbalance-vertical">
          <div class="compact-item">
            <div class="compact-header">
              <span class="compact-label">{{ t('dashboard.meter.voltage') }}</span>
              <span class="compact-value" :class="getUnbalanceClass(data2.Ubal1)">
                {{ data2.Ubal1?.toFixed(1) || 0 }}%
              </span>
            </div>
            <div class="mini-progress">
              <div class="mini-fill bg-violet-400" :style="{ width: Math.min(data2.Ubal1 || 0, 100) + '%' }"></div>
            </div>
          </div>
          <div class="compact-item">
            <div class="compact-header">
              <span class="compact-label">{{ t('dashboard.meter.current') }}</span>
              <span class="compact-value" :class="getUnbalanceClass(data2.Ibal1)">
                {{ data2.Ibal1?.toFixed(1) || 0 }}%
              </span>
            </div>
            <div class="mini-progress">
              <div class="mini-fill bg-sky-400" :style="{ width: Math.min(data2.Ibal1 || 0, 100) + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 하단: 역률(좌) + THD 링(우) -->
      <div class="bottom-group">
        <!-- 역률 게이지 -->
        <div class="pf-section">
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

        <!-- THD 링 인디케이터 -->
        <div class="thd-section">
          <h3 class="subsection-title">{{ t('dashboard.pq.THD') }}</h3>
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
  name: 'SingleMeasCard_PQ',
  props: {
    channel: String,
    asset: String,
  },
  setup(props) {
    const { t } = useI18n()
    const channel = computed(() => props.channel)
    const asset = computed(() => props.asset)
    const store = useRealtimeStore()
    const data2 = computed(() => {
      // 'main' → 'Main' 변환 (Store의 getter가 'Main'/'Sub'를 기대)
      const channelName = channel.value?.toLowerCase() === 'main' ? 'Main' : 'Sub'
      return store.getChannelData(channelName) || {}
    })

    const hasData = computed(() => Object.keys(data2.value).length > 0)

    const dataKeys = ['thdu total', 'thdi total', 'tddi total']
    const labels = ['THD-U', 'THD-I', 'TDD-I']
    const colors = ['pink', 'indigo', 'teal']

    const chartItems = computed(() => {
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

    return {
      channel,
      data2,
      t,
      getUnbalanceClass,
      getPFClass,
      chartItems,
      hasData,
      asset,
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
  @apply text-xs;
}
.card-body {
  @apply px-4 py-3;
}

/* ── layout ── */
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
  @apply space-y-3;
}

.bottom-group {
  @apply flex gap-4 pt-3 border-t border-gray-100 dark:border-gray-700;
}

.pf-section {
  @apply flex-1 space-y-2;
}

.thd-section {
  @apply flex-1 space-y-2;
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

/* ── THD 링 인디케이터 ── */
.thd-rings {
  @apply flex justify-around items-center gap-2;
}
.ring-item {
  @apply flex flex-col items-center gap-1;
  position: relative;
}
.ring-svg {
  width: 56px;
  height: 56px;
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
.ring-fill.bar-pink {
  stroke: #ec4899;
}
.ring-fill.bar-indigo {
  stroke: #6366f1;
}
.ring-fill.bar-teal {
  stroke: #14b8a6;
}
.ring-center {
  position: absolute;
  top: 0;
  left: 0;
  width: 56px;
  height: 56px;
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
  @apply text-[10px] font-semibold text-gray-600 dark:text-gray-400;
}

/* 반응형 개선 */
@media (max-width: 640px) {
  .unbalance-vertical {
    @apply space-y-4;
  }

  .card-body {
    @apply space-y-3;
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
