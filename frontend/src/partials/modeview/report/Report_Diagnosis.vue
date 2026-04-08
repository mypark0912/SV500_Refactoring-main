<template>
  <div class="col-span-full xl:col-span-12 space-y-4">

    <!-- 로딩 표시 -->
    <div v-if="isLoading" class="flex justify-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
    </div>

    <!-- 컨텐츠 -->
    <div v-else class="space-y-4">

      <!-- Bands 상태 카드 -->
      <div v-if="categories.length > 0" class="bands-container bg-white dark:bg-gray-800 rounded-2xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
        <!-- 헤더 -->
        <div class="flex items-center justify-between px-5 py-3 border-b border-gray-200/50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-900/50">
          <span class="text-sm font-semibold text-gray-700 dark:text-gray-200">{{ t('report.cardContext.info.status') }}</span>
          <span v-if="timestamp" class="text-xs text-gray-500 dark:text-gray-400 tabular-nums">{{ formatTimestamp(timestamp) }}</span>
        </div>

        <!-- 카테고리 -->
        <div :class="['columns-grid', isTransformer ? 'cols-4' : 'cols-3']">
          <div v-for="cat in categories" :key="cat.id" class="category-column">
            <div class="col-header">
              <div class="col-color-bar" :style="{ backgroundColor: cat.color }"></div>
              <span class="col-label">{{ cat.label }}</span>
            </div>
            <div class="col-items">
              <div
                v-for="item in cat.items"
                :key="item.name"
                class="item-card"
                :style="isAlert(item) ? { borderColor: STATUS_COLORS[item.status] + '30', boxShadow: '0 1px 4px ' + STATUS_COLORS[item.status] + '12' } : {}"
              >
                <div class="item-card-left">
                  <span class="item-name">{{ item.name }}</span>
                </div>
                <div class="status-blocks">
                  <div
                    v-for="seg in 4"
                    :key="seg"
                    class="status-block"
                    :class="seg <= item.status && item.status > 0 ? `seg-${seg}` : 'seg-off'"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 범례 -->
        <div class="legend-inline">
          <span class="legend-label">{{ t('diagnosis.tabContext.legend') }}</span>
          <div v-for="s in STATUS_LEGEND" :key="s.key" class="legend-item">
            <div class="legend-dot" :style="{ backgroundColor: s.color, opacity: s.key === 0 ? 0.4 : 1 }"></div>
            <span>{{ s.text }}</span>
          </div>
        </div>
      </div>

      <!-- 상태 리포트 -->
      <div class="flex flex-col gap-4">
        <template v-for="item in items" :key="item.Item.Name">
          <StatusReport :data="item" />
        </template>
      </div>

      <!-- 트렌드 차트 -->
      <div class="grid grid-cols-12 gap-4">
        <div v-for="(option, idx) in chartOptions" :key="idx" class="col-span-6">
          <ReportTrend :data="option" />
        </div>
      </div>

      <!-- 데이터 없음 -->
      <div v-if="categories.length === 0 && !isLoading" class="text-gray-500 text-center py-8">
        {{ t('report.noData') }}
      </div>

    </div>
  </div>
</template>

<script>
import { ref, watch, computed } from 'vue'
import { useSetupStore } from '@/store/setup'
import axios from 'axios'
import StatusReport from '../../inners/report/StatusReport.vue'
import ReportTrend from '../../inners/report/ReportTrend.vue'
import { useI18n } from 'vue-i18n'

