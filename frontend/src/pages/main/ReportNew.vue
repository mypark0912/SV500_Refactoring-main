<template>
  <div class="flex h-[100dvh] overflow-hidden">
    <!-- Sidebar -->
    <Sidebar
      :sidebarOpen="sidebarOpen"
      @close-sidebar="sidebarOpen = true"
      :channel="channel"
    />

    <!-- Content area -->
    <div
      class="relative flex flex-col flex-1 overflow-y-auto overflow-x-hidden"
    >
      <!-- Site header -->
      <Header
        :sidebarOpen="sidebarOpen"
        @toggle-sidebar="sidebarOpen = !sidebarOpen"
      />

      <main class="grow">
        <div class="px-2 sm:px-4 lg:px-6 py-4 w-full max-w-full">
          <!-- Dashboard actions -->
          <div class="sm:flex sm:justify-between sm:items-center mb-4">
            <!-- Left: Title -->
            <div class="mb-4 sm:mb-0">
              <h2
                class="text-lg md:text-xl text-gray-800 dark:text-gray-100 font-bold"
              >
                {{ t("report.sitemap.title") }} >
                {{
                  channelComputed == "Main"
                    ? t("report.sitemap.main")
                    : t("report.sitemap.sub")
                }}
              </h2>
            </div>
          </div>

          <!-- 다운로드 모달 -->
          <div
            v-if="showDownloadModal"
            class="fixed inset-0 z-50 flex items-center justify-center"
          >
            <div
              class="absolute inset-0 bg-black/50"
              @click="!isDownloading && closeDownloadModal()"
            ></div>
            <div
              class="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4 p-6"
            >
              <div class="flex items-center gap-3 mb-4">
                <div
                  class="w-10 h-10 bg-violet-100 dark:bg-violet-900/30 rounded-full flex items-center justify-center"
                >
                  <svg
                    class="w-5 h-5 text-violet-600 dark:text-violet-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <h3 class="text-lg font-bold text-gray-900 dark:text-white">
                  {{ t("report.modal.weeklyReport") || "통합 주간 리포트 다운로드" }}
                </h3>
              </div>

              <div
                class="mb-6 text-sm text-gray-600 dark:text-gray-300 space-y-3"
              >
                <p>
                  {{ t("report.modal.weeklyReportDesc") || "선택한 주간의 모든 데이터를 통합한 Word 문서를 다운로드합니다." }}
                </p>
                
                <!-- 포함 내용 -->
                <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                  <p class="font-medium text-gray-800 dark:text-gray-200 mb-2">
                    {{ t("report.modal.downloadIncludes") || "포함 내용:" }}
                  </p>
                  <div class="grid grid-cols-2 gap-2 text-sm">
                    <div class="flex items-center gap-2 text-gray-600 dark:text-gray-100">
                      <svg class="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      {{ t("report.modal.assetInfo") || "설비 정보" }}
                    </div>
                    <div class="flex items-center gap-2 text-gray-600 dark:text-gray-100">
                      <svg class="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      {{ t("report.modal.equipmentDiag") || "설비 진단" }}
                    </div>
                    <div class="flex items-center gap-2 text-gray-600 dark:text-gray-100">
                      <svg class="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      {{ t("report.modal.pqDiag") || "전력품질 진단" }}
                    </div>
                    <div class="flex items-center gap-2 text-gray-600 dark:text-gray-100">
                      <svg class="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      {{ t("report.modal.en50160") || "EN50160 분석" }}
                    </div>
                    <div class="flex items-center gap-2 text-gray-600 dark:text-gray-100">
                      <svg class="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      {{ t("report.modal.energyAnalysis") || "전력량 분석" }}
                    </div>
                    <div class="flex items-center gap-2 text-gray-600 dark:text-gray-100">
                      <svg class="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      {{ t("report.modal.trendCharts") || "트렌드 차트" }}
                    </div>
                  </div>
                </div>
                
                <!-- 기준 날짜 -->
                <div class="flex items-center gap-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <span class="text-blue-600 dark:text-blue-400">📅</span>
                  <span class="text-blue-700 dark:text-blue-300">
                    {{ t("report.modal.downloadDate") || "기준 날짜" }}: 
                    <span class="font-semibold">{{ formatDateStr(selectedReport) }}</span>
                  </span>
                </div>
              </div>

              <!-- 로딩 상태 -->
              <div
                v-if="isDownloading"
                class="mb-4 p-4 bg-amber-50 dark:bg-amber-900/30 rounded-lg"
              >
                <div class="flex items-center gap-3">
                  <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-amber-500"></div>
                  <div>
                    <p class="text-sm font-medium text-amber-700 dark:text-amber-400">
                      {{ t("report.modal.generating") || "리포트 생성 중..." }}
                    </p>
                    <p class="text-xs text-amber-600 dark:text-amber-500 mt-0.5">
                      {{ t("report.modal.generatingDesc") || "차트와 데이터를 처리하고 있습니다. 잠시만 기다려주세요." }}
                    </p>
                  </div>
                </div>
                <!-- 프로그레스 바 (애니메이션) -->
                <div class="mt-3 w-full bg-amber-200 dark:bg-amber-800 rounded-full h-1.5 overflow-hidden">
                  <div class="bg-amber-500 h-1.5 rounded-full animate-pulse" style="width: 70%"></div>
                </div>
              </div>

              <!-- 버튼 -->
              <div class="flex justify-end gap-3">
                <button
                  @click="closeDownloadModal"
                  :disabled="isDownloading"
                  class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {{ t("report.modal.cancel") || "취소" }}
                </button>
                <button
                  @click="downloadWeeklyReport"
                  :disabled="isDownloading || !selectedReport"
                  class="px-4 py-2 text-sm font-medium bg-violet-500 text-white rounded-lg hover:bg-violet-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  <svg
                    v-if="!isDownloading"
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  <span v-if="isDownloading">{{ t("report.modal.downloading") || "다운로드 중..." }}</span>
                  <span v-else>{{ t("report.modal.confirmDownload") || "다운로드" }}</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Cards -->
          <div class="grid grid-cols-12 gap-6">
            <!-- 설비 정보 카드 -->
            <Report_Info
              v-if="mode"
              :channel="channelComputed"
              :mode="mode"
              :key="`info-${channelComputed}`"
            />

            <!-- 탭 영역 -->
            <div class="col-span-full xl:col-span-12 bg-white dark:bg-gray-800 shadow-sm rounded-xl">
              
              <!-- Tab Navigation + 툴바 -->
              <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <div class="flex items-center justify-between flex-wrap gap-3">
                  <!-- 왼쪽: 탭 버튼들 -->
                  <ul class="text-sm font-medium flex flex-nowrap overflow-x-auto no-scrollbar -mb-px">
                    <li v-for="(tab, index) in tabs" :key="index" class="mr-1 last:mr-0">
                      <button
                        @click="changeTab(tab.name)"
                        class="relative px-5 py-3 whitespace-nowrap transition-all duration-200 ease-in-out rounded-t-lg border-b-2"
                        :class="activeTab === tab.name
                          ? 'text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-900/20 border-violet-500 font-semibold'
                          : 'text-gray-500 dark:text-gray-100 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700/50 border-transparent cursor-pointer'">
                        {{ t(`report.cardTitle.${tab.label}`) }}
                        <span 
                          v-if="activeTab === tab.name" 
                          class="absolute bottom-0 left-0 right-0 h-0.5 bg-violet-500 rounded-full"
                        ></span>
                      </button>
                    </li>
                  </ul>
                  
                  <!-- 오른쪽: 보고서 조회 툴바 -->
                  <div class="flex items-center gap-3 flex-wrap">
                    <span class="text-sm font-medium text-gray-600 dark:text-gray-100">
                      {{ t('report.searchReport') || '보고서 조회' }}
                    </span>
                    
                    <select 
                      v-model="selectedReport"
                      class="w-48 px-3 py-1.5 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    >
                      <option value="">{{ t('report.selectReport') || '선택하세요' }}</option>
                      <option v-for="date in reportDates" :key="date" :value="date">
                        {{ formatDateStr(date) }}
                      </option>
                    </select>
                    
                    <!-- Load 버튼 -->
                    <button 
                      @click="onLoadClick"
                      :disabled="!selectedReport || isLoading"
                      class="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                      <svg v-if="isLoading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      {{ t('report.load') || 'Load' }}
                    </button>
                    
                    <!-- Download 버튼 -->
                    <button 
                      @click="openDownloadModal"
                      :disabled="!selectedReport || isDownloading"
                      class="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-violet-500 text-white rounded-lg hover:bg-violet-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      {{ t('report.modal.download') || 'Download' }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- Tab Content -->
              <div class="text-gray-700 dark:text-white text-left pt-3 px-4 pb-4">
                <div class="flex flex-col space-y-2">
                  
                  <!-- 설비 진단 -->
                  <Report_Diagnosis
                    v-if="activeTab === 'Equipment' && mode"
                    ref="diagnosisRef"
                    :channel="channelComputed"
                    :mode="'diagnosis'"
                    :reportData="diagnosisReportData"
                    :key="`diag-${channelComputed}`"
                  />
                  
                  <!-- 전력품질 진단 -->
                  <Report_Diagnosis
                    v-if="activeTab === 'PowerQuality'"
                    ref="pqDiagnosisRef"
                    :channel="channelComputed"
                    :mode="'powerquality'"
                    :reportData="pqReportData"
                    :key="`pq-diag-${channelComputed}`" 
                  />
                  
                  <!-- EN50160 보고서 -->
                  <ReportComponent 
                    v-if="activeTab === 'EN50160'" 
                    :data="tbdata" 
                    :channel="channelComputed" 
                    :mode="mode"
                    :reportData="en50160ReportData"
                    :key="`component-${channelComputed}-${selectedReport}`" 
                  />
                  
                  <!-- 전력량 -->
                  <Report_WattHour 
                    v-if="activeTab === 'Energy'" 
                    :mode="mode" 
                    :channel="channelComputed" 
                    :key="`wh-${channelComputed}`" 
                  />
                  
                </div>
              </div>

            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  </div>
