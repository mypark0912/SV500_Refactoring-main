<template>
  <div class="card-wrap">
    <div class="card-header">
      <h3 class="card-title">{{ t('dashboard.kwh') }}</h3>
      <span class="card-channel">
        {{ channel === 'Main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>

    <div class="card-body">
      <div class="energy-grid">
        <!-- KPI 2x2 -->
        <div class="kpi-area">
          <div class="kpi-row">
            <div class="kpi-item">
              <span class="kpi-label">{{ t('dashboard.kwh_realtime.today') }}</span>
              <div class="kpi-value">
                {{ parseFloat(consumptionData.daily).toFixed(2) }}
                <span class="kpi-unit">kWh</span>
              </div>
              <span class="kpi-delta" :class="deltaClass(consumptionData.daily_comparison)">
                {{ deltaText(consumptionData.daily_comparison) }}
                <span class="kpi-delta-label">{{ t('dashboard.kwh_realtime.comparetoyesterday') }}</span>
              </span>
            </div>
            <div class="kpi-item">
              <span class="kpi-label">{{ t('dashboard.kwh_realtime.thisweek') }}</span>
              <div class="kpi-value">
                {{ parseFloat(consumptionData.weekly).toFixed(2) }}
                <span class="kpi-unit">kWh</span>
              </div>
              <span class="kpi-delta" :class="deltaClass(consumptionData.weekly_comparison)">
                {{ deltaText(consumptionData.weekly_comparison) }}
                <span class="kpi-delta-label">{{ t('dashboard.kwh_realtime.comparetolastweek') }}</span>
              </span>
            </div>
          </div>
          <div class="kpi-row">
            <div class="kpi-item">
              <span class="kpi-label">{{ t('dashboard.kwh_realtime.thismonth') }}</span>
              <div class="kpi-value">
                {{ parseFloat(consumptionData.monthly).toFixed(2) }}
                <span class="kpi-unit">kWh</span>
              </div>
              <span class="kpi-delta" :class="deltaClass(consumptionData.monthly_comparison)">
                {{ deltaText(consumptionData.monthly_comparison) }}
                <span class="kpi-delta-label">{{ t('dashboard.kwh_realtime.comparetolastmonth') }}</span>
              </span>
            </div>
            <div class="kpi-item">
              <span class="kpi-label">{{ t('dashboard.kwh_realtime.thisyear') }}</span>
              <div class="kpi-value">
                {{ parseFloat(consumptionData.yearly).toFixed(2) }}
                <span class="kpi-unit">kWh</span>
              </div>
              <span class="kpi-delta" :class="deltaClass(consumptionData.yearly_comparison)">
                {{ deltaText(consumptionData.yearly_comparison) }}
                <span class="kpi-delta-label">{{ t('dashboard.kwh_realtime.comparetolastyyear') }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- 시간대별 차트 -->
        <div class="chart-area">
          <div class="chart-header">
            <span class="chart-label">금일 시간대별 사용량 (kWh)</span>
          </div>
          <RealtimeChart :data="chartData" width="100%" height="180" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { chartAreaGradient } from '@/charts/ChartjsConfig'
import RealtimeChart from '@/charts/connect/RealtimeChart2.vue'
import axios from 'axios'
import { tailwindConfig, hexToRGB } from '@/utils/Utils'
import { useI18n } from 'vue-i18n'

export default {
  name: 'MeasCard_Energy',
  components: { RealtimeChart },
  props: {
    channel: { type: String, required: true },
  },
  setup(props) {
    const { t } = useI18n()
    const updateInterval = ref(null)
    const computedChannel = computed(() =>
      (props.channel?.toLowerCase() === 'main') ? 'Main' : 'Sub'
    )

    const consumptionData = ref({
      daily: 0, weekly: 0, monthly: 0, yearly: 0,
      daily_comparison: 0, weekly_comparison: 0,
      monthly_comparison: 0, yearly_comparison: 0,
    })

    const todayHourlyData = ref([])

    // ── API calls (동일 패턴) ──
    const fetchTodayHourlyData = async (ch) => {
      try {
        const response = await axios.get(`/api/getHourlyEnergyData/${ch}`, {
          params: { date: new Date().toISOString().split('T')[0] }
        })
        if (response.data.success && response.data.hourlyData) {
          todayHourlyData.value = response.data.hourlyData
        }
      } catch (error) {
        console.error('시간별 데이터 가져오기 실패:', error)
      }
    }

    const fetchRedisData = async (ch) => {
      try {
        const response = await axios.get(`/api/getEnergyRedis/${ch}`)
        if (response.data.success) {
          consumptionData.value = {
            daily: response.data.data.daily || 0,
            weekly: response.data.data.weekly || 0,
            monthly: response.data.data.monthly || 0,
            yearly: response.data.data.yearly || 0,
            daily_comparison: response.data.data.daily_comparison || 0,
            weekly_comparison: response.data.data.weekly_comparison || 0,
            monthly_comparison: response.data.data.monthly_comparison || 0,
            yearly_comparison: response.data.data.yearly_comparison || 0,
          }
        }
      } catch (error) {
        console.error('데이터 가져오기 실패:', error)
      }
    }

    // ── Chart.js data ──
    const chartData = computed(() => {
      const now = new Date()
      const currentHour = now.getHours()
      const currentMinute = now.getMinutes()
      const labels = []
      const data = []

      if (!todayHourlyData.value || todayHourlyData.value.length === 0) {
        return {
          labels: [],
          datasets: [{
            data: [],
            fill: true,
            backgroundColor: function (context) {
              const chart = context.chart
              const { ctx, chartArea } = chart
              if (!chartArea) return null
              return chartAreaGradient(ctx, chartArea, [
                { stop: 0, color: `rgba(${hexToRGB(tailwindConfig().theme.colors.violet[500])}, 0)` },
                { stop: 1, color: `rgba(${hexToRGB(tailwindConfig().theme.colors.violet[500])}, 0.2)` }
              ])
            },
            borderColor: tailwindConfig().theme.colors.violet[500],
            borderWidth: 2, pointRadius: 0, pointHoverRadius: 3,
            pointBackgroundColor: tailwindConfig().theme.colors.violet[500],
            clip: 20, tension: 0.4,
          }]
        }
      }

      const hourDataMap = new Map()
      todayHourlyData.value.forEach(item => hourDataMap.set(item.hour, item.value))

      const interval = 10
      for (let hour = 0; hour <= currentHour; hour++) {
        const hourValue = hourDataMap.get(hour) || 0
        const nextHourValue = hourDataMap.get(hour + 1) || hourValue
        const lastMinute = (hour === currentHour) ? currentMinute : 59
        for (let minute = 0; minute <= lastMinute; minute += interval) {
          const ts = new Date()
          ts.setHours(hour); ts.setMinutes(minute); ts.setSeconds(0); ts.setMilliseconds(0)
          const progress = minute / 60
          labels.push(ts)
          data.push(Math.max(0, hourValue + (nextHourValue - hourValue) * progress))
        }
      }

      return {
        labels,
        datasets: [{
          data,
          fill: true,
          backgroundColor: function (context) {
            const chart = context.chart
            const { ctx, chartArea } = chart
            if (!chartArea) return null
            return chartAreaGradient(ctx, chartArea, [
              { stop: 0, color: `rgba(${hexToRGB(tailwindConfig().theme.colors.violet[500])}, 0)` },
              { stop: 1, color: `rgba(${hexToRGB(tailwindConfig().theme.colors.violet[500])}, 0.2)` }
            ])
          },
          borderColor: tailwindConfig().theme.colors.violet[500],
          borderWidth: 2, pointRadius: 0, pointHoverRadius: 3,
          pointBackgroundColor: tailwindConfig().theme.colors.violet[500],
          clip: 20, tension: 0.4,
        }],
      }
    })

    // ── Lifecycle ──
    const initializeData = async () => {
      if (updateInterval.value) { clearInterval(updateInterval.value); updateInterval.value = null }
      await fetchRedisData(computedChannel.value)
      await fetchTodayHourlyData(computedChannel.value)
      updateInterval.value = setInterval(() => {}, 60000) // chartData computed 자동 갱신
      scheduleHourlyUpdate()
    }

    const scheduleHourlyUpdate = () => {
      const now = new Date()
      const msUntilNextHour = (60 - now.getMinutes()) * 60000 - now.getSeconds() * 1000
      setTimeout(() => {
        fetchTodayHourlyData(computedChannel.value)
        fetchRedisData(computedChannel.value)
        setInterval(() => {
          fetchTodayHourlyData(computedChannel.value)
          fetchRedisData(computedChannel.value)
        }, 3600000)
      }, msUntilNextHour)
    }

    onMounted(initializeData)
    watch(() => props.channel, async (n, o) => { if (n !== o) await initializeData() })
    onUnmounted(() => { if (updateInterval.value) clearInterval(updateInterval.value) })

    // ── Helpers ──
    const deltaClass = (val) => {
      const v = parseInt(val)
      if (v === 0) return 'delta-zero'
      return v > 0 ? 'delta-up' : 'delta-down'
    }
    const deltaText = (val) => {
      const v = parseInt(val)
      if (v === 0) return '-'
      return `${v > 0 ? '+' : ''}${v}%`
    }

    return { t, consumptionData, chartData, computedChannel, channel: computedChannel, deltaClass, deltaText }
  },
}
</script>

<style scoped>
.card-wrap {
  @apply col-span-full;
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

/* Grid */
.energy-grid {
  @apply grid grid-cols-12 gap-5;
}

/* KPI */
.kpi-area {
  @apply col-span-3 flex flex-col gap-2 justify-center;
}
.kpi-row {
  @apply flex gap-2;
}
.kpi-item {
  @apply flex-1 text-center px-2 py-3 rounded-xl bg-gray-50 dark:bg-gray-700/50;
}
.kpi-label {
  @apply text-xs text-gray-400 dark:text-gray-500;
}
.kpi-value {
  @apply text-lg font-bold text-gray-800 dark:text-white mt-1 tabular-nums;
}
.kpi-unit {
  @apply text-xs text-gray-400 dark:text-gray-500;
}
.kpi-delta {
  @apply text-xs font-medium block mt-0.5;
}
.kpi-delta-label {
  @apply text-gray-300 dark:text-gray-600 font-normal;
}
.delta-up { @apply text-rose-400; }
.delta-down { @apply text-emerald-500; }
.delta-zero { @apply text-gray-300 dark:text-gray-600; }

/* Chart */
.chart-area {
  @apply col-span-9 bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4;
}
.chart-header {
  @apply flex items-center justify-between mb-2;
}
.chart-label {
  @apply text-xs font-medium text-gray-500 dark:text-gray-400;
}

/* 반응형 */
@media (max-width: 1024px) {
  .energy-grid {
    @apply grid-cols-1;
  }
  .kpi-area {
    @apply col-span-full;
  }
  .chart-area {
    @apply col-span-full;
  }
}
</style>