const STATUS_COLORS = { 0: '#c4c4c4', 1: '#16a34a', 2: '#ca8a04', 3: '#ea580c', 4: '#dc2626' }
const STATUS_TEXT = { 0: 'STOP', 1: 'NORMAL', 2: 'ATTENTION', 3: 'WARNING', 4: 'INSPECT' }
const CATEGORY_COLORS = {
  'voltage-inverter': '#1e3a8a',
  'components': '#8b5cf6',
  'mechanical': '#ec4899',
  'electrical': '#0ea5e9',
}
const ITEM_CATEGORY_MAP = {
  'IncomingVoltage': 'voltage-inverter',
  'DCLink': 'voltage-inverter',
  'Rectifier': 'voltage-inverter',
  'Switching': 'voltage-inverter',
  'Capacitor': 'components',
  'TapChanger': 'components',
  'Bushings': 'components',
  'NoiseVibration': 'mechanical',
  'Rotor': 'mechanical',
  'Bearing': 'mechanical',
  'TorqueRipple': 'mechanical',
  'MechanicalUnbalance': 'mechanical',
  'SoftFoot': 'mechanical',
  'Cavitation': 'mechanical',
  'Vane': 'mechanical',
  'Turbulence': 'mechanical',
  'Blade': 'mechanical',
  'Stress': 'electrical',
  'LoadUnbalance': 'electrical',
  'CableConnection': 'electrical',
  'Winding': 'electrical',
  'Heat': 'electrical',
  'Core': 'electrical',
  'Load': 'electrical',
  'NeutralLoading': 'electrical',
  'Stator': 'electrical',
}

