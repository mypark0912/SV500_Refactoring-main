<template>
  <div
    v-if="isUseAIEnabled"
    class="relative col-span-full xl:col-span-12 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg"
  >
    <div class="absolute top-0 left-0 right-0 h-0.5 bg-orange-500" aria-hidden="true"></div>
    <div class="px-5 pt-5 pb-6 border-b border-gray-200 dark:border-gray-700/60">
      <header class="flex items-center mb-2">
        <div class="w-6 h-6 rounded-full shrink-0 bg-orange-500 mr-3">
          <svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <circle cx="17" cy="17" r="4" stroke="currentColor" stroke-width="2" fill="none" />
            <path d="M20 20l2 2" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">AI Module MODBUS Configuration</h3>
      </header>
    </div>

    <div class="px-4 py-3 space-y-4">
      <div class="flex space-x-2">
        <button @click="addRow" class="px-3 py-1.5 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500">
          + Add Row
        </button>
        <button @click="handleReset" class="px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-violet-500">
          Reset
        </button>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700/60">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b-2 border-gray-300 dark:border-gray-600">
                <th class="px-2 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50 w-14">Index</th>
                <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">Enable</th>
                <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">AI Type</th>
                <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">Dev ID</th>
                <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">Start<br />Address</th>
                <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">Count</th>
                <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">Data<br />Type</th>
                <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">Destination</th>
                <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">Period<br />(ms)</th>
                <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">FC</th>
                <th class="px-3 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50">Scale</th>
                <th class="px-2 py-3 text-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700/50 w-20">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, idx) in modbusConfig"
                :key="row.id"
                class="border-b border-gray-200 dark:border-gray-700/60 hover:bg-gray-50 dark:hover:bg-gray-700/30"
              >
                <td class="px-2 py-2 text-center text-xs text-gray-800 dark:text-gray-200 font-medium">{{ idx + 1 }}</td>
                <td class="px-2 py-2 text-center">
                  <input type="checkbox" :checked="row.enable === 1" @change="row.enable = $event.target.checked ? 1 : 0"
                    class="w-4 h-4 text-violet-600 border-gray-300 rounded focus:ring-violet-500" />
                </td>
                <!-- AI Type -->
                <td class="px-2 py-2 text-center">
                  <select v-model.number="row.m_name"
                    class="w-24 px-1 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500">
                    <option :value="0">ExtIO</option>
                    <option :value="1">P300-C</option>
                  </select>
                </td>
                <!-- Dev ID: serialList에서 row.m_name(type)과 일치하는 항목만 표시 -->
                <td class="px-2 py-2 text-center">
                  <select v-model.number="row.devId"
                    class="w-16 px-1 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500">
                    <option
                      v-for="item in serialList.filter(s => s.type === row.m_name)"
                      :key="item.devId"
                      :value="item.devId"
                    >{{ item.devId }}</option>
                    <option v-if="serialList.filter(s => s.type === row.m_name).length === 0" :value="0" disabled>-</option>
                  </select>
                </td>
                <td class="px-2 py-2 text-center">
                  <input type="number" v-model.number="row.startAddr" min="0"
                    class="w-20 px-1.5 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500" />
                </td>
                <td class="px-2 py-2 text-center">
                  <input type="number" v-model.number="row.count" min="0"
                    class="w-16 px-1.5 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500" />
                </td>
                <td class="px-2 py-2 text-center">
                  <select v-model.number="row.dataType"
                    class="w-20 px-1 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500">
                    <option :value="0">UINT16</option>
                    <option :value="1">UINT32</option>
                    <option :value="2">Float</option>
                    <option :value="3">F002</option>
                  </select>
                </td>
                <td class="px-2 py-2 text-center">
                  <select v-model.number="row.destination"
                    class="w-24 px-1 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500">
                    <option :value="0">{{ t("config.channelPanel.tempR") }}</option>
                    <option :value="1">{{ t("config.channelPanel.tempS") }}</option>
                    <option :value="2">{{ t("config.channelPanel.tempT") }}</option>
                  </select>
                </td>
                <td class="px-2 py-2 text-center">
                  <input type="number" v-model.number="row.period" min="0" step="100"
                    class="w-20 px-1.5 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500" />
                </td>
                <td class="px-2 py-2 text-center">
                  <select v-model.number="row.fc"
                    class="w-16 px-1 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500">
                    <option :value="0">-</option>
                    <option :value="1">01</option>
                    <option :value="2">02</option>
                    <option :value="3">03</option>
                    <option :value="4">04</option>
                    <option :value="5">05</option>
                    <option :value="6">06</option>
                    <option :value="15">15</option>
                    <option :value="16">16</option>
                  </select>
                </td>
                <td class="px-2 py-2 text-center">
                  <input type="number" v-model.number="row.scale" step="0.01"
                    class="w-20 px-1.5 py-1 text-xs text-center border rounded-md bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100 border-gray-300 dark:border-gray-500 focus:ring-violet-500 focus:border-violet-500" />
                </td>
                <td class="px-2 py-2 text-center">
                  <button @click="removeRow(idx)" :disabled="modbusConfig.length <= 1"
                    class="px-2 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                    title="Delete row">
                    Delete
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
          <p class="text-xs text-blue-800 dark:text-blue-200">
            <strong>Note:</strong>
            • FC: Function Code (03=Read Holding Registers, 04=Read Input Registers, 16=Write Multiple Registers)
            <br />• Data Type: UINT16, UINT32, Float, F002 (F002=Float value/100)
            <br />• Destination: Target address (Temp R-phase, Temp S-phase, Temp T-phase)
            <br />• Scale: Scale factor (e.g. 0.01, 0.1, 1.0, 100.0)
            <br />• Dev ID: Populated from General &gt; Modbus Serial Type (matching AI Type)
          </p>
        </div>

        <div class="flex justify-between items-center mt-6">
          <div class="text-sm text-gray-600 dark:text-gray-400">
            Total Configurations: <span class="font-semibold">{{ modbusConfig.length }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, computed, watch, onMounted } from "vue";
