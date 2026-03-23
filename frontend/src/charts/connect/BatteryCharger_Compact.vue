<template>
  <div class="modern-chart-container">
    <!-- 배터리 컨테이너 (헤더 제거) -->
    <div class="battery-wrapper">
      <div class="battery-grid" :style="gridStyle">
        <div
          v-for="(item, index) in batteryData"
          :key="index"
          class="battery-item"
          @mouseenter="showTooltip($event, item, index)"
          @mouseleave="hideTooltip"
          @mousemove="updateTooltipPosition($event)"
        >
          <div class="item-title">{{ item.title }}</div>
          <div class="battery-container">
            <div class="battery-body">
              <div class="battery-segments">
                <div
                  v-for="segment in 4"
                  :key="segment"
                  class="battery-segment"
                  :class="[
                    `segment-${segment}`,
                    {
                      'active': segment <= item.value && item.value > 0,
                      'inactive': segment > item.value || item.value === 0
                    }
                  ]"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 툴팁 -->
      <div
        v-if="tooltip.show"
        class="custom-tooltip"
        :style="tooltipStyle"
      >
        <div class="tooltip-content">
          <div class="tooltip-title">{{ tooltip.title }}</div>
          <div class="tooltip-status">{{ tooltip.status }}</div>
        </div>
      </div>

      <!-- 로딩 오버레이 -->
      <div v-if="isLoading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <span class="loading-text">Loading...</span>
      </div>
    </div>

    <!-- 범례 (한줄) -->
    <div class="legend-inline">
      <span class="legend-label">{{t('diagnosis.tabContext.legend')}}</span>
      <div class="legend-item"><div class="legend-color status-stopped"></div><span>{{t('diagnosis.tabContext.st0')}}</span></div>
      <div class="legend-item"><div class="legend-color status-normal"></div><span>{{t('diagnosis.tabContext.st1')}}</span></div>
      <div class="legend-item"><div class="legend-color status-warning"></div><span>{{t('diagnosis.tabContext.st2')}}</span></div>
      <div class="legend-item"><div class="legend-color status-alert"></div><span>{{t('diagnosis.tabContext.st3')}}</span></div>
      <div class="legend-item"><div class="legend-color status-danger"></div><span>{{t('diagnosis.tabContext.st4')}}</span></div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, inject } from 'vue'
import { useDark } from '@vueuse/core'
import { useI18n } from 'vue-i18n'

export default {
  name: 'BatteryChargerCompact',
  props: ['data', 'width', 'height'],
  setup(props) {
    const { t, locale } = useI18n()
    const isLoading = ref(false)
    const darkMode = useDark()
    const data_state = inject('data_state');
    const data_recordtime = inject('data_recordtime');
    const tooltip = ref({
      show: false,
      title: '',
      status: '',
      x: 0,
      y: 0
    })

    const batteryData = computed(() => {
      if (!props.data?.labels || !props.data?.datasets?.[0]?.data) return []

      return props.data.labels.map((label, index) => {
        const value = props.data.datasets[0].data[index]
        const title = props.data.titles?.[index]?.[locale.value] || label

        return {
          title: title,
          value: value === 0.2 ? 0 : value,
          originalIndex: index
        }
      })
    })

    const gridStyle = computed(() => {
      const itemCount = batteryData.value.length
      let columns = 4

      if (itemCount <= 4) columns = 4
      else if (itemCount <= 8) columns = 4
      else if (itemCount <= 12) columns = 4
      else columns = 5

      return {
        'grid-template-columns': `repeat(${columns}, 1fr)`,
        'gap': '20px'
      }
    })

    const getStatusText = (value) => {
      const statusLabels = [
        t('diagnosis.tabContext.st0'),
        t('diagnosis.tabContext.st1'),
        t('diagnosis.tabContext.st2'),
        t('diagnosis.tabContext.st3'),
        t('diagnosis.tabContext.st4')
      ]
      return statusLabels[Math.floor(value)] || t('diagnosis.tabContext.st0')
    }

    const showTooltip = (event, item, index) => {
      const batteryItem = event.currentTarget
      const containerRect = batteryItem.closest('.battery-wrapper').getBoundingClientRect()
      const itemRect = batteryItem.getBoundingClientRect()

      tooltip.value = {
        show: true,
        title: item.title,
        status: getStatusText(item.value),
        x: itemRect.left - containerRect.left + itemRect.width / 2,
        y: itemRect.top - containerRect.top - 10
      }
    }

    const updateTooltipPosition = (event) => {
      if (tooltip.value.show) {
        const batteryItem = event.currentTarget
        const containerRect = batteryItem.closest('.battery-wrapper').getBoundingClientRect()

        tooltip.value.x = event.clientX - containerRect.left
        tooltip.value.y = event.clientY - containerRect.top - 40
      }
    }

    const hideTooltip = () => {
      tooltip.value.show = false
    }

    const tooltipStyle = computed(() => {
      return {
        left: `${tooltip.value.x}px`,
        top: `${tooltip.value.y}px`,
        transform: 'translate(-50%, -100%)'
      }
    })

    const handleScroll = () => {
      if (tooltip.value.show) {
        hideTooltip()
      }
    }

    onMounted(() => {
      isLoading.value = false
      window.addEventListener('scroll', handleScroll, true)
    })

    onUnmounted(() => {
      window.removeEventListener('scroll', handleScroll, true)
    })

    return {
      isLoading,
      batteryData,
      gridStyle,
      tooltip,
      tooltipStyle,
      getStatusText,
      showTooltip,
      hideTooltip,
      updateTooltipPosition,
      t,
      locale,
      data_state,
      data_recordtime,
    }
  }
}
</script>

