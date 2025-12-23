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
              <h2 class="text-xl md:text-2xl text-gray-800 dark:text-gray-100 font-bold">
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
                  <!-- 콤보박스 -->
                  <div class="mt-2 mb-4 flex items-center gap-x-2">
                    <span>DriveType : {{ driveType }}</span>
                    <label class="sr-only" :for="tab.name + '-select'">
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

                  <!-- 차트 컨테이너 -->
                  <div class="flex flex-col space-y-4">
                    <!-- DOL: 3개 차트 표시 -->
                    <template v-if="driveType !== 'VFD'">
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
                    </template>
                    
                    <!-- VFD: 1개 차트 표시 -->
                    <template v-else>
                      <BarChart v-if="
                        activeTab === 'Harmonics' &&
                        tbdataH !== null &&
                        btnOptions === 'chart'
                      " :data="chartData" :width="600" :height="350" :mode="vfdChartMode"
                        :key="`harmonics-vfd-chart-${chartUpdateKey}`" />
                    </template>
                    
                    <PowerQ_Table v-if="
                      activeTab === 'Harmonics' &&
                      tbdataH !== null &&
                      btnOptions === 'table'
                    " :data="tbdataH" :option="selectedOptions.Harmonics" :driveType="driveType"
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
  },
  setup(props) {
    const { t } = useI18n();
    const route = useRoute();
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
    
    const options = computed(() => [
      { label: t("pq.Button.table"), value: "table" },
      { label: t("pq.Button.chart"), value: "chart" },
    ]);

    const chartData = ref({});
    const chartData2 = ref({});
    const chartData3 = ref({});
    const linechartData = ref({});
    const setupStore = useSetupStore();
    const linechartData2 = ref({});
    const waveUpdate = ref(false);
    const waveInterval = ref(null);
    let timeout_harmonics = 5;
    const w_mode = ref(0);
    const channelComputed = computed(
      () => props.channel || route.params.channel || "Default"
    );

    const assetName = computed(() => {
      const mainName = setupStore.getAssetConfig.assetName_main;
      const subName = setupStore.getAssetConfig.assetName_sub;
      if (channelComputed.value == 'Main' || channelComputed.value == 'main') {
        if (mainName != '') {
          return "(" + mainName + ")";
        } else {
          return "";
        }
      } else {
        if (subName != '') {
          return "(" + subName + ")";
        } else {
          return "";
        }
      }
    })

    const driveType = computed(()=>{
      if (channelComputed.value == 'Main' || channelComputed.value == 'main')
        return setupStore.getAssetConfig.assetdriveType_main;
      else
        return setupStore.getAssetConfig.assetdriveType_sub;
    })

    const asset = computed(()=>{
      if (channelComputed.value == 'Main' || channelComputed.value == 'main')
        return setupStore.getAssetConfig.assetName_main;
      else
        return setupStore.getAssetConfig.assetName_sub;
    });

    const assetType = computed(()=>{
      if (channelComputed.value == 'Main' || channelComputed.value == 'main')
        return setupStore.getAssetConfig.assetType_main;
      else
        return setupStore.getAssetConfig.assetType_sub;
    });

    // VFD 차트 모드 (전압/전류)
    const vfdChartMode = computed(() => {
      if (selectedOptions.Harmonics === 'voltage') {
        return w_mode.value === 0 ? 'Line Voltage' : 'Phase Voltage';
      } else {
        return 'Current';
      }
    });

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

    const waveMap = {
      voltage: ["Wave Form V1", "Wave Form V2", "Wave Form V3"],  // w_mode에 따라 동적 처리
      phaseVoltage: ["Wave Form V1", "Wave Form V2", "Wave Form V3"],
      lineVoltage: ["Wave Form V12", "Wave Form V23", "Wave Form V31"],
      current: ["Wave Form I1", "Wave Form I2", "Wave Form I3"],
    };
    
    const harmonicsMap = {
      phaseVoltage: ["U1", "U2", "U3"],
      lineVoltage: ["Upp1", "Upp2", "Upp3"],
      current: ["I1", "I2", "I3"],
    };

    // 선택된 옵션 저장
    const selectedOptions = reactive({
      Harmonics: "voltage",  // 기본값 변경
      Waveform: "voltage",   // 기본값 변경
    });

    const selectChanged = (tabName, selectedValue) => {
      selectedOptions[tabName] = selectedValue;
      updateChartByOption(tabName, selectedValue);
    };

    const updateChartByOption = async(tab, option) => {
      if (tab === "Waveform") {
        if (!tbdata.value) return;

        // w_mode에 따라 전압 키 결정
        let voltageKeys;
        if (option === 'voltage') {
          voltageKeys = w_mode.value === 0 
            ? waveMap.lineVoltage 
            : waveMap.phaseVoltage;
        } else {
          voltageKeys = waveMap[option] || waveMap.phaseVoltage;
        }

        const [k1, k2, k3] = voltageKeys;
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

        const [k11, k12, k13] = waveMap['current'] || [];
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

        // VFD인 경우
        if (driveType.value === 'VFD') {
          updateVfdChart(option);
        } 
        // DOL인 경우 (기존 로직)
        else {
          // option이 'voltage'인 경우 w_mode에 따라 변환
          let actualOption = option;
          if (option === 'voltage') {
            actualOption = w_mode.value === 0 ? 'lineVoltage' : 'phaseVoltage';
          }
          
          const [k1, k2, k3] = harmonicsMap[actualOption] || harmonicsMap.phaseVoltage;

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
        }

        chartUpdateKey.value++;
        await nextTick();
      }
    };

    // VFD 차트 업데이트 함수
    const updateVfdChart = (option) => {
      if (!tbdataH.value) return;

      // 백엔드에서 이미 추출된 배열 사용
      const harmonicsData = option === 'voltage' 
        ? tbdataH.value.voltage 
        : tbdataH.value.current;

      if (!harmonicsData || harmonicsData.length === 0) {
        console.log('하모닉스 데이터 없음');
        return;
      }

      chartData.value = {
        labels: Array.from({ length: 62 }, (_, i) => i + 2),
        datasets: [
          {
            label: option === 'voltage' ? 'Voltage Harmonics' : 'Current Harmonics',
            data: harmonicsData,
            backgroundColor: option === 'voltage' 
              ? tailwindConfig().theme.colors.violet[500]
              : tailwindConfig().theme.colors.sky[500],
            borderRadius: 4,
          },
        ],
      };
    };

    const fetchWave = async (ch) => {
      try {
        const response = await axios.get(`/api/getWave/${ch}`);
        if (response.data.success) {
          tbdata.value = { ...response.data.data };
          
          // 현재 선택된 옵션으로 차트 업데이트
          updateChartByOption('Waveform', selectedOptions.Waveform);
        } else {
          console.warn("서버 응답이 success: false 입니다.");
          tbdata.value = null;
        }
      } catch (error) {
        console.log("데이터 가져오기 실패:", error);
      }
    };

    // DOL용 fetchData
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

    // VFD용 fetchData
    const fetchDataVFD = async () => {
      try {
        if (!isComponentActive.value) return;

        const response = await axios.get(`/api/getRealTimeHarmonics/${channelComputed.value}/${asset.value}`);
        
        if (response.data && response.data.success) {
          if (!isComponentActive.value) return;

          tbdataH.value = response.data.data;
          updateChartByOption('Harmonics', selectedOptions.Harmonics);

          if(response.data.request){
            const res = await axios.get(`/setting/HarmTrigger/${channelComputed.value}`)
            if (res.success){
              console.warn("VFD Waveform file trigger 전송");
            }
          }
        } else {
          tbdataH.value = null;
        }
      } catch (error) {
        if (isComponentActive.value) {
          console.log("VFD 데이터 가져오기 실패:", error);
        }
      }
    };

    const fetchInterval = async () => {
      try {
        const response = await axios.get(`/api/getInteverval/sampling/${channelComputed.value}`);
        if (response.data.success) {
          timeout_harmonics = parseInt(response.data.data);
          //w_mode.value = response.data.w_mode;
        }
      } catch (error) {
        console.log("데이터 가져오기 실패:", error);
      }
    };

    const fetchChannels = async () => {
      try {
        const response = await axios.get(`/api/getChData/${channelComputed.value}`);
        if (response.data.success) {
          w_mode.value = parseInt(response.data.data["PT_WiringMode"]);
          //console.log(channelComputed.value,'- wmode:', w_mode.value);
        }
      } catch (error) {
        console.log("데이터 가져오기 실패:", error);
      }
    };

    const dataInterval = ref(null);
    const isComponentActive = ref(false);

    // 데이터 갱신 함수
    const refreshData = async () => {
      if (!isComponentActive.value) return;

      if (channel.value && activeTab.value === 'Harmonics') {
        if (driveType.value === 'VFD') {
          await fetchDataVFD();
        } else {
          await fetchData(channel.value);
        }
      }
    };

    // interval 시작 함수
    const startInterval = async() => {
      stopInterval();  // 먼저 기존 interval 정리
      
      if(driveType.value === 'VFD')
        await fetchInterval();  // 그 다음 timeout 가져오기
      
      console.log('harmonics -', timeout_harmonics);
      if (activeTab.value === 'Harmonics' && isComponentActive.value) {
        refreshData();
        dataInterval.value = setInterval(refreshData, timeout_harmonics * 1000);
      }
    };

    const stopInterval = () => {
      if (dataInterval.value) {
        clearInterval(dataInterval.value);
        dataInterval.value = null;
      }
    };

    const stopAllIntervals = () => {
      stopInterval();
      stopWaveInterval();
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

    const stopWaveInterval = () => {
      if (waveInterval.value) {
        clearInterval(waveInterval.value);
        waveInterval.value = null;
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

    onMounted(async() => {
      isComponentActive.value = true;
      await fetchChannels();
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
      if(waveUpdate.value)
        endWave();
    });

    watch(
      () => route.params.channel,
      async (newChannel) => {
        stopAllIntervals();
        
        if (waveUpdate.value) {
          await endWave();
        }
        
        channel.value = newChannel;
        
        chartData.value = {};
        chartData2.value = {};
        chartData3.value = {};
        linechartData.value = {};
        linechartData2.value = {};
        tbdata.value = null;
        tbdataH.value = null;
        
        // w_mode 다시 가져오기
        await fetchChannels();
        
        if (activeTab.value === 'Harmonics') {
          startInterval();
        } else if (activeTab.value === 'Waveform') {
          startWave();
        }
      },
      { immediate: true }
    );

    watch(activeTab, async (newTab, oldTab) => {
      await nextTick();

      if (oldTab === 'Waveform' && waveUpdate.value) {
        await endWave();
      }

      if (newTab === 'Harmonics') {
        startInterval();
      } else {
        stopInterval();
      }
      
      if (newTab === 'Waveform') {
        startWave();
      }
    });

    // 탭 정의 - voltage/current 2개 옵션
    const tabs = computed(() => [
      {
        name: "Harmonics",
        label: t("pq.tabs.harmonics"),
        options: [
          { key: "voltage", label: t("pq.options.voltage") },
          { key: "current", label: t("pq.options.current") },
        ],
      },
      {
        name: "Waveform",
        label: t("pq.tabs.waveform"),
        options: [
          { key: "voltage", label: t("pq.options.voltage") },
          { key: "current", label: t("pq.options.current") },
        ],
      },
    ]);

    const setbtnOption = (value) => {
      btnOptions.value = value;
      
      if (value === 'chart' && tbdataH.value) {
        updateChartByOption('Harmonics', selectedOptions.Harmonics);
      }
    };

    const changeTab = (tabName) => {
      activeTab.value = tabName;
    };

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
      driveType,
      asset,
      w_mode,
      vfdChartMode,
    };
  },
};
</script>