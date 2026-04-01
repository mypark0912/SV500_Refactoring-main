<template>
<div class="grid grid-cols-12 gap-6">
  <div class="col-span-12">
    <div class="bands-container bg-white dark:bg-gray-800 rounded-2xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
      <!-- 헤더 -->
      <div class="flex items-center justify-between px-5 py-3 border-b border-gray-200/50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-900/50">
        <span class="text-sm font-semibold text-gray-700 dark:text-gray-200">{{ t('diagnosis.tabTitle.detailTitle') }}</span>
        <span class="text-xs text-gray-500 dark:text-gray-400 tabular-nums">{{ data_state }} / {{ data_recordtime || '-' }}</span>
      </div>

      <!-- 4컬럼 카테고리 -->
      <div class="columns-grid">
        <div v-for="cat in categories" :key="cat.id" class="category-column">
          <!-- 카테고리 헤더 -->
          <div class="col-header">
            <div class="col-color-bar" :style="{ backgroundColor: cat.color }"></div>
            <span class="col-label">{{ cat.label }}</span>
            <span v-if="getAlertCount(cat) > 0" class="col-badge col-badge--danger">{{ getAlertCount(cat) }}</span>
            <span v-if="getWarnCount(cat) > 0" class="col-badge col-badge--warn">{{ getWarnCount(cat) }}</span>
          </div>
          <!-- 항목 리스트 -->
          <div class="col-items">
            <div
              v-for="item in cat.items"
              :key="item.name"
              class="item-card"
              :style="isAlert(item) ? { borderColor: STATUS_COLORS[item.status] + '30', boxShadow: '0 1px 4px ' + STATUS_COLORS[item.status] + '12' } : {}"
            >
              <div class="item-card-left">
                <span class="item-name">{{ item.name }}</span>
                <span
                  v-if="isAlert(item)"
                  class="item-alert-tag"
                  :style="{ color: STATUS_COLORS[item.status], backgroundColor: STATUS_COLORS[item.status] + '10', borderColor: STATUS_COLORS[item.status] + '20' }"
                >{{ STATUS_TEXT[item.status] }}</span>
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

      <!-- 범례 (한줄) -->
      <div class="legend-inline">
        <span class="legend-label">{{ t('diagnosis.tabContext.legend') }}</span>
        <div v-for="s in STATUS_LEGEND" :key="s.key" class="legend-item">
          <div class="legend-dot" :style="{ backgroundColor: s.color, opacity: s.key === 0 ? 0.4 : 1 }"></div>
          <span>{{ s.text }}</span>
        </div>
      </div>
    </div>
  </div>

  <!-- 트리테이블 -->
  <div class="col-span-12">
    <Diagnosis_TreeTable
      v-if="allTreeData.length > 0"
      :channel="channel"
      :data="allTreeData"
      :mode="mode"
    />
  </div>
</div>
</template>

<script>
import { ref, computed, watch, onMounted, provide } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import Diagnosis_TreeTable from '../../inners/diagnosis/Diagnosis_TreeTable2.vue'

const STATUS_COLORS = { 0: '#c4c4c4', 1: '#16a34a', 2: '#ca8a04', 3: '#ea580c', 4: '#dc2626' }
const STATUS_TEXT = { 0: 'STOP', 1: 'NORMAL', 2: 'ATTENTION', 3: 'WARNING', 4: 'INSPECT' }
const CATEGORY_COLORS = {
  'voltage-inverter': '#1e3a8a',  // blue-900 남색
  'components': '#8b5cf6',         // violet-500 바이올렛
  'mechanical': '#ec4899',         // pink-500 핑크
  'electrical': '#0ea5e9',         // sky-500 스카이블루
}

