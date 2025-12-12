<template>
    <div class="col-span-full xl:col-span-12 space-y-4">
      
      <!-- 버튼 그룹 -->
      <div class="flex justify-start">
        <div class="inline-flex rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden">
          <button 
            @click="activeTab = 'diagnosis'"
            :class="[
              'px-6 py-2 text-sm font-medium transition-colors',
              activeTab === 'diagnosis' 
                ? 'bg-indigo-500 text-white' 
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            ]"
          >
            📊 {{ t('report.accordionTitle1') }}
          </button>
          <button 
            @click="activeTab = 'powerquality'"
            :class="[
              'px-6 py-2 text-sm font-medium transition-colors border-l border-gray-200 dark:border-gray-600',
              activeTab === 'powerquality' 
                ? 'bg-indigo-500 text-white' 
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            ]"
          >
            ⚡ {{ t('report.accordionTitle2') }}
          </button>
          <button 
            @click="activeTab = 'event'"
            :class="[
              'px-6 py-2 text-sm font-medium transition-colors border-l border-gray-200 dark:border-gray-600',
              activeTab === 'event' 
                ? 'bg-indigo-500 text-white' 
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            ]"
          >
            🔔 {{ t('report.accordionTitle3') }}
          </button>
          <button 
            @click="activeTab = 'fault'"
            :class="[
              'px-6 py-2 text-sm font-medium transition-colors border-l border-gray-200 dark:border-gray-600',
              activeTab === 'fault' 
                ? 'bg-indigo-500 text-white' 
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            ]"
          >
            🚨 {{ t('report.accordionTitle4') }}
          </button>
        </div>
      </div>
  
      <!-- 날짜/시간 선택 -->
      <div class="flex items-center justify-start gap-4">
        <input 
          type="date" 
          v-model="currentDate" 
          class="px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          @change="onDateChange"
        />
        <select 
          v-model="currentTime" 
          class="w-48 px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          :disabled="currentTimeOptions.length === 0"
          @change="onTimeChange"
        >
          <option v-if="currentTimeOptions.length === 0" value="">{{ t('report.noData') }}</option>
          <option v-for="time in currentTimeOptions" :key="time.value" :value="time.value">
            {{ time.label }}
          </option>
        </select>
      </div>
  
      <!-- 설비 진단 -->
      <div v-show="activeTab === 'diagnosis'" class="space-y-4">
        <div class="grid grid-cols-12">
          <Diagnosis_Barchart 
            v-if="equipmentChartData !== null" 
            :channel="channel" 
            :data="equipmentChartData" 
            :mode="'DiagnosisDetail'" 
            :height="300"
            class="col-span-12" 
          />
        </div>
        
        <div class="flex flex-col gap-4">
          <template v-for="item in equipmentItems" :key="item.Item.id">
            <StatusReport :data="item" />
          </template>
        </div>
        
        <div class="grid grid-cols-12 gap-4">
          <div v-for="(option, idx) in equipmentChartOptions" :key="idx" class="col-span-6">
            <ReportTrend :data="option" />
          </div>
        </div>
      </div>
  
      <!-- 전력품질 -->
      <div v-show="activeTab === 'powerquality'" class="space-y-4">
        <div class="grid grid-cols-12">
          <Diagnosis_Barchart 
            v-if="pqChartData !== null" 
            :channel="channel" 
            :data="pqChartData" 
            :mode="'PowerQuality'" 
            :height="300"
            class="col-span-12" 
          />
        </div>
        
        <div class="flex flex-col gap-4">
          <template v-for="item in pqItems" :key="item.Item.id">
            <StatusReport :data="item" />
          </template>
        </div>
        
        <div class="grid grid-cols-12 gap-4">
          <div v-for="(option, idx) in pqChartOptions" :key="idx" class="col-span-6">
            <ReportTrend :data="option" />
          </div>
        </div>
      </div>
  
      <!-- 이벤트 -->
      <div v-show="activeTab === 'event'" class="space-y-4">
        <div class="grid grid-cols-12">
          <Diagnosis_Barchart 
            v-if="eventChartData !== null" 
            :channel="channel" 
            :data="eventChartData" 
            :mode="'Event'" 
            :height="300"
            class="col-span-12" 
          />
        </div>
        
        <div class="flex flex-col gap-4">
          <template v-for="item in eventItems" :key="item.Item.id">
            <StatusReport :data="item" />
          </template>
        </div>
        
        <div v-if="eventChartData === null || eventChartData.Names.length === 0" class="text-gray-500 text-center py-8">
          {{ t('report.noEventData') }}
        </div>
      </div>
  
      <!-- 폴트 -->
      <div v-show="activeTab === 'fault'" class="space-y-4">
        <div class="grid grid-cols-12">
          <Diagnosis_Barchart 
            v-if="faultChartData !== null" 
            :channel="channel" 
            :data="faultChartData" 
            :mode="'Fault'" 
            :height="300"
            class="col-span-12" 
          />
        </div>
        
        <div class="flex flex-col gap-4">
          <template v-for="item in faultItems" :key="item.Item.id">
            <StatusReport :data="item" />
          </template>
        </div>
        
        <div v-if="faultChartData === null || faultChartData.Names.length === 0" class="text-gray-500 text-center py-8">
          {{ t('report.noFaultData') }}
        </div>
      </div>
  
    </div>
  </template>
  
  <script>
  import { ref, watch, computed, onMounted } from 'vue'
  import { useRoute } from 'vue-router'
  import { useSetupStore } from '@/store/setup';
  import axios from 'axios'
  import Diagnosis_Barchart from '../diagnosis/ReportBarChart.vue'
  import StatusReport from './StatusReport.vue'
  import ReportTrend from './ReportTrend.vue'
  import { useI18n } from 'vue-i18n'
  import { useInputDict } from "@/composables/useInputDict";
  
  export default {
    name: 'Report_Diagnosis',
    props: ['channel'],
    components: {
      Diagnosis_Barchart,
      StatusReport,
      ReportTrend,
    },
    setup(props) {
      const { t, locale } = useI18n();
      const route = useRoute();
      const channel = ref(props.channel);
      const setupStore = useSetupStore();
      const asset = computed(() => setupStore.getAssetConfig);
  
      const todayStr = new Date().toISOString().split('T')[0];
  
      // === 탭 ===
      const activeTab = ref('diagnosis');
  
      // === 각 탭별 날짜/시간 저장 ===
      const tabState = ref({
        diagnosis: { date: todayStr, time: '', timeOptions: [] },
        powerquality: { date: todayStr, time: '', timeOptions: [] },
        event: { date: todayStr, time: '', timeOptions: [] },
        fault: { date: todayStr, time: '', timeOptions: [] },
      });
  
      // === 현재 탭의 날짜/시간 ===
      const currentDate = computed({
        get: () => tabState.value[activeTab.value].date,
        set: (val) => { tabState.value[activeTab.value].date = val; }
      });
      const currentTime = computed({
        get: () => tabState.value[activeTab.value].time,
        set: (val) => { tabState.value[activeTab.value].time = val; }
      });
      const currentTimeOptions = computed(() => tabState.value[activeTab.value].timeOptions);
  
      // === 데이터 ===
      const equipmentChartData = ref(null);
      const equipmentItems = ref([]);
      const equipmentChartOptions = ref([]);
  
      const pqChartData = ref(null);
      const pqItems = ref([]);
      const pqChartOptions = ref([]);
  
      const eventChartData = ref(null);
      const eventItems = ref([]);
  
      const faultChartData = ref(null);
      const faultItems = ref([]);
  
      const today = ref(new Date());
      const weekAgo = computed(() => {
        const date = new Date();
        date.setDate(date.getDate() - 7);
        return date;
      });
  
      const { formatToISOString } = useInputDict();
  
      // === 시간 목록 조회 ===
      const fetchTimeOptions = async (date, mode) => {
        const chName = channel.value == 'Main' ? asset.value.assetName_main : asset.value.assetName_sub;
        
        try {
          const response = await axios.get(`/report/reportTimes/${date}/${chName}/${mode}`);
          if (response.data.success) {
            return response.data.data.map(time => ({
              value: time,
              label: time.split('T')[1]?.substring(0, 8) || time
            }));
          }
        } catch (error) {
          console.error(`${mode} 시간 목록 조회 실패:`, error);
        }
        return [];
      };
  
      // === 날짜 변경 ===
      const onDateChange = async () => {
        const mode = activeTab.value;
        const state = tabState.value[mode];
        
        state.timeOptions = await fetchTimeOptions(state.date, mode);
        
        if (state.timeOptions.length > 0) {
          state.time = state.timeOptions[0].value;
          await onTimeChange();
        } else {
          state.time = '';
          clearData(mode);
        }
      };
  
      // === 시간 변경 ===
      const onTimeChange = async () => {
        const mode = activeTab.value;
        const state = tabState.value[mode];
        
        if (!state.time) return;
        
        await fetchReportData(mode, state.time);
      };
  
      // === 데이터 초기화 ===
      const clearData = (mode) => {
        if (mode === 'diagnosis') {
          equipmentChartData.value = null;
          equipmentItems.value = [];
          equipmentChartOptions.value = [];
        } else if (mode === 'powerquality') {
          pqChartData.value = null;
          pqItems.value = [];
          pqChartOptions.value = [];
        } else if (mode === 'event') {
          eventChartData.value = null;
          eventItems.value = [];
        } else if (mode === 'fault') {
          faultChartData.value = null;
          faultItems.value = [];
        }
      };
  
      // === 탭 변경 시 ===
      watch(activeTab, async (newTab) => {
        const state = tabState.value[newTab];
        if (state.timeOptions.length === 0) {
          await onDateChange();
        }
      });
  
      // === 공통 함수 ===
      const setParamIds = async (assetName, datalist, type = 'diagnostic') => {
        const idList = [];
        try {
          const response = await axios.get(`/api/getParameters/${assetName}/${type}`);
          if (response.data.success) {
            const paramData = response.data.data;
            for (let i = 0; i < paramData.length; i++) {
              for (let j = 0; j < datalist.length; j++) {
                if (paramData[i]["Name"] == datalist[j].Name && paramData[i]["AssemblyID"] == datalist[j].AssemblyID) {
                  idList.push({ idx: paramData[i]["ID"], Assembly: paramData[i]["AssemblyID"], title: paramData[i]["Title"] });
                }
              }
            }
          }
        } catch (error) {
          console.error(error);
        }
        return idList;
      };
  
      const setChartData = async (effectiveIds, Title) => {
        let option = {};
        const trendDataRequest = {
          ParametersIds: [effectiveIds],
          StartDate: formatToISOString(weekAgo.value, 0),
          EndDate: formatToISOString(today.value, 1),
        };
  
        try {
          const response = await axios.post(`/api/getTrendData`, trendDataRequest, {
            headers: { "Content-Type": "application/json" },
          });
  
          if (response.data.success) {
            const resData = response.data.data;
            let datasets = [], labels = [];
  
            Object.keys(resData).forEach((key) => {
              if (key !== "Thresholds") {
                const dataPoints = resData[key].data;
                if (dataPoints && dataPoints.length > 0) {
                  if (labels.length === 0) {
                    labels = dataPoints.map((point) => point.XAxis);
                  }
                  datasets.push({
                    name: resData[key].Title,
                    data: dataPoints.map((point) => point.YAxis),
                    isThreshold: false,
                  });
                }
              }
            });
  
            // Threshold 처리
            if (resData.Thresholds && resData.Thresholds.length > 0 && labels.length > 0) {
              const ThresholdString = ["Out of Range(Down side)", "Repair", "Inspect", "Warning", "Warning", "Inspect", "Repair", "Out of Range(Upper side)"];
              if (resData.Thresholds[0].Thresholds != null) {
                const thresholdCount = resData.Thresholds[0].Thresholds.length;
                for (let idx = 0; idx < thresholdCount; idx++) {
                  const hasValidValue = resData.Thresholds.some(t => {
                    const value = t.Thresholds[idx];
                    return value !== "NaN" && value !== null && value !== undefined && typeof value === 'number';
                  });
                  if (!hasValidValue) continue;
  
                  const timeList = resData.Thresholds
                    .filter(t => t.Thresholds[idx] !== "NaN" && t.Thresholds[idx] !== null && typeof t.Thresholds[idx] === 'number')
                    .map(t => ({ time: new Date(t.XAxis), value: t.Thresholds[idx] }))
                    .sort((a, b) => a.time - b.time);
  
                  if (timeList.length === 0) continue;
  
                  const thresholdData = labels.map((lbl) => {
                    const labelTime = new Date(lbl);
                    let applicableThreshold = timeList[0].value;
                    for (let i = 0; i < timeList.length; i++) {
                      if (labelTime >= timeList[i].time) applicableThreshold = timeList[i].value;
                      else break;
                    }
                    return applicableThreshold;
                  });
  
                  datasets.push({ name: ThresholdString[idx], data: thresholdData, isThreshold: true });
                }
              }
            }
  
            option = { lineLabels: labels, lineData: datasets, lineTitle: Title };
          } else {
            option = { lineLabels: [], lineData: [], lineTitle: '' };
          }
        } catch (error) {
          console.error("요청 실패:", error);
        }
        return option;
      };
  
      // === InfluxDB 데이터 변환 ===
      const transformInfluxData = (main, detail) => {
        let itemlist = [], valuelist = [], datalist = [];
        for (let i = 0; i < main.length; i++) {
          const titleKey = `title_${locale.value}`;
          const displayName = main[i][titleKey] || main[i].title || main[i].item_name;
          itemlist.push(displayName);
          valuelist.push(main[i].status);
          datalist.push({
            en: main[i].title_en || main[i].item_name,
            ko: main[i].title_ko || main[i].item_name,
            ja: main[i].title_ja || main[i].item_name
          });
        }
        const chartData = { "Names": itemlist, "Values": valuelist, "Titles": datalist };
  
        const mainByName = {};
        for (let i = 0; i < main.length; i++) {
          const key = main[i].item_name.replace(/\s/g, '');
          mainByName[key] = main[i];
        }
  
        const groupedByParent = {};
        for (let i = 0; i < detail.length; i++) {
          const parentName = detail[i].parent_name;
          const parentKey = parentName.replace(/\s/g, '');
          
          if (!groupedByParent[parentName]) {
            const parentInfo = mainByName[parentKey] || {};
            groupedByParent[parentName] = {
              item_name: parentName,
              status: 0,
              Titles: {
                en: parentInfo.title_en || parentName,
                ko: parentInfo.title_ko || parentName,
                ja: parentInfo.title_ja || parentName
              },
              Descriptions: {
                en: parentInfo.description_en || '',
                ko: parentInfo.description_ko || '',
                ja: parentInfo.description_ja || ''
              },
              children: []
            };
          }
          if (detail[i].status > groupedByParent[parentName].status) {
            groupedByParent[parentName].status = detail[i].status;
          }
          groupedByParent[parentName].children.push(detail[i]);
        }
  
        const items = [], chartList = [];
        for (const parentName in groupedByParent) {
          const parent = groupedByParent[parentName];
          if (parent.status > 1) {
            const childDict = [];
            for (let j = 0; j < parent.children.length; j++) {
              const child = parent.children[j];
              if (child.status > 1) {
                chartList.push({
                  Name: child.item_name,
                  AssemblyID: child.assembly_id,
                  Status: child.status,
                  Value: child.value
                });
                const childTitle = child[`title_${locale.value}`] || child.title || child.item_name;
                childDict.push({
                  Title: childTitle,
                  Assembly: child.assembly_id,
                  Value: child.value !== undefined ? child.value : 'NaN'
                });
              }
            }
            if (childDict.length > 0) {
              items.push({
                Item: {
                  Name: parentName,
                  Title: parent.Titles[locale.value],
                  Titles: parent.Titles,
                  Descriptions: parent.Descriptions,
                  Status: parent.status
                },
                Child: childDict
              });
            }
          }
        }
  
        return { chartData, items, chartList };
      };
  
      // === 데이터 조회 ===
      const fetchReportData = async (mode, timestamp) => {
        const chName = channel.value == 'Main' ? asset.value.assetName_main : asset.value.assetName_sub;
        
        try {
          const response = await axios.get(`/report/reportDataByTime/${mode}/${chName}/${timestamp}`);
          
          if (response.data.success) {
            const { main, detail } = response.data.data;
            const { chartData, items, chartList } = transformInfluxData(main, detail);
            
            if (mode === 'diagnosis') {
              equipmentChartData.value = chartData;
              equipmentItems.value = items;
              equipmentChartOptions.value = [];
              
              if (chartList.length > 0) {
                const effectiveIds = await setParamIds(chName, chartList, 'diagnostic');
                let idxList = [], idList = [];
                for (let i = 0; i < effectiveIds.length; i++) {
                  if (!idxList.includes(effectiveIds[i].idx)) {
                    idList.push(effectiveIds[i]);
                    idxList.push(effectiveIds[i].idx);
                  }
                }
                for (let i = 0; i < idList.length; i++) {
                  const titleName = '[' + idList[i].Assembly + ']' + idList[i].title;
                  const chartValue = await setChartData(idList[i].idx, titleName);
                  equipmentChartOptions.value.push(chartValue);
                }
              }
            } else if (mode === 'powerquality') {
              pqChartData.value = chartData;
              pqItems.value = items;
              pqChartOptions.value = [];
              
              if (chartList.length > 0) {
                const effectiveIds = await setParamIds(chName, chartList, 'powerquality');
                let idxList = [], idList = [];
                for (let i = 0; i < effectiveIds.length; i++) {
                  if (!idxList.includes(effectiveIds[i].idx)) {
                    idList.push(effectiveIds[i]);
                    idxList.push(effectiveIds[i].idx);
                  }
                }
                for (let i = 0; i < idList.length; i++) {
                  const titleName = '[' + idList[i].Assembly + ']' + idList[i].title;
                  const chartValue = await setChartData(idList[i].idx, titleName);
                  pqChartOptions.value.push(chartValue);
                }
              }
            } else if (mode === 'event') {
              eventChartData.value = chartData;
              eventItems.value = items;
            } else if (mode === 'fault') {
              faultChartData.value = chartData;
              faultItems.value = items;
            }
          }
        } catch (error) {
          console.error(`${mode} 데이터 조회 실패:`, error);
        }
      };
  
      // === 초기 로드 ===
      onMounted(async () => {
        await onDateChange();
      });
  
      // === 채널 변경 ===
      watch(() => route.params.channel, async (newChannel) => {
        channel.value = newChannel;
        // 모든 탭 상태 초기화
        for (const key in tabState.value) {
          tabState.value[key].timeOptions = [];
          tabState.value[key].time = '';
        }
        await onDateChange();
      });
  
      return {
        channel,
        asset,
        t,
        locale,
        // 탭
        activeTab,
        // 날짜/시간
        currentDate,
        currentTime,
        currentTimeOptions,
        onDateChange,
        onTimeChange,
        // Diagnosis
        equipmentChartData,
        equipmentItems,
        equipmentChartOptions,
        // PQ
        pqChartData,
        pqItems,
        pqChartOptions,
        // Event
        eventChartData,
        eventItems,
        // Fault
        faultChartData,
        faultItems,
      };
    }
  }
  </script>