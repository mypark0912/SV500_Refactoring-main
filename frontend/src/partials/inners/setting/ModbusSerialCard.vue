<template>
  <div
    class="relative h-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg flex flex-col flex-1"
  >
    <div class="absolute top-0 left-0 right-0 h-0.5 bg-violet-500" aria-hidden="true"></div>
    <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700/60">
      <header class="flex items-center">
        <div class="w-6 h-6 rounded-full shrink-0 bg-violet-500 mr-3">
          <svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24">
            <path d="M4 12h16m-4-4 4 4-4 4M8 8l-4 4 4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">Modbus Serial</h3>
      </header>
    </div>
    <div class="px-4 py-3 space-y-4">

      <!-- Serial Log enable + 사용 한 줄 -->
      <div class="flex gap-3">
        <div class="flex-1">
          <label class="block text-sm font-medium mb-2">{{ t("config.plansPanel.communication.logEnable") }}</label>
          <div
            class="relative inline-flex items-center cursor-pointer"
            @click="inputDict.modbus.serial_log = inputDict.modbus.serial_log === 1 ? 0 : 1"
          >
            <div
              class="w-11 h-6 rounded-full transition-colors duration-200"
              :class="inputDict.modbus.serial_log === 1 ? 'bg-sky-500' : 'bg-gray-300 dark:bg-gray-600'"
            ></div>
            <div
              class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
              :class="inputDict.modbus.serial_log === 1 ? 'translate-x-5' : 'translate-x-0'"
            ></div>
          </div>
        </div>
        <div class="flex-1">
          <label class="block text-sm font-medium mb-2">{{ t("config.plansPanel.modbus.rtu_use") }}</label>
          <select
            v-model.number="inputDict.modbus.rtu_use"
            class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-violet-500 focus:border-violet-500"
          >
            <option :value="0">{{ t("config.plansPanel.modbus.no") }}</option>
            <option :value="1">{{ t("config.plansPanel.modbus.yes") }}</option>
          </select>
        </div>
      </div>

      <!-- Baud Rate + Parity -->
      <div class="flex space-x-3">
        <div class="flex-1">
          <label class="block text-sm font-medium mb-2">{{ t("config.plansPanel.modbus.baudrate") }}</label>
          <select
            :disabled="inputDict.modbus.rtu_use == 0"
            v-model.number="inputDict.modbus.baud_rate"
            class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-violet-500 focus:border-violet-500"
          >
            <option :value="0">9600</option>
            <option :value="1">19200</option>
            <option :value="2">38400</option>
            <option :value="3">57600</option>
            <option :value="4">115200</option>
          </select>
        </div>
        <div class="flex-1">
          <label class="block text-sm font-medium mb-2">{{ t("config.plansPanel.modbus.parity") }}</label>
          <select
            :disabled="inputDict.modbus.rtu_use == 0"
            v-model.number="inputDict.modbus.parity"
            class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-violet-500 focus:border-violet-500"
          >
            <option :value="0">None</option>
            <option :value="1">Odd</option>
            <option :value="2">Even</option>
          </select>
        </div>
      </div>

      <!-- Data Bits + Stop Bits -->
      <div class="flex space-x-3">
        <div class="flex-1">
          <label class="block text-sm font-medium mb-2">{{ t("config.plansPanel.modbus.dbits") }}</label>
          <select
            :disabled="inputDict.modbus.rtu_use == 0"
            v-model.number="inputDict.modbus.data_bits"
            class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-violet-500 focus:border-violet-500"
          >
            <option :value="7">7</option>
            <option :value="8">8</option>
          </select>
        </div>
        <div class="flex-1">
          <label class="block text-sm font-medium mb-2">{{ t("config.plansPanel.modbus.sbits") }}</label>
          <select
            :disabled="inputDict.modbus.rtu_use == 0"
            v-model.number="inputDict.modbus.stop_bits"
            class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-violet-500 focus:border-violet-500"
          >
            <option :value="1">1</option>
            <option :value="2">2</option>
          </select>
        </div>
      </div>

      <!-- Serial Device Info 테이블 -->
      <div :class="inputDict.modbus.rtu_use == 0 ? 'opacity-40 pointer-events-none' : ''">
        <div class="flex items-center justify-between mb-2">
          <div class="text-xs text-gray-800 dark:text-gray-100 font-semibold uppercase">Serial Device Info</div>
          <button
            v-if="inputDict.modbus.serialinfo.length < 4"
            @click="addSerialRow"
            class="px-2 py-0.5 text-xs font-medium text-white bg-green-600 hover:bg-green-700 rounded focus:outline-none"
          >+ Add</button>
        </div>
        <div class="border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden">
          <!-- 헤더 -->
          <div class="grid text-center text-xs font-semibold text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50" style="grid-template-columns: 55px 1fr 80px 36px">
            <div class="px-1 py-2 border-r border-gray-200 dark:border-gray-600">idx</div>
            <div class="px-2 py-2 border-r border-gray-200 dark:border-gray-600">type</div>
            <div class="px-1 py-2 border-r border-gray-200 dark:border-gray-600">devId</div>
            <div class="px-1 py-2"></div>
          </div>
          <!-- 행 -->
          <div
            v-for="(item, idx) in inputDict.modbus.serialinfo"
            :key="item.id"
            class="grid text-center text-sm border-t border-gray-200 dark:border-gray-700"
            style="grid-template-columns: 55px 1fr 80px 36px"
          >
            <div class="px-1 py-1.5 border-r border-gray-200 dark:border-gray-600 flex items-center justify-center text-gray-700 dark:text-gray-200">
              {{ idx + 1 }}
            </div>
            <div class="px-2 py-1.5 border-r border-gray-200 dark:border-gray-600 flex items-center justify-center">
              <select
                v-model.number="item.type"
                :disabled="inputDict.modbus.rtu_use == 0"
                class="form-select w-full text-sm bg-white dark:bg-gray-700 border-gray-300 rounded focus:ring-violet-500 focus:border-violet-500 py-0.5"
              >
                <option :value="0">ExtIO</option>
                <option :value="1">P300-C</option>
              </select>
            </div>
            <div class="px-1 py-1.5 border-r border-gray-200 dark:border-gray-600 flex items-center justify-center">
              <input
                v-model.number="item.devId"
                type="number"
                min="1"
                max="255"
                :disabled="inputDict.modbus.rtu_use == 0"
                class="form-input w-full text-sm text-center py-0.5"
              />
            </div>
            <div class="flex items-center justify-center">
              <button
                v-if="inputDict.modbus.serialinfo.length > 1"
                @click="removeSerialRow(idx)"
                class="w-5 h-5 flex items-center justify-center text-red-500 hover:text-red-700"
                title="Delete"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import { inject, onMounted, watch } from "vue";
