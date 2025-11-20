<template>
  <div
    v-if="isUseDOEnabled && AssetType && AssetType !== ''"
    class="relative col-span-full xl:col-span-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg"
  >
    <div
      class="absolute top-0 left-0 right-0 h-0.5 bg-orange-500"
      aria-hidden="true"
    ></div>
    <div
      class="px-5 pt-5 pb-6 border-b border-gray-200 dark:border-gray-700/60"
    >
      <header class="flex items-center mb-2">
        <div class="w-6 h-6 rounded-full shrink-0 bg-orange-500 mr-3">
          <svg
            class="w-6 h-6 fill-current text-white"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle
              cx="17"
              cy="17"
              r="4"
              stroke="currentColor"
              stroke-width="2"
              fill="none"
            />
            <path
              d="M20 20l2 2"
              stroke="currentColor"
              stroke-width="2"
              fill="none"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>
        <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">
          Diagnostic Status Setting
        </h3>
      </header>
    </div>

    <div class="px-4 py-3 space-y-4">
      <!-- AssetType이 없을 때 메시지 표시 -->
      <div v-if=false class="text-center py-8 text-gray-500 dark:text-gray-400">
        <p class="text-sm">No asset type selected. Please select an asset type first.</p>
      </div>
      
      <!-- AssetType이 있을 때만 탭과 리스트 표시 -->
      <template v-else>
        <!-- 탭 네비게이션 -->
        <div class="flex border-b border-gray-200 dark:border-gray-700/60">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'px-4 py-2 text-sm font-medium transition-colors duration-200',
              activeTab === tab.id
                ? 'text-violet-600 dark:text-violet-400 border-b-2 border-violet-600 dark:border-violet-400'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            ]"
          >
            {{ tab.label }}
          </button>
        </div>

        <div
          class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700/60"
        >
          <div class="mt-6 pt-2">
            <div class="flex flex-col">
              <!-- 헤더 -->
              <div
                class="grid grid-cols-[1fr_100px_120px] gap-4 text-xs font-semibold text-gray-500 dark:text-gray-400 px-1 mb-4 border-b pb-2"
              >
                <div class="text-left">Parameter</div>
                <div class="text-center">Enable</div>
                <div class="text-center">Select Level</div>
              </div>

              <!-- 데이터가 없을 때 -->
              <div v-if="currentTabData.length === 0" class="text-center py-8 text-gray-400">
                <p class="text-sm">No items available for this asset type</p>
              </div>

              <!-- 스크롤 가능한 데이터 목록 -->
              <div v-else class="overflow-y-auto max-h-[400px] space-y-2 pr-2">
                <div
                  v-for="(item, idx) in currentTabData"
                  :key="idx"
                  class="grid grid-cols-[1fr_100px_120px] gap-4 items-center border-b border-gray-200 dark:border-gray-700/60 py-3 text-sm px-1 hover:bg-gray-50 dark:hover:bg-gray-700/30"
                >
                  <!-- Parameter Name -->
                  <div class="text-left text-xs text-gray-800 dark:text-gray-200 flex items-center">
                    <span 
                      class="inline-block w-3 h-3 rounded-full mr-2 flex-shrink-0"
                      :class="item.color"
                    ></span>
                    {{ item.name }}
                  </div>
                  
                  <!-- Enable Checkbox -->
                  <div class="flex justify-center">
                    <input
                      type="checkbox"
                      v-model="item.enabled"
                      class="w-4 h-4 cursor-pointer text-violet-600 focus:ring-violet-500 border-gray-300 rounded"
                    />
                  </div>
                  
                  <!-- Select Level Combobox -->
                  <div class="flex justify-center">
                    <select
                      v-model="item.level"
                      :disabled="!item.enabled"
                      class="w-full px-3 py-1.5 text-xs border rounded-md transition-all"
                      :class="
                        !item.enabled
                          ? 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 border-gray-300 dark:border-gray-600 cursor-not-allowed'
                          : 'bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500'
                      "
                    >
                      <option :value="2">Warning</option>
                      <option :value="3">Inspect</option>
                      <option :value="4">Repair</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, watch, onMounted, nextTick } from "vue";

const isDataLoaded = ref(false);
const props = defineProps({
  channel: { type: String, default: '' }
});

const activeTab = ref('diagnostic');
const mainData = inject('channel_main');
const subData = inject('channel_sub');
const channel = ref(props.channel);

const stDict = computed(() => {
  if (channel.value === 'Main' && mainData.value) {
    return mainData.value.status_Info;
  } else if (channel.value === 'Sub' && subData.value) {
    return subData.value.status_Info;
  }
  return { diagnosis: [], pq: [] };
});

const AssetType = computed(() => {
  if (channel.value === 'Main' && mainData.value) {
    return mainData.value.assetInfo?.type || '';
  } else if (channel.value === 'Sub' && subData.value) {
    return subData.value.assetInfo?.type || '';
  }
  return '';
});

const tabs = [
  { id: 'diagnostic', label: 'Diagnostic' },
  { id: 'pq', label: 'PQ' }
];

// 초기값은 빈 배열로 설정
const diagnosticData = ref([]);
const pqData = ref([]);

const currentTabData = computed(() => {
  switch (activeTab.value) {
    case 'diagnostic':
      return diagnosticData.value;
    case 'pq':
      return pqData.value;
    default:
      return diagnosticData.value;
  }
});

