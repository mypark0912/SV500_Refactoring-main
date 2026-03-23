<template>
<div class="grid grid-cols-12 gap-6">
  <!-- 상단: 왼쪽 스테이지 버튼 + 오른쪽 배터리 차트 -->
  <div class="col-span-12">
    <div class="stage-chart-container bg-white dark:bg-gray-800 rounded-2xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
      <!-- 상단 헤더: data_state / recordtime -->
      <div class="flex items-center justify-between px-5 py-3 border-b border-gray-200/50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-900/50">
        <span class="text-sm font-semibold text-gray-700 dark:text-gray-200">{{ t('diagnosis.tabTitle.detailTitle') }}</span>
        <span class="text-xs text-gray-500 dark:text-gray-400 tabular-nums">{{ data_state }} / {{ data_recordtime || '-' }}</span>
      </div>
      <div class="flex">
        <!-- 왼쪽: 스테이지 세로 탭 -->
        <div class="stage-tabs">
          <button
            v-for="stage in stageList"
            :key="stage.key"
            class="stage-tab"
            :class="{ 'stage-tab--active': selected === stage.key }"
            @click="selected = stage.key"
          >
            <div class="stage-tab-status" :style="{ backgroundColor: getStatusColor(stage.status) }"></div>
            <span class="stage-tab-label">{{ stage.label }}</span>
            <span v-if="stage.alertCount > 0" class="stage-tab-badge stage-tab-badge--danger">{{ stage.alertCount }}</span>
            <span v-else-if="stage.warnCount > 0" class="stage-tab-badge stage-tab-badge--warn">{{ stage.warnCount }}</span>
          </button>
        </div>
        <!-- 오른쪽: 배터리 차트 + 트리테이블 -->
        <div class="flex-1 min-w-0 overflow-auto p-2">
          <Diagnosis_Barchart
            v-if="selectedChartData !== null"
            :channel="channel"
            :data="selectedChartData"
            :mode="mode"
            class="h-auto"
            :key="'chart-' + selected"
          />
          <div v-else class="flex items-center justify-center text-gray-400 dark:text-gray-500 text-sm py-20">
            데이터 없음
          </div>
          <div class="mt-4 px-2">
            <Diagnosis_TreeTable
              v-if="selectedTreeData.length > 0"
              :channel="channel"
              :data="selectedTreeData"
              :mode="mode"
              :key="'tree-' + selected"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script>
import { ref, computed, watch, onMounted, provide } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import Diagnosis_TreeTable from './Diagnosis_TreeTable2.vue'
import Diagnosis_Barchart from './Diagnosis_BarChart_Compact.vue'

const STATUS_COLORS = { 0: '#c4c4c4', 1: '#16a34a', 2: '#ca8a04', 3: '#ea580c', 4: '#dc2626' }

