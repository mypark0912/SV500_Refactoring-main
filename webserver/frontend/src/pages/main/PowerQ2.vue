<template>
  <div class="flex h-[100dvh] overflow-hidden">
    <!-- Sidebar -->
    <Sidebar :sidebarOpen="sidebarOpen" @close-sidebar="sidebarOpen = true" :channel="channel" />

    <!-- Content area -->
    <div class="relative flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
      <!-- Site header -->
      <Header :sidebarOpen="sidebarOpen" @toggle-sidebar="sidebarOpen = !sidebarOpen" />

      <main class="grow">
        <div class="px-4 sm:px-6 lg:px-8 py-5 w-full max-w-full">
          <!-- Dashboard actions -->
          <div class="sm:flex sm:justify-between sm:items-center mb-5">
            <!-- Left: Title -->
            <div class="mb-3 sm:mb-0">
              <h2 class="text-lg md:text-xl text-gray-800 dark:text-gray-100 font-bold">
                {{
                  channel == "Main" ? t("pq.sitemap.main") : t("pq.sitemap.sub")
                }} {{ assetName }}
                > {{ t("pq.sitemap.title") }}
              </h2>
            </div>
          </div>

          <!-- Cards -->
          <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
            <!-- Card (탭이 포함될 카드 섹션) -->
            <div class="md:col-span-12 bg-white dark:bg-gray-800 shadow-md rounded-lg p-4 w-full">
              <!-- Tab Navigation -->
              <div class="px-4">
                <ul class="text-sm font-medium flex flex-nowrap overflow-x-auto no-scrollbar w-full">
                  <li v-for="(tab, index) in tabs" :key="index" class="mr-4 last:mr-0 relative">
                    <button @click="changeTab(tab.name)"
                      class="px-4 py-2 whitespace-nowrap transition duration-200 ease-in-out" :class="activeTab === tab.name
                        ? 'text-violet-500 border-b-2 border-violet-500'
                        : 'text-gray-500 dark:text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
                        ">
                      {{ tab.label }}
                    </button>
                  </li>
                </ul>
              </div>

              <!-- Tab Content -->
              <div v-for="(tab, index) in tabs" :key="index">
                <div v-if="activeTab === tab.name" class="text-gray-700 dark:text-white text-left pt-3 px-4">
                  <!-- Status 탭: PQ 진단 -->
                  <template v-if="activeTab === 'Status'">
                    <DiagnosisTab :channel="channelComputed" :asset="assetConfig" mode="PowerQuality" :key="`pq-status-${statusRefreshKey}`" />
                  </template>

                  <!-- 콤보박스 (Harmonics / Waveform 탭만) -->
                  <div v-if="activeTab !== 'Status'" class="mt-2 mb-4 flex items-center gap-x-2">
                    <label :for="tab.name + '-select'"
                      class="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Select Option
                    </label>
                    <select :id="tab.name + '-select'" :value="selectedOptions[tab.name]"
                      class="form-select w-64 flex-shrink-0 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-violet-500 focus:border-violet-500"
                      @change="selectChanged(tab.name, $event.target.value)">
                      <option v-for="(option, i) in tab.options" :key="i" :value="option.key">
                        {{ option.label }}
                      </option>
                    </select>
                    <div v-if="activeTab === 'Harmonics'" class="flex flex-wrap -space-x-px">
                      <button v-for="option in options" :key="option.value" :value="option.value"
                        @click.prevent="setbtnOption(option.value)" :class="[
                          'btn border px-4 py-2 transition-colors duration-200 rounded-none first:rounded-l-lg last:rounded-r-lg',
                          btnOptions === option.value
                            ? 'bg-violet-500 text-white border-violet-500'
                            : 'bg-white text-violet-500 border-gray-200 hover:bg-gray-100 dark:bg-gray-800 dark:text-white dark:hover:bg-gray-900',
                        ]">
                        {{ option.label }}
                      </button>
                    </div>
                  </div>

                  <!-- 차트 컨테이너 (Harmonics / Waveform 탭만) -->
                  <div v-if="activeTab !== 'Status'" class="flex flex-col space-y-4">
                    <BarChart v-if="
                      activeTab === 'Harmonics' &&
                      tbdataH !== null &&
                      btnOptions === 'chart'
                    " :data="chartData" :width="600" :height="250" :mode="mode1"
                      :key="`harmonics-chart1-${chartUpdateKey}`" />
                    <BarChart v-if="
                      activeTab === 'Harmonics' &&
                      tbdataH !== null &&
                      btnOptions === 'chart'
                    " :data="chartData2" :width="600" :height="250" :mode="mode2"
                      :key="`harmonics-chart2-${chartUpdateKey}`" />
                    <BarChart v-if="
                      activeTab === 'Harmonics' &&
                      tbdataH !== null &&
                      btnOptions === 'chart'
                    " :data="chartData3" :width="600" :height="250" :mode="mode3"
                      :key="`harmonics-chart3-${chartUpdateKey}`" />

                    <PowerQ_Table v-if="
                      activeTab === 'Harmonics' &&
                      tbdataH !== null &&
                      btnOptions === 'table'
                    " :data="tbdataH" :option="selectedOptions.Harmonics"
                      :key="`harmonics-table-${selectedOptions.Harmonics}`" />
                    
                    <LineChart v-if="activeTab === 'Waveform'" :data="linechartData" width="495" height="348"
                      :mode="'Voltage'" />
                    <LineChart v-if="activeTab === 'Waveform'" :data="linechartData2" width="495" height="348"
                      :mode="'Current'" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { ref, watch, computed, nextTick, onMounted, onUnmounted, onBeforeUnmount, reactive } from "vue";