export default {
  name: 'Report_Diagnosis_Bands',
  props: {
    channel: { type: String, default: '' },
    mode: { type: String, default: 'diagnosis' },
    reportData: { type: Object, default: () => ({ main: [], detail: [], timestamp: null }) }
  },
  components: {
    StatusReport,
    ReportTrend,
  },
  setup(props) {
    const { t, locale } = useI18n()
    const setupStore = useSetupStore()
    const asset = computed(() => setupStore.getAssetConfig)

    const timestamp = computed(() => props.reportData?.timestamp || null)

    const isLoading = ref(false)
    const items = ref([])
    const chartOptions = ref([])

    const STATUS_LEGEND = [
      { key: 0, text: t('diagnosis.tabContext.st0'), color: '#c4c4c4' },
      { key: 1, text: t('diagnosis.tabContext.st1'), color: '#16a34a' },
      { key: 2, text: t('diagnosis.tabContext.st2'), color: '#ca8a04' },
      { key: 3, text: t('diagnosis.tabContext.st3'), color: '#ea580c' },
      { key: 4, text: t('diagnosis.tabContext.st4'), color: '#dc2626' },
    ]

    const formatTimestamp = (ts) => {
      if (!ts) return ''
      const date = new Date(ts)
      return date.toLocaleString(navigator.language, {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
      })
    }

    /* ───────── reportData → bands 카테고리 변환 ───────── */
    const categories = computed(() => {
      const { main } = props.reportData || {}
      if (!main || main.length === 0) return []

      const cats = [
        { id: 'voltage-inverter', label: 'Voltage / Inverter', color: CATEGORY_COLORS['voltage-inverter'], items: [] },
        { id: 'components',       label: 'Components',         color: CATEGORY_COLORS['components'],       items: [] },
        { id: 'mechanical',       label: 'Mechanical',         color: CATEGORY_COLORS['mechanical'],       items: [] },
        { id: 'electrical',       label: 'Electrical',         color: CATEGORY_COLORS['electrical'],       items: [] },
      ]
      const catMap = {}
      cats.forEach(c => { catMap[c.id] = c })

      for (const item of main) {
        const itemName = (item.item_name || '').replace(/\s/g, '')
        const catId = ITEM_CATEGORY_MAP[itemName]
        if (catId && catMap[catId]) {
          const titleKey = `title_${locale.value}`
          catMap[catId].items.push({
            name: item[titleKey] || item.title || item.item_name,
            rawName: itemName,
            status: item.status || 0,
          })
        }
      }
      return cats.filter(c => c.items.length > 0)
    })

    const isTransformer = computed(() => {
      if (props.channel === 'Main') {
        return asset.value.assetType_main === 'Transformer' || asset.value.assetType_main === 'PrimaryTransformer'
      } else {
        return asset.value.assetType_sub === 'Transformer' || asset.value.assetType_sub === 'PrimaryTransformer'
      }
    })

    const getAlertCount = (cat) => cat.items.filter(i => i.status >= 3).length
    const getWarnCount = (cat) => cat.items.filter(i => i.status === 2).length
    const isAlert = (item) => item.status >= 3

    /* ───────── 트렌드 차트 데이터 조회 ───────── */
    const setChartData = async (itemName, title) => {
      let option = {}
      const chName = props.channel == 'Main' ? asset.value.assetName_main : asset.value.assetName_sub
      try {
        const response = await axios.get(`/report/status_trend/${props.mode}/${chName}/${itemName}`)
        if (response.data.success) {
          const trendData = response.data.data.trend
          if (trendData && trendData.length > 0) {
            option = {
              lineLabels: trendData.map(item => item.timestamp),
              lineData: [{ name: title, data: trendData.map(item => item.status), isThreshold: false }],
              lineTitle: title,
              mode: 'DiagnosisDetail',
            }
          } else {
            option = { lineLabels: [], lineData: [], lineTitle: title, mode: 'DiagnosisDetail' }
          }
        } else {
          option = { lineLabels: [], lineData: [], lineTitle: title, mode: 'DiagnosisDetail' }
        }
      } catch (error) {
        console.error('트렌드 데이터 요청 실패:', error)
        option = { lineLabels: [], lineData: [], lineTitle: title, mode: 'DiagnosisDetail' }
      }
      return option
    }

    const loadTrendCharts = async (chartList) => {
      const options = []
      const seenNames = new Set()
      const uniqueItems = []
      for (const item of chartList) {
        if (!seenNames.has(item.Name)) {
          seenNames.add(item.Name)
          uniqueItems.push(item)
        }
      }
      for (const item of uniqueItems) {
        const titleName = item.Title || item.Name
        const chartValue = await setChartData(item.Name, titleName)
        if (chartValue.lineLabels.length > 0) options.push(chartValue)
      }
      return options
    }

    /* ───────── InfluxDB 데이터 변환 (상태 리포트 + 트렌드용) ───────── */
    const transformInfluxData = (main, detail) => {
      const mainByName = {}
      for (let i = 0; i < main.length; i++) {
        const key = main[i].item_name.replace(/\s/g, '')
        mainByName[key] = main[i]
      }

      const groupedByParent = {}
      for (let i = 0; i < detail.length; i++) {
        const parentName = detail[i].parent_name
        const parentKey = parentName.replace(/\s/g, '')
        if (!groupedByParent[parentName]) {
          const parentInfo = mainByName[parentKey] || {}
          groupedByParent[parentName] = {
            item_name: parentName,
            status: 0,
            Titles: {
              en: parentInfo.title_en || parentName,
              ko: parentInfo.title_ko || parentName,
              ja: parentInfo.title_ja || parentName
            },
            Descriptions: {
              en: parentInfo.description_en || '',
              ko: parentInfo.description_ko || '',
              ja: parentInfo.description_ja || ''
            },
            children: []
          }
        }
        if (detail[i].status > groupedByParent[parentName].status) {
          groupedByParent[parentName].status = detail[i].status
        }
        groupedByParent[parentName].children.push(detail[i])
      }

      const itemsResult = [], chartList = []
      for (const parentName in groupedByParent) {
        const parent = groupedByParent[parentName]
        if (parent.status > 1) {
          const childDict = []
          for (let j = 0; j < parent.children.length; j++) {
            const child = parent.children[j]
            if (child.status > 1) {
              const childTitle = child[`title_${locale.value}`] || child.title || child.item_name
              childDict.push({
                Title: childTitle,
                Assembly: child.assembly_id,
                Value: child.value !== undefined ? child.value : 'NaN'
              })
            }
          }
          if (childDict.length > 0) {
            chartList.push({
              Name: parentName.replace(/\s/g, ''),
              Title: parent.Titles[locale.value],
              Status: parent.status
            })
            itemsResult.push({
              Item: {
                Name: parentName,
                Title: parent.Titles[locale.value],
                Titles: parent.Titles,
                Descriptions: parent.Descriptions,
                Status: parent.status
              },
              Child: childDict
            })
          }
        }
      }
      return { items: itemsResult, chartList }
    }

    /* ───────── 데이터 처리 ───────── */
    const processReportData = async () => {
      const { main, detail } = props.reportData
      if (!main || main.length === 0) {
        items.value = []
        chartOptions.value = []
        return
      }

      isLoading.value = true
      const { items: it, chartList } = transformInfluxData(main, detail)
      items.value = it
      chartOptions.value = await loadTrendCharts(chartList)
      isLoading.value = false
    }

    /* ───────── Watch reportData ───────── */
    watch(() => props.reportData, async (newVal) => {
      if (newVal && newVal.main && newVal.main.length > 0) {
        await processReportData()
      } else {
        items.value = []
        chartOptions.value = []
      }
    }, { deep: true, immediate: true })

    return {
      t, isLoading, items, chartOptions, timestamp, categories,
      channel: props.channel, mode: props.mode,
      STATUS_COLORS, STATUS_TEXT, STATUS_LEGEND,
      getAlertCount, getWarnCount, isAlert, isTransformer, formatTimestamp,
    }
  }
}
</script>