</template>

<script>
import { ref, watch, computed, onMounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import { useSetupStore } from "@/store/setup";
import axios from "axios";
import Sidebar from "../common/SideBar3.vue";
import Header from "../common/Header.vue";
import Footer from "../common/Footer.vue";
import ReportComponent from "../../partials/inners/report/ReportComponent.vue";
import Report_WattHour from "../../partials/inners/report/Report_WattHour.vue";
import Report_Diagnosis from "../../partials/inners/report/Report_Diagnosis_New.vue";
import Report_Info from "../../partials/inners/report/Report_Info.vue";
import { useI18n } from "vue-i18n";

export default {
  name: "Report",
  props: ["channel"],
  components: {
    Sidebar,
    Header,
    Footer,
    ReportComponent,
    Report_WattHour,
    Report_Diagnosis,
    Report_Info,
  },
  setup(props) {
    const { t, locale } = useI18n();
    const route = useRoute();
    const sidebarOpen = ref(true);
    const channel = ref(props.channel);
    const setupStore = useSetupStore();
    const channelComputed = computed(
      () => props.channel || route.params.channel || "Default"
    );
    const asset = computed(() => setupStore.getAssetConfig);
    const selectedReport = ref("");
    const reportDates = ref([]);
    const todayStr = new Date().toISOString().split("T")[0];

    // === 상태 ===
    const tbdata = ref([]);
    const activeTab = ref("Equipment");
    const isLoading = ref(false);
    const isDownloading = ref(false);
    const showDownloadModal = ref(false);

    // === PQ 정렬 순서 정의 ===
    const pqDisplayOrder = [
      'VoltagePhaseAngle',
      'VoltageRMS',
      'DC',
      'CurrentRMS',
      'CurrentPhaseAngle',
      'CrestFactor',
      'Unbalance',
      'Harmonics',
      'ZeroSequence',
      'NegativeSequence',
      'Power',
      'PowerFactor',
      'TotalDemandDistortion',
      'PhaseAngle',
      'Events',
    ];

    const sortByOrder = (arr, orderList) => {
      if (!arr || !Array.isArray(arr)) return arr;
      return [...arr].sort((a, b) => {
        const nameA = a.item_name || a.Name || '';
        const nameB = b.item_name || b.Name || '';
        const indexA = orderList.indexOf(nameA);
        const indexB = orderList.indexOf(nameB);
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        return indexA - indexB;
      });
    };

    // === 날짜/시간 상태 (탭별 분리) ===
    const tabState = ref({
      Equipment: { date: todayStr, time: "", timeOptions: [], displayTime: null },
      PowerQuality: { date: todayStr, time: "", timeOptions: [], displayTime: null },
    });

    const currentDate = computed({
      get: () => tabState.value[activeTab.value]?.date || todayStr,
      set: (val) => { if (tabState.value[activeTab.value]) tabState.value[activeTab.value].date = val; },
    });
    const currentTime = computed({
      get: () => tabState.value[activeTab.value]?.time || "",
      set: (val) => { if (tabState.value[activeTab.value]) tabState.value[activeTab.value].time = val; },
    });
    const currentTimeOptions = computed(() => tabState.value[activeTab.value]?.timeOptions || []);
    const displayTimestamp = computed(() => tabState.value[activeTab.value]?.displayTime || null);

    // === 리포트 데이터 (탭별 분리) ===
    const diagnosisReportData = ref({ main: [], detail: [], trends: null, timestamp: null });
    const pqReportData = ref({ main: [], detail: [], trends: null, timestamp: null });
    const en50160ReportData = ref(null);

    const diagnosisRef = ref(null);
    const pqDiagnosisRef = ref(null);

    const channelStatus = computed(() => setupStore.getChannelSetting);
    const setupMenu = ref({});

    const mode = computed(() => {
      if (channelComputed.value === "Main")
        return channelComputed.value === "Main" && setupMenu.value.MainDiagnosis;
      else
        return channelComputed.value === "Sub" && setupMenu.value.SubDiagnosis;
    });

    const tabs = computed(() => {
      if (mode.value) {
        return [
          { name: "Equipment", label: "Diagnosis" },
          { name: "PowerQuality", label: "PowerQuality" },
          { name: "EN50160", label: "EN50160" },
          { name: "Energy", label: "Energy" },
        ];
      } else {
        return [
          { name: "EN50160", label: "EN50160" },
          { name: "Energy", label: "Energy" },
        ];
      }
    });

    const formatTimestamp = (timestamp) => {
      if (!timestamp) return "";
      const date = new Date(timestamp);
      return date.toLocaleString(navigator.language, {
        year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit", second: "2-digit",
      });
    };

    const formatDateStr = (dateStr) => {
      if (!dateStr || dateStr.length !== 8) return dateStr;
      return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
    };

    const getCurrentMode = () => {
      return activeTab.value === "Equipment" ? "diagnosis" : "powerquality";
    };

    const fetchTimeOptions = async (date, modeType) => {
      const chName = channelComputed.value == "Main"
        ? asset.value.assetName_main
        : asset.value.assetName_sub;

      try {
        const response = await axios.get(`/report/reportTimes/${date}/${chName}/${modeType}`);
        if (response.data.success) {
          return response.data.data.map((time) => ({
            value: time,
            label: time.split("T")[1]?.substring(0, 8) || time,
          }));
        }
      } catch (error) {
        console.error("시간 목록 조회 실패:", error);
      }
      return [];
    };

    const fetchLastSavedData = async (modeType) => {
      const chName = channelComputed.value == "Main"
        ? asset.value.assetName_main
        : asset.value.assetName_sub;

      try {
        const response = await axios.get(`/report/lastReportData/${modeType}/${chName}`);
        if (response.data.success) {
          let data = response.data.data;
          if (modeType === 'powerquality' && data) {
            data.main = sortByOrder(data.main, pqDisplayOrder);
            data.detail = sortByOrder(data.detail, pqDisplayOrder);
          }
          return data;
        }
      } catch (error) {
        console.error("마지막 저장 데이터 조회 실패:", error);
      }
      return null;
    };

    const onDateChange = async () => {
      const modeType = getCurrentMode();
      const state = tabState.value[activeTab.value];
      state.timeOptions = await fetchTimeOptions(state.date, modeType);
      if (state.timeOptions.length > 0) {
        state.time = state.timeOptions[0].value;
      } else {
        state.time = "";
      }
    };

    // === Load 버튼 클릭 ===
    const onLoadClick = async () => {
      if (!selectedReport.value) return;

      isLoading.value = true;
      
      const chName = channelComputed.value == "Main"
        ? asset.value.assetName_main
        : asset.value.assetName_sub;

      try {
        if (mode.value) {
          // Diagnosis 데이터 조회
          try {
            const diagResponse = await axios.get(
              `/report/getReportDiagnosis/diagnosis/${chName}/${channelComputed.value}/${selectedReport.value}`
            );
            if (diagResponse.data.success) {
              diagnosisReportData.value = {
                main: diagResponse.data.data.main,
                detail: diagResponse.data.data.detail,
                trends: diagResponse.data.data.trends,
                timestamp: diagResponse.data.data.timestamp,
              };
              tabState.value.Equipment.displayTime = diagResponse.data.data.timestamp;
            }
          } catch (diagError) {
            console.warn("Diagnosis 데이터 조회 실패:", diagError);
          }

          // PowerQuality 데이터 조회
          try {
            const pqResponse = await axios.get(
              `/report/getReportDiagnosis/powerquality/${chName}/${channelComputed.value}/${selectedReport.value}`
            );
            if (pqResponse.data.success) {
              const sortedMain = sortByOrder(pqResponse.data.data.main || [], pqDisplayOrder);
              const sortedDetail = sortByOrder(pqResponse.data.data.detail || [], pqDisplayOrder);
              pqReportData.value = {
                main: sortedMain,
                detail: sortedDetail,
                trends: pqResponse.data.data.trends,
                timestamp: pqResponse.data.data.timestamp,
              };
              tabState.value.PowerQuality.displayTime = pqResponse.data.data.timestamp;
            }
          } catch (pqError) {
            console.warn("PowerQuality 데이터 조회 실패:", pqError);
          }
        }

        // EN50160 데이터 조회
        try {
          const filename = `en50160_weekly_${selectedReport.value}.parquet`;
          const en50160Response = await axios.get(`/report/week/${channelComputed.value}/${filename}`);
          if (en50160Response.data) {
            en50160ReportData.value = en50160Response.data;
            //console.log(en50160ReportData.value);
          }
        } catch (en50160Error) {
          console.warn("EN50160 데이터 조회 실패:", en50160Error);
          en50160ReportData.value = null;
        }
      } catch (error) {
        console.error("데이터 조회 실패:", error);
      }
      
      isLoading.value = false;
    };

    const fetchReportData = async (timestamp) => {
      const chName = channelComputed.value == "Main"
        ? asset.value.assetName_main
        : asset.value.assetName_sub;
      const modeType = getCurrentMode();

      try {
        const response = await axios.get(`/report/reportDataByTime/${modeType}/${chName}/${timestamp}`);
        if (response.data.success) {
          let mainData = response.data.data.main;
          let detailData = response.data.data.detail;

          if (modeType === 'powerquality') {
            mainData = sortByOrder(mainData, pqDisplayOrder);
            detailData = sortByOrder(detailData, pqDisplayOrder);
          }

          const data = { main: mainData, detail: detailData, timestamp: timestamp };

          if (activeTab.value === "Equipment") {
            diagnosisReportData.value = data;
          } else {
            pqReportData.value = data;
          }
        }
      } catch (error) {
        console.error("데이터 조회 실패:", error);
      }
    };

    const initialLoad = async () => {
      const modeType = getCurrentMode();
      const state = tabState.value[activeTab.value];

      isLoading.value = true;

      state.timeOptions = await fetchTimeOptions(state.date, modeType);

      if (state.timeOptions.length > 0) {
        state.time = state.timeOptions[0].value;
        await fetchReportData(state.time);
        state.displayTime = state.time;
      } else {
        state.time = "";
        const lastData = await fetchLastSavedData(modeType);
        if (lastData && lastData.timestamp) {
          state.displayTime = lastData.timestamp;
          const data = { main: lastData.main, detail: lastData.detail, timestamp: lastData.timestamp };
          if (activeTab.value === "Equipment") {
            diagnosisReportData.value = data;
          } else {
            pqReportData.value = data;
          }
        }
      }

      isLoading.value = false;
    };

    const changeTab = async (tabName) => {
      activeTab.value = tabName;
      if (mode.value) {
        if (tabName === "Equipment" || tabName === "PowerQuality") {
          const targetData = tabName === "Equipment" ? diagnosisReportData.value : pqReportData.value;
          if (!targetData.main || targetData.main.length === 0) {
            await initialLoad();
          }
        }
      }
    };

    // === 다운로드 모달 ===
    const openDownloadModal = () => {
      showDownloadModal.value = true;
    };

    const closeDownloadModal = () => {
      if (!isDownloading.value) {
        showDownloadModal.value = false;
      }
    };

    // === 통합 주간 리포트 다운로드 ===
    const downloadWeeklyReport = async () => {
      if (!selectedReport.value) return;

      isDownloading.value = true;

      try {
        const chName = channelComputed.value == "Main"
          ? asset.value.assetName_main
          : asset.value.assetName_sub;

        // 통합 주간 리포트 API 호출
        const response = await axios.get(
          `/report/downloadWeeklyReport/${channelComputed.value}/${selectedReport.value}`,
          {
            params: {
              locale: locale.value,
              asset_name: chName
            },
            responseType: "blob",
            timeout: 120000  // 2분 타임아웃 (리포트 생성에 시간이 걸릴 수 있음)
          }
        );

        // 파일 다운로드
        const blob = new Blob([response.data], {
          type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `weekly_report_${channelComputed.value}_${selectedReport.value}.docx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        closeDownloadModal();
      } catch (error) {
        console.error("리포트 다운로드 실패:", error);
        
        // 에러 메시지 표시
        let errorMessage = t("report.downloadError") || "다운로드에 실패했습니다.";
        if (error.code === 'ECONNABORTED') {
          errorMessage = t("report.downloadTimeout") || "리포트 생성 시간이 초과되었습니다. 다시 시도해주세요.";
        }
        alert(errorMessage);
      } finally {
        isDownloading.value = false;
      }
    };

    const fetchEN50160Data = async () => {
      try {
        const res = await fetch("/en50160_info.json");
        const data = await res.json();
        tbdata.value = [...data.tbdata];
      } catch (error) {
        console.log("EN50160 데이터 가져오기 실패:", error);
      }
    };

    const fetchDates = async () => {
      try {
        const response = await axios.get(`/report/list/${channelComputed.value}`);
        if (response.data.success) {
          reportDates.value = response.data.data;
          if (reportDates.value.length > 0) {
            selectedReport.value = reportDates.value[0];
          }
        } else {
          reportDates.value = [];
        }
      } catch (error) {
        console.log("데이터 가져오기 실패:", error);
        reportDates.value = [];
      }
    };

    // === Watch ===
    watch(
      () => route.params.channel,
      async (newChannel) => {
        channel.value = newChannel;
        tabState.value = {
          Equipment: { date: todayStr, time: "", timeOptions: [], displayTime: null },
          PowerQuality: { date: todayStr, time: "", timeOptions: [], displayTime: null },
        };
        diagnosisReportData.value = { main: [], detail: [], trends: null, timestamp: null };
        pqReportData.value = { main: [], detail: [], trends: null, timestamp: null };
        en50160ReportData.value = null;
        
        await fetchDates();
        if (mode.value) await initialLoad();
      }
    );

    watch(channelStatus, (newVal) => { setupMenu.value = newVal; }, { immediate: true });

    watch(mode, async (newVal) => {
      if (newVal) {
        activeTab.value = "Equipment";
        await initialLoad();
      } else {
        activeTab.value = "PowerQuality";
      }
    });

    // === Mounted ===
    onMounted(async () => {
      await setupStore.checkSetting();
      await fetchDates();
      await fetchEN50160Data();
      if (mode.value) await initialLoad();
    });

    return {
      tabs,
      sidebarOpen,
      channel,
      tbdata,
      channelComputed,
      mode,
      t,
      activeTab,
      changeTab,
      currentDate,
      currentTime,
      currentTimeOptions,
      displayTimestamp,
      onDateChange,
      onLoadClick,
      formatTimestamp,
      formatDateStr,
      isLoading,
      isDownloading,
      showDownloadModal,
      openDownloadModal,
      closeDownloadModal,
      downloadWeeklyReport,
      diagnosisReportData,
      pqReportData,
      en50160ReportData,
      diagnosisRef,
      pqDiagnosisRef,
      asset,
      selectedReport,
      reportDates,
    };
  },
};
</script>

<style>
@import "../../css/card-styles.css";
</style>