import { useRoute } from "vue-router";
import axios from "axios";
import Sidebar from "../common/SideBar3.vue";
import Header from "../common/Header.vue";
import BarChart from "../../charts/connect/BarChart05.vue";
import LineChart from "../../charts/connect/LineChart02.vue";
import Report_table from "../../partials/inners/power/ReportTable2.vue";
import PowerQ_Table from "../../partials/inners/power/PowerQ_Table.vue";
import DiagnosisTab from "../../partials/inners/diagnosis/DiagnosisTab.vue";
import { tailwindConfig } from "../../utils/Utils";
import { useI18n } from "vue-i18n";
import { useSetupStore } from '@/store/setup'

export default {
  name: "PowerQ",
  props: ["channel"],
  components: {
    Sidebar,
    Header,
    BarChart,
    LineChart,
    Report_table,
    PowerQ_Table,
    DiagnosisTab,
  },
  setup(props) {
    const { t } = useI18n();
    const route = useRoute();
    const setupStore = useSetupStore();

    // ========== 모든 ref/reactive 먼저 선언 ==========
    const sidebarOpen = ref(true);
    const channel = ref(props.channel);
    const activeTab = ref("Harmonics");
    const mode1 = ref("L1");
    const mode2 = ref("L2");
    const mode3 = ref("L3");
    const tbdata = ref(null);
    const tbdataH = ref(null);
    const btnOptions = ref("chart");
    const chartUpdateKey = ref(0);
    const chartData = ref({});
    const chartData2 = ref({});
    const chartData3 = ref({});
    const linechartData = ref({});
    const linechartData2 = ref({});
    const waveUpdate = ref(false);
    const waveInterval = ref(null);
    const dataInterval = ref(null);
    const isComponentActive = ref(false);
    const isInitializing = ref(false);
    const statusRefreshKey = ref(0);
    const statusInterval = ref(null);

    let timeout_harmonics = 5;

    // 선택된 옵션 저장
    const selectedOptions = reactive({
      Harmonics: "phaseVoltage",
      Waveform: "phaseVoltage",
    });

    // ========== computed ==========
    const options = computed(() => [
      { label: t("pq.Button.table"), value: "table" },
      { label: t("pq.Button.chart"), value: "chart" },
    ]);

    const channelComputed = computed(
      () => props.channel || route.params.channel || "Default"
    );

    const assetName = computed(() => {
      const mainName = setupStore.getAssetConfig.assetName_main;
      const subName = setupStore.getAssetConfig.assetName_sub;
      if (channelComputed.value == 'Main' || channelComputed.value == 'main') {
        return mainName != '' ? "(" + mainName + ")" : "";
      } else {
        return subName != '' ? "(" + subName + ")" : "";
      }
    });

    const assetConfig = computed(() => setupStore.getAssetConfig);

    const tabs = computed(() => [
      {
        name: "Harmonics",
        label: t("pq.tabs.harmonics"),
        options: [
          { key: "phaseVoltage", label: t("pq.options.phaseVoltage") },
          { key: "lineVoltage", label: t("pq.options.lineVoltage") },
          { key: "current", label: t("pq.options.current") },
        ],
      },
      {
        name: "Waveform",
        label: t("pq.tabs.waveform"),
        options: [
          { key: "phaseVoltage", label: t("pq.options.phaseVoltage") },
          { key: "lineVoltage", label: t("pq.options.lineVoltage") },
        ],
      },
      {
        name: "Status",
        label: t("pq.tabs.status"),
        options: [],
      },
    ]);

    // ========== 상수 ==========
    const waveMap = {
      phaseVoltage: ["Wave Form V1", "Wave Form V2", "Wave Form V3"],
      lineVoltage: ["Wave Form V12", "Wave Form V23", "Wave Form V31"],
      current: ["Wave Form I1", "Wave Form I2", "Wave Form I3"],
      Voltage: ["Wave Form V12", "Wave Form V23", "Wave Form V31"],
      Current: ["Wave Form I1", "Wave Form I2", "Wave Form I3"],
    };

    const harmonicsMap = {
      phaseVoltage: ["U1", "U2", "U3"],
      lineVoltage: ["Upp1", "Upp2", "Upp3"],
      current: ["I1", "I2", "I3"],
    };

    // ========== 함수들 ==========
    
    const initSelectedOptions = () => {
      selectedOptions.Harmonics = 'phaseVoltage';
      selectedOptions.Waveform = 'phaseVoltage';
    };

    const scaledDataV = (waveform) => {
      const vscale = tbdata.value["vscale"];
      if (!Array.isArray(waveform) || typeof vscale !== "number") return [];
      const scaleFactor = Number(vscale.toFixed(5));
      return waveform.map((y) => y * scaleFactor);
    };

    const scaledDataI = (waveform) => {
      const iscale = tbdata.value["iscale"];
      if (!Array.isArray(waveform) || typeof iscale !== "number") return [];
      const scaleFactor = Number(iscale.toFixed(5));
      return waveform.map((y) => y * scaleFactor);
    };

    const updateChartByOption = async (tab, option) => {
      //console.log('=== updateChartByOption 호출 ===', tab, option);
      if (tab === "Waveform") {
        if (!tbdata.value) return;

        const [k1, k2, k3] = waveMap[option] || [];
        const scaleFactorV = typeof tbdata.value["vscale"] === "number" ? Number(tbdata.value["vscale"]) : 1;
        const scaleFactorI = typeof tbdata.value["iscale"] === "number" ? Number(tbdata.value["iscale"]) : 1;

        const scale = (arr, isCurrent = false) =>
          Array.isArray(arr) ? arr.map((y) => y * (isCurrent ? scaleFactorI : scaleFactorV)) : [];

        linechartData.value = {
          labels: Array.from({ length: 160 }, (_, i) => i + 1),
          datasets: [
            {
              label: "L1",
              data: scale(tbdata.value[k1], false),
              borderColor: tailwindConfig().theme.colors.violet[500],
              backgroundColor: "transparent",
              borderWidth: 2,
              tension: 0.2,
            },
            {
              label: "L2",
              data: scale(tbdata.value[k2], false),
              borderColor: tailwindConfig().theme.colors.sky[500],
              backgroundColor: "transparent",
              borderWidth: 2,
              tension: 0.2,
            },
            {
              label: "L3",
              data: scale(tbdata.value[k3], false),
              borderColor: tailwindConfig().theme.colors.lime[500],
              backgroundColor: "transparent",
              borderWidth: 2,
              tension: 0.2,
            },
          ],
        };

        const currentKeys = waveMap['current'] || waveMap['Current'] || [];
        const [k11, k12, k13] = currentKeys;
        linechartData2.value = {
          labels: Array.from({ length: 160 }, (_, i) => i + 1),
          datasets: [
            {
              label: "L1",
              data: scale(tbdata.value[k11], true),
              borderColor: tailwindConfig().theme.colors.violet[500],
              backgroundColor: "transparent",
              borderWidth: 2,
              tension: 0.2,
            },
            {
              label: "L2",
              data: scale(tbdata.value[k12], true),
              borderColor: tailwindConfig().theme.colors.sky[500],
              backgroundColor: "transparent",
              borderWidth: 2,
              tension: 0.2,
            },
            {
              label: "L3",
              data: scale(tbdata.value[k13], true),
              borderColor: tailwindConfig().theme.colors.lime[500],
              backgroundColor: "transparent",
              borderWidth: 2,
              tension: 0.2,
            },
          ],
        };
        await nextTick();
      }
      else if (tab === "Harmonics") {
        if (!tbdataH.value) return;

        const [k1, k2, k3] = harmonicsMap[option] || [];

        if (!k1 || !k2 || !k3) {
          console.log('유효하지 않은 옵션:', option);
          return;
        }

        chartData.value = {
          labels: Array.from({ length: 62 }, (_, i) => i + 2),
          datasets: [
            {
              label: "L1",
              data: tbdataH.value[k1]?.slice(2) || [],
              backgroundColor: tailwindConfig().theme.colors.violet[500],
              borderRadius: 4,
            },
          ],
        };

        chartData2.value = {
          labels: Array.from({ length: 62 }, (_, i) => i + 2),
          datasets: [
            {
              label: "L2",
              data: tbdataH.value[k2]?.slice(2) || [],
              backgroundColor: tailwindConfig().theme.colors.sky[500],
              borderRadius: 4,
            },
          ],
        };

        chartData3.value = {
          labels: Array.from({ length: 62 }, (_, i) => i + 2),
          datasets: [
            {
              label: "L3",
              data: tbdataH.value[k3]?.slice(2) || [],
              backgroundColor: tailwindConfig().theme.colors.lime[500],
              borderRadius: 4,
            },
          ],
        };

        chartUpdateKey.value++;
        await nextTick();
      }
    };

    const selectChanged = (tabName, selectedValue) => {
      selectedOptions[tabName] = selectedValue;
      updateChartByOption(tabName, selectedValue);
    };

    const fetchWave = async (ch) => {
      try {
        const response = await axios.get(`/api/getWave/${ch}`);
        if (response.data.success) {
          tbdata.value = { ...response.data.data };

          linechartData.value = {
            labels: Array.from({ length: 160 }, (_, i) => i + 1),
            datasets: [
              {
                label: "L1",
                data: scaledDataV(tbdata.value["Wave Form V1"]),
                borderColor: tailwindConfig().theme.colors.violet[500],
                backgroundColor: "transparent",
                borderWidth: 2,
                tension: 0.2,
              },
              {
                label: "L2",
                data: scaledDataV(tbdata.value["Wave Form V2"]),
                borderColor: tailwindConfig().theme.colors.sky[500],
                backgroundColor: "transparent",
                borderWidth: 2,
                tension: 0.2,
              },
              {
                label: "L3",
                data: scaledDataV(tbdata.value["Wave Form V3"]),
                borderColor: tailwindConfig().theme.colors.lime[500],
                backgroundColor: "transparent",
                borderWidth: 2,
                tension: 0.2,
              },
            ],
          };

          linechartData2.value = {
            labels: Array.from({ length: 160 }, (_, i) => i + 1),
            datasets: [
              {
                label: "L1",
                data: scaledDataI(tbdata.value["Wave Form I1"]),
                borderColor: tailwindConfig().theme.colors.violet[500],
                backgroundColor: "transparent",
                borderWidth: 2,
                tension: 0.2,
              },
              {
                label: "L2",
                data: scaledDataI(tbdata.value["Wave Form I2"]),
                borderColor: tailwindConfig().theme.colors.sky[500],
                backgroundColor: "transparent",
                borderWidth: 2,
                tension: 0.2,
              },
              {
                label: "L3",
                data: scaledDataI(tbdata.value["Wave Form I3"]),
                borderColor: tailwindConfig().theme.colors.lime[500],
                backgroundColor: "transparent",
                borderWidth: 2,
                tension: 0.2,
              },
            ],
          };
        } else {
          console.warn("서버 응답이 success: false 입니다.");
          tbdata.value = null;
        }
      } catch (error) {
        console.log("데이터 가져오기 실패:", error);
      }
    };

    const fetchData = async (ch) => {
      try {
        if (!isComponentActive.value) return;

        const response = await axios.get(`/api/getHarmonics/${ch}`);

        if (response.data.success) {
          if (!isComponentActive.value) return;

          tbdataH.value = { ...response.data.data };
          updateChartByOption('Harmonics', selectedOptions.Harmonics);
        } else {
          console.warn("서버 응답이 success: false 입니다.");
          tbdataH.value = null;
        }
      } catch (error) {
        if (isComponentActive.value) {
          console.log("데이터 가져오기 실패:", error);
        }
      }
    };

    const refreshData = async () => {
      if (!isComponentActive.value) return;

      if (channel.value && activeTab.value === 'Harmonics') {
        await fetchData(channel.value);
      }
    };

    const stopInterval = () => {
      if (dataInterval.value) {
        clearInterval(dataInterval.value);
        dataInterval.value = null;
      }
    };

    const startInterval = async () => {
      stopInterval();

      if (!isComponentActive.value) return;

      tbdataH.value = null;

      if (activeTab.value === 'Harmonics' && isComponentActive.value) {
        await refreshData();
        dataInterval.value = setInterval(refreshData, timeout_harmonics * 1000);
      }
    };

    const stopWaveInterval = () => {
      if (waveInterval.value) {
        clearInterval(waveInterval.value);
        waveInterval.value = null;
      }
    };

    const startStatusInterval = () => {
      stopStatusInterval();
      if (isComponentActive.value) {
        statusInterval.value = setInterval(() => {
          statusRefreshKey.value++;
        }, 5 * 60 * 1000);
      }
    };

    const stopStatusInterval = () => {
      if (statusInterval.value) {
        clearInterval(statusInterval.value);
        statusInterval.value = null;
      }
    };

    const stopAllIntervals = () => {
      stopInterval();
      stopWaveInterval();
      stopStatusInterval();
    };

    const refreshWaveData = async () => {
      if (!isComponentActive.value || activeTab.value !== 'Waveform') return;

      try {
        const response = await axios.get(`/api/getWave/${channel.value}`);
        if (response.data.success) {
          tbdata.value = { ...response.data.data };
          updateChartByOption('Waveform', selectedOptions.Waveform);
        }
      } catch (error) {
        console.error("Waveform 데이터 갱신 실패:", error);
      }
    };

    const startWaveInterval = () => {
      stopWaveInterval();

      if (activeTab.value === 'Waveform' && isComponentActive.value && waveUpdate.value) {
        waveInterval.value = setInterval(refreshWaveData, 5000);
      }
    };

    const startWave = async () => {
      try {
        const response = await axios.get(`/api/setWave/${channel.value}/1`);

        if (response.data.success) {
          waveUpdate.value = true;

          setTimeout(async () => {
            if (activeTab.value === 'Waveform' && isComponentActive.value) {
              await fetchWave(channel.value);
              startWaveInterval();
            }
          }, 2000);
        }
      } catch (error) {
        console.error('Wave 업데이트 시작 실패:', error);
      }
    };

    const endWave = async () => {
      try {
        stopWaveInterval();

        const response = await axios.get(`/api/setWave/${channel.value}/0`);

        if (response.data.success) {
          waveUpdate.value = false;
        }
      } catch (error) {
        console.error('Wave 업데이트 종료 실패:', error);
      }
    };

    const setbtnOption = (value) => {
      btnOptions.value = value;

      if (value === 'chart' && tbdataH.value) {
        updateChartByOption('Harmonics', selectedOptions.Harmonics);
      }
    };

    const changeTab = (tabName) => {
      activeTab.value = tabName;
    };

    // 채널/드라이브 타입 변경 시 초기화하는 통합 함수
    const initializeForChannel = async (newChannel) => {
      if (isInitializing.value) {
        return;
      }
      
      isInitializing.value = true;
      
      try {
        stopAllIntervals();
        
        if (waveUpdate.value) {
          await endWave();
        }
        
        channel.value = newChannel;
        
        // 차트 데이터 초기화
        chartData.value = {};
        chartData2.value = {};
        chartData3.value = {};
        linechartData.value = {};
        linechartData2.value = {};
        tbdata.value = null;
        tbdataH.value = null;
        timeout_harmonics = 5;
        
        // selectedOptions 초기화
        initSelectedOptions();
        
        // 현재 탭에 따라 데이터 로드
        if (activeTab.value === 'Status') {
          statusRefreshKey.value++;
          startStatusInterval();
        } else if (activeTab.value === 'Harmonics') {
          await startInterval();
        } else if (activeTab.value === 'Waveform') {
          await startWave();
        }
      } finally {
        isInitializing.value = false;
      }
    };

    // ========== 라이프사이클 훅 ==========
    onMounted(() => {
      isComponentActive.value = true;
      
      const initialChannel = props.channel || route.params.channel;
      
      initializeForChannel(initialChannel);
    });

    onBeforeUnmount(() => {
      isComponentActive.value = false;

      chartData.value = { labels: [], datasets: [] };
      chartData2.value = { labels: [], datasets: [] };
      chartData3.value = { labels: [], datasets: [] };
      linechartData.value = { labels: [], datasets: [] };
      linechartData2.value = { labels: [], datasets: [] };
      stopAllIntervals();

      if (waveUpdate.value) {
        endWave();
      }
    });

    onUnmounted(() => {
      isComponentActive.value = false;
      stopInterval();
      if (waveUpdate.value)
        endWave();
    });

    // ========== watch ==========

    // 채널 변경 감지
    watch(
      () => route.params.channel,
      async (newChannel, oldChannel) => {
        if (!isComponentActive.value) return;
        if (!newChannel) return;
        if (newChannel === oldChannel) return;
        
        console.log('채널 변경 감지:', oldChannel, '->', newChannel);
        
        await initializeForChannel(newChannel);
      }
    );

    // 탭 변경 감지
    watch(activeTab, async (newTab, oldTab) => {
        //console.log('=== activeTab watch 실행 ===', oldTab, '->', newTab);
        //console.trace(); // 호출 스택 확인
      if (isInitializing.value) return;
      
      // 먼저 모든 인터벌 정리
      stopAllIntervals();
      
      await nextTick();

      if (oldTab === 'Waveform' && waveUpdate.value) {
        await endWave();
      }

      if (newTab === 'Status') {
        startStatusInterval();
      }

      if (newTab === 'Harmonics') {
        await startInterval();
      }

      if (newTab === 'Waveform') {
        await startWave();
      }
    });

    return {
      t,
      sidebarOpen,
      channel,
      channelComputed,
      activeTab,
      tabs,
      selectedOptions,
      chartData,
      chartData2,
      chartData3,
      chartUpdateKey,
      linechartData,
      linechartData2,
      changeTab,
      mode1,
      mode2,
      mode3,
      tbdata,
      tbdataH,
      options,
      setbtnOption,
      btnOptions,
      fetchWave,
      selectChanged,
      assetName,
      startWave,
      endWave,
      waveUpdate,
      waveInterval,
      startWaveInterval,
      stopWaveInterval,
      stopAllIntervals,
      assetConfig,
      statusRefreshKey,
    };
  },
};
</script>