import { useI18n } from "vue-i18n";

const defaultSerialtype = [
  { id: 1, type: 0, devId: 1 },
  { id: 2, type: 0, devId: 2 },
  { id: 3, type: 0, devId: 3 },
  { id: 4, type: 0, devId: 4 },
];

export default {
  name: "ModbusSerialCard",
  setup() {
    const { t } = useI18n();
    const inputDict = inject("inputDict");

    const addSerialRow = () => {
      const list = inputDict.value.modbus.serialinfo;
      if (list.length >= 4) return;
      const nextId = list.length > 0 ? Math.max(...list.map(i => i.id)) + 1 : 1;
      list.push({ id: nextId, type: 0, devId: 1 });
    };

    const removeSerialRow = (idx) => {
      const list = inputDict.value.modbus.serialinfo;
      if (list.length <= 1) return;
      list.splice(idx, 1);
      list.forEach((item, i) => { item.id = i + 1; });
    };

    const ensureSerialtype = () => {
      if (!inputDict.value.modbus) return;
      if (!inputDict.value.modbus.serialinfo || inputDict.value.modbus.serialinfo.length === 0) {
        inputDict.value.modbus.serialinfo = defaultSerialtype.map(item => ({ ...item }));
      }
    };

    watch(
      () => inputDict.value.modbus,
      () => { ensureSerialtype(); },
      { immediate: true, deep: false }
    );

    onMounted(() => {
      ensureSerialtype();
    });

    return { t, inputDict, addSerialRow, removeSerialRow };
  },
};
</script>
