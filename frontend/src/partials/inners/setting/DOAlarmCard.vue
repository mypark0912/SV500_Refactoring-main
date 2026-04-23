<template>
  <div
    class="relative col-span-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg"
  >
    <div class="absolute top-0 left-0 right-0 h-0.5 bg-purple-500" aria-hidden="true"></div>

    <!-- Header -->
    <div class="px-5 pt-5 pb-4 border-b border-gray-200 dark:border-gray-700/60">
      <div class="flex items-center justify-between">
        <header class="flex items-center">
          <div class="w-6 h-6 rounded-full shrink-0 bg-purple-500 mr-3">
            <svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"
              />
            </svg>
          </div>
          <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">
            Configuration of Status
          </h3>
        </header>

    
      </div>
    </div>

    <!-- Body -->
    <div class="px-4 py-3">
      <div class="grid grid-cols-2 gap-4">

        <!-- Equipment Status -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700/60 p-3">
          <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 pb-2 border-b border-gray-200 dark:border-gray-700/60">
            Equipment Status
          </h4>
          <div class="grid grid-cols-[200px_1fr_100px_150px] gap-3 text-xs font-semibold text-gray-500 dark:text-gray-400 px-1 mb-2 border-b pb-2">
            <div class="text-left">Parameter</div>
            <div></div>
            <div class="flex items-center justify-center gap-1">
              <input
                type="checkbox"
                v-model="allEquipmentEnabled"
                class="w-4 h-4 cursor-pointer text-violet-600 focus:ring-violet-500 border-gray-300 rounded"
              />
              <span>Enable</span>
            </div>
            <div class="text-center">Level</div>
          </div>
          <div v-if="equipmentItems.length === 0" class="text-center py-8 text-gray-400">
            <p class="text-sm">No items available for this asset type</p>
          </div>
          <div v-else class="overflow-y-auto max-h-[400px] space-y-1 pr-1">
            <div
              v-for="(item, idx) in equipmentItems"
              :key="idx"
              class="grid grid-cols-[200px_1fr_100px_150px] gap-3 items-center border-b border-gray-200 dark:border-gray-700/60 py-2 px-1 hover:bg-gray-50 dark:hover:bg-gray-700/30"
            >
              <div class="text-left text-xs text-gray-800 dark:text-gray-200 flex items-center min-w-0">
                <span class="truncate">{{ item.parameter }}</span>
              </div>
              <div></div>
              <div class="flex justify-center">
                <input
                  type="checkbox"
                  v-model="item.enable"
                  class="w-4 h-4 cursor-pointer text-violet-600 focus:ring-violet-500 border-gray-300 rounded"
                />
              </div>
              <div class="flex justify-center">
                <select
                  v-model="item.level"
                  :disabled="!item.enable"
                  class="w-24 px-2 py-1.5 text-xs border rounded-md transition-all"
                  :class="!item.enable
                    ? 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 border-gray-300 dark:border-gray-600 cursor-not-allowed'
                    : 'bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500'"
                >
                  <option :value="2">{{ t("diagnosis.tabContext.st2") }}</option>
                  <option :value="3">{{ t("diagnosis.tabContext.st3") }}</option>
                  <option :value="4">{{ t("diagnosis.tabContext.st4") }}</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- PQ Status -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700/60 p-3">
          <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 pb-2 border-b border-gray-200 dark:border-gray-700/60">
            PQ Status
          </h4>
          <div class="grid grid-cols-[minmax(140px,1fr)_100px_150px] gap-3 text-xs font-semibold text-gray-500 dark:text-gray-400 px-1 mb-2 border-b pb-2">
            <div class="text-left">Parameter</div>
            <div class="flex items-center justify-center gap-1">
              <input
                type="checkbox"
                v-model="allPqEnabled"
                class="w-4 h-4 cursor-pointer text-violet-600 focus:ring-violet-500 border-gray-300 rounded"
              />
              <span>Enable</span>
            </div>
            <div class="text-center">Level</div>
          </div>
          <div v-if="pqItems.length === 0" class="text-center py-8 text-gray-400">
            <p class="text-sm">No items available</p>
          </div>
          <div v-else class="overflow-y-auto max-h-[400px] space-y-1 pr-1">
            <div
              v-for="(item, idx) in pqItems"
              :key="idx"
              class="grid grid-cols-[minmax(140px,1fr)_100px_150px] gap-3 items-center border-b border-gray-200 dark:border-gray-700/60 py-2 px-1 hover:bg-gray-50 dark:hover:bg-gray-700/30"
            >
              <div class="text-left text-xs text-gray-800 dark:text-gray-200 flex items-center min-w-0">
                <span class="truncate">{{ item.parameter }}</span>
              </div>
              <div class="flex justify-center">
                <input
                  type="checkbox"
                  v-model="item.enable"
                  class="w-4 h-4 cursor-pointer text-violet-600 focus:ring-violet-500 border-gray-300 rounded"
                />
              </div>
              <div class="flex justify-center">
                <select
                  v-model="item.level"
                  :disabled="!item.enable"
                  class="w-24 px-2 py-1.5 text-xs border rounded-md transition-all"
                  :class="!item.enable
                    ? 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 border-gray-300 dark:border-gray-600 cursor-not-allowed'
                    : 'bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500'"
                >
                  <option :value="2">{{ t("diagnosis.tabContext.pqfe2") }}</option>
                  <option :value="3">{{ t("diagnosis.tabContext.pqfe3") }}</option>
                  <option :value="4">{{ t("diagnosis.tabContext.pqfe4") }}</option>
                </select>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, watch, onMounted, nextTick } from "vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const isDataLoaded = ref(false);
