<template>
<div class="grid grid-cols-12 gap-6">
  <div class="col-span-12">
    <div v-if="chartdata !== null" class="bands-container bg-white dark:bg-gray-800 rounded-2xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-3 border-b border-gray-200/50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-900/50">
        <span class="text-sm font-semibold text-gray-700 dark:text-gray-200">{{ t('diagnosis.tabTitle.detailTitle') }}</span>
        <span class="text-xs text-gray-500 dark:text-gray-400 tabular-nums">{{ data_state }} / {{ data_recordtime || '-' }}</span>
      </div>

      <!-- Flat grid of items -->
      <div class="bands-grid">
        <div
          v-for="(item, idx) in bandItems"
          :key="idx"
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

      <!-- Legend -->
      <div class="legend-inline">
        <span class="legend-label">{{ t('diagnosis.tabContext.legend') }}</span>
        <div v-for="s in STATUS_LEGEND" :key="s.key" class="legend-item">
          <div class="legend-dot" :style="{ backgroundColor: s.color, opacity: s.key === 0 ? 0.4 : 1 }"></div>
          <span>{{ s.text }}</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Tree Table -->
  <div class="col-span-12">
    <Diagnosis_TreeTable v-if="items.length > 0" :channel="channel" :data="items" :mode="mode" />
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

