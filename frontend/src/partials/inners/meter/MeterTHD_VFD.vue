<template>
  <div class="col-span-full xl:col-span-7 bg-white dark:bg-gray-800 shadow-sm rounded-xl">
    <div class="card">
      <div class="premium-card-header">
        <div class="header-content">
          <div class="header-left">
            <h2 class="card-title">{{ t('meter.cardTitle.title_thd') }}</h2>
          </div>
        </div>
      </div>
    </div>

    <!-- 로딩 -->
    <div v-if="loading" class="p-4 text-center text-gray-400 text-sm">
      {{ t('common.loading') || 'Loading...' }}
    </div>

    <!-- 데이터 테이블 -->
    <div v-else-if="thdList.length > 0" class="overflow-x-auto px-4 py-4">
      <table class="table-auto w-full dark:text-white">
        <thead class="text-xs uppercase text-gray-400 bg-gray-50 dark:bg-gray-300 dark:text-gray-200 dark:bg-opacity-50 rounded-sm">
        <tr>
            <th class="px-4 py-2">
            <div class="font-bold text-left">{{ t('meter.Table.th_tilte') }}</div>
            </th>
            <th class="px-4 py-2">
            <div class="font-bold text-center">{{ t('meter.Table.th_value') }}</div>
            </th>
        </tr>
        </thead>
        <tbody class="text-sm font-medium divide-y divide-gray-100 dark:divide-gray-700/60">
        <tr v-for="(item, index) in thdList" :key="index">
            <td class="px-4 py-2 font-bold text-left">{{ item.label }}</td>
            <td class="px-4 py-2 text-center font-bold">{{ item.value }} {{ item.unit }}</td>
        </tr>
        </tbody>
      </table>
    </div>

    <!-- 데이터 없음 -->
    <div v-else class="p-4 text-center text-gray-400 text-sm">
      No Data
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'

export default {
  name: 'MeterThdVfd',
  props: {
    channel: String,
    assetName: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const { t } = useI18n()
    const chartData = ref([])
    const loading = ref(false)
    let pollTimer = null

    const labels = ['THD-U', 'THD-I', 'TDD-I']

    const thdList = computed(() => {
      return chartData.value.map((item, index) => ({
        label: labels[index],
        value: parseFloat(item.Value || 0).toFixed(2),
        unit: item.Unit || '%'
      }))
    })

    // const rowBgClass = (index) => {
    //   const classes = [
    //     'bg-purple-50 dark:bg-purple-900/20',
    //     'bg-blue-50 dark:bg-blue-900/20',
    //     'bg-green-50 dark:bg-green-900/20',
    //   ]
    //   return classes[index % classes.length]
    // }

    const fetchTHD = async () => {
      if (!props.assetName) return
      try {
        loading.value = chartData.value.length === 0
        const response = await axios.get(`/api/getRealTimeTHD/${props.assetName}`)
        if (response.data.success) {
          chartData.value = response.data.data
        }
      } catch (err) {
        console.error('❌ VFD THD 데이터 실패:', err)
      } finally {
        loading.value = false
      }
    }

    const startPolling = () => {
      stopPolling()
      fetchTHD()
      pollTimer = setInterval(fetchTHD, 5 * 60 * 1000)
    }

    const stopPolling = () => {
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    }

    watch(
      () => props.assetName,
      (newName) => {
        if (newName) {
          startPolling()
        } else {
          stopPolling()
          chartData.value = []
        }
      },
      { immediate: true }
    )

    onBeforeUnmount(() => {
      stopPolling()
    })

    return {
      thdList,
      loading,
      //rowBgClass,
      t
    }
  }
}
</script>

<style>
@import '../../../css/card-styles.css';
</style>