export default {
  name: 'DiagnosisTab_New',
  components: {
    Diagnosis_TreeTable,
    Diagnosis_Barchart,
  },
  props: {
    asset: {
      type: Object,
      default: () => ({})
    },
    channel: {
      type: String,
      default: ''
    },
    mode: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const { t, locale } = useI18n()
    const channel = ref(props.channel)
    const asset = ref(props.asset)
    const selected = ref('source')
    const data_recordtime = ref('')
    const data_state = ref('')
    const groupedTree = ref([])
    const allChartData = ref(null)
    const mode = ref(props.mode)

    /* ───────── 스테이지 목록 (탭 버튼용) ───────── */
    const stageList = computed(() => {
      const stages = [
        { key: 'source',      label: '전압소스' },
        { key: 'inverter',    label: '인버터' },
        { key: 'motor-elec',  label: '전기적 상태' },
        { key: 'motor-mech',  label: '기계적 상태' },
      ]
      return stages.map(s => {
        let maxStatus = 0
        let alertCount = 0
        let warnCount = 0
        for (const node of groupedTree.value) {
          if ((node.Stage || 'motor-mech') !== s.key) continue
          if (node.children) {
            for (const child of node.children) {
              const st = child.Status || 0
              maxStatus = Math.max(maxStatus, st)
              if (st >= 3) alertCount++
              else if (st === 2) warnCount++
            }
          }
        }
        return { ...s, status: maxStatus, alertCount, warnCount }
      })
    })

    /* ───────── 선택된 스테이지의 트리 데이터 ───────── */
    const selectedTreeData = computed(() => {
      const nodes = groupedTree.value.filter(n => (n.Stage || 'motor-mech') === selected.value)
      const result = []
      for (const node of nodes) {
        if (node.children) {
          result.push(...node.children)
        }
      }
      return result
    })

    /* ───────── 선택된 스테이지의 배터리 차트 데이터 ───────── */
    const selectedChartData = computed(() => {
      if (!allChartData.value) return null
      const stageNodes = groupedTree.value.filter(n => (n.Stage || 'motor-mech') === selected.value)
      const nameSet = new Set()
      for (const node of stageNodes) {
        if (node.children) {
          for (const child of node.children) {
            nameSet.add(child.Name)
          }
        }
      }
      const names = []
      const values = []
      const titles = []
      const all = allChartData.value
      for (let i = 0; i < all.origNames.length; i++) {
        if (nameSet.has(all.origNames[i])) {
          names.push(all.Names[i])
          values.push(all.Values[i])
          if (all.Titles?.[i]) titles.push(all.Titles[i])
        }
      }
      if (names.length === 0) return null
      return { Names: names, Values: values, Titles: titles }
    })

    /* ───────── API 데이터 패칭 ───────── */
    const fetchDetailData = async () => {
      const chName = channel.value === 'Main'
        ? asset.value.assetName_main
        : asset.value.assetName_sub
      try {
        const response = await axios.get(`/api/getDiagnosisGrouped/${chName}`)
        if (response.data.success) {
          data_recordtime.value = response.data.data_recordtime
          data_state.value = response.data.data_state
          groupedTree.value = response.data.data_tree

          const status = response.data.data_status
          if (status && status.length > 0) {
            const itemlist = []
            const valuelist = []
            const datalist = []
            const origNames = []
            for (let i = 0; i < status.length; i++) {
              itemlist.push(status[i]["Titles"]?.[locale.value] || status[i]["Title"] || status[i]["Name"])
              valuelist.push(status[i]["Status"])
              datalist.push(status[i]["Titles"])
              origNames.push(status[i]["Name"])
            }
            allChartData.value = { Names: itemlist, Values: valuelist, Titles: datalist, origNames }
          }
        } else {
          console.log('No Data')
        }
      } catch (error) {
        console.log('데이터 가져오기 실패:', error)
      }
    }

    const getStatusColor = (status) => STATUS_COLORS[status] || STATUS_COLORS[0]

    /* ───────── 라이프사이클 ───────── */
    onMounted(async () => {
      await fetchDetailData()
    })

    watch(() => props.asset, async (newAsset) => {
      if (newAsset !== asset.value) {
        asset.value = newAsset
        await fetchDetailData()
      }
    })

    provide('data_recordtime', computed(() => data_recordtime.value))
    provide('data_state', computed(() => data_state.value))

    return {
      selected,
      stageList,
      selectedTreeData,
      selectedChartData,
      data_recordtime,
      data_state,
      channel,
      mode,
      groupedTree,
      getStatusColor,
      t,
    }
  }
}
</script>

<style scoped>
.stage-chart-container {
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  margin-top: 8px;
}

/* 세로 탭 */
.stage-tabs {
  display: flex;
  flex-direction: column;
  width: 160px;
  flex-shrink: 0;
  border-right: 1px solid #e5e7eb;
  background: #f9fafb;
  padding-top: 12px;
}
:is(.dark) .stage-tabs {
  border-right-color: #374151;
  background: #111827;
}

.stage-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 14px;
  text-align: left;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
  border-left: 3px solid transparent;
  position: relative;
}
.stage-tab:hover {
  background: #f1f5f9;
  color: #334155;
}
:is(.dark) .stage-tab:hover {
  background: #1f2937;
  color: #d1d5db;
}
.stage-tab--active {
  background: #fff;
  color: #1e40af;
  font-weight: 600;
  border-left-color: #3b82f6;
}
:is(.dark) .stage-tab--active {
  background: #1e293b;
  color: #60a5fa;
  border-left-color: #3b82f6;
}

.stage-tab-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.stage-tab-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stage-tab-badge {
  font-size: 10px;
  font-weight: 700;
  color: #fff;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  flex-shrink: 0;
}
.stage-tab-badge--danger {
  background: #dc2626;
}
.stage-tab-badge--warn {
  background: #ca8a04;
}
</style>