export default {
  name: 'Diagnosis',
  props:{
    asset:{
      type: Object,
      default: () => {}
    },
    channel:{
      type:String,
      default: ''
    },
    mode:{
      type:String,
      default: ''
    }
  },
  components: {
    Diagnosis_TreeTable,
  },
  setup(props) {
    const { t, locale } = useI18n();
    const channel = ref(props.channel)
    const asset = ref(props.asset);
    const chartdata = ref(null);
    const data_recordtime = ref('');
    const data_state = ref('');
    const items = ref([]);
    const mode=ref(props.mode);

    const STATUS_LEGEND = [
      { key: 0, text: t('diagnosis.tabContext.st0'), color: '#c4c4c4' },
      { key: 1, text: t('diagnosis.tabContext.st1'), color: '#16a34a' },
      { key: 2, text: t('diagnosis.tabContext.st2'), color: '#ca8a04' },
      { key: 3, text: t('diagnosis.tabContext.st3'), color: '#ea580c' },
      { key: 4, text: t('diagnosis.tabContext.st4'), color: '#dc2626' },
    ]

    /* Map chartdata to flat band items */
    const bandItems = computed(() => {
      if (!chartdata.value) return []
      const result = []
      for (let i = 0; i < chartdata.value.Names.length; i++) {
        result.push({
          name: chartdata.value.Names[i],
          status: chartdata.value.Values[i] || 0,
        })
      }
      return result
    })

    const isAlert = (item) => item.status >= 3

    const fetchDetailData = async () => {

      const chName = channel.value == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;
      try {
        const response = await axios.get(`/api/getDiagnosisDetail/${chName}`);
        if (response.data.success) {
          let itemlist = [], valuelist=[], datalist=[];
          for(let i = 0; i < response.data.data_status.length;i++){

            itemlist.push(response.data.data_status[i]["Titles"][locale.value]);
            valuelist.push(response.data.data_status[i]["Status"]);
            datalist.push(response.data.data_status[i]["Titles"])
          }
          chartdata.value = {"Names" : itemlist, "Values" : valuelist, "Titles": datalist};
          items.value = response.data.data_tree;
          data_recordtime.value = response.data.data_recordtime;
          data_state.value = response.data.data_state;
        }else{
          console.log('No Data');
        }
      }catch (error) {
        console.log("데이터 가져오기 실패:", error);
      }
    };

const fetchPQData = async () => {
  const chName = channel.value == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;

  // 원하는 순서 정의 (Name 기준)
  const pqDisplayOrder = [
    // 전압 관련
    'VoltagePhaseAngle',
    'VoltageRMS',
    'DC',
    // 전류 관련
    'CurrentRMS',
    'CurrentPhaseAngle',
    'CrestFactor',
    // 파형, 왜곡 관련
    'Unbalance',
    'Harmonics',
    'ZeroSequence',
    'NegativeSequence',
    // 전력, 효율 관련
    'Power',
    'PowerFactor',
    'TotalDemandDistortion',
    // 기타
    'PhaseAngle',
    'Events',
  ];

  try {
    const response = await axios.get(`/api/getDiagPQ/${chName}`);

    if (response.data.success) {
      // data_status 정렬
      const sortedStatus = [...response.data.data_status].sort((a, b) => {
        const indexA = pqDisplayOrder.indexOf(a.Name);
        const indexB = pqDisplayOrder.indexOf(b.Name);
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        return indexA - indexB;
      });

      // data_tree도 같은 순서로 정렬
      const sortedTree = [...response.data.data_tree].sort((a, b) => {
        const indexA = pqDisplayOrder.indexOf(a.Name);
        const indexB = pqDisplayOrder.indexOf(b.Name);
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        return indexA - indexB;
      });

      let itemlist = [], valuelist = [], datalist = [];
      for (let i = 0; i < sortedStatus.length; i++) {
        itemlist.push(sortedStatus[i]["Titles"][locale.value]);
        valuelist.push(sortedStatus[i]["Status"]);
        datalist.push(sortedStatus[i]["Titles"]);
      }

      chartdata.value = { "Names": itemlist, "Values": valuelist, "Titles": datalist };
      items.value = sortedTree;  // 정렬된 tree 사용
      data_recordtime.value = response.data.data_recordtime;
      data_state.value = response.data.data_state;
    } else {
      console.log('No Data');
    }
  } catch (error) {
    console.log("데이터 가져오기 실패:", error);
  }
};
    const fetchFaultData = async () => {

      const chName = channel.value == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;
      try {
        const response = await axios.get(`/api/getFaults/${chName}`);
        if (response.data.success) {
          let itemlist = [], valuelist=[], datalist=[];
          for(let i = 0; i < response.data.data_status.length;i++){
            itemlist.push(response.data.data_status[i]["Title"]);
            valuelist.push(response.data.data_status[i]["Status"]);
            datalist.push(response.data.data_status[i]["Titles"]);
          }
          chartdata.value = {"Names" : itemlist, "Values" : valuelist, "Titles": datalist};
          items.value = response.data.data_tree;
        }else{
          console.log('No Data');
        }
      }catch (error) {
        console.log("데이터 가져오기 실패:", error);
      }
    };

    const fetchEventData = async () => {

      const chName = channel.value == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;
      try {
        const response = await axios.get(`/api/getEvents/${chName}`);
        if (response.data.success) {
          let itemlist = [], valuelist=[], datalist=[];
          for(let i = 0; i < response.data.data_status.length;i++){
            itemlist.push(response.data.data_status[i]["Titles"][locale.value]);
            valuelist.push(response.data.data_status[i]["Status"]);
            datalist.push(response.data.data_status[i]["Titles"]);
          }
          chartdata.value = {"Names" : itemlist, "Values" : valuelist, "Titles": datalist};
          items.value = response.data.data_tree;
        }else{
          console.log('No Data');
        }
      }catch (error) {
        console.log("데이터 가져오기 실패:", error);
      }
    };


    onMounted(async () => {

        if(mode.value == 'Status')
          await fetchDetailData();
        else if(mode.value == 'PowerQuality')
          await fetchPQData();
        else if(mode.value == 'Fault')
          await fetchFaultData();
        else
          await fetchEventData();

    });

    watch(() => props.asset, async(newChannel) => {
      if (newChannel !== asset.value) {
        asset.value = newChannel;
        await fetchDetailData();
      }
    });

    provide('data_recordtime', computed(() => data_recordtime.value));
    provide('data_state', computed(() => data_state.value));

    return {
      t,
      channel,
      chartdata,
      items,
      asset,
      fetchDetailData,
      mode,
      data_recordtime,
      data_state,
      bandItems,
      isAlert,
      STATUS_COLORS,
      STATUS_TEXT,
      STATUS_LEGEND,
    }
  }
}
</script>

<style scoped>
.bands-container {
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* Flat 4-column grid */
.bands-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 16px 20px;
}

/* Item card */
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
  min-width: 0;
}
.item-name {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  white-space: nowrap;
  flex-shrink: 0;
}

/* Status blocks (battery segments) */
.status-blocks {
  display: flex;
  gap: 3px;
  flex-shrink: 0;
  margin-left: 8px;
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

/* Legend */
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

/* Responsive */
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