import { useI18n } from "vue-i18n";

let nextId = 1;
const { t } = useI18n();

const props = defineProps({
  channel: { type: String, default: '' }
});

const mainData = inject('channel_main');
const subData = inject('channel_sub');
const inputDict = inject('inputDict');

const currentChannelData = computed(() =>
  props.channel === 'Main' ? mainData.value : subData.value
);

// serialinfo / serialtype 둘 다 대응 (키 이름 방어)
const serialList = computed(() => {
  const m = inputDict?.value?.modbus;
  if (!m) return [];
  return m.serialinfo ?? m.serialtype ?? [];
});

const modbusConfig = ref([]);

const createDefaultRow = (id) => ({
  id,
  enable: 0,
  m_name: 0,
  devId: 0,
  startAddr: 0,
  count: 0,
  dataType: 0,
  destination: 0,
  period: 1000,
  fc: 0,
  scale: 1.0,
});

const defaultConfig = [
  { id: 1, enable: 1, m_name: 0, devId: 0, startAddr: 0, count: 6, dataType: 3, destination: 0, period: 1000, fc: 4, scale: 1.0 }
];

const loadFromChannel = () => {
  const aiModbus = currentChannelData.value?.ai_modbus;
  if (aiModbus && Array.isArray(aiModbus) && aiModbus.length > 0) {
    modbusConfig.value = aiModbus.map((item, idx) => ({
      id: item.id || idx + 1,
      enable: item.enable ?? 0,
      m_name: item.m_name ?? 0,
      devId: item.devId ?? 0,
      startAddr: item.startAddr ?? 0,
      count: item.count ?? 0,
      dataType: item.dataType ?? 0,
      destination: item.destination ?? 0,
      period: item.period ?? 1000,
      fc: item.fc ?? 0,
      scale: item.scale ?? 1.0,
    }));
    nextId = Math.max(...modbusConfig.value.map(r => r.id)) + 1;
  } else {
    modbusConfig.value = JSON.parse(JSON.stringify(defaultConfig));
    nextId = 3;
  }
};

const syncToChannel = () => {
  if (currentChannelData.value) {
    currentChannelData.value.ai_modbus = JSON.parse(JSON.stringify(modbusConfig.value));
  }
};

onMounted(() => { loadFromChannel(); });
watch(() => props.channel, () => { loadFromChannel(); });
watch(modbusConfig, () => { syncToChannel(); }, { deep: true });

const addRow = () => { modbusConfig.value.push(createDefaultRow(nextId++)); };
const removeRow = (index) => { if (modbusConfig.value.length > 1) modbusConfig.value.splice(index, 1); };
const handleReset = () => {
  if (confirm("Are you sure you want to reset to default configuration?")) {
    nextId = 3;
    modbusConfig.value = JSON.parse(JSON.stringify(defaultConfig));
  }
};

const isUseAIEnabled = computed(() => {
  const d = currentChannelData.value;
  return d?.useAI === 1 || d?.useAI === true;
});
</script>

<style scoped>
input[type="number"]:focus, select:focus { outline: none; }
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
input[type="number"] { -moz-appearance: textfield; }
</style>