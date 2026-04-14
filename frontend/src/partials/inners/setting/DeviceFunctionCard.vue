<template>
  <div
    class="relative h-full flex flex-col bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg"
  >
    <div class="absolute top-0 left-0 right-0 h-0.5 bg-purple-500" aria-hidden="true"></div>
    <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700/60">
      <header class="flex items-center">
        <div class="w-6 h-6 rounded-full shrink-0 bg-purple-500 mr-3 flex items-center justify-center">
          <svg class="w-4 h-4 fill-current text-white" viewBox="0 0 24 24">
            <path d="M17 6H7a6 6 0 100 12h10a6 6 0 100-12zm0 10a4 4 0 110-8 4 4 0 010 8z" />
          </svg>
        </div>
        <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">{{ t("config.plansPanel.deviceFunction.title") }}</h3>
      </header>
    </div>
    <div class="px-4 py-4 space-y-3 flex-1">
      <!-- FTP -->
      <div class="flex items-center justify-between">
        <label class="block text-sm font-medium">{{ t("config.plansPanel.useWaveFormFTP") }}</label>
        <div
          class="relative inline-flex items-center cursor-pointer"
          @click="toggleFTP"
        >
          <div
            class="w-11 h-6 rounded-full transition-colors duration-200"
            :class="isFTP ? 'bg-purple-500' : 'bg-gray-300 dark:bg-gray-600'"
          ></div>
          <div
            class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
            :class="isFTP ? 'translate-x-5' : 'translate-x-0'"
          ></div>
        </div>
      </div>
      <!-- SNTP -->
      <div class="flex items-center justify-between">
        <label class="block text-sm font-medium">{{ t("config.plansPanel.useSNTP") }}</label>
        <div
          class="relative inline-flex items-center cursor-pointer"
          @click="inputDict.useFuction.sntp = inputDict.useFuction.sntp === 1 ? 0 : 1"
        >
          <div
            class="w-11 h-6 rounded-full transition-colors duration-200"
            :class="inputDict.useFuction.sntp === 1 ? 'bg-purple-500' : 'bg-gray-300 dark:bg-gray-600'"
          ></div>
          <div
            class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
            :class="inputDict.useFuction.sntp === 1 ? 'translate-x-5' : 'translate-x-0'"
          ></div>
        </div>
      </div>
      <!-- Modbus Serial -->
      <div class="flex items-center justify-between">
        <label class="block text-sm font-medium">Modbus Serial</label>
        <div
          class="relative inline-flex items-center cursor-pointer"
          @click="inputDict.modbus.rtu_use = inputDict.modbus.rtu_use === 1 ? 0 : 1"
        >
          <div
            class="w-11 h-6 rounded-full transition-colors duration-200"
            :class="inputDict.modbus.rtu_use === 1 ? 'bg-purple-500' : 'bg-gray-300 dark:bg-gray-600'"
          ></div>
          <div
            class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
            :class="inputDict.modbus.rtu_use === 1 ? 'translate-x-5' : 'translate-x-0'"
          ></div>
        </div>
      </div>
      <!-- MQTT -->
      <div class="flex items-center justify-between">
        <label class="block text-sm font-medium">MQTT</label>
        <div
          class="relative inline-flex items-center cursor-pointer"
          @click="inputDict.MQTT.Use = inputDict.MQTT.Use === 1 ? 0 : 1"
        >
          <div
            class="w-11 h-6 rounded-full transition-colors duration-200"
            :class="inputDict.MQTT.Use === 1 ? 'bg-purple-500' : 'bg-gray-300 dark:bg-gray-600'"
          ></div>
          <div
            class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
            :class="inputDict.MQTT.Use === 1 ? 'translate-x-5' : 'translate-x-0'"
          ></div>
        </div>
      </div>

      <!-- FTP 상태 안내 (카드 맨 아래) -->
      <div
        v-if="showConflictWarning"
        class="mt-auto flex items-start px-3 py-2 bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700/50 rounded-md"
      >
        <svg class="w-4 h-4 text-yellow-600 dark:text-yellow-400 mr-2 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        <span class="text-xs text-yellow-800 dark:text-yellow-200 leading-snug font-medium">
          {{ t("config.plansPanel.deviceFunction.ftpDxConflict") }}
        </span>
      </div>
      <div
        v-else-if="!isFTP"
        class="mt-auto flex items-center px-3 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700/50 rounded-md"
      >
        <svg class="w-4 h-4 text-blue-500 mr-2 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="text-xs text-blue-700 dark:text-blue-300">
          {{ t("config.plansPanel.info") }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import { inject, computed } from "vue";
import { useI18n } from "vue-i18n";

export default {
  name: "DeviceFunctionCard",
  setup() {
    const { t } = useI18n();
    const inputDict = inject("inputDict");
    const channel_main = inject("channel_main");
    const channel_sub = inject("channel_sub");

    const isFTP = computed(() =>
      inputDict.value.useFuction.ftp === 1 || inputDict.value.useFuction.ftp === true
    );

    const isDiagnosisEnabled = computed(() => {
      const mainDx = inputDict.value.useFuction?.diagnosis_main === true || inputDict.value.useFuction?.diagnosis_main === 1;
      const subDx = inputDict.value.useFuction?.diagnosis_sub === true || inputDict.value.useFuction?.diagnosis_sub === 1;
      const mainCh = channel_main.value?.Enable === 1 || channel_main.value?.Enable === true;
      const subCh = channel_sub.value?.Enable === 1 || channel_sub.value?.Enable === true;
      return (mainDx && mainCh) || (subDx && subCh);
    });

    const showConflictWarning = computed(() => isFTP.value && isDiagnosisEnabled.value);

    const toggleFTP = () => {
      inputDict.value.useFuction.ftp = isFTP.value ? 0 : 1;
    };

    return { t, inputDict, isFTP, showConflictWarning, toggleFTP };
  },
};
</script>
