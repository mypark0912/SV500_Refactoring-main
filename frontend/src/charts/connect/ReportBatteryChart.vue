<template>
  <div 
    class="battery-chart-container"
    :class="isPdfMode ? 'bg-white border-gray-200' : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'"
  >
    <!-- 헤더 섹션 -->
    <div 
      class="chart-header"
      :class="isPdfMode ? 'bg-blue-50 border-blue-100' : 'bg-blue-50 dark:bg-gray-900 border-blue-100 dark:border-gray-700'"
    >
      <div class="flex justify-between items-center">
        <h3 
          class="chart-title"
          :class="isPdfMode ? 'text-gray-800' : 'text-gray-800 dark:text-gray-100'"
        >
          {{ chartTitle }}
        </h3>
        <!-- 타임스탬프 표시 -->
        <div v-if="timestamp" class="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 dark:bg-indigo-900/30 rounded-md">
          <span class="text-sm text-indigo-600 dark:text-indigo-400 font-medium">📌 {{ t('report.lastSaved') || 'Last saved datetime' }}:</span>
          <span class="text-sm text-indigo-700 dark:text-indigo-300 font-semibold">{{ formatTimestamp(timestamp) }}</span>
        </div>
      </div>
    </div>

    <!-- 배터리 그리드 -->
    <div class="battery-wrapper">
      <div class="battery-grid" :style="gridStyle">
        <div
          v-for="(item, index) in batteryData"
          :key="index"
          class="battery-item"
          @mouseenter="showTooltip($event, item)"
          @mouseleave="hideTooltip"
          @mousemove="updateTooltipPosition($event)"
        >
          <!-- 항목 타이틀 (위에) -->
          <div 
            class="item-title"
            :class="isPdfMode ? 'text-gray-700' : 'text-gray-700 dark:text-gray-300'"
          >
            {{ item.title }}
          </div>
          
          <!-- 배터리 바디 (가로) -->
          <div class="battery-body" :class="getStatusClass(item.status)">
            <!-- 배터리 헤드 (양극 - 오른쪽) -->
            <div class="battery-head" :class="getStatusClass(item.status)"></div>
            <!-- 충전 레벨 표시 -->
            <div 
              class="battery-fill" 
              :class="getStatusClass(item.status)"
            ></div>
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
          <div class="tooltip-status" :class="getStatusClass(tooltip.status)">
            {{ getStatusText(tooltip.status) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 범례 -->
    <div class="chart-legend">
      <div v-for="(item, idx) in legendItems" :key="idx" class="legend-item">
        <span class="legend-battery" :class="item.class"></span>
        <span 
          class="legend-label"
          :class="isPdfMode ? 'text-gray-600' : 'text-gray-600 dark:text-gray-400'"
        >
          {{ item.label }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, inject } from 'vue'
import { useDark } from '@vueuse/core'
import { useI18n } from 'vue-i18n'

export default {
  name: 'ReportBatteryChart',
  props: {
    data: {
      type: Object,
      required: true
    },
    mode: {
      type: String,
      default: 'DiagnosisDetail'
    },
    height: {
      type: Number,
      default: 350
    },
    timestamp: {
      type: String,
      default: null
    }
  },
  setup(props) {
    const isPdfMode = inject('isPdfMode', false)
    const { t, locale } = useI18n()
    const darkMode = useDark()

    // 툴팁 상태
    const tooltip = ref({
      show: false,
      title: '',
      status: 0,
      x: 0,
      y: 0
    })

    // 타임스탬프 포맷
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return '';
      const date = new Date(timestamp);
      return date.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    };

    // 모드에 따른 타이틀
    const chartTitle = computed(() => {
      const titleMap = {
        'PowerQuality': t('diagnosis.tabTitle.detailTitle_pq'),
        'DiagnosisDetail': t('diagnosis.tabTitle.detailTitle'),
      }
      return titleMap[props.mode] || t('diagnosis.tabTitle.detailTitle')
    })

    // 배터리 데이터 변환
    const batteryData = computed(() => {
      if (!props.data?.Names || !props.data?.Values) return []

      return props.data.Names.map((name, index) => {
        const status = props.data.Values[index]
        const title = props.data.Titles?.[index]?.[locale.value] || name
        return {
          title: title,
          status: status === 0.2 ? 0 : Math.floor(status),
          originalIndex: index
        }
      })
    })

    // 그리드 스타일 계산
    const gridStyle = computed(() => {
      const itemCount = batteryData.value.length
      let columns = 6
      
      if (itemCount <= 4) columns = 4
      else if (itemCount <= 6) columns = 6
      else if (itemCount <= 9) columns = 6
      else if (itemCount <= 12) columns = 6
      else columns = 8
      
      return {
        'grid-template-columns': `repeat(${columns}, 1fr)`,
        'gap': '16px'
      }
    })

    // 상태별 클래스 반환
    const getStatusClass = (status) => {
      const statusClasses = {
        0: 'status-stop',
        1: 'status-ok',
        2: 'status-warning',
        3: 'status-inspect',
        4: 'status-repair'
      }
      return statusClasses[Math.floor(status)] || 'status-stop'
    }

    // 상태별 채움 높이 (항상 100%)
    const getFillHeight = (status) => {
      return '100%'
    }

    // 상태 텍스트 반환
    const getStatusText = (status) => {
      if (props.mode === 'PowerQuality') {
        const labels = [
          t('diagnosis.tabContext.pqfe0'),
          t('diagnosis.tabContext.pqfe1'),
          t('diagnosis.tabContext.pqfe2'),
          t('diagnosis.tabContext.pqfe3'),
          t('diagnosis.tabContext.pqfe4'),
        ]
        return labels[Math.floor(status)] || labels[0]
      } else {
        const labels = [
          t('diagnosis.tabContext.st0'),
          t('diagnosis.tabContext.st1'),
          t('diagnosis.tabContext.st2'),
          t('diagnosis.tabContext.st3'),
          t('diagnosis.tabContext.st4'),
        ]
        return labels[Math.floor(status)] || labels[0]
      }
    }

    // 범례 아이템
    const legendItems = computed(() => {
      if (props.mode === 'PowerQuality') {
        return [
          { label: t('diagnosis.tabContext.pqfe0'), class: 'status-stop' },
          { label: t('diagnosis.tabContext.pqfe1'), class: 'status-ok' },
          { label: t('diagnosis.tabContext.pqfe2'), class: 'status-warning' },
          { label: t('diagnosis.tabContext.pqfe3'), class: 'status-inspect' },
          { label: t('diagnosis.tabContext.pqfe4'), class: 'status-repair' },
        ]
      } else {
        return [
          { label: t('diagnosis.tabContext.st0'), class: 'status-stop' },
          { label: t('diagnosis.tabContext.st1'), class: 'status-ok' },
          { label: t('diagnosis.tabContext.st2'), class: 'status-warning' },
          { label: t('diagnosis.tabContext.st3'), class: 'status-inspect' },
          { label: t('diagnosis.tabContext.st4'), class: 'status-repair' },
        ]
      }
    })

    // 툴팁 표시
    const showTooltip = (event, item) => {
      const batteryItem = event.currentTarget
      const containerRect = batteryItem.closest('.battery-wrapper').getBoundingClientRect()
      const itemRect = batteryItem.getBoundingClientRect()
      
      tooltip.value = {
        show: true,
        title: item.title,
        status: item.status,
        x: itemRect.left - containerRect.left + itemRect.width / 2,
        y: itemRect.top - containerRect.top - 10
      }
    }

    // 마우스 이동 시 툴팁 위치 업데이트
    const updateTooltipPosition = (event) => {
      if (tooltip.value.show) {
        const batteryItem = event.currentTarget
        const containerRect = batteryItem.closest('.battery-wrapper').getBoundingClientRect()
        
        tooltip.value.x = event.clientX - containerRect.left
        tooltip.value.y = event.clientY - containerRect.top - 50
      }
    }

    // 툴팁 숨기기
    const hideTooltip = () => {
      tooltip.value.show = false
    }

    // 툴팁 위치 스타일
    const tooltipStyle = computed(() => {
      return {
        left: `${tooltip.value.x}px`,
        top: `${tooltip.value.y}px`,
        transform: 'translate(-50%, -100%)'
      }
    })

    // timestamp computed로 변경 (reactive)
    const timestampValue = computed(() => props.timestamp)

    return {
      isPdfMode,
      t,
      chartTitle,
      batteryData,
      gridStyle,
      legendItems,
      tooltip,
      tooltipStyle,
      getStatusClass,
      getFillHeight,
      getStatusText,
      showTooltip,
      hideTooltip,
      updateTooltipPosition,
      formatTimestamp,
      timestamp: timestampValue,
    }
  }
}
</script>

<style scoped>
.battery-chart-container {
  @apply rounded-xl border overflow-hidden shadow-lg;
}

.chart-header {
  @apply px-5 py-4 border-b;
}

.chart-title {
  @apply text-lg font-bold;
}

.battery-wrapper {
  @apply relative p-5;
  min-height: 200px;
}

.battery-grid {
  @apply grid w-full;
}

/* 배터리 아이템 */
.battery-item {
  @apply flex flex-col items-center gap-2 p-3 rounded-lg cursor-pointer;
  @apply transition-all duration-300 ease-out;
  @apply hover:scale-105 hover:shadow-md;
  @apply bg-gray-50/50 dark:bg-gray-700/30;
}

/* 아이템 타이틀 (위에) */
.item-title {
  @apply text-xs font-medium text-center leading-tight;
  @apply max-w-full truncate;
}

/* 배터리 바디 (가로) */
.battery-body {
  @apply relative w-20 h-10 rounded-lg border-2;
  @apply bg-gray-100 dark:bg-gray-700;
  @apply overflow-hidden;
  @apply transition-all duration-300;
}

/* 배터리 헤드 (양극 - 오른쪽) */
.battery-head {
  @apply absolute top-1/2 -right-2 transform -translate-y-1/2;
  @apply w-2 h-5 rounded-r-sm border-2 border-l-0;
  @apply bg-gray-100 dark:bg-gray-700;
}

/* 배터리 채움 (가로 - 왼쪽에서 오른쪽으로) */
.battery-fill {
  @apply absolute top-0 bottom-0 left-0;
  @apply w-full;
  @apply transition-all duration-500 ease-out;
  @apply rounded-md;
}

/* 상태별 색상 */
.status-stop {
  @apply border-gray-400 dark:border-gray-500;
}
.status-stop.battery-fill {
  @apply bg-gray-400 dark:bg-gray-500;
}
.status-stop.battery-head {
  @apply border-gray-400 dark:border-gray-500 bg-gray-100 dark:bg-gray-700;
}

.status-ok {
  @apply border-emerald-500 dark:border-emerald-400;
}
.status-ok.battery-fill {
  @apply bg-emerald-500 dark:bg-emerald-400;
}
.status-ok.battery-head {
  @apply border-emerald-500 dark:border-emerald-400 bg-gray-100 dark:bg-gray-700;
}

.status-warning {
  @apply border-yellow-500 dark:border-yellow-400;
}
.status-warning.battery-fill {
  @apply bg-yellow-500 dark:bg-yellow-400;
}
.status-warning.battery-head {
  @apply border-yellow-500 dark:border-yellow-400 bg-gray-100 dark:bg-gray-700;
}

.status-inspect {
  @apply border-orange-500 dark:border-orange-400;
}
.status-inspect.battery-fill {
  @apply bg-orange-500 dark:bg-orange-400;
}
.status-inspect.battery-head {
  @apply border-orange-500 dark:border-orange-400 bg-gray-100 dark:bg-gray-700;
}

.status-repair {
  @apply border-red-500 dark:border-red-400;
}
.status-repair.battery-fill {
  @apply bg-red-500 dark:bg-red-400;
}
.status-repair.battery-head {
  @apply border-red-500 dark:border-red-400 bg-gray-100 dark:bg-gray-700;
}

/* 툴팁 */
.custom-tooltip {
  @apply absolute z-50 px-3 py-2 rounded-lg shadow-xl;
  @apply bg-gray-900 dark:bg-gray-800 text-white;
  @apply text-sm font-medium;
  @apply border border-gray-700 dark:border-gray-600;
  @apply pointer-events-none whitespace-nowrap;
}

.custom-tooltip::after {
  content: '';
  @apply absolute top-full left-1/2 transform -translate-x-1/2;
  @apply border-4 border-transparent border-t-gray-900 dark:border-t-gray-800;
}

.tooltip-title {
  @apply font-semibold text-sm;
}

.tooltip-status {
  @apply text-xs mt-1 px-2 py-0.5 rounded;
}

.tooltip-status.status-stop { @apply bg-gray-600; }
.tooltip-status.status-ok { @apply bg-emerald-600; }
.tooltip-status.status-warning { @apply bg-yellow-600; }
.tooltip-status.status-inspect { @apply bg-orange-600; }
.tooltip-status.status-repair { @apply bg-red-600; }

/* 범례 */
.chart-legend {
  @apply flex flex-wrap justify-center gap-4 px-4 py-3 border-t border-gray-100 dark:border-gray-700;
}

.legend-item {
  @apply flex items-center gap-2;
}

.legend-battery {
  @apply w-6 h-3 rounded border-2;
}

.legend-battery.status-stop { @apply border-gray-400 bg-gray-400; }
.legend-battery.status-ok { @apply border-emerald-500 bg-emerald-500; }
.legend-battery.status-warning { @apply border-yellow-500 bg-yellow-500; }
.legend-battery.status-inspect { @apply border-orange-500 bg-orange-500; }
.legend-battery.status-repair { @apply border-red-500 bg-red-500; }

.legend-label {
  @apply text-xs font-medium;
}

/* 호버 효과 */
.battery-chart-container:hover {
  @apply shadow-xl transition-shadow duration-300;
}

/* 반응형 */
@media (max-width: 768px) {
  .battery-grid {
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 12px !important;
  }
}

@media (max-width: 640px) {
  .battery-grid {
    grid-template-columns: repeat(3, 1fr) !important;
    gap: 10px !important;
  }
  
  .battery-body {
    @apply w-10 h-16;
  }
  
  .chart-legend {
    @apply gap-2;
  }
  
  .legend-label {
    @apply text-[10px];
  }
}
</style>
