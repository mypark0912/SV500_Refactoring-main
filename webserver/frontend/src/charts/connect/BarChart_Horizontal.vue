<template>
    <div 
      class="modern-chart-container"
      :class="isPdfMode ? 'bg-white border-gray-200' : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'"
    >
      <!-- 헤더 섹션 -->
      <div 
        class="chart-header"
        :class="isPdfMode ? 'bg-blue-50 border-blue-100' : 'bg-blue-50 dark:bg-gray-900 border-blue-100 dark:border-gray-700'"
      >
        <div class="header-content">
          <h3 
            class="chart-title"
            :class="isPdfMode ? 'text-gray-800' : 'text-gray-800 dark:text-gray-100'"
          >
            {{ chartTitle }}
          </h3>
          <span 
            class="update-time"
            :class="isPdfMode ? 'text-gray-500' : 'text-gray-500 dark:text-gray-400'"
          >
          </span>
        </div>
      </div>
  
      <!-- 차트 컨테이너 -->
      <div class="chart-wrapper" :style="{ height: dynamicHeight + 'px' }">
        <div 
          class="chart-background"
          :class="isPdfMode ? 'bg-gray-50' : 'bg-gray-50 dark:bg-gray-900'"
        >
          <canvas ref="canvas" :data="data"></canvas>
        </div>
        
        <!-- 로딩 오버레이 -->
        <div v-if="isLoading" class="loading-overlay">
          <div class="loading-spinner"></div>
          <span class="loading-text">loading...</span>
        </div>
      </div>
  
      <!-- 범례 -->
      <div class="chart-legend">
        <div v-for="(item, idx) in legendItems" :key="idx" class="legend-item">
          <span class="legend-color" :style="{ backgroundColor: item.color }"></span>
          <span class="legend-label" :class="isPdfMode ? 'text-gray-600' : 'text-gray-600 dark:text-gray-400'">
            {{ item.label }}
          </span>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, watch, onMounted, onUnmounted, computed, inject } from 'vue'
  import { useDark } from '@vueuse/core'
  import { chartColors } from '../ChartjsConfig'
  import { useI18n } from 'vue-i18n'
  
  import {
    Chart, BarController, BarElement, LinearScale, TimeScale, Tooltip, Legend, CategoryScale
  } from 'chart.js'
  import 'chartjs-adapter-moment'
  
  import { tailwindConfig, formatValue } from '../../utils/Utils'
  
  Chart.register(BarController, BarElement, LinearScale, CategoryScale, TimeScale, Tooltip, Legend)
  
  export default {
    name: 'ReportBarChartHorizontal',
    props: ['data', 'width', 'height', 'mode'],
    setup(props) {
      const isPdfMode = inject('isPdfMode', false)
      
      const { t, locale } = useI18n()
      const canvas = ref(null)
      const isLoading = ref(false)
      let chart = null
      const darkMode = useDark()
  
      const { textColor, gridColor, tooltipBodyColor, tooltipBgColor, tooltipBorderColor } = chartColors
  
      // 모드에 따른 타이틀 계산
      const chartTitle = computed(() => {
        const titleMap = {
          'PowerQuality': t('diagnosis.tabTitle.detailTitle_pq'),
          'DiagnosisDetail': t('diagnosis.tabTitle.detailTitle'),
        }
        return titleMap[props.mode] || t('diagnosis.tabTitle.detailTitle_pq')
      })
  
      // 항목 개수에 따른 동적 높이 계산
      const dynamicHeight = computed(() => {
        const itemCount = props.data?.labels?.length || 1
        const minHeight = 200
        const itemHeight = 40 // 항목당 높이
        return Math.max(minHeight, itemCount * itemHeight + 80)
      })
  
      // 동적 바 굵기 계산
      const dynamicBarThickness = computed(() => {
        const itemCount = props.data?.labels?.length || 1
        if (itemCount <= 5) return 30
        else if (itemCount <= 10) return 25
        else if (itemCount <= 15) return 20
        else return 16
      })
  
      // 상태별 색상
      const getBarColors = (value) => {
        const colorMap = {
          0: { bg: 'rgba(100, 116, 139, 0.8)', border: 'rgba(100, 116, 139, 1)' },  // Stop - Gray
          1: { bg: 'rgba(16, 185, 129, 0.8)', border: 'rgba(16, 185, 129, 1)' },    // OK - Green
          2: { bg: 'rgba(245, 158, 11, 0.8)', border: 'rgba(245, 158, 11, 1)' },    // Low - Yellow
          3: { bg: 'rgba(249, 115, 22, 0.8)', border: 'rgba(249, 115, 22, 1)' },    // Medium - Orange
          4: { bg: 'rgba(239, 68, 68, 0.8)', border: 'rgba(239, 68, 68, 1)' }       // High - Red
        }
        return colorMap[Math.floor(value)] || colorMap[0]
      }
  
      // 범례 아이템
      const legendItems = computed(() => [
        { label: t('diagnosis.tabContext.pqfe0'), color: 'rgba(100, 116, 139, 0.8)' },
        { label: t('diagnosis.tabContext.pqfe1'), color: 'rgba(16, 185, 129, 0.8)' },
        { label: t('diagnosis.tabContext.pqfe2'), color: 'rgba(245, 158, 11, 0.8)' },
        { label: t('diagnosis.tabContext.pqfe3'), color: 'rgba(249, 115, 22, 0.8)' },
        { label: t('diagnosis.tabContext.pqfe4'), color: 'rgba(239, 68, 68, 0.8)' },
      ])
  
      // 언어 변경 감지
      watch(locale, () => {
        if (!chart) return
        
        // X축 (값) 라벨 업데이트
        chart.options.scales.x.ticks.callback = (value) => {
          const textstr = [
            t('diagnosis.tabContext.pqfe0'),
            t('diagnosis.tabContext.pqfe1'),
            t('diagnosis.tabContext.pqfe2'),
            t('diagnosis.tabContext.pqfe3'),
            t('diagnosis.tabContext.pqfe4')
          ]
          return textstr[Math.floor(value)]
        }
  
        // Y축 (항목명) 라벨 업데이트
        chart.options.scales.y.ticks.callback = (value, index) => {
          const title = props.data.titles?.[index]?.[locale.value]
          return (title && title.trim() !== '') ? title : chart.data.labels?.[index]
        }
  
        chart.update('none')
      })
      
      onMounted(() => {
        const ctx = canvas.value
        const dataValues = props.data.datasets[0].data
  
        chart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: props.data.labels,
            datasets: [{
              label: 'Status',
              data: dataValues.map(value => value === 0 ? 0.2 : value),
              backgroundColor: dataValues.map(value => getBarColors(value).bg),
              borderColor: dataValues.map(value => getBarColors(value).border),
              borderWidth: 2,
              borderRadius: 6,
              borderSkipped: false,
              barThickness: dynamicBarThickness.value,
            }]
          },
          options: {
            indexAxis: 'y', // 가로 바차트
            responsive: true,
            maintainAspectRatio: false,
            layout: {
              padding: {
                top: 10,
                bottom: 10,
                left: 10,
                right: 30,
              },
            },
            scales: {
              x: {
                max: 4,
                border: { display: false },
                grid: {
                  display: true,
                  color: (context) => {
                    const colors = [
                      'rgba(100, 116, 139, 0.15)',
                      'rgba(16, 185, 129, 0.15)',
                      'rgba(245, 158, 11, 0.15)',
                      'rgba(249, 115, 22, 0.15)',
                      'rgba(239, 68, 68, 0.15)'
                    ]
                    return colors[context.tick.value] || 'rgba(156, 163, 175, 0.1)'
                  },
                  lineWidth: 1,
                },
                ticks: {
                  stepSize: 1,
                  padding: 8,
                  font: { size: 11, weight: '600' },
                  callback: (value) => {
                    const textstr = [
                      t('diagnosis.tabContext.pqfe0'),
                      t('diagnosis.tabContext.pqfe1'),
                      t('diagnosis.tabContext.pqfe2'),
                      t('diagnosis.tabContext.pqfe3'),
                      t('diagnosis.tabContext.pqfe4')
                    ]
                    return textstr[Math.floor(value)]
                  },
                  color: (context) => {
                    const colors = ['#64748B', '#10B981', '#F59E0B', '#F97316', '#EF4444']
                    return colors[context.tick.value] || '#6B7280'
                  },
                },
              },
              y: {
                border: { display: false },
                grid: { display: false },
                ticks: {
                  padding: 8,
                  font: { size: 12, weight: '500' },
                  color: isPdfMode ? '#374151' : (darkMode.value ? '#D1D5DB' : '#374151'),
                  callback: (value, index) => {
                    const title = props.data.titles?.[index]?.[locale.value]
                    return (title && title.trim() !== '') ? title : props.data.labels?.[index]
                  },
                },
              },
            },
            plugins: {
              legend: { display: false },
              tooltip: {
                enabled: true,
                backgroundColor: isPdfMode ? 'rgba(255, 255, 255, 0.95)' : (darkMode.value ? 'rgba(17, 24, 39, 0.95)' : 'rgba(255, 255, 255, 0.95)'),
                titleColor: isPdfMode ? '#111827' : (darkMode.value ? '#F9FAFB' : '#111827'),
                bodyColor: isPdfMode ? '#374151' : (darkMode.value ? '#E5E7EB' : '#374151'),
                borderColor: isPdfMode ? '#E5E7EB' : (darkMode.value ? '#4B5563' : '#E5E7EB'),
                borderWidth: 1,
                cornerRadius: 8,
                padding: 10,
                displayColors: false,
                titleFont: { size: 12, weight: '600' },
                bodyFont: { size: 11, weight: '500' },
                callbacks: {
                  title: (context) => context[0].label,
                  label: (context) => {
                    const value = context.parsed.x
                    const statusLabels = [
                      t('diagnosis.tabContext.pqfe0'),
                      t('diagnosis.tabContext.pqfe1'),
                      t('diagnosis.tabContext.pqfe2'),
                      t('diagnosis.tabContext.pqfe3'),
                      t('diagnosis.tabContext.pqfe4')
                    ]
                    const actualValue = value === 0.2 ? 0 : value
                    return statusLabels[Math.floor(actualValue)]
                  },
                },
              },
            },
            interaction: {
              intersect: false,
              mode: 'index',
            },
            animation: {
              duration: 800,
              easing: 'easeOutQuart',
            },
            onHover: (event, elements) => {
              event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default'
            }
          },
        })
      })
  
      onUnmounted(() => chart?.destroy())
  
      // 다크모드 감지
      watch(
        () => darkMode.value,
        () => {
          if (!chart || isPdfMode) return
          
          if (darkMode.value) {
            chart.options.scales.y.ticks.color = '#D1D5DB'
            chart.options.plugins.tooltip.backgroundColor = 'rgba(17, 24, 39, 0.95)'
            chart.options.plugins.tooltip.titleColor = '#F9FAFB'
            chart.options.plugins.tooltip.bodyColor = '#E5E7EB'
            chart.options.plugins.tooltip.borderColor = '#4B5563'
          } else {
            chart.options.scales.y.ticks.color = '#374151'
            chart.options.plugins.tooltip.backgroundColor = 'rgba(255, 255, 255, 0.95)'
            chart.options.plugins.tooltip.titleColor = '#111827'
            chart.options.plugins.tooltip.bodyColor = '#374151'
            chart.options.plugins.tooltip.borderColor = '#E5E7EB'
          }
          chart.update('none')
        }
      )
  
      // 데이터 변경 감지
      watch(
        () => props.data,
        (newData) => {
          if (!chart || !newData) return
          
          const dataValues = newData.datasets[0].data
          chart.data.labels = newData.labels
          chart.data.datasets[0].data = dataValues.map(value => value === 0 ? 0.2 : value)
          chart.data.datasets[0].backgroundColor = dataValues.map(value => getBarColors(value).bg)
          chart.data.datasets[0].borderColor = dataValues.map(value => getBarColors(value).border)
          chart.data.datasets[0].barThickness = dynamicBarThickness.value
          chart.update()
        },
        { deep: true }
      )
  
      return {
        canvas,
        isLoading,
        isPdfMode,
        chartTitle,
        dynamicHeight,
        legendItems,
        t,
        locale,
      }
    }
  }
  </script>
  
  <style scoped>
  .modern-chart-container {
   @apply rounded-xl border;
   @apply overflow-hidden shadow-lg;
  }
  
  /* 헤더 */
  .chart-header {
   @apply px-4 py-3;
   @apply border-b;
  }
  
  .header-content {
   @apply flex items-center justify-between gap-3;
  }
  
  .chart-title {
   @apply text-base font-bold;
  }
  
  .update-time {
    @apply text-xs font-medium tabular-nums;
  }
  
  /* 차트 래퍼 */
  .chart-wrapper {
   @apply relative px-4 py-2;
  }
  
  .chart-background {
   @apply relative h-full rounded-lg p-2;
  }
  
  /* 범례 */
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
  
  /* 로딩 오버레이 */
  .loading-overlay {
   @apply absolute inset-0 flex flex-col items-center justify-center;
   @apply bg-white/90 dark:bg-gray-900/90 rounded-lg;
  }
  
  .loading-spinner {
   @apply w-8 h-8 border-3 border-blue-200 border-t-blue-500 rounded-full;
   animation: spin 1s linear infinite;
  }
  
  .loading-text {
   @apply mt-3 text-sm font-medium text-gray-600 dark:text-gray-400;
  }
  
  @keyframes spin {
   to { transform: rotate(360deg); }
  }
  
  /* 호버 효과 */
  .modern-chart-container:hover {
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
  