const isLoading = ref(false);

const props = defineProps({
  channel: { type: String, default: '' },
});

const mainData = inject('channel_main');
const subData = inject('channel_sub');
const diagnosis_detail = inject('diagnosis_detail');

// 현재 채널 데이터
const channelData = computed(() =>
  props.channel === 'Main' ? mainData.value : subData.value
);

// status_Info 참조
const stDict = computed(() =>
  channelData.value?.status_Info ?? {diagnosis: [], pq: [] }
);

// Use DO Alarm 체크 여부
const isUseDO = computed(() => {
  const d = channelData.value;
  return d?.useDO === 1 || d?.useDO === true;
});





// Asset type
const AssetType = computed(() => channelData.value?.assetInfo?.type || '');
const assetDriveType = computed(() => channelData.value?.assetInfo?.driveType || '');

const channelKey = computed(() => (props.channel === 'Main' ? 'main' : 'sub'));
const tableData = computed(() => diagnosis_detail?.value?.[channelKey.value]?.tableData || []);

const equipmentItems = ref([]);
const pqItems = ref([]);

const allEquipmentEnabled = computed({
  get: () => equipmentItems.value.length > 0 && equipmentItems.value.every(i => i.enable),
  set: (val) => { equipmentItems.value.forEach(i => { i.enable = val; }); },
});
const allPqEnabled = computed({
  get: () => pqItems.value.length > 0 && pqItems.value.every(i => i.enable),
  set: (val) => { pqItems.value.forEach(i => { i.enable = val; }); },
});

const findTableValueByName = (name) => {
  const entry = tableData.value.find(t => t.Name === name);
  if (!entry) return null;
  const raw = entry.Value;
  if (raw === undefined || raw === null || raw === '') return null;
  const num = typeof raw === 'string' ? parseFloat(raw) : raw;
  return Number.isNaN(num) ? null : num;
};

const anyTableValuePositive = (name) => {
  return tableData.value.some(t => {
    if (t.Name !== name) return false;
    const raw = t.Value;
    if (raw === undefined || raw === null || raw === '') return false;
    const num = typeof raw === 'string' ? parseFloat(raw) : raw;
    return !Number.isNaN(num) && num > 0;
  });
};