// JSON에서 데이터 가져오기
const fetchData = async () => {
  // AssetType이 없으면 빈 배열 설정하고 종료
  if (!AssetType.value || AssetType.value === '') {
    diagnosticData.value = [];
    pqData.value = [];
    console.log('No AssetType - skipping data fetch');
    return false;
  }

  try {
    const res = await fetch('/diagnosis_items.json');
    const data = await res.json();
    
    // AssetType에 따라 diagnosis 항목 가져오기
    const diagnosisItems = data.Diagnosis[AssetType.value] || [];
    const pqItems = data.PQ || [];
    
    // diagnosticData 구성 - Title을 name으로 매핑
    diagnosticData.value = diagnosisItems.map(item => ({
      name: item.Title,
      component: item.Component,
      enabled: false,
      level: 2,
      color: 'bg-red-500'
    }));
    
    // pqData 구성
    pqData.value = pqItems.map(item => ({
      name: item.Title,
      component: item.Component,
      enabled: false,
      level: 2,
      color: item.Title.includes('Voltage') ? 'bg-blue-500' : 'bg-green-500'
    }));
    
    console.log(`${AssetType.value} 진단 항목 로드:`, diagnosticData.value);
    console.log("PQ 항목 로드:", pqData.value);
    
    return true;
  } catch (error) {
    console.error("데이터 가져오기 실패:", error);
    diagnosticData.value = [];
    pqData.value = [];
    return false;
  }
};
// useDO 상태 확인을 위한 computed property 추가
const isUseDOEnabled = computed(() => {

  const currentChannelData = channel.value === 'Main' ? mainData.value : subData.value;
  const channelUseDO = currentChannelData?.useDO === 1 || 
                       currentChannelData?.useDO === true;
  
  // 채널 레벨에서 useDO가 활성화되어 있으면 카드 표시
  return channelUseDO;
});

const loadSavedData = () => {
  const statusInfo = stDict.value;
  const actualStatusInfo = JSON.parse(JSON.stringify(statusInfo));
  
  if (!statusInfo || (!actualStatusInfo.diagnosis?.length && !actualStatusInfo.pq?.length)) {
    return;
  }

  // 모든 항목 초기화
  diagnosticData.value.forEach(item => {
    item.enabled = false;
    item.level = 2;
  });
  
  pqData.value.forEach(item => {
    item.enabled = false;
    item.level = 2;
  });

  // Diagnostic 데이터 로드
  const diagnosisArray = JSON.parse(JSON.stringify(statusInfo.diagnosis || []));
  if (diagnosisArray.length > 0) {
    diagnosisArray.forEach(savedItem => {
      const item = diagnosticData.value.find(d => d.name === savedItem.name);
      if (item) {
        item.enabled = true;
        item.level = savedItem.level;
      }
    });
  }

  // PQ 데이터 로드
  const pqArray = JSON.parse(JSON.stringify(statusInfo.pq || []));
  if (pqArray.length > 0) {
    pqArray.forEach(savedItem => {
      const item = pqData.value.find(p => p.name === savedItem.name);
      if (item) {
        item.enabled = true;
        item.level = savedItem.level;
      }
    });
  }
};

const updateInputDict = () => {
  const statusInfo = stDict.value;
  
  if (!statusInfo) {
    console.error('status_Info is not available!');
    return;
  }

  statusInfo["diagnosis"] = diagnosticData.value
    .filter(item => item.enabled)
    .map(item => ({
      name: item.name,
      level: item.level
    }));

  statusInfo["pq"] = pqData.value
    .filter(item => item.enabled)
    .map(item => ({
      name: item.name,
      level: item.level
    }));
};

// AssetType 변경 감지 - 데이터 다시 로드
watch(AssetType, async (newType, oldType) => {
  if (newType !== oldType) {
    await fetchData();
    if (isDataLoaded.value) {
      loadSavedData(); // 저장된 데이터 다시 로드
    }
  }
});

// 데이터가 로드된 후에만 watch 실행
watch(diagnosticData, () => { 
  if (isDataLoaded.value) {
    updateInputDict(); 
  }
}, { deep: true });

watch(pqData, () => { 
  if (isDataLoaded.value) {
    updateInputDict(); 
  }
}, { deep: true });

onMounted(async () => {
  console.log('=== Component Mounted ===');
  
  // 먼저 JSON 데이터 가져오기
  await fetchData();
  
  // 데이터가 준비될 때까지 대기
  let retries = 0;
  const maxRetries = 10;
  
  while (retries < maxRetries) {
    const data = channel.value === 'Main' ? mainData.value : subData.value;
    
    if (data && data.status_Info) {
      await nextTick();
      loadSavedData();
      isDataLoaded.value = true;
      break;
    }
    
    await new Promise(resolve => setTimeout(resolve, 100));
    retries++;
  }
  
  if (retries === maxRetries) {
    console.error('Failed to load data after maximum retries');
    isDataLoaded.value = true;
  }
});
</script>

<style scoped>
.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  @apply bg-gray-100 dark:bg-gray-800;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  @apply bg-gray-300 dark:bg-gray-600 rounded;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400 dark:bg-gray-500;
}

select:focus {
  outline: none;
}

input[type="checkbox"]:focus {
  outline: none;
}
</style>