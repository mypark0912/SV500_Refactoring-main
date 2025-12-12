<template>
    <div 
      class="treemap-container"
      :class="isPdfMode ? 'bg-white border-gray-200' : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'"
    >
      <!-- 헤더 섹션 -->
      <div 
        class="chart-header"
        :class="isPdfMode ? 'bg-blue-50 border-blue-100' : 'bg-blue-50 dark:bg-gray-900 border-blue-100 dark:border-gray-700'"
      >
        <h3 
          class="chart-title"
          :class="isPdfMode ? 'text-gray-800' : 'text-gray-800 dark:text-gray-100'"
        >
          {{ chartTitle }}
        </h3>
      </div>
  
      <!-- 차트 영역 -->
      <div class="chart-wrapper">
        <apexchart
          v-if="chartSeries.length > 0"
          type="treemap"
          :height="chartHeight"
          :options="chartOptions"
          :series="chartSeries"
        />
        <div v-else class="no-data">
          {{ t('report.noData') || '데이터 없음' }}
        </div>
      </div>
  
      <!-- 범례 -->
      <div class="chart-legend">
        <div v-for="(item, idx) in legendItems" :key="idx" class="legend-item">
          <span class="legend-color" :style="{ backgroundColor: item.color }"></span>
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
  import { ref, computed, watch, inject } from 'vue'
  import { useDark } from '@vueuse/core'
  import { useI18n } from 'vue-i18n'
  import VueApexCharts from 'vue3-apexcharts'
  
  export default {
    name: 'ReportTreeMap',
    components: {
      apexchart: VueApexCharts,
    },
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
      }
    },
    setup(props) {
      const isPdfMode = inject('isPdfMode', false)
      const { t, locale } = useI18n()
      const darkMode = useDark()
  
      // 상태별 색상 매핑
      const statusColors = {
        0: '#94A3B8', // Stop - Gray
        1: '#10B981', // OK - Green
        2: '#F59E0B', // Warning - Yellow
        3: '#F97316', // Inspect - Orange
        4: '#EF4444', // Repair - Red
      }
  
      // 모드에 따른 타이틀
      const chartTitle = computed(() => {
        const titleMap = {
          'PowerQuality': t('diagnosis.tabTitle.detailTitle_pq'),
          'DiagnosisDetail': t('diagnosis.tabTitle.detailTitle'),
        }
        return titleMap[props.mode] || t('diagnosis.tabTitle.detailTitle')
      })
  
      // 동적 높이 계산
      const chartHeight = computed(() => {
        const itemCount = props.data?.Names?.length || 0
        if (itemCount <= 6) return 250
        else if (itemCount <= 12) return 300
        else return 350
      })
  
      // 범례 아이템
      const legendItems = computed(() => [
        { label: t('diagnosis.tabContext.pqfe0') || 'Stop', color: statusColors[0] },
        { label: t('diagnosis.tabContext.pqfe1') || 'OK', color: statusColors[1] },
        { label: t('diagnosis.tabContext.pqfe2') || 'Warning', color: statusColors[2] },
        { label: t('diagnosis.tabContext.pqfe3') || 'Inspect', color: statusColors[3] },
        { label: t('diagnosis.tabContext.pqfe4') || 'Repair', color: statusColors[4] },
      ])
  
      // 차트 데이터 변환
      const chartSeries = computed(() => {
        if (!props.data?.Names || !props.data?.Values) return []
  
        const data = props.data.Names.map((name, index) => {
          const status = props.data.Values[index]
          const title = props.data.Titles?.[index]?.[locale.value] || name
          return {
            x: title,
            y: 10, // 동일한 크기로 표시
            fillColor: statusColors[Math.floor(status)] || statusColors[0],
            status: status
          }
        })
  
        return [{
          data: data
        }]
      })
  
      // 차트 옵션
      const chartOptions = computed(() => ({
        chart: {
          type: 'treemap',
          toolbar: { show: false },
          background: 'transparent',
          animations: {
            enabled: true,
            speed: 500
          }
        },
        legend: { show: false },
        dataLabels: {
          enabled: true,
          style: {
            fontSize: '13px',
            fontWeight: 600,
            colors: ['#FFFFFF']
          },
          formatter: function(text, op) {
            return text
          },
          offsetY: 0,
          dropShadow: {
            enabled: true,
            top: 1,
            left: 1,
            blur: 2,
            opacity: 0.5
          }
        },
        plotOptions: {
          treemap: {
            distributed: true,
            enableShades: false,
            borderRadius: 6,
            useFillColorAsStroke: false
          }
        },
        stroke: {
          width: 2,
          colors: [isPdfMode ? '#E5E7EB' : (darkMode.value ? '#374151' : '#E5E7EB')]
        },
        tooltip: {
          enabled: true,
          theme: isPdfMode ? 'light' : (darkMode.value ? 'dark' : 'light'),
          custom: function({ series, seriesIndex, dataPointIndex, w }) {
            const data = w.config.series[seriesIndex].data[dataPointIndex]
            const statusLabels = ['Stop', 'OK', 'Warning', 'Inspect', 'Repair']
            const statusLabel = statusLabels[Math.floor(data.status)] || 'Unknown'
            return `
              <div class="apexcharts-tooltip-custom" style="padding: 8px 12px;">
                <div style="font-weight: 600; margin-bottom: 4px;">${data.x}</div>
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span style="width: 10px; height: 10px; border-radius: 2px; background: ${data.fillColor};"></span>
                  <span>${statusLabel}</span>
                </div>
              </div>
            `
          }
        },
        states: {
          hover: {
            filter: {
              type: 'darken',
              value: 0.15
            }
          },
          active: {
            filter: {
              type: 'darken',
              value: 0.2
            }
          }
        }
      }))
  
      // 다크모드 변경 감지
      watch(darkMode, () => {
        // 차트 옵션이 computed라서 자동 업데이트됨
      })
  
      return {
        isPdfMode,
        t,
        chartTitle,
        chartHeight,
        chartSeries,
        chartOptions,
        legendItems,
      }
    }
  }
  </script>
  
  <style scoped>
  .treemap-container {
    @apply rounded-xl border overflow-hidden shadow-lg;
  }
  
  .chart-header {
    @apply px-4 py-3 border-b;
  }
  
  .chart-title {
    @apply text-base font-bold;
  }
  
  .chart-wrapper {
    @apply p-4;
  }
  
  .no-data {
    @apply flex items-center justify-center h-48 text-gray-500 dark:text-gray-400;
  }
  
  .chart-legend {
    @apply flex flex-wrap justify-center gap-4 px-4 py-3 border-t border-gray-100 dark:border-gray-700;
  }
  
  .legend-item {
    @apply flex items-center gap-1.5;
  }
  
  .legend-color {
    @apply w-3 h-3 rounded-sm;
  }
  
  .legend-label {
    @apply text-xs font-medium;
  }
  
  /* 호버 효과 */
  .treemap-container:hover {
    @apply shadow-xl transition-shadow duration-300;
  }
  
  /* 반응형 */
  @media (max-width: 640px) {
    .chart-header {
      @apply px-3 py-2;
    }
    
    .chart-title {
      @apply text-sm;
    }
    
    .chart-legend {
      @apply gap-2;
    }
    
    .legend-label {
      @apply text-[10px];
    }
  }
  </style>
  