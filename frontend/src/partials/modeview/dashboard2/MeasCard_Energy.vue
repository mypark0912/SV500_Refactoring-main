<template>
  <div class="card-wrap">
    <!-- 헤더 -->
    <div class="card-header">
      <h3 class="card-title meter-accent-indigo">{{ t('dashboard.kwh') }}</h3>
      <span class="card-channel">
        {{ channel === 'Main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>

    <div class="card-body">
      <!-- Summary Section -->
      <div class="summary-grid">
        <!-- 금일 -->
        <div class="summary-item today">
          <div class="summary-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div class="summary-content">
            <span class="summary-label">{{ t('dashboard.kwh_realtime.today') }}</span>
            <div class="summary-value">
              {{ parseFloat(consumptionData.daily).toFixed(2) }}
              <span class="summary-unit">kWh</span>
            </div>
            <div class="summary-compare">
              <span class="compare-label">{{ t('dashboard.kwh_realtime.comparetoyesterday') }}</span>
              <span class="compare-value" :class="parseInt(consumptionData.daily_comparison) >= 0 ? 'up' : 'down'">
                {{ parseInt(consumptionData.daily_comparison) }}%
              </span>
            </div>
          </div>
        </div>

        <!-- 금주 -->
        <div class="summary-item week">
          <div class="summary-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
          </div>
          <div class="summary-content">
            <span class="summary-label">{{ t('dashboard.kwh_realtime.thisweek') }}</span>
            <div class="summary-value">
              {{ parseFloat(consumptionData.weekly).toFixed(2) }}
              <span class="summary-unit">kWh</span>
            </div>
            <div class="summary-compare">
              <span class="compare-label">{{ t('dashboard.kwh_realtime.comparetolastweek') }}</span>
              <span class="compare-value" :class="parseInt(consumptionData.weekly_comparison) >= 0 ? 'up' : 'down'">
                {{ parseInt(consumptionData.weekly_comparison) }}%
              </span>
            </div>
          </div>
        </div>

        <!-- 금월 -->
        <div class="summary-item month">
          <div class="summary-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            </svg>
          </div>
          <div class="summary-content">
            <span class="summary-label">{{ t('dashboard.kwh_realtime.thismonth') }}</span>
            <div class="summary-value">
              {{ parseFloat(consumptionData.monthly).toFixed(2) }}
              <span class="summary-unit">kWh</span>
            </div>
            <div class="summary-compare">
              <span class="compare-label">{{ t('dashboard.kwh_realtime.comparetolastmonth') }}</span>
              <span class="compare-value" :class="parseInt(consumptionData.monthly_comparison) >= 0 ? 'up' : 'down'">
                {{ parseInt(consumptionData.monthly_comparison) }}%
              </span>
            </div>
          </div>
        </div>

        <!-- 연간 -->
        <div class="summary-item year">
          <div class="summary-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
          </div>
          <div class="summary-content">
            <span class="summary-label">{{ t('dashboard.kwh_realtime.thisyear') }}</span>
            <div class="summary-value">
              {{ parseFloat(consumptionData.yearly).toFixed(2) }}
              <span class="summary-unit">kWh</span>
            </div>
            <div class="summary-compare">
              <span class="compare-label">{{ t('dashboard.kwh_realtime.comparetolastyyear') }}</span>
              <span class="compare-value" :class="parseInt(consumptionData.yearly_comparison) >= 0 ? 'up' : 'down'">
                {{ parseInt(consumptionData.yearly_comparison) }}%
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Chart -->
      <div class="chart-area">
        <RealtimeChart :data="chartData" width="100%" height="200" />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { chartAreaGradient } from '../../../charts/ChartjsConfig'
import RealtimeChart from '../../../charts/connect/RealtimeChart2.vue'
import axios from 'axios'
import { tailwindConfig, hexToRGB } from '../../../utils/Utils'
import { useI18n } from 'vue-i18n'

export default {
  name: 'MeasCard_Energy',
  components: {
    RealtimeChart,
  },
  props: {
    channel: {
      type: String,
      default: ''
    },
  },
  setup(props) {
    const { t } = useI18n();
    const updateInterval = ref(null);
    const channel = computed(() => (props.channel == 'main' || props.channel == 'Main') ? 'Main' : 'Sub');

    const consumptionData = ref({
      today: 0,
      daily: 0,
      weekly: 0,
      monthly: 0,
      yearly: 0,
      daily_comparison: 0,
      weekly_comparison: 0,
      monthly_comparison: 0,
      yearly_comparison: 0,
    });

    const todayHourlyData = ref([]);

    const fetchTodayHourlyData = async (ch) => {
      try {
        const response = await axios.get(`/api/getHourlyEnergyData/${ch}`, {
          params: {
            date: new Date().toISOString().split('T')[0],
          }
        });
        if (response.data.success && response.data.hourlyData) {
          todayHourlyData.value = response.data.hourlyData;
        }
      } catch (error) {
        console.error("시간별 데이터 가져오기 실패:", error);
      }
    };

    const fetchRedisOnehData = async (ch) => {
      try {
        const response = await axios.get(`/api/getEnergyRedis/${ch}`);
        if (response.data.success) {
          consumptionData.value = {
            today: response.data.data.today || 0,
            daily: response.data.data.daily || 0,
            weekly: response.data.data.weekly || 0,
            monthly: response.data.data.monthly || 0,
            yearly: response.data.data.yearly || 0,
            daily_comparison: response.data.data.daily_comparison || 0,
            weekly_comparison: response.data.data.weekly_comparison || 0,
            monthly_comparison: response.data.data.monthly_comparison || 0,
            yearly_comparison: response.data.data.yearly_comparison || 0,
          };
        }
      } catch (error) {
        console.error("데이터 가져오기 실패:", error);
      }
    };

    const chartData = computed(() => {
      const now = new Date();
      const currentHour = now.getHours();
      const currentMinute = now.getMinutes();

      const labels = [];
      const data = [];

      if (!todayHourlyData.value || todayHourlyData.value.length === 0) {
        return {
          labels: [],
          datasets: [{
            data: [],
            fill: true,
            backgroundColor: function(context) {
              const chart = context.chart;
              const {ctx, chartArea} = chart;
              if (!chartArea) return null;
              return chartAreaGradient(ctx, chartArea, [
                { stop: 0, color: `rgba(${hexToRGB(tailwindConfig().theme.colors.violet[500])}, 0)` },
                { stop: 1, color: `rgba(${hexToRGB(tailwindConfig().theme.colors.violet[500])}, 0.2)` }
              ]);
            },
            borderColor: tailwindConfig().theme.colors.violet[500],
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 3,
            pointBackgroundColor: tailwindConfig().theme.colors.violet[500],
            clip: 20,
            tension: 0.4,
          }]
        };
      }

      const hourDataMap = new Map();
      todayHourlyData.value.forEach(item => {
        hourDataMap.set(item.hour, item.value);
      });

      const interval = 10;

      for (let hour = 0; hour <= currentHour; hour++) {
        const hourValue = hourDataMap.get(hour) || 0;
        const nextHourValue = hourDataMap.get(hour + 1) || hourValue;
        const lastMinute = (hour === currentHour) ? currentMinute : 59;

        for (let minute = 0; minute <= lastMinute; minute += interval) {
          const today = new Date();
          today.setHours(hour);
          today.setMinutes(minute);
          today.setSeconds(0);
          today.setMilliseconds(0);

          const progress = minute / 60;
          const interpolatedValue = hourValue + (nextHourValue - hourValue) * progress;

          labels.push(today);
          data.push(Math.max(0, interpolatedValue));
        }
      }

      return {
        labels: labels,
        datasets: [
          {
            data: data,
            fill: true,
            backgroundColor: function(context) {
              const chart = context.chart;
              const {ctx, chartArea} = chart;
              if (!chartArea) return null;
              return chartAreaGradient(ctx, chartArea, [
                { stop: 0, color: `rgba(${hexToRGB(tailwindConfig().theme.colors.violet[500])}, 0)` },
                { stop: 1, color: `rgba(${hexToRGB(tailwindConfig().theme.colors.violet[500])}, 0.2)` }
              ]);
            },
            borderColor: tailwindConfig().theme.colors.violet[500],
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 3,
            pointBackgroundColor: tailwindConfig().theme.colors.violet[500],
            clip: 20,
            tension: 0.4,
          },
        ],
      };
    });

    const initializeData = async () => {
      if (updateInterval.value) {
        clearInterval(updateInterval.value);
        updateInterval.value = null;
      }

      await fetchRedisOnehData(channel.value);
      await fetchTodayHourlyData(channel.value);

      updateInterval.value = setInterval(() => {}, 60000);
      scheduleHourlyUpdate();
    };

    const scheduleHourlyUpdate = () => {
      const now = new Date();
      const msUntilNextHour = (60 - now.getMinutes()) * 60000 - now.getSeconds() * 1000;

      setTimeout(() => {
        fetchTodayHourlyData(channel.value);
        fetchRedisOnehData(channel.value);

        setInterval(() => {
          fetchTodayHourlyData(channel.value);
          fetchRedisOnehData(channel.value);
        }, 3600000);
      }, msUntilNextHour);
    };

    onMounted(async () => {
      await initializeData();
    });

    watch(
      () => props.channel,
      async (newChannel, oldChannel) => {
        if (newChannel !== oldChannel) {
          await initializeData();
        }
      }
    );

    onUnmounted(() => {
      if (updateInterval.value) {
        clearInterval(updateInterval.value);
        updateInterval.value = null;
      }
    });

    return {
      chartData,
      t,
      channel,
      consumptionData,
      todayHourlyData,
    };
  }
}
</script>

<style scoped>
.card-wrap {
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
.meter-accent-indigo::before {
  @apply bg-indigo-500;
}
.card-channel {
  @apply text-gray-500 dark:text-gray-500;
  font-size: 10px;
}
.card-body {
  @apply px-4 py-3;
}

/* Summary Grid */
.summary-grid {
  @apply grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4;
}
.summary-item {
  @apply flex items-start gap-3 p-3 rounded-lg;
  @apply border border-gray-100 dark:border-gray-700;
  @apply transition-all duration-200 hover:shadow-md;
}
.summary-item.today {
  @apply bg-blue-50/60 dark:bg-blue-900/20;
}
.summary-item.today .summary-icon {
  @apply text-blue-500 dark:text-blue-400;
}
.summary-item.week {
  @apply bg-emerald-50/60 dark:bg-emerald-900/20;
}
.summary-item.week .summary-icon {
  @apply text-emerald-500 dark:text-emerald-400;
}
.summary-item.month {
  @apply bg-violet-50/60 dark:bg-violet-900/20;
}
.summary-item.month .summary-icon {
  @apply text-violet-500 dark:text-violet-400;
}
.summary-item.year {
  @apply bg-amber-50/60 dark:bg-amber-900/20;
}
.summary-item.year .summary-icon {
  @apply text-amber-500 dark:text-amber-400;
}
.summary-icon {
  @apply flex-shrink-0 mt-0.5;
}
.summary-content {
  @apply flex-1 min-w-0;
}
.summary-label {
  @apply text-sm text-gray-500 dark:text-gray-400 block;
}
.summary-value {
  @apply text-base font-bold text-gray-800 dark:text-white tabular-nums leading-tight;
}
.summary-unit {
  @apply text-xs font-medium text-gray-600 dark:text-gray-400;
}
.summary-compare {
  @apply flex items-center gap-1 mt-0.5;
}
.compare-label {
  @apply text-xs text-gray-600 dark:text-gray-400;
}
.compare-value {
  @apply text-xs font-semibold;
}
.compare-value.up {
  @apply text-green-600 dark:text-green-400;
}
.compare-value.down {
  @apply text-red-500 dark:text-red-400;
}

/* Chart */
.chart-area {
  @apply bg-gray-50/50 dark:bg-gray-800/50 rounded-lg p-2;
  @apply border border-gray-100 dark:border-gray-700;
}

@media (max-width: 640px) {
  .summary-grid {
    @apply grid-cols-2 gap-2;
  }
  .summary-value {
    @apply text-lg;
  }
}
</style>