const resolveSetup = (item, assetType, driveType) => {
  if (assetType === 'PSupply' || assetType === 'PrimaryTransformer') return true;

  if (assetType === 'Transformer') {
    if (item.Title === 'NeutralLoading') {
      return findTableValueByName('ConnectionType') === 0;
    }
    if (item.Title === 'Switching') {
      const v = findTableValueByName('SwitchingFrequency');
      return v != null && v > 0;
    }
    if (item.Title === 'Rectifier') {
      const v = findTableValueByName('PulseNumber');
      return v != null && v > 0;
    }
    return true;
  }

  const rotatingTypes = ['Motor', 'MotorFeed', 'Compressor', 'Fan', 'Pump'];
  if (rotatingTypes.includes(assetType)) {
    const isVFD = driveType === 'VFD';

    if (item.Title === 'DCLink') return isVFD;
    if (item.Title === 'Switching') {
      if (!isVFD) return false;
      const v = findTableValueByName('SwitchingFrequency');
      return v != null && v > 0;
    }
    if (item.Title === 'Rectifier') {
      if (!isVFD) return false;
      const v = findTableValueByName('PulseNumber');
      return v != null && v > 0;
    }
    if (item.Title === 'Blade') {
      const v = findTableValueByName('NumberOfBlades');
      return v != null && v > 0;
    }
    if (item.Title === 'Vane' && assetType === 'Pump') {
      const v = findTableValueByName('NumberOfVanes');
      return v != null && v > 0;
    }
    if (item.Title === 'Bearing' && assetType !== 'MotorFeed') {
      return anyTableValuePositive('BearingType');
    }
    return true;
  }

  return true;
};

const fetchData = async () => {
  if (!AssetType.value) {
    equipmentItems.value = [];
    pqItems.value = [];
    return false;
  }
  try {
    const res = await fetch('/diagnosis_items.json');
    const data = await res.json();
    const rawDiagnosis = data.Diagnosis?.[AssetType.value] || [];

    equipmentItems.value = rawDiagnosis
      .filter(item => resolveSetup(item, AssetType.value, assetDriveType.value))
      .map(item => ({
        parameter: item.Title, enable: false, level: 2,
      }));
    pqItems.value = (data.PQ || []).map(item => ({
      parameter: item.Title, enable: false, level: 2,
    }));
    return true;
  } catch (e) {
    console.error("데이터 가져오기 실패:", e);
    return false;
  }
};

const matchSaved = (item, saved) => saved.name === item.parameter;

const loadSavedData = async () => {
  const statusInfo = stDict.value;
  if (!statusInfo) return;

  const savedDiag = statusInfo.diagnosis || [];
  const savedPq = statusInfo.pq || [];

  equipmentItems.value = equipmentItems.value.map(item => {
    const saved = savedDiag.find(s => matchSaved(item, s));
    if (saved) {
      return {
        ...item,
        enable: true,
        level: saved.level ?? 2,
      };
    }
    return { ...item, enable: false, level: 2 };
  });

  pqItems.value = pqItems.value.map(item => {
    const saved = savedPq.find(s => matchSaved(item, s));
    if (saved) {
      return {
        ...item,
        enable: true,
        level: saved.level ?? 2,
      };
    }
    return { ...item, enable: false, level: 2 };
  });
};

const toConfEntry = i => ({
  name: i.parameter,
  level: i.level,
});

const updateInputDict = () => {
  const statusInfo = stDict.value;
  if (!statusInfo) return;
  statusInfo.diagnosis = equipmentItems.value.filter(i => i.enable).map(toConfEntry);
  statusInfo.pq = pqItems.value.filter(i => i.enable).map(toConfEntry);
};

onMounted(async () => {
  isLoading.value = true;
  try {
    await fetchData();
    await loadSavedData();
    isDataLoaded.value = true;
  } finally {
    await nextTick();
    isLoading.value = false;
  }
});

watch([equipmentItems, pqItems], () => {
  if (isDataLoaded.value && !isLoading.value) updateInputDict();
}, { deep: true });
</script>