<style scoped>
.modern-chart-container {
  @apply bg-gradient-to-br from-white via-gray-50 to-white dark:from-gray-800 dark:via-gray-900 dark:to-gray-800;
  @apply overflow-hidden backdrop-blur-sm;
}

/* 배터리 래퍼 */
.battery-wrapper {
  @apply relative px-4 pt-4 pb-2;
  min-height: 200px;
}

.battery-grid {
  @apply grid w-full;
}

/* 배터리 아이템 */
.battery-item {
  @apply flex flex-col items-center p-4 rounded-lg cursor-pointer;
  @apply transition-all duration-300 ease-in-out;
  @apply transform hover:scale-105 hover:shadow-md;
  @apply bg-white/60 dark:bg-gray-800/60 backdrop-blur-sm;
  @apply border border-gray-200/30 dark:border-gray-700/30;
  @apply min-h-[100px];
  animation: fadeInUp 0.6s ease-out forwards;
  opacity: 0;
  transform: translateY(20px);
}

.battery-item:nth-child(1) { animation-delay: 0.1s; }
.battery-item:nth-child(2) { animation-delay: 0.2s; }
.battery-item:nth-child(3) { animation-delay: 0.3s; }
.battery-item:nth-child(4) { animation-delay: 0.4s; }
.battery-item:nth-child(5) { animation-delay: 0.5s; }
.battery-item:nth-child(6) { animation-delay: 0.6s; }
.battery-item:nth-child(n+7) { animation-delay: 0.7s; }

.item-title {
  @apply text-sm font-semibold text-gray-800 dark:text-gray-200;
  @apply text-center mb-3;
  @apply leading-tight;
  pointer-events: none;
}

.battery-container {
  @apply relative;
  pointer-events: none;
}

.battery-body {
  @apply w-24 h-12 rounded-lg border-2 border-gray-300 dark:border-gray-600;
  @apply bg-gray-100 dark:bg-gray-700;
  @apply p-1.5;
  @apply transition-all duration-300;
}

.battery-segments {
  @apply flex gap-1.5 h-full;
}

.battery-segment {
  @apply flex-1 rounded-sm;
  @apply transition-all duration-500 ease-out;
  @apply relative;
}

.battery-segment.segment-1 { @apply bg-green-500; }
.battery-segment.segment-2 { @apply bg-yellow-500; }
.battery-segment.segment-3 { @apply bg-orange-500; }
.battery-segment.segment-4 { @apply bg-red-500; }

.battery-segment.active {
  @apply opacity-100 scale-100;
  @apply shadow-inner;
  filter: none;
}

.battery-segment.inactive {
  @apply opacity-40;
  @apply bg-gray-400 dark:bg-gray-500;
  filter: blur(1px) grayscale(80%);
  transform: scale(0.95);
}

/* 툴팁 */
.custom-tooltip {
  @apply absolute z-[9999] px-3 py-2 rounded-lg shadow-lg;
  @apply bg-gray-900 dark:bg-gray-800 text-white;
  @apply text-sm font-medium;
  @apply border border-gray-700 dark:border-gray-600;
  @apply pointer-events-none;
  @apply whitespace-nowrap;
  max-width: 200px;
  margin-top: -10px;
}

.custom-tooltip::after {
  content: '';
  @apply absolute top-full left-1/2 transform -translate-x-1/2;
  @apply border-4 border-transparent border-t-gray-900 dark:border-t-gray-800;
}

.tooltip-content { @apply relative z-10; }
.tooltip-title { @apply font-semibold; }
.tooltip-status { @apply text-gray-300 text-xs mt-1; }

/* 범례 (한줄) */
.legend-inline {
  @apply flex items-center gap-4 px-4 py-2;
  @apply border-t border-gray-200/50 dark:border-gray-700/50;
  @apply bg-gray-50/30 dark:bg-gray-800/30;
}

.legend-label {
  @apply text-xs font-semibold text-gray-500 dark:text-gray-400;
  @apply mr-1;
}

.legend-item {
  @apply flex items-center gap-1.5;
}

.legend-color {
  @apply w-2.5 h-2.5 rounded-full border;
}

.status-stopped { @apply bg-gray-400 border-gray-500; }
.status-normal { @apply bg-green-500 border-green-600; }
.status-warning { @apply bg-yellow-500 border-yellow-600; }
.status-alert { @apply bg-orange-500 border-orange-600; }
.status-danger { @apply bg-red-500 border-red-600; }

.legend-item span {
  @apply text-xs text-gray-600 dark:text-gray-400;
}

/* 로딩 오버레이 */
.loading-overlay {
  @apply absolute inset-0 flex flex-col items-center justify-center;
  @apply bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm;
  @apply rounded-xl;
}

.loading-spinner {
  @apply w-8 h-8 border-3 border-blue-200 border-t-blue-600 rounded-full;
  animation: spin 1s linear infinite;
}

.loading-text {
  @apply mt-3 text-sm font-medium text-gray-600 dark:text-gray-400;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeInUp {
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .battery-grid { grid-template-columns: repeat(3, 1fr) !important; @apply gap-4; }
}

@media (max-width: 640px) {
  .battery-grid { grid-template-columns: repeat(2, 1fr) !important; @apply gap-3; }
  .battery-item { @apply p-3; }
  .legend-inline { @apply gap-2; }
}

@media (max-width: 480px) {
  .battery-grid { grid-template-columns: repeat(1, 1fr) !important; }
  .battery-wrapper { @apply px-3; }
}
</style>
