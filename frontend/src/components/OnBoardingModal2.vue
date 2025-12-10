<template>
    <!-- Modal backdrop -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-out duration-100"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-show="modalOpen"
        class="fixed inset-0 bg-gray-900 bg-opacity-30 z-50 transition-opacity"
        aria-hidden="true"
      ></div>
    </transition>
  
    <!-- Modal dialog -->
    <transition
      enter-active-class="transition ease-in-out duration-200"
      enter-from-class="opacity-0 translate-y-4"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in-out duration-200"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-4"
    >
      <div
        v-show="modalOpen"
        class="fixed inset-0 z-50 overflow-hidden flex items-center my-4 justify-center px-4 sm:px-6"
        role="dialog"
        aria-modal="true"
      >
        <div
          ref="modalContent"
          class="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-auto max-w-2xl w-full max-h-full"
        >
          <!-- Close button -->
          <div class="absolute top-4 right-4 z-10">
            <button
              class="text-gray-400 dark:text-gray-500 hover:text-gray-500 dark:hover:text-gray-400"
              @click.stop="closeModal"
            >
              <div class="sr-only">Close</div>
              <svg
                class="fill-current"
                width="16"
                height="16"
                viewBox="0 0 16 16"
              >
                <path
                  d="M7.95 6.536l4.242-4.243a1 1 0 111.415 1.414L9.364 7.95l4.243 4.242a1 1 0 11-1.415 1.415L7.95 9.364l-4.243 4.243a1 1 0 01-1.414-1.415L6.536 7.95 2.293 3.707a1 1 0 011.414-1.414L7.95 6.536z"
                />
              </svg>
            </button>
          </div>
  
          <div class="p-6">
            <!-- Progress bar (not shown for device0 mode) -->
            <div class="mb-8" v-if="OpMode !== 'device0'">
              <div class="relative">
                <div
                  class="absolute left-0 top-1/2 -mt-px w-full h-0.5 bg-gray-200 dark:bg-gray-700/60"
                  aria-hidden="true"
                ></div>
                <ul class="relative flex justify-between w-full">
                  <li v-for="(step, index) in availableSteps" :key="step.id">
                    <div
                      class="flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold transition-colors"
                      :class="
                        currentStepIndex >= index
                          ? 'bg-violet-500 text-white'
                          : 'bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400'
                      "
                    >
                      {{ index + 1 }}
                    </div>
                  </li>
                </ul>
              </div>
            </div>
  
            <!-- Step 1: Restart Check (새로운 첫 단계) -->
            <div v-show="currentStep === 1" class="step-content">
              <h2
                class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-6"
              >
                Restart Check
              </h2>
  
              <div v-if="isCheckingRestart" class="text-center py-10">
                <div
                  class="inline-flex items-center justify-center w-16 h-16 mb-4 bg-violet-100 dark:bg-violet-900/20 rounded-full"
                >
                  <svg
                    class="animate-spin w-8 h-8 text-violet-500"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      class="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      stroke-width="4"
                    ></circle>
                    <path
                      class="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                </div>
                <div class="text-sm text-gray-500">
                  Checking restart requirement...
                </div>
              </div>
  
              <div v-else class="space-y-4">
                <!-- Restart Check Result -->
                <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <h3 class="font-semibold mb-3 flex items-center">
                    <svg
                      class="w-5 h-5 mr-2 text-blue-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    Restart Status
                  </h3>
                  <div class="space-y-2 text-sm">
                    <div class="flex items-center justify-between">
                      <span class="text-gray-600 dark:text-gray-400"
                        >Restart Required:</span
                      >
                      <span
                        :class="
                          needsRestart
                            ? 'text-yellow-600 font-semibold'
                            : 'text-green-600 font-semibold'
                        "
                      >
                        {{ needsRestart ? "YES" : "NO" }}
                      </span>
                    </div>
                    <div class="flex items-center justify-between">
                      <span class="text-gray-600 dark:text-gray-400"
                        >Check Time:</span
                      >
                      <span class="text-gray-700 dark:text-gray-300">{{
                        new Date().toLocaleString()
                      }}</span>
                    </div>
                  </div>
                </div>
  
                <!-- Restart Info -->
                <div
                  v-if="needsRestart"
                  class="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4"
                >
                  <div class="flex items-center">
                    <svg
                      class="w-5 h-5 text-yellow-500 mr-2"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                        clip-rule="evenodd"
                      />
                    </svg>
                    <span class="text-yellow-700 dark:text-yellow-400 font-medium"
                      >Device restart is required. Click "Next" to proceed with restart.</span
                    >
                  </div>
                </div>
  
                <!-- No Restart Message -->
                <div
                  v-else
                  class="bg-green-50 dark:bg-green-900/20 rounded-lg p-4"
                >
                  <div class="flex items-center">
                    <svg
                      class="w-5 h-5 text-green-500 mr-2"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clip-rule="evenodd"
                      />
                    </svg>
                    <span class="text-green-700 dark:text-green-400 font-medium"
                      >No restart required. Click "Next" to proceed.</span
                    >
                  </div>
                </div>
              </div>
  
              <div class="flex items-center justify-between mt-6 space-x-2">
                <button
                  type="button"
                  class="btn bg-gray-500 text-white hover:bg-gray-600"
                  @click="closeModal"
                >
                  Cancel
                </button>
                <div
                  v-if="isRestarting"
                  class="flex items-center text-sm text-blue-600"
                >
                  <svg
                    class="animate-spin w-4 h-4 mr-2"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      class="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      stroke-width="4"
                    ></circle>
                    <path
                      class="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  {{ restartMessage }}
                </div>
                <button
                  type="button"
                  class="btn bg-gray-900 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white"
                  @click="nextStep"
                  :disabled="isCheckingRestart"
                >
                  Next Step →
                </button>
              </div>
            </div>
  
            <!-- Step 2: Main Test Result (When Diagnosis_main is true) -->
            <div
              v-show="currentStep === 2 && diagnosis_main"
              class="step-content"
            >
              <!-- 기존 Main Test 코드 유지 -->
              <h2
                class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-6"
              >
                Main Test Result
              </h2>
  
              <div v-if="isLoadingMain" class="text-center py-10">
                <div
                  class="inline-flex items-center justify-center w-16 h-16 mb-4 bg-violet-100 dark:bg-violet-900/20 rounded-full"
                >
                  <svg
                    class="animate-spin w-8 h-8 text-violet-500"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      class="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      stroke-width="4"
                    ></circle>
                    <path
                      class="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                </div>
                <div class="text-sm text-gray-500">
                  Loading main test result...This process may take 20 seconds or
                  longer.
                </div>
              </div>
  
              <div
                v-else
                class="space-y-4 text-xs text-gray-800 dark:text-gray-100"
              >
                <div class="text-sm font-semibold uppercase">
                  Main Device Report
                </div>
                <div class="flex flex-wrap justify-between gap-4">
                  <div>Asset Type: {{ mainTestData.AssetName || "N/A" }}</div>
                  <div>
                    Serial Number: {{ mainTestData.SerialNumber || "N/A" }}
                  </div>
                  <div>Channel: {{ mainTestData.Channel || "N/A" }}</div>
                </div>
                <div class="font-semibold mb-4 mt-2">
                  Result: {{ mainTestResult.err || 0 }} Errors,
                  {{ mainTestResult.warn || 0 }} Warnings
                </div>
                <div
                  class="grid grid-cols-[10%_1fr_10%] gap-2 font-semibold text-gray-500 border-b border-gray-200 pb-1"
                >
                  <div class="text-left">AssemblyId</div>
                  <div class="text-center">Detail</div>
                  <div class="text-center">Status</div>
                </div>
                <div class="space-y-1">
                  <div
                    v-for="(item, index) in mainTestData.Commissions"
                    :key="index"
                    class="grid grid-cols-[10%_1fr_10%] gap-2 px-1 py-1 rounded hover:bg-gray-50"
                  >
                    <div class="text-left">{{ item.AssemblyID }}</div>
                    <div class="text-left text-gray-600">
                      <span v-for="(msg, i) in item.Messages" :key="i">
                        • {{ msg }}
                      </span>
                    </div>
                    <div
                      class="text-center font-bold"
                      :class="{
                        'text-green-600': item.Status < 2,
                        'text-red-600': item.Status === 3,
                        'text-yellow-500': item.Status === 2,
                      }"
                    >
                      {{ stList[item.Status] }}
                    </div>
                  </div>
                </div>
  
                <!-- Chart View Toggle Button -->
                <div class="mt-4">
                  <button
                    @click="getWaveShow('main')"
                    class="btn bg-violet-500 text-white hover:bg-violet-600"
                  >
                    <svg
                      class="w-4 h-4 inline-block mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                    View Charts
                  </button>
                </div>
  
                <!-- Chart View -->
                <div v-if="showMainDiagChart" class="space-y-4">
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="option in ChartTypes"
                      :key="option"
                      @click.prevent="
                        selectedMainChart = option;
                        updateMainChart();
                      "
                      :class="[
                        'btn border px-3 py-1 text-xs transition-colors duration-200 rounded-lg',
                        selectedMainChart === option
                          ? 'bg-violet-500 text-white border-violet-500'
                          : 'bg-white text-violet-500 border-gray-200 hover:bg-gray-100 dark:bg-gray-800 dark:text-white dark:hover:bg-gray-900',
                      ]"
                    >
                      {{ option }}
                    </button>
                  </div>
  
                  <div
                    class="text-sm font-semibold text-gray-600 dark:text-gray-300 mt-4"
                  >
                    {{ selectedMainChart }} Chart
                  </div>
  
                  <!-- Chart Components -->
                  <div class="max-h-[30vh] overflow-y-auto">
                    <LineChart
                      v-if="selectedMainChart == 'Time Domain(Voltage)'"
                      :label="mainWaveformLabelT"
                      :data="mainWaveformDataT"
                      :title="'3-Phase ' + selectedMainChart"
                      :legend="['V1', 'V2', 'V3']"
                      :mode="'3phase'"
                      :noData="mainWaveformNoData"
                    />
                    <LineChart
                      v-if="selectedMainChart == 'Time Domain(Current)'"
                      :label="mainWaveformLabelT"
                      :data="mainWaveformDataT"
                      :title="'3-Phase ' + selectedMainChart"
                      :legend="['I1', 'I2', 'I3']"
                      :mode="'3phase'"
                      :noData="mainWaveformNoData"
                    />
                    <LineChart
                      v-if="selectedMainChart == 'Frequency Domain(Voltage)'"
                      :label="mainWaveformLabelT"
                      :data="mainWaveformDataT"
                      :title="selectedMainChart"
                      :legend="['VFFT']"
                      :mode="'1phase'"
                      :noData="mainWaveformNoData"
                    />
                    <LineChart
                      v-if="selectedMainChart == 'Frequency Domain(Current)'"
                      :label="mainWaveformLabelT"
                      :data="mainWaveformDataT"
                      :title="selectedMainChart"
                      :legend="['IFFT']"
                      :mode="'1phase'"
                      :noData="mainWaveformNoData"
                    />
                  </div>
                </div>
              </div>
  
              <div class="flex items-center justify-between mt-6">
                <button
                  type="button"
                  class="btn bg-gray-500 text-white hover:bg-gray-600"
                  @click="closeModal"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  class="btn"
                  :class="
                    mainTestResult.err > 0
                      ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                      : 'bg-gray-900 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white'
                  "
                  @click="handleMainTestNext"
                  :disabled="!canProceedFromMain"
                >
                  {{
                    mainTestResult.err > 0 ? "Fix Errors First" : "Next Step →"
                  }}
                </button>
              </div>
            </div>
  
            <!-- Step 3: Sub Test Result (When Diagnosis_sub is true) -->
            <div v-show="currentStep === 3 && diagnosis_sub" class="step-content">
              <!-- 기존 Sub Test 코드 유지 -->
              <h2
                class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-6"
              >
                Sub Test Result
              </h2>
  
              <div v-if="isLoadingSub" class="text-center py-10">
                <div
                  class="inline-flex items-center justify-center w-16 h-16 mb-4 bg-violet-100 dark:bg-violet-900/20 rounded-full"
                >
                  <svg
                    class="animate-spin w-8 h-8 text-violet-500"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      class="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      stroke-width="4"
                    ></circle>
                    <path
                      class="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                </div>
                <div class="text-sm text-gray-500">
                  Loading sub test result...This process may take 20 seconds or
                  longer.
                </div>
              </div>
  
              <div
                v-else
                class="space-y-4 text-xs text-gray-800 dark:text-gray-100"
              >
                <div class="text-sm font-semibold uppercase">
                  Sub Device Report
                </div>
                <div class="flex flex-wrap justify-between gap-4">
                  <div>Asset Type: {{ subTestData.AssetName || "N/A" }}</div>
                  <div>
                    Serial Number: {{ subTestData.SerialNumber || "N/A" }}
                  </div>
                  <div>Channel: {{ subTestData.Channel || "N/A" }}</div>
                </div>
                <div class="font-semibold mb-4 mt-2">
                  Result: {{ subTestResult.err || 0 }} Errors,
                  {{ subTestResult.warn || 0 }} Warnings
                </div>
                <div
                  class="grid grid-cols-[10%_1fr_10%] gap-2 font-semibold text-gray-500 border-b border-gray-200 pb-1"
                >
                  <div class="text-left">AssemblyId</div>
                  <div class="text-center">Detail</div>
                  <div class="text-center">Status</div>
                </div>
                <div class="space-y-1">
                  <div
                    v-for="(item, index) in subTestData.Commissions"
                    :key="index"
                    class="grid grid-cols-[10%_1fr_10%] gap-2 px-1 py-1 rounded hover:bg-gray-50"
                  >
                    <div class="text-left">{{ item.AssemblyID }}</div>
                    <div class="text-left text-gray-600">
                      <span v-for="(msg, i) in item.Messages" :key="i">
                        • {{ msg }}
                      </span>
                    </div>
                    <div
                      class="text-center font-bold"
                      :class="{
                        'text-green-600': item.Status < 2,
                        'text-red-600': item.Status === 3,
                        'text-yellow-500': item.Status === 2,
                      }"
                    >
                      {{ stList[item.Status] }}
                    </div>
                  </div>
                </div>
  
                <!-- Chart View Toggle Button -->
                <div class="mt-4">
                  <button
                    @click="getWaveShow('sub')"
                    class="btn bg-violet-500 text-white hover:bg-violet-600"
                  >
                    <svg
                      class="w-4 h-4 inline-block mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                    View Charts
                  </button>
                </div>
  
                <!-- Sub Chart View -->
                <div v-if="showSubDiagChart" class="space-y-4">
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="option in ChartTypes"
                      :key="option"
                      @click.prevent="
                        selectedSubChart = option;
                        updateSubChart();
                      "
                      :class="[
                        'btn border px-3 py-1 text-xs transition-colors duration-200 rounded-lg',
                        selectedSubChart === option
                          ? 'bg-violet-500 text-white border-violet-500'
                          : 'bg-white text-violet-500 border-gray-200 hover:bg-gray-100 dark:bg-gray-800 dark:text-white dark:hover:bg-gray-900',
                      ]"
                    >
                      {{ option }}
                    </button>
                  </div>
  
                  <div
                    class="text-sm font-semibold text-gray-600 dark:text-gray-300 mt-4"
                  >
                    {{ selectedSubChart }} Chart
                  </div>
  
                  <!-- Sub Chart Components -->
                  <div class="max-h-[30vh] overflow-y-auto">
                    <LineChart
                      v-if="selectedSubChart == 'Time Domain(Voltage)'"
                      :label="subWaveformLabelT"
                      :data="subWaveformDataT"
                      :title="'3-Phase ' + selectedSubChart"
                      :legend="['V1', 'V2', 'V3']"
                      :mode="'3phase'"
                      :noData="subWaveformNoData"
                    />
                    <LineChart
                      v-if="selectedSubChart == 'Time Domain(Current)'"
                      :label="subWaveformLabelT"
                      :data="subWaveformDataT"
                      :title="'3-Phase ' + selectedSubChart"
                      :legend="['I1', 'I2', 'I3']"
                      :mode="'3phase'"
                      :noData="subWaveformNoData"
                    />
                    <LineChart
                      v-if="selectedSubChart == 'Frequency Domain(Voltage)'"
                      :label="subWaveformLabelT"
                      :data="subWaveformDataT"
                      :title="selectedSubChart"
                      :legend="['VFFT']"
                      :mode="'1phase'"
                      :noData="subWaveformNoData"
                    />
                    <LineChart
                      v-if="selectedSubChart == 'Frequency Domain(Current)'"
                      :label="subWaveformLabelT"
                      :data="subWaveformDataT"
                      :title="selectedSubChart"
                      :legend="['IFFT']"
                      :mode="'1phase'"
                      :noData="subWaveformNoData"
                    />
                  </div>
                </div>
              </div>
  
              <div class="flex items-center justify-between mt-6">
                <button
                  type="button"
                  class="btn bg-gray-500 text-white hover:bg-gray-600"
                  @click="closeModal"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  class="btn"
                  :class="
                    subTestResult.err > 0
                      ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                      : 'bg-gray-900 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white'
                  "
                  @click="nextStep"
                  :disabled="!canProceedFromSub"
                >
                  {{ subTestResult.err > 0 ? "Fix Errors First" : "Next Step →" }}
                </button>
              </div>
            </div>
  
            <!-- Step 4: Complete (Final step) -->
            <div v-show="currentStep === 4" class="step-content">
              <h2
                class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-6"
              >
                Complete Setup
              </h2>
  
              <div class="space-y-4">
                <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <h3 class="font-semibold mb-3">Configuration Summary</h3>
                  <div class="space-y-2 text-sm">
                    <div class="flex items-center justify-between">
                      <span class="text-gray-600 dark:text-gray-400"
                        >Restart Check:</span
                      >
                      <span class="text-green-600 font-semibold">COMPLETED</span>
                    </div>
                    <div
                      v-if="diagnosis_main"
                      class="flex items-center justify-between"
                    >
                      <span class="text-gray-600 dark:text-gray-400"
                        >Main Test:</span
                      >
                      <span
                        :class="
                          mainTestResult.err > 0
                            ? 'text-red-600'
                            : 'text-green-600'
                        "
                        class="font-semibold"
                      >
                        {{
                          mainTestResult.err > 0
                            ? `${mainTestResult.err} Errors`
                            : "PASSED"
                        }}
                      </span>
                    </div>
                    <div
                      v-if="diagnosis_sub"
                      class="flex items-center justify-between"
                    >
                      <span class="text-gray-600 dark:text-gray-400"
                        >Sub Test:</span
                      >
                      <span
                        :class="
                          subTestResult.err > 0
                            ? 'text-red-600'
                            : 'text-green-600'
                        "
                        class="font-semibold"
                      >
                        {{
                          subTestResult.err > 0
                            ? `${subTestResult.err} Errors`
                            : "PASSED"
                        }}
                      </span>
                    </div>
                    <div class="flex items-center justify-between">
                      <span class="text-gray-600 dark:text-gray-400"
                        >Overall Status:</span
                      >
                      <span class="text-green-600 font-semibold">READY</span>
                    </div>
                  </div>
                </div>
  
                <div class="text-xs text-gray-500">
                  By completing this setup, you confirm that all tests
                  have been reviewed and the system is ready for operation.
                </div>
              </div>
  
              <!-- Modal footer -->
              <div class="flex flex-wrap justify-between items-center mt-6">
                <button
                  v-if="!restartDone"
                  type="button"
                  class="btn bg-gray-500 text-white hover:bg-gray-600"
                  @click="closeModal"
                >
                  Cancel
                </button>
                <div class="ml-auto flex space-x-3">
                  <button
                    v-if="!restartDone"
                    class="btn bg-violet-500 text-white hover:bg-violet-600"
                    @click="restartValidation"
                  >
                    Restart
                  </button>
                  <button
                    v-else
                    class="btn bg-gray-900 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white"
                    @click="closeModal"
                  >
                    Finish
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </template>
  
  <script>
    import { ref, onMounted, onUnmounted, watch, computed, inject } from "vue";
    import LineChart from "../charts/connect/LineChart01_Echart2.vue";
    import axios from "axios";
    
    export default {
      name: "OnboardingModal",
      components: {
        LineChart,
      },
      props: {
        modalOpen: {
          type: Boolean,
          default: false,
        },
        OpMode: {
          type: String,
          default: "device0",
        },
        restartDone: { type: Boolean, default: false },
        applyMode: {
          type: Number,
          default: -1,
        },
      },
      emits: ["close-modal", "complete-setup", "restart-validation"],
      setup(props, { emit }) {
        const modalContent = ref(null);
        const currentStep = ref(1);
        const setupDict = ref({});
    
        // Restart check states
        const needsRestart = ref(false);
        const needsComm_main = ref(false);
        const needsComm_sub = ref(false);
        const isCheckingRestart = ref(false);
    
        // Loading states
        const isLoadingMain = ref(false);
        const isLoadingSub = ref(false);
        const stList = ref(["Info", "Pass", "Warning", "Error"]);
        const diagnosis_detail = inject("diagnosis_detail");
    
        const mainWaveformNoData = ref(false);
        const subWaveformNoData = ref(false);
    
        const mainTestData = ref({
          AssetName: "N/A",
          SerialNumber: "N/A",
          Channel: "N/A",
          Commissions: [],
        });
        const isProcessing = ref(false);
        const applyMode = computed(() => props.applyMode);
    
        const diagnosis_main = computed(() => {
          if (Object.keys(setupDict.value).length == 0) return false;
          if (setupDict.value.main.Enable) {
            if (
              setupDict.value.main.assetInfo.name != "" &&
              setupDict.value.General.useFuction.diagnosis_main
            )
              return true;
            else return false;
          } else {
            return false;
          }
        });
    
        const diagnosis_sub = computed(() => {
          if (Object.keys(setupDict.value).length == 0) return false;
          if (setupDict.value.sub.Enable) {
            if (
              setupDict.value.sub.assetInfo.name != "" &&
              setupDict.value.General.useFuction.diagnosis_sub
            )
              return true;
            else return false;
          } else {
            return false;
          }
        });
    
        const channelDiagnosis = computed(() => {
          if (diagnosis_main.value && diagnosis_sub.value) return 2;
          else if (diagnosis_main.value && !diagnosis_sub.value) return 0;
          else if (!diagnosis_main.value && diagnosis_sub.value) return 1;
          else return -1;
        });
    
        const mainTestResult = ref({ err: 0, warn: 0 });
        const mainTestLoaded = ref(false);
        const showMainDiagChart = ref(false);
        const mainWaveformData = ref({});
        const mainWaveformDataT = ref([]);
        const mainWaveformLabelT = ref([]);
        const selectedMainChart = ref("Time Domain(Voltage)");
    
        const subTestData = ref({
          AssetName: "N/A",
          SerialNumber: "N/A",
          Channel: "N/A",
          Commissions: [],
        });
        const subTestResult = ref({ err: 0, warn: 0 });
        const subTestLoaded = ref(false);
        const showSubDiagChart = ref(false);
        const subWaveformData = ref({});
        const subWaveformDataT = ref([]);
        const subWaveformLabelT = ref([]);
        const selectedSubChart = ref("Time Domain(Voltage)");
        const isRestarting = ref(false);
        const restartMessage = ref("");
    
        const ChartTypes = ref([
          "Time Domain(Voltage)",
          "Time Domain(Current)",
          "Frequency Domain(Voltage)",
          "Frequency Domain(Current)",
        ]);
    
        // ===== checkRestart 함수 =====
        const checkRestart = async () => {
          try {
            isCheckingRestart.value = true;
            const response = await axios.get(`/setting/apply`);
            console.log("apply response:", response.data);
    
            needsRestart.value = response.data.restartDevice || false;
    
            return needsRestart.value;
          } catch (e) {
            console.error("Error checking restart:", e);
            needsRestart.value = false;
            return false;
          } finally {
            isCheckingRestart.value = false;
          }
        };
    
        // ===== checkCommission 함수 =====
        const checkCommission = async (chName) => {
          try {
            const assetName = chName === 'Main' 
              ? setupDict.value.main.assetInfo.name 
              : setupDict.value.sub.assetInfo.name;
    
            console.log(`[DEBUG] checkCommission for ${chName}, asset: ${assetName}`);
    
            const response = await axios.get(`/setting/checkCommision/${assetName}`);
            
            console.log(`[DEBUG] checkCommission response for ${chName}:`, response.data);
    
            const needsComm = response.data.result || false;
    
            // 각 채널별로 저장
            if (chName === 'Main') {
              needsComm_main.value = needsComm;
            } else {
              needsComm_sub.value = needsComm;
            }
    
            return needsComm;
          } catch (e) {
            console.error(`Error checking commission for ${chName}:`, e);
            return false;
          }
        };
    
        // Load settings data
        const GetSettingData = async () => {
          try {
            const response = await axios.get(`/setting/getSetting`);
            if (response.data.passOK == 1) {
              setupDict.value = response.data.data;
            }
          } catch (error) {
            console.error("Settings data loading failed:", error);
          }
        };
    
        const getWaveShow = async (channel) => {
          if (channel == "main") showMainDiagChart.value = true;
          else showSubDiagChart.value = true;
          await getWaveform(channel);
        };
    
        const getWaveform = async (channel) => {
          const isMain = channel === "main" ? true : false;
          const waveformDataRef = isMain ? mainWaveformData : subWaveformData;
          const noDataRef = isMain ? mainWaveformNoData : subWaveformNoData;
          const assetName = isMain
            ? setupDict.value["main"]["assetInfo"]["name"]
            : setupDict.value["sub"]["assetInfo"]["name"];
    
          const showChartRef = isMain ? showMainDiagChart : showSubDiagChart;
    
          try {
            const response = await axios.get(`/setting/testwave/${assetName}`);
    
            if (response.data.success) {
              if (
                response.data.waveT &&
                Object.keys(response.data.waveT).length > 0
              ) {
                showChartRef.value = true;
                waveformDataRef.value = response.data.waveT;
                noDataRef.value = false;
    
                if (isMain) {
                  updateMainChart();
                } else {
                  updateSubChart();
                }
              } else {
                showChartRef.value = true;
                noDataRef.value = true;
              }
            } else {
              showChartRef.value = true;
              noDataRef.value = true;
            }
          } catch (error) {
            console.error(`Error loading waveform for ${channel}:`, error);
            showChartRef.value = true;
            noDataRef.value = true;
          }
        };
    
        const getCommision = async (channel) => {
          const isMain = channel === "main" ? true : false;
          const loadingRef = isMain ? isLoadingMain : isLoadingSub;
          const testDataRef = isMain ? mainTestData : subTestData;
          const testResultRef = isMain ? mainTestResult : subTestResult;
          const testLoadedRef = isMain ? mainTestLoaded : subTestLoaded;
    
          try {
            loadingRef.value = true;
            testLoadedRef.value = false;
            const assetName = isMain
              ? setupDict.value["main"]["assetInfo"]["name"]
              : setupDict.value["sub"]["assetInfo"]["name"];
            const chName = isMain ? "Main" : "Sub";
            const response = await axios.get(
              `/setting/test/${chName}/${assetName}`
            );
    
            if (response.data.success) {
              testDataRef.value = response.data.data;
              let errCount = 0,
                warnCount = 0;
              for (let i = 0; i < testDataRef.value["Commissions"].length; i++) {
                if (testDataRef.value["Commissions"][i]["Status"] == 3)
                  errCount += 1;
                else if (testDataRef.value["Commissions"][i]["Status"] == 2)
                  warnCount += 1;
              }
              testResultRef.value = { err: errCount, warn: warnCount };
              testLoadedRef.value = true;
    
              if (errCount > 0 || warnCount > 0) {
                restartMessage.value = "Failed Commisioning";
              }
            }
          } catch (e) {
            console.error(`Error loading ${channel} test:`, e);
            testResultRef.value = { err: 1, warn: 0 };
            testLoadedRef.value = true;
          } finally {
            loadingRef.value = false;
          }
        };
    
        const canProceedFromMain = computed(() => {
          return (
            !isLoadingMain.value &&
            mainTestLoaded.value &&
            mainTestResult.value.err === 0
          );
        });
    
        const canProceedFromSub = computed(() => {
          return (
            !isLoadingSub.value &&
            subTestLoaded.value &&
            subTestResult.value.err === 0
          );
        });
    
        const updateMainChart = () => {
          if (
            !mainWaveformData.value ||
            Object.keys(mainWaveformData.value).length === 0
          )
            return;
    
          const SR = mainWaveformData.value["SR"];
          const Duration = mainWaveformData.value["Duration"];
          const deltaT = 1 / SR;
          const deltaF = 1 / Duration;
    
          const chartResult = {
            "Time Domain(Voltage)": mainWaveformData.value["Vwave"],
            "Time Domain(Current)": mainWaveformData.value["Iwave"],
            "Frequency Domain(Voltage)": mainWaveformData.value["Vfft"],
            "Frequency Domain(Current)": mainWaveformData.value["Ifft"],
          };
    
          if (selectedMainChart.value.includes("Time")) {
            mainWaveformLabelT.value = Array.from(
              { length: chartResult[selectedMainChart.value][0].length },
              (_, i) => i * deltaT
            );
            mainWaveformDataT.value = chartResult[selectedMainChart.value];
          } else {
            mainWaveformLabelT.value = Array.from(
              { length: chartResult[selectedMainChart.value].length },
              (_, i) => i * deltaF
            );
            mainWaveformDataT.value = [chartResult[selectedMainChart.value]];
          }
        };
    
        const updateSubChart = () => {
          if (
            !subWaveformData.value ||
            Object.keys(subWaveformData.value).length === 0
          )
            return;
    
          const SR = subWaveformData.value["SR"];
          const Duration = subWaveformData.value["Duration"];
          const deltaT = 1 / SR;
          const deltaF = 1 / Duration;
    
          const chartResult = {
            "Time Domain(Voltage)": subWaveformData.value["Vwave"],
            "Time Domain(Current)": subWaveformData.value["Iwave"],
            "Frequency Domain(Voltage)": subWaveformData.value["Vfft"],
            "Frequency Domain(Current)": subWaveformData.value["Ifft"],
          };
    
          if (selectedSubChart.value.includes("Time")) {
            subWaveformLabelT.value = Array.from(
              { length: chartResult[selectedSubChart.value][0].length },
              (_, i) => i * deltaT
            );
            subWaveformDataT.value = chartResult[selectedSubChart.value];
          } else {
            subWaveformLabelT.value = Array.from(
              { length: chartResult[selectedSubChart.value].length },
              (_, i) => i * deltaF
            );
            subWaveformDataT.value = [chartResult[selectedSubChart.value]];
          }
        };
    
        const availableSteps = computed(() => {
          if (props.OpMode === "device0") {
            return [{ id: 4, name: "Complete" }];
          }
    
          const steps = [{ id: 1, name: "Restart Check" }];
    
          if (diagnosis_main.value) {
            steps.push({ id: 2, name: "Main Test" });
          }
    
          if (diagnosis_sub.value) {
            steps.push({ id: 3, name: "Sub Test" });
          }
    
          steps.push({ id: 4, name: "Complete" });
    
          return steps;
        });
    
        const currentStepIndex = computed(() => {
          return availableSteps.value.findIndex(
            (step) => step.id === currentStep.value
          );
        });
    
        const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    
        // ===== nextStep: 수정됨 =====
const nextStep = async () => {
  if (isProcessing.value) {
    console.log("[DEBUG] 이미 처리 중, 무시");
    return;
  }
  isProcessing.value = true;

  try {
    // ===== Step 1: Restart Check =====
    if (currentStep.value === 1) {
      console.log("[DEBUG] Step 1: 펌웨어 재시작 처리");

      // 1. 펌웨어 재시작 필요 시
      if (needsRestart.value) {
        console.log("[DEBUG] 펌웨어 재시작 필요 - restartDevice 실행");
        isRestarting.value = true;
        restartMessage.value = "Restarting firmware...";

        const restartSuccess = await restartDevice();

        if (!restartSuccess) {
          restartMessage.value = "Firmware restart failed";
          isRestarting.value = false;
          return;
        }

        console.log("[DEBUG] 펌웨어 재시작 완료");
        isRestarting.value = false;
      } else {
        console.log("[DEBUG] 펌웨어 재시작 불필요");
      }

      // 2. Main 진단 사용 시 checkCommission
      if (diagnosis_main.value) {
        console.log("[DEBUG] Main 진단 활성화 - checkCommission('Main') 실행");
        isRestarting.value = true;
        restartMessage.value = "Checking Main commission...";
        
        await checkCommission('Main');
        
        console.log(`[DEBUG] Main checkCommission 결과: ${needsComm_main.value}`);
        isRestarting.value = false;
      }

      // 3. Sub 진단 사용 시 checkCommission
      if (diagnosis_sub.value) {
        console.log("[DEBUG] Sub 진단 활성화 - checkCommission('Sub') 실행");
        isRestarting.value = true;
        restartMessage.value = "Checking Sub commission...";
        
        await checkCommission('Sub');
        
        console.log(`[DEBUG] Sub checkCommission 결과: ${needsComm_sub.value}`);
        isRestarting.value = false;
      }

      // 4. trigger 실행 (한 번만, target 결정)
      // 두 채널 모두 commission 불필요하면 Complete로
      if (!needsComm_main.value && !needsComm_sub.value) {
        console.log("[DEBUG] 두 채널 모두 commission 불필요 - Complete로");
        currentStep.value = 4;
        return;
      }

      // commission 필요한 채널이 있으면 trigger 실행
      let triggerTarget = -1;
      
      if (needsComm_main.value && needsComm_sub.value) {
        triggerTarget = 2; // 둘 다
        console.log("[DEBUG] Main, Sub 둘 다 commission 필요");
      } else if (needsComm_main.value) {
        triggerTarget = 0; // Main만
        console.log("[DEBUG] Main만 commission 필요");
      } else if (needsComm_sub.value) {
        triggerTarget = 1; // Sub만
        console.log("[DEBUG] Sub만 commission 필요");
      }

      console.log(`[DEBUG] trigger 실행 - target: ${triggerTarget}`);
      isRestarting.value = true;
      restartMessage.value = "Acquiring waveform file...";

      const response = await axios.get(`/setting/trigger?target=${triggerTarget}`);
      console.log("[DEBUG] trigger 응답:", response.data);

      isRestarting.value = false;

      if (!response.data.success) {
        restartMessage.value = response.data.message || "Trigger failed";
        return;
      }

      // 5. Step 1 완료 후 다음 단계 결정
      console.log("[DEBUG] Step 1 완료 - 다음 단계 결정");
      
      // Main commission 필요 → Main Test (Sub도 필요하면 나중에 진행)
      if (needsComm_main.value) {
        console.log("[DEBUG] Main Test로 이동");
        isLoadingMain.value = true;
        mainTestLoaded.value = false;
        currentStep.value = 2;
        await getCommision("main");
      }
      // Main 불필요, Sub commission 필요 → Sub Test
      else if (needsComm_sub.value) {
        console.log("[DEBUG] Sub Test로 이동");
        isLoadingSub.value = true;
        subTestLoaded.value = false;
        currentStep.value = 3;
        await getCommision("sub");
      }
      
      return; // Step 1에서는 여기서 종료
    }

    // ===== Step 2: Main Test (에러 있으면 진행 불가) =====
    if (currentStep.value === 2 && mainTestResult.value.err > 0) {
      console.log("[DEBUG] Main Test에 에러 있음 - 진행 불가");
      return;
    }

    // ===== Step 3: Sub Test (에러 있으면 진행 불가) =====
    if (currentStep.value === 3 && subTestResult.value.err > 0) {
      console.log("[DEBUG] Sub Test에 에러 있음 - 진행 불가");
      return;
    }

    // ===== Step 2 또는 3에서 다음으로 =====
    if (currentStep.value === 2 || currentStep.value === 3) {
      const currentIndex = currentStepIndex.value;
      if (currentIndex < availableSteps.value.length - 1) {
        currentStep.value = availableSteps.value[currentIndex + 1].id;
      }
    }
  } finally {
    isProcessing.value = false;
  }
};

// ===== handleMainTestNext: Sub commission 필요 여부 확인 =====
const handleMainTestNext = async () => {
  if (mainTestResult.value.err > 0) {
    console.log("[DEBUG] Main Test 에러 - 진행 불가");
    return;
  }

  // Sub commission 필요한 경우 Sub Test로
  if (needsComm_sub.value) {
    console.log("[DEBUG] Sub commission 필요 - Sub Test로 이동");
    isLoadingSub.value = true;
    subTestLoaded.value = false;
    currentStep.value = 3;
    await getCommision("sub");
  } else {
    // Sub commission 불필요하면 바로 Complete
    console.log("[DEBUG] Sub commission 불필요 - Complete로 이동");
    currentStep.value = 4;
  }
};
    
        const prevStep = () => {
          const currentIndex = currentStepIndex.value;
          if (currentIndex > 0) {
            currentStep.value = availableSteps.value[currentIndex - 1].id;
          }
        };
    
        const restartDevice = async () => {
          try {
            isRestarting.value = true;
            restartMessage.value = "Waiting for restart firmware";
    
            const response = await axios.get(`/setting/restartdevice`);
            if (response.data.success) {
              return true;
            } else {
              return false;
            }
          } catch (error) {
            return false;
          }
        };
    
        const closeModal = () => {
          emit("close-modal");
        };
    
        const completeSetup = () => {
          emit("complete-setup");
          closeModal();
        };
    
        const restartValidation = async () => {
          emit("restart-validation");
        };
    
        // ===== 모달 열릴 때 checkRestart 자동 실행 =====
        watch(
          () => props.modalOpen,
          async (newValue) => {
            if (newValue) {
              await GetSettingData();
              currentStep.value = 1;
    
              // Step 1에서 자동으로 checkRestart 실행
              await checkRestart();
            }
          }
        );
    
        watch([() => diagnosis_main, () => diagnosis_sub], () => {
          const validStepIds = availableSteps.value.map((s) => s.id);
          if (!validStepIds.includes(currentStep.value)) {
            currentStep.value = validStepIds[0];
          }
        });
    
        const clickHandler = ({ target }) => {
          return;
          if (!props.modalOpen || modalContent.value.contains(target)) return;
          closeModal();
        };
    
        const keyHandler = ({ keyCode }) => {
          if (!props.modalOpen || keyCode !== 27) return;
          closeModal();
        };
    
        onMounted(() => {
          document.addEventListener("click", clickHandler);
          document.addEventListener("keydown", keyHandler);
    
          if (props.modalOpen) {
            GetSettingData();
          }
        });
    
        onUnmounted(() => {
          document.removeEventListener("click", clickHandler);
          document.removeEventListener("keydown", keyHandler);
        });
    
        return {
          modalContent,
          currentStep,
          currentStepIndex,
          availableSteps,
          isCheckingRestart,
          needsRestart,
          isLoadingMain,
          isLoadingSub,
          mainTestData,
          mainTestResult,
          showMainDiagChart,
          mainWaveformDataT,
          mainWaveformLabelT,
          selectedMainChart,
          subTestData,
          subTestResult,
          showSubDiagChart,
          subWaveformDataT,
          subWaveformLabelT,
          selectedSubChart,
          ChartTypes,
          nextStep,
          prevStep,
          handleMainTestNext,
          closeModal,
          completeSetup,
          restartValidation,
          updateMainChart,
          updateSubChart,
          stList,
          diagnosis_main,
          diagnosis_sub,
          getWaveShow,
          restartDevice,
          isRestarting,
          restartMessage,
          diagnosis_detail,
          mainTestLoaded,
          subTestLoaded,
          canProceedFromMain,
          canProceedFromSub,
          mainWaveformNoData,
          subWaveformNoData,
          channelDiagnosis,
          applyMode,
          isProcessing,
          needsComm_main,
          needsComm_sub,
        };
      },
    };
    </script>
  <style scoped>
  .step-content {
    animation: fadeIn 0.3s ease-in-out;
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .btn {
    @apply px-4 py-2 rounded-lg font-medium transition-colors duration-200;
  }
  
  .btn-sm {
    @apply px-3 py-1.5 rounded-lg font-medium transition-colors duration-200 text-sm;
  }
  
  .btn:disabled {
    opacity: 0.6;
  }
  </style>