<style scoped>
.bands-container {
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.columns-grid {
  display: grid;
  gap: 16px;
  padding: 16px 20px;
}
.columns-grid.cols-4 {
  grid-template-columns: repeat(4, 1fr);
}
.columns-grid.cols-3 {
  grid-template-columns: repeat(3, 1fr);
  gap: 40px;
}
.category-column {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.col-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid #f1f5f9;
}
:is(.dark) .col-header {
  border-bottom-color: #1e293b;
}
.col-color-bar {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  flex-shrink: 0;
}
.col-label {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}
:is(.dark) .col-label {
  color: #e2e8f0;
}
.col-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 8px;
}
.col-badge--danger {
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fecaca;
}
.col-badge--warn {
  color: #ca8a04;
  background: #fefce8;
  border: 1px solid #fde68a;
}
.col-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.item-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e8ecf0;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
:is(.dark) .item-card {
  background: #1e293b;
  border-color: #334155;
}
.item-card-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.item-name {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
}
:is(.dark) .item-name {
  color: #e2e8f0;
}
.item-alert-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 8px;
  border: 1px solid;
}
.status-blocks {
  display: flex;
  gap: 3px;
}
.status-block {
  width: 20px;
  height: 26px;
  border-radius: 4px;
  transition: all 0.3s;
}
.status-block.seg-1 { @apply bg-green-500; }
.status-block.seg-2 { @apply bg-yellow-500; }
.status-block.seg-3 { @apply bg-orange-500; }
.status-block.seg-4 { @apply bg-red-500; }
.status-block.seg-off {
  @apply bg-gray-400 dark:bg-gray-500;
  @apply opacity-30;
}
.legend-inline {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px 20px;
  border-top: 1px solid #f1f5f9;
  background: rgba(249,250,251,0.3);
}
:is(.dark) .legend-inline {
  border-top-color: #1e293b;
  background: rgba(17,24,39,0.3);
}
.legend-label {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #64748b;
}
:is(.dark) .legend-item {
  color: #9ca3af;
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
@media (max-width: 768px) {
  .columns-grid.cols-4,
  .columns-grid.cols-3 {
    grid-template-columns: repeat(2, auto);
  }
}
@media (max-width: 480px) {
  .columns-grid.cols-4,
  .columns-grid.cols-3 {
    grid-template-columns: auto;
  }
}
</style>
