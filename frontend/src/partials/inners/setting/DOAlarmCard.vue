<template>
  <div
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

            <!-- 스크롤 가능한 데이터 목록 -->
            <div class="overflow-y-auto max-h-[400px] space-y-2 pr-2">
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
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, watch } from "vue";

const props = defineProps({
  channel: { type: String, default: '' }
});

const activeTab = ref('diagnostic');
const stDict = inject('status_Info');

const tabs = [
  { id: 'diagnostic', label: 'Diagnostic' },
  { id: 'pq', label: 'PQ' }
];

const diagnosticData = ref([
  { name: 'Capacitor', enabled: true, level: 2, color: 'bg-red-500' },
  { name: 'Tap Changer', enabled: true, level: 2, color: 'bg-red-500' },
  { name: 'Bushings', enabled: false, level: 2, color: 'bg-red-500' },
  { name: 'Stress', enabled: false, level: 2, color: 'bg-red-500' },
  { name: 'Load Unbalance', enabled: false, level: 2, color: 'bg-red-500' },
  { name: 'Cable Connection', enabled: false, level: 2, color: 'bg-red-500' },
  { name: 'Winding', enabled: false, level: 2, color: 'bg-red-500' },
  { name: 'Noise Vibration', enabled: false, level: 2, color: 'bg-red-500' },
  { name: 'Heat', enabled: false, level: 2, color: 'bg-red-500' },
  { name: 'Incoming Voltage', enabled: false, level: 2, color: 'bg-red-500' },
]);

const pqData = ref([
  { name: 'Voltage Phase Angle', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Current RMS', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Crest Factor', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Unbalance', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Harmonics', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Zero Sequence', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Negative Sequence', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Current Phase Angle', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Phase Angle', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Power Factor', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Total Demand Distortion', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Power', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Events', enabled: false, level: 2, color: 'bg-green-500' },
  { name: 'Voltage RMS', enabled: false, level: 2, color: 'bg-blue-500' },
  { name: 'DC', enabled: false, level: 2, color: 'bg-blue-500' },
  { name: 'Harmonics', enabled: false, level: 2, color: 'bg-blue-500' },
]);

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

const updateInputDict = () => {
  console.log('1. stDict:', stDict);
  // channel prop에 따라 Main 또는 Sub에 저장
  const targetChannel = props.channel || 'Main'; // 기본값 Main
  
  if (!stDict) {
    console.error('status_Info is not injected!');
    return;
  }

  // Diagnostic 데이터 저장
  stDict[targetChannel].diagnosis = diagnosticData.value
    .filter(item => item.enabled)
    .map(item => ({
      name: item.name,
      level: item.level
    }));

  // PQ 데이터 저장
  stDict[targetChannel].pq = pqData.value
    .filter(item => item.enabled)
    .map(item => ({
      name: item.name,
      level: item.level
    }));
};

watch(diagnosticData, () => { updateInputDict(); }, { deep: true });
watch(pqData, () => { updateInputDict(); }, { deep: true });
watch(() => props.channel, () => { updateInputDict(); }); // channel 변경 시에도 업데이트

updateInputDict();
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