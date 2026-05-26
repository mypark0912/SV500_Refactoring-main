<template>
  <div class="col-span-full xl:col-span-12 space-y-4">

    <!-- 로딩 표시 -->
    <div v-if="isLoading" class="flex justify-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
    </div>

    <!-- 컨텐츠 -->
    <div v-else class="space-y-4">

      <!-- Bands 상태 카드 (카테고리 없이 플랫 나열) -->
      <div v-if="bandItems.length > 0" class="bands-container bg-white dark:bg-gray-800 rounded-2xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
        <div class="flex items-center justify-between px-5 py-3 border-b border-gray-200/50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-900/50">
          <span class="text-sm font-semibold text-gray-700 dark:text-gray-200">{{ t('report.cardContext.info.status') }}</span>
          <span v-if="timestamp" class="text-xs text-gray-500 dark:text-gray-400 tabular-nums">{{ formatTimestamp(timestamp) }}</span>
        </div>
        <div class="bands-grid">
          <div
            v-for="item in bandItems"
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
      <div v-if="bandItems.length === 0 && !isLoading" class="text-gray-500 text-center py-8">
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

export default {
  name: 'Report_PQ',
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
    const trendCache = ref({})

    const STATUS_LEGEND = computed(() => [
      { key: 0, text: t('diagnosis.tabContext.st0'), color: '#c4c4c4' },
      { key: 1, text: t('diagnosis.tabContext.st1'), color: '#16a34a' },
      { key: 2, text: t('diagnosis.tabContext.st2'), color: '#ca8a04' },
      { key: 3, text: t('diagnosis.tabContext.st3'), color: '#ea580c' },
      { key: 4, text: t('diagnosis.tabContext.st4'), color: '#dc2626' },
    ])

    const isAlert = (item) => item.status >= 3

    const formatTimestamp = (ts) => {
      if (!ts) return ''
      const date = new Date(ts)
      return date.toLocaleString(navigator.language, {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
      })
    }

    const chartMode = computed(() => props.mode === 'diagnosis' ? 'DiagnosisDetail' : 'PowerQuality')

    /* ───────── raw main (bands용, locale 무관) ───────── */
    const rawMain = computed(() => {
      const { main = [] } = props.reportData || {}
      return main.map(m => ({
        rawName: (m.item_name || '').replace(/\s/g, ''),
        status: m.status || 0,
        Titles: {
          en: m.title_en || m.title || m.item_name,
          ko: m.title_ko || m.title || m.item_name,
          ja: m.title_ja || m.title || m.item_name,
        },
      }))
    })

    /* ───────── raw 그룹 데이터 (locale 무관) ───────── */
    const groupedParents = computed(() => {
      const { main = [], detail = [] } = props.reportData || {}
      if (main.length === 0) return []

      const mainByName = {}
      for (const m of main) {
        mainByName[m.item_name.replace(/\s/g, '')] = m
      }

      const groupedByParent = {}
      for (const d of detail) {
        const parentName = d.parent_name
        const parentKey = parentName.replace(/\s/g, '')
        if (!groupedByParent[parentName]) {
          const parentInfo = mainByName[parentKey] || {}
          groupedByParent[parentName] = {
            item_name: parentName,
            status: 0,
            Titles: {
              en: parentInfo.title_en || parentName,
              ko: parentInfo.title_ko || parentName,
              ja: parentInfo.title_ja || parentName,
            },
            Descriptions: {
              en: parentInfo.description_en || '',
              ko: parentInfo.description_ko || '',
              ja: parentInfo.description_ja || '',
            },
            children: [],
          }
        }
        if (d.status > groupedByParent[parentName].status) {
          groupedByParent[parentName].status = d.status
        }
        groupedByParent[parentName].children.push(d)
      }

      const result = []
      for (const name in groupedByParent) {
        const parent = groupedByParent[name]
        if (parent.status <= 1) continue
        const alertChildren = parent.children.filter(c => c.status > 1)
        if (alertChildren.length === 0) continue
        result.push({
          Name: name.replace(/\s/g, ''),
          ParentName: name,
          Titles: parent.Titles,
          Descriptions: parent.Descriptions,
          Status: parent.status,
          children: alertChildren,
        })
      }
      return result
    })

    /* ───────── bandItems (locale 반응) ───────── */
    const bandItems = computed(() => {
      const currentLocale = locale.value
      return rawMain.value.map(m => ({
        name: m.Titles[currentLocale],
        rawName: m.rawName,
        status: m.status,
      }))
    })

    /* ───────── items (locale 반응) ───────── */
    const items = computed(() => {
      const currentLocale = locale.value
      return groupedParents.value.map(p => ({
        Item: {
          Name: p.ParentName,
          Title: p.Titles[currentLocale],
          Titles: p.Titles,
          Descriptions: p.Descriptions,
          Status: p.Status,
        },
        Child: p.children.map(child => ({
          Title: child[`title_${currentLocale}`] || child.title || child.item_name,
          Assembly: child.assembly_id,
          Value: child.value !== undefined ? child.value : 'NaN',
        })),
      }))
    })

    /* ───────── chartOptions (trendCache + locale) ───────── */
    const chartOptions = computed(() => {
      const currentLocale = locale.value
      const cache = trendCache.value
      const mode = chartMode.value
      const options = []
      for (const p of groupedParents.value) {
        const trend = cache[p.Name]
        if (!trend || trend.length === 0) continue
        const title = p.Titles[currentLocale]
        options.push({
          lineLabels: trend.map(t => t.timestamp),
          lineData: [{ name: title, data: trend.map(t => t.status), isThreshold: false }],
          lineTitle: title,
          mode,
        })
      }
      return options
    })

    /* ───────── 트렌드 데이터 fetch (reportData 변경 시만) ───────── */
    const fetchTrends = async () => {
      const chName = props.channel == 'Main' ? asset.value.assetName_main : asset.value.assetName_sub
      const newCache = {}
      for (const p of groupedParents.value) {
        if (newCache[p.Name]) continue
        try {
          const response = await axios.get(`/report/status_trend/${props.mode}/${chName}/${p.Name}`)
          newCache[p.Name] = response.data.success ? (response.data.data.trend || []) : []
        } catch (e) {
          console.error('트렌드 데이터 요청 실패:', e)
          newCache[p.Name] = []
        }
      }
      trendCache.value = newCache
    }

    watch(() => props.reportData, async (newVal) => {
      if (newVal && newVal.main && newVal.main.length > 0) {
        isLoading.value = true
        await fetchTrends()
        isLoading.value = false
      } else {
        trendCache.value = {}
      }
    }, { deep: true, immediate: true })

    return {
      t, isLoading, bandItems, items, chartOptions, timestamp,
      channel: props.channel, mode: props.mode, formatTimestamp,
      STATUS_COLORS, STATUS_TEXT, STATUS_LEGEND, isAlert,
    }
  }
}
</script>

<style scoped>
.bands-container {
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.bands-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 16px 20px;
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
  .bands-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 480px) {
  .bands-grid {
    grid-template-columns: 1fr;
  }
}
</style>