const ITEM_CATEGORY_MAP = {
  // Voltage / Inverter
  'Incoming Voltage': 'voltage-inverter',
  'DCLink': 'voltage-inverter',
  'Rectifier': 'voltage-inverter',
  'Switching': 'voltage-inverter',
  // Components
  'Capacitor': 'components',
  'TapChanger': 'components',
  'Bushings': 'components',
  // Mechanical
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
  // Electrical
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
  name: 'DiagnosisTab_Bands',
  components: { Diagnosis_TreeTable },
  props: {
    asset: { type: Object, default: () => ({}) },
    channel: { type: String, default: '' },
    mode: { type: String, default: '' },
  },
  setup(props) {
    const { t, locale } = useI18n()
    const channel = ref(props.channel)
    const asset = ref(props.asset)
    const data_recordtime = ref('')
    const data_state = ref('')
    const groupedTree = ref([])
    const mode = ref(props.mode)

    const STATUS_LEGEND = [
      { key: 0, text: t('diagnosis.tabContext.st0'), color: '#c4c4c4' },
      { key: 1, text: t('diagnosis.tabContext.st1'), color: '#16a34a' },
      { key: 2, text: t('diagnosis.tabContext.st2'), color: '#ca8a04' },
      { key: 3, text: t('diagnosis.tabContext.st3'), color: '#ea580c' },
      { key: 4, text: t('diagnosis.tabContext.st4'), color: '#dc2626' },
    ]

    /* ───────── 카테고리 데이터 (API → 변환) ───────── */
    const categories = computed(() => {
      const cats = [
        { id: 'voltage-inverter', label: 'Voltage / Inverter', color: CATEGORY_COLORS['voltage-inverter'], items: [] },
        { id: 'components',       label: 'Components',         color: CATEGORY_COLORS['components'],       items: [] },
        { id: 'mechanical',       label: 'Mechanical',         color: CATEGORY_COLORS['mechanical'],       items: [] },
        { id: 'electrical',       label: 'Electrical',         color: CATEGORY_COLORS['electrical'],       items: [] },
      ]
      const catMap = {}
      cats.forEach(c => { catMap[c.id] = c })

      for (const node of groupedTree.value) {
        if (!node.children) continue
        for (const child of node.children) {
          const itemName = child.Name || child.Title || ''
          const catId = ITEM_CATEGORY_MAP[itemName]
          if (catId && catMap[catId]) {
            catMap[catId].items.push({
              name: child.Titles?.[locale.value] || child.Title || child.Name,
              rawName: itemName,
              status: child.Status || 0,
            })
          }
        }
      }
      return cats.filter(c => c.items.length > 0)
    })

    /* ───────── 트리테이블 데이터 (전체) ───────── */
    const allTreeData = computed(() => {
      const result = []
      for (const node of groupedTree.value) {
        if (node.children) result.push(...node.children)
      }
      return result
    })

    /* ───────── 헬퍼 ───────── */
    const getAlertCount = (cat) => cat.items.filter(i => i.status >= 3).length
    const getWarnCount = (cat) => cat.items.filter(i => i.status === 2).length
    const isAlert = (item) => item.status >= 3

    /* ───────── API ───────── */
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
        }
      } catch (error) {
        console.log('데이터 가져오기 실패:', error)
      }
    }

    onMounted(async () => { await fetchDetailData() })

    watch(() => props.asset, async (newAsset) => {
      if (newAsset !== asset.value) {
        asset.value = newAsset
        await fetchDetailData()
      }
    })

    provide('data_recordtime', computed(() => data_recordtime.value))
    provide('data_state', computed(() => data_state.value))

    return {
      t, categories, allTreeData,
      data_recordtime, data_state, channel, mode,
      STATUS_COLORS, STATUS_TEXT, STATUS_LEGEND,
      getAlertCount, getWarnCount, isAlert,
    }
  }
}
</script>

<style scoped>
.bands-container {
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* 4컬럼 레이아웃 */
.columns-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 16px 20px;
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

/* 항목 카드 */
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

/* 상태 블록 (배터리 세그먼트) */
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

/* 범례 */
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

/* 반응형 */
@media (max-width: 768px) {
  .columns-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 480px) {
  .columns-grid {
    grid-template-columns: 1fr;
  }
}
</style>
