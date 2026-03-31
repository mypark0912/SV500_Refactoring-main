<template>
  <div class="css-bar-chart">
    <div class="chart-bars">
      <div
        v-for="(item, index) in chartItems"
        :key="index"
        class="bar-item"
      >
        <div class="bar-container">
          <div
            class="bar-fill"
            :class="item.colorClass"
            :style="{ height: item.height + '%' }"
          >
            <div class="bar-label">{{ item.value }}%</div>
          </div>
        </div>
        <div class="bar-name">{{ item.label }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import axios from 'axios'

export default {
  name: 'DualMeasCard_THD',
  props: {
    data: { type: Object, default: () => ({}) },
    asset: { type: Object, default: () => ({}) },
    height: { type: [String, Number], default: 120 },
    dataKeys: { type: Array, default: () => ['thdu total', 'thdi total', 'tddi total'] },
    labels: { type: Array, default: () => ['THD-U', 'THD-I', 'TDD-I'] },
    colors: { type: Array, default: () => ['purple', 'blue', 'green'] },
    channelmode: { type: Number, default: 0 },
  },
  setup(props) {
    const chartData = ref([])
    const pollTimer = ref(null)

    const getTHD = async () => {
      try {
        const assetName = props.asset?.name || ''
        if (!assetName) return
        const response = await axios.get(`/api/getRealTimeTHD/${assetName}`)
        if (response.data.success) {
          chartData.value = response.data.data
        }
      } catch (err) {
        console.error('THD 데이터 실패:', err)
      }
    }

    const isInverter = computed(() => {
      if (props.channelmode > 1) {
        return props.asset['driveType'] !== 'DOL'
      }
      return false
    })

    const chartItems = computed(() => {
      let values, items

      if (isInverter.value) {
        values = chartData.value.map(item => parseFloat(item.Value || 0))
        const maxValue = Math.max(...values, 100)
        items = chartData.value.map((item, index) => {
          const val = parseFloat(item.Value || 0)
          const height = Math.min(Math.max((val / maxValue) * 100, 5), 100)
          return {
            label: props.labels[index] || item.Title,
            value: val.toFixed(1),
            height,
            colorClass: `bar-${props.colors[index % props.colors.length]}`,
          }
        })
      } else {
        values = props.dataKeys.map(key => parseFloat(props.data[key] || 0))
        const maxValue = Math.max(...values, 100)
        items = props.labels.map((label, index) => {
          const val = values[index]
          const height = Math.min(Math.max((val / maxValue) * 100, 5), 100)
          return {
            label,
            value: val.toFixed(1),
            height,
            colorClass: `bar-${props.colors[index]}`,
          }
        })
      }

      return items
    })

    const startPolling = () => {
      stopPolling()
      getTHD()
      pollTimer.value = setInterval(getTHD, 5 * 60 * 1000)
    }

    const stopPolling = () => {
      if (pollTimer.value) {
        clearInterval(pollTimer.value)
        pollTimer.value = null
      }
    }

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

    onBeforeUnmount(() => { stopPolling() })

    return { chartItems, isInverter }
  },
}
</script>

<style scoped>
.css-bar-chart {
  @apply w-full p-2 pt-6;
}

.chart-bars {
  @apply flex justify-around items-end gap-3 h-20;
  @apply relative;
}

.bar-item {
  @apply flex-1 flex flex-col items-center;
  @apply max-w-[60px];
}

.bar-container {
  @apply relative w-full h-14 flex items-end justify-center;
}

.bar-fill {
  @apply w-full rounded-t transition-all duration-700 ease-out;
  @apply relative flex items-start justify-center;
  @apply min-h-[6px];
}

.bar-label {
  @apply text-xs font-bold;
  @apply absolute bottom-full left-1/2 transform -translate-x-1/2;
  @apply text-center whitespace-nowrap;
  @apply text-gray-800 dark:text-gray-200;
  @apply mb-0.5;
}

.bar-name {
  @apply text-xs font-semibold text-gray-700 dark:text-gray-300;
  @apply mt-1 text-center;
}

.bar-purple {
  @apply bg-gradient-to-t from-purple-500 to-purple-400;
}
.bar-blue {
  @apply bg-gradient-to-t from-blue-500 to-blue-400;
}
.bar-green {
  @apply bg-gradient-to-t from-green-500 to-green-400;
}
</style>
