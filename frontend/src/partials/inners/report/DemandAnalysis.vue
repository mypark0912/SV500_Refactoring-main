<template>
  <div class="col-span-full xl:col-span-12 bg-white dark:bg-gray-800 shadow-sm rounded-xl mt-4">

    <!-- Chart 1: Demand Power Trend -->
    <div class="relative col-span-full xl:col-span-12 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg mb-4">
      <div class="absolute top-0 left-0 right-0 h-0.5 bg-violet-500" aria-hidden="true"></div>
      <div class="px-5 pt-5 pb-6 border-b border-gray-200 dark:border-gray-700/60">
        <header class="flex items-center mb-2">
          <div class="w-6 h-6 rounded-full shrink-0 bg-violet-500 mr-3">
            <svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z" fill="currentColor"/>
            </svg>
          </div>
          <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">
            {{ t('report.cardTitle.DemandPowerTrend') }}
          </h3>
        </header>
      </div>
      <div class="px-4 py-3 space-y-2">
        <!-- 로딩 -->
        <div v-if="trendLoading" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500"></div>
          <p class="mt-2 text-gray-500">Loading...</p>
        </div>
        <div v-else-if="!hasTrendData" class="text-center py-8 text-gray-400">No Data</div>
        <div v-else class="dual-axis-section">
          <!-- 차트 -->
          <div ref="demandTrendChart" class="demand-trend-chart"></div>

          <!-- 요약 지표 -->
          <div class="chart-info">
            <div class="info-card">
              <span class="info-label">{{ t('report.cardContext.peakDemand') }}</span>
              <span class="info-value">{{ summary.peak_demand.toFixed(2) }} kW</span>
              <span class="info-sub">{{ formatPeakTime(summary.peak_demand_time) }}</span>
            </div>
            <div class="info-card">
              <span class="info-label">{{ t('report.cardContext.averageDemand') }}</span>
              <span class="info-value">{{ summary.average_demand.toFixed(2) }} kW</span>
            </div>
            <div class="info-card">
              <span class="info-label">{{ t('report.cardContext.demandLoadFactor') }}</span>
              <span class="info-value">{{ summary.demand_load_factor.toFixed(1) }}%</span>
            </div>
            <div class="info-card" v-if="summary.peak_load_rate !== null">
              <span class="info-label">{{ t('report.cardContext.peakLoadRate') }}</span>
              <span class="info-value">{{ summary.peak_load_rate.toFixed(1) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chart 2: Demand Pattern Analysis (Day × Hour 히트맵) -->
    <div class="relative col-span-full xl:col-span-12 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg mb-4">
      <div class="absolute top-0 left-0 right-0 h-0.5 bg-indigo-500" aria-hidden="true"></div>
      <div class="px-5 pt-5 pb-6 border-b border-gray-200 dark:border-gray-700/60">
        <header class="flex items-center mb-2">
          <div class="w-6 h-6 rounded-full shrink-0 bg-indigo-500 mr-3">
            <svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 3h18v4H3V3zm0 6h18v2H3V9zm0 4h18v2H3v-2zm0 4h18v4H3v-4z" fill="currentColor"/>
            </svg>
          </div>
          <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">
            {{ t('report.cardTitle.DemandPatternAnalysis') }}
          </h3>
        </header>
      </div>
      <div class="px-4 py-3 space-y-4">
        <div v-if="heatmapLoading" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
          <p class="mt-2 text-gray-500">Loading...</p>
        </div>
        <div v-else-if="!hasHeatmapData" class="text-center py-8 text-gray-400">No Data</div>
        <div v-else class="heatmap-section">
          <div ref="demandHeatmapChart" class="heatmap-chart"></div>
        </div>
      </div>
    </div>

    <!-- Chart 3: Demand Load Factor Monthly Trend -->
    <div class="relative col-span-full xl:col-span-12 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg">
      <div class="absolute top-0 left-0 right-0 h-0.5 bg-emerald-500" aria-hidden="true"></div>
      <div class="px-5 pt-5 pb-6 border-b border-gray-200 dark:border-gray-700/60">
        <header class="flex items-center mb-2">
          <div class="w-6 h-6 rounded-full shrink-0 bg-emerald-500 mr-3">
            <svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z" fill="currentColor"/>
            </svg>
          </div>
          <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">
            {{ t('report.cardTitle.DemandLoadFactorMonthly') }}
          </h3>
        </header>
      </div>
      <div class="px-4 py-3 space-y-2">
        <div v-if="monthlyLoading" class="text-center py-8">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
          <p class="mt-2 text-gray-500">Loading...</p>
        </div>
        <div v-else-if="!hasMonthlyData" class="text-center py-8 text-gray-400">No Data</div>
        <div v-else>
          <div ref="demandMonthlyChart" class="monthly-chart"></div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, nextTick, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { useI18n } from 'vue-i18n'
import { useReportData } from '@/composables/ReportDict'
import dayjs from 'dayjs'

export default {
  name: 'DemandAnalysis',
  props: {
    channel: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const { t, locale } = useI18n()
    const {
      reportData,
      loadDemandTrendData,
      loadDemandHeatmapData,
      loadDemandLoadFactorMonthly,
    } = useReportData()

    const channel = ref(props.channel)

    // Chart refs
    const demandTrendChart = ref(null)
    const demandHeatmapChart = ref(null)
    const demandMonthlyChart = ref(null)

    // Loading states
    const trendLoading = ref(false)
    const heatmapLoading = ref(false)
    const monthlyLoading = ref(false)

    // Data availability
    const hasTrendData = ref(false)
    const hasHeatmapData = ref(false)
    const hasMonthlyData = ref(false)

    // Chart instances
    let trendChartInstance = null
    let heatmapChartInstance = null
    let monthlyChartInstance = null

    // Summary data
    const summary = ref({
      peak_demand: 0,
      peak_demand_time: '',
      average_demand: 0,
      demand_load_factor: 0,
      peak_load_rate: null,
    })

    // ========================================
    // 유틸
    // ========================================

    const formatPeakTime = (isoStr) => {
      if (!isoStr) return '-'
      return dayjs(isoStr).format('YYYY-MM-DD HH:mm')
    }

    // ========================================
    // Chart 1: Demand Power Trend (바 + 라인)
    // ========================================

    const loadTrendData = async () => {
      trendLoading.value = true
      try {
        const data = await loadDemandTrendData(channel.value, 'hourly')
        if (data && data.summary) {
          summary.value = {
            ...data.summary,
            peak_demand: data.summary.peak_demand / 1000,
            average_demand: data.summary.average_demand / 1000,
          }
        }
        if (data && data.trend && data.trend.length > 0) {
          hasTrendData.value = true
          trendLoading.value = false
          await createTrendChart(data.trend)
        }
      } catch (error) {
        console.error('Demand trend 로딩 실패:', error)
      } finally {
        trendLoading.value = false
      }
    }

    const createTrendChart = async (trendData) => {
      await nextTick()
      if (!demandTrendChart.value) return
      if (!trendChartInstance) trendChartInstance = echarts.init(demandTrendChart.value)

      const times = trendData.map(item => {
        return dayjs(item.time).format('HH:00')
      })
      const maxData = trendData.map(item => item.demand_max / 1000)
      const loadFactorData = trendData.map(item => item.demand_load_factor)

      const maxDemandValue = maxData.length > 0 ? Math.max(...maxData.filter(v => v > 0)) : 1
      const maxLoadFactor = loadFactorData.length > 0 ? Math.max(...loadFactorData.filter(v => v > 0)) : 100

      const demandAxisMax = Math.ceil(maxDemandValue * 1.3 * 100) / 100
      const loadFactorAxisMax = Math.ceil(Math.max(maxLoadFactor * 1.3, 10))

      const option = {
        grid: {
          left: '1%',
          right: '1%',
          top: '12%',
          bottom: '10%',
          containLabel: true
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross', crossStyle: { color: '#999' } },
          formatter: function (params) {
            let result = params[0].axisValueLabel + '<br/>'
            params.forEach(function (item) {
              if (item.seriesIndex === 0) {
                result += item.marker + item.seriesName + ': ' + item.value.toFixed(2) + ' kW<br/>'
              } else {
                result += item.marker + item.seriesName + ': ' + item.value.toFixed(1) + '%<br/>'
              }
            })
            return result
          }
        },
        legend: {
          data: [t('report.cardContext.peakDemand'), t('report.cardContext.demandLoadFactor')],
          top: '2%',
          textStyle: { fontSize: 12 }
        },
        xAxis: [{
          type: 'category',
          data: times,
          boundaryGap: true,
          axisLabel: {
            formatter: function (value) {
              if (times.length > 20) {
                const hourNum = parseInt(value.split(':')[0])
                return hourNum % 2 === 0 ? value : ''
              }
              return value
            }
          }
        }],
        yAxis: [
          {
            type: 'value',
            name: t('report.cardContext.peakDemand') + ' (kW)',
            position: 'left',
            axisLabel: {
              formatter: (value) => value === 0 ? '0' : value.toFixed(2),
              margin: 55
            },
            splitLine: { show: true, lineStyle: { type: 'dashed', color: '#e0e0e0' } },
            min: 0,
            max: demandAxisMax,
            interval: demandAxisMax / 5
          },
          {
            type: 'value',
            name: t('report.cardContext.demandLoadFactor') + ' (%)',
            position: 'right',
            axisLabel: {
              formatter: (value) => value === 0 ? '0' : value.toFixed(1),
              fontSize: 10,
              margin: 55
            },
            min: 0,
            max: loadFactorAxisMax,
            splitLine: { show: false }
          }
        ],
        series: [
          {
            name: t('report.cardContext.peakDemand'),
            type: 'bar',
            yAxisIndex: 0,
            data: maxData,
            barMaxWidth: 20,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#c084fc' },
                { offset: 0.5, color: '#8b5cf6' },
                { offset: 1, color: '#7c3aed' }
              ])
            }
          },
          {
            name: t('report.cardContext.demandLoadFactor'),
            type: 'line',
            yAxisIndex: 1,
            data: loadFactorData,
            lineStyle: { width: 3, color: '#10b981' },
            itemStyle: { color: '#10b981' },
            areaStyle: { opacity: 0.1, color: '#10b981' },
            smooth: true
          }
        ]
      }

      trendChartInstance.setOption(option)
    }

    // ========================================
    // Chart 2: Demand Pattern Heatmap
    // ========================================

    const loadHeatmap = async () => {
      heatmapLoading.value = true
      try {
        const data = await loadDemandHeatmapData(channel.value)
        if (data && data.data && data.data.length > 0) {
          hasHeatmapData.value = true
          heatmapLoading.value = false
          await createHeatmapChart(data.data, data.max_value / 1000)
        }
      } catch (error) {
        console.error('Demand heatmap 로딩 실패:', error)
      } finally {
        heatmapLoading.value = false
      }
    }

    const createHeatmapChart = async (heatmapData, maxValue) => {
      await nextTick()
      if (!demandHeatmapChart.value) return
      if (!heatmapChartInstance) heatmapChartInstance = echarts.init(demandHeatmapChart.value)

      const days = [
        t('report.cardContext.days.mon'),
        t('report.cardContext.days.tue'),
        t('report.cardContext.days.wed'),
        t('report.cardContext.days.thu'),
        t('report.cardContext.days.fri'),
        t('report.cardContext.days.sat'),
        t('report.cardContext.days.sun')
      ]
      const hours = Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, '0'))

      // API 응답 형식: [{day, hour, value}, ...] → [hour, day, value/1000]
      const chartData = heatmapData.map(item => {
        if (Array.isArray(item)) return [item[0], item[1], (item[2] || 0) / 1000]
        return [item.hour || 0, item.day || 0, (item.value || 0) / 1000]
      })

      const option = {
        grid: {
          left: '10%',
          right: '10%',
          top: '12%',
          bottom: '22%',
          containLabel: true
        },
        tooltip: {
          position: 'top',
          formatter: function (params) {
            const hour = hours[params.data[0]] || '00'
            const day = days[params.data[1]] || '-'
            const value = params.data[2] || 0
            return `${day} ${hour}:00<br/>${t('report.cardContext.demand')}: ${value.toFixed(2)} kW`
          }
        },
        xAxis: {
          type: 'category',
          data: hours,
          splitArea: { show: true },
          axisLabel: {
            formatter: function (value) {
              const hourNum = parseInt(value)
              return hourNum % 2 === 0 ? value + ':00' : ''
            }
          }
        },
        yAxis: {
          type: 'category',
          data: days,
          splitArea: { show: true }
        },
        visualMap: {
          min: 0,
          max: Math.max(maxValue * 1.2, 1),
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: '2%',
          inRange: {
            color: [
              '#eef2ff', '#c7d2fe', '#a5b4fc', '#818cf8',
              '#6366f1', '#4f46e5', '#4338ca', '#3730a3'
            ]
          },
          text: [t('report.cardContext.high'), t('report.cardContext.low')],
          textStyle: { color: '#333', fontSize: 12 }
        },
        series: [{
          name: t('report.cardContext.demand'),
          type: 'heatmap',
          data: chartData,
          label: { show: false },
          itemStyle: {
            borderWidth: 0.5,
            borderColor: '#fff'
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
              borderWidth: 2,
              borderColor: '#333'
            }
          }
        }]
      }

      heatmapChartInstance.setOption(option, true)
    }

    // ========================================
    // Chart 3: Monthly Load Factor Trend
    // ========================================

    const loadMonthlyData = async () => {
      monthlyLoading.value = true
      try {
        const data = await loadDemandLoadFactorMonthly(channel.value, 12)
        if (data && data.data && data.data.length > 0) {
          hasMonthlyData.value = true
          monthlyLoading.value = false
          await createMonthlyChart(data.data)
        }
      } catch (error) {
        console.error('Demand monthly 로딩 실패:', error)
      } finally {
        monthlyLoading.value = false
      }
    }

    const createMonthlyChart = async (monthlyData) => {
      await nextTick()
      if (!demandMonthlyChart.value) return
      if (!monthlyChartInstance) monthlyChartInstance = echarts.init(demandMonthlyChart.value)

      const months = monthlyData.map(item => item.month)
      const loadFactors = monthlyData.map(item => item.load_factor)
      const peakDemands = monthlyData.map(item => item.peak_demand / 1000)
      const avgDemands = monthlyData.map(item => item.average_demand / 1000)

      const maxPeak = peakDemands.length > 0 ? Math.max(...peakDemands.filter(v => v > 0)) : 1
      const peakAxisMax = Math.ceil(maxPeak * 1.3 * 100) / 100

      const option = {
        grid: {
          left: '1%',
          right: '1%',
          top: '15%',
          bottom: '10%',
          containLabel: true
        },
        tooltip: {
          trigger: 'axis',
          formatter: function (params) {
            let result = params[0].axisValueLabel + '<br/>'
            params.forEach(function (item) {
              if (item.seriesName.includes('kW')) {
                result += item.marker + item.seriesName + ': ' + item.value.toFixed(2) + ' kW<br/>'
              } else {
                result += item.marker + item.seriesName + ': ' + item.value.toFixed(1) + '%<br/>'
              }
            })
            return result
          }
        },
        legend: {
          data: [
            t('report.cardContext.peakDemand') + ' (kW)',
            t('report.cardContext.averageDemand') + ' (kW)',
            t('report.cardContext.demandLoadFactor') + ' (%)'
          ],
          top: '2%',
          textStyle: { fontSize: 11 }
        },
        xAxis: [{
          type: 'category',
          data: months,
          axisLabel: { rotate: 45 }
        }],
        yAxis: [
          {
            type: 'value',
            name: 'kW',
            position: 'left',
            axisLabel: {
              formatter: (value) => value.toFixed(1)
            },
            min: 0,
            max: peakAxisMax,
            splitLine: { show: true, lineStyle: { type: 'dashed', color: '#e0e0e0' } }
          },
          {
            type: 'value',
            name: t('report.cardContext.demandLoadFactor') + ' (%)',
            position: 'right',
            axisLabel: {
              formatter: (value) => value.toFixed(0) + '%'
            },
            min: 0,
            max: 100,
            splitLine: { show: false }
          }
        ],
        series: [
          {
            name: t('report.cardContext.peakDemand') + ' (kW)',
            type: 'bar',
            yAxisIndex: 0,
            data: peakDemands,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#c084fc' },
                { offset: 1, color: '#7c3aed' }
              ])
            },
            barWidth: '30%'
          },
          {
            name: t('report.cardContext.averageDemand') + ' (kW)',
            type: 'bar',
            yAxisIndex: 0,
            data: avgDemands,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#93c5fd' },
                { offset: 1, color: '#3b82f6' }
              ])
            },
            barWidth: '30%'
          },
          {
            name: t('report.cardContext.demandLoadFactor') + ' (%)',
            type: 'line',
            yAxisIndex: 1,
            data: loadFactors,
            lineStyle: { width: 3, color: '#10b981' },
            itemStyle: { color: '#10b981' },
            areaStyle: { opacity: 0.08, color: '#10b981' },
            smooth: true,
            symbol: 'circle',
            symbolSize: 8
          }
        ]
      }

      monthlyChartInstance.setOption(option)
    }

    // ========================================
    // Lifecycle
    // ========================================

    onMounted(async () => {
      // Load all data
      await Promise.all([
        loadTrendData(),
        loadHeatmap(),
        loadMonthlyData(),
      ])

      // Resize handler
      window.addEventListener('resize', () => {
        trendChartInstance?.resize()
        heatmapChartInstance?.resize()
        monthlyChartInstance?.resize()
      })
    })

    // Locale change → re-render charts
    watch(locale, () => {
      if (reportData.demandTrendData?.trend) {
        createTrendChart(reportData.demandTrendData.trend)
      }
      if (reportData.demandHeatmapData?.data) {
        createHeatmapChart(
          reportData.demandHeatmapData.data,
          reportData.demandHeatmapData.max_value
        )
      }
      if (reportData.demandLoadFactorMonthlyData?.data) {
        createMonthlyChart(reportData.demandLoadFactorMonthlyData.data)
      }
    })

    onUnmounted(() => {
      trendChartInstance?.dispose()
      heatmapChartInstance?.dispose()
      monthlyChartInstance?.dispose()
      window.removeEventListener('resize', () => {})
    })

    return {
      // Refs
      demandTrendChart,
      demandHeatmapChart,
      demandMonthlyChart,
      // State
      trendLoading,
      heatmapLoading,
      monthlyLoading,
      hasTrendData,
      hasHeatmapData,
      hasMonthlyData,
      summary,
      // Utils
      formatPeakTime,
      t,
    }
  }
}
</script>

<style scoped>
.demand-trend-chart {
  @apply h-80 w-full;
}

.heatmap-chart {
  @apply h-56 w-full;
}

.monthly-chart {
  @apply h-80 w-full;
}

.chart-info {
  @apply flex justify-around mt-3 pt-3 border-t border-gray-200 dark:border-gray-700;
}

.info-card {
  @apply text-center;
}

.info-label {
  @apply block text-sm text-gray-500 dark:text-gray-400 mb-1;
}

.info-value {
  @apply text-lg font-bold text-gray-900 dark:text-gray-100;
}

.info-sub {
  @apply block text-xs text-gray-400 dark:text-gray-500 mt-1;
}

@media (max-width: 1024px) {
  .demand-trend-chart {
    @apply h-80;
  }
  .heatmap-chart {
    @apply h-64;
  }
  .monthly-chart {
    @apply h-72;
  }
}

@media (max-width: 640px) {
  .chart-info {
    @apply flex-col gap-3;
  }
}
</style>
