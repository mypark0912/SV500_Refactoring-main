<template>
    <div class="col-span-full xl:col-span-12 space-y-4">
      
      <!-- 아코디언 1: 설비 진단 -->
      <AccordionBasic :title="'📊 ' + t('report.accordionTitle1')" :defaultOpen="true">
        <div class="space-y-4">
          <!-- 바 그래프 -->
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
          
          <!-- 상태 리포트 -->
          <div class="flex flex-col gap-4">
            <template v-for="item in equipmentItems" :key="item.Item.id">
              <StatusReport :data="item" />
            </template>
          </div>
          
          <!-- 트렌드 차트 -->
          <div class="grid grid-cols-12 gap-4">
            <div v-for="(option, idx) in equipmentChartOptions" :key="idx" class="col-span-6">
              <ReportTrend :data="option" />
            </div>
          </div>
        </div>
      </AccordionBasic>
  
      <!-- 아코디언 2: 전력품질 진단 -->
      <AccordionBasic :title="'⚡ ' + t('report.accordionTitle2')" :defaultOpen="true">
        <div class="space-y-4">
          <!-- 바 그래프 -->
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
          
          <!-- 상태 리포트 -->
          <div class="flex flex-col gap-4">
            <template v-for="item in pqItems" :key="item.Item.id">
              <StatusReport :data="item" />
            </template>
          </div>
          
          <!-- 트렌드 차트 -->
          <div class="grid grid-cols-12 gap-4">
            <div v-for="(option, idx) in pqChartOptions" :key="idx" class="col-span-6">
              <ReportTrend :data="option" />
            </div>
            <div v-if="equipmentEventData.length > 0" class="col-span-6">
              <ReportEventFault :data="equipmentEventData" />
            </div>
          </div>
        </div>
      </AccordionBasic>
  
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
  import ReportEventFault from './ReportEventFault.vue'
  import AccordionBasic from '../../../components/AccordionBasic_report.vue'
  import { useI18n } from 'vue-i18n'
  import { useInputDict } from "@/composables/useInputDict";
  
  export default {
    name: 'Report_Diagnosis',
    props:['channel'],
    components: {
      Diagnosis_Barchart,
      StatusReport,
      ReportTrend,
      ReportEventFault,
      AccordionBasic,
    },
    setup(props) {
      const { t, locale } = useI18n();
      const route = useRoute()
      const channel = ref(props.channel)
      const setupStore = useSetupStore();
      const asset = computed(() => setupStore.getAssetConfig);
      
      // 설비 진단 데이터
      const equipmentChartData = ref(null);
      const equipmentItems = ref([]);
      const equipmentChartOptions = ref([]);
      const equipmentEventData = ref([]);
      
      // 전력품질 진단 데이터
      const pqChartData = ref(null);
      const pqItems = ref([]);
      const pqChartOptions = ref([]);
      
      const today = ref(new Date());
      const weekAgo = computed(() => {
        const date = new Date()
        date.setDate(date.getDate() - 7)
        return date
      });
      
      const { formatToISOString } = useInputDict();
  
      // === 공통 함수 ===
      const setParamIds = async(assetName, datalist, type = 'diagnostic') => {
        const idList = [];
        try{
          const response = await axios.get(`/api/getParameters/${assetName}/${type}`);
          if (response.data.success) {
            const paramData = response.data.data;
            for(let i = 0 ; i < paramData.length ; i++){
              for(let j = 0; j < datalist.length; j++){
                if(paramData[i]["Name"] == datalist[j].Name && paramData[i]["AssemblyID"] == datalist[j].AssemblyID ){
                  idList.push({idx:paramData[i]["ID"], Assembly:paramData[i]["AssemblyID"], title:paramData[i]["Title"]});
                }
              }
            }
          }
        }catch (error){
          console.error(error);
        }
        return idList;
      }
  
      const setChartData = async (effectiveIds, Title) => {
        let option = {};
  
        const trendDataRequest = {
          ParametersIds: [effectiveIds],
          StartDate: formatToISOString(weekAgo.value, 0),
          EndDate: formatToISOString(today.value, 1),
        };
  
        try {
          const url = `/api/getTrendData`;
          const response = await axios.post(url, trendDataRequest, {
            headers: { "Content-Type": "application/json" },
          });
  
          if (response.data.success) {
            const resData = response.data.data;
            let datasets = [];
            let labels = [];
  
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
  
            if (resData.Thresholds && resData.Thresholds.length > 0 && labels.length > 0) {
              const ThresholdString = [
                "Out of Range(Down side)",
                "Repair",
                "Inspect",
                "Warning",
                "Warning",
                "Inspect",
                "Repair",
                "Out of Range(Upper side)",
              ];
  
              if(resData.Thresholds[0].Thresholds != null){
                const thresholdCount = resData.Thresholds[0].Thresholds.length;
              
                for (let idx = 0; idx < thresholdCount; idx++) {
                  const hasValidValue = resData.Thresholds.some(t => {
                    const value = t.Thresholds[idx];
                    return value !== "NaN" && value !== null && value !== undefined && typeof value === 'number';
                  });
  
                  if (!hasValidValue) continue;
  
                  const timeList = resData.Thresholds
                    .filter(t => {
                      const value = t.Thresholds[idx];
                      return value !== "NaN" && value !== null && value !== undefined && typeof value === 'number';
                    })
                    .map(t => ({
                      time: new Date(t.XAxis),
                      value: t.Thresholds[idx]
                    }))
                    .sort((a, b) => a.time - b.time);
  
                  if (timeList.length === 0) continue;
  
                  const thresholdData = labels.map((lbl) => {
                    const labelTime = new Date(lbl);
                    let applicableThreshold = timeList[0].value;
                    
                    for (let i = 0; i < timeList.length; i++) {
                      if (labelTime >= timeList[i].time) {
                        applicableThreshold = timeList[i].value;
                      } else {
                        break;
                      }
                    }
                    
                    return applicableThreshold;
                  });
  
                  datasets.push({
                    name: ThresholdString[idx],
                    data: thresholdData,
                    isThreshold: true,
                  });
                }
              }
            }
  
            option = {
              lineLabels: labels,
              lineData: datasets,
              lineTitle : Title,
            };
          } else {
            console.error("서버 오류:", response.data.error);
            option = {
              lineLabels: [],
              lineData: [],
              lineTitle : '',
            };
          }
        } catch (error) {
          console.error("요청 실패:", error);
        }
        return option;
      };
  
      const processTreeData = (treeItems) => {
        const items = [];
        const chartList = [];
        
        for(let i = 0 ; i< treeItems.length;i++){
          if(treeItems[i]["Status"] > 1 ){
            let childDict = [];
            if(treeItems[i]["children"].length > 0){
              for(let j = 0 ; j < treeItems[i]["children"].length ; j++ ){
                if(treeItems[i]["children"][j]["isSub"]){
                  for(let k = 0 ; k < treeItems[i]["children"][j]["children"].length ; k++ ){
                    if( treeItems[i]["children"][j]["children"][k]["Status"] > 1){
                      chartList.push(treeItems[i]["children"][j]["children"][k]);
                      childDict.push({
                        Title:treeItems[i]["children"][j]["children"][k]["Title"],
                        Assembly:treeItems[i]["children"][j]["AssemblyID"],
                        Value:treeItems[i]["children"][j]["children"][k]["Value"]
                      })
                    }
                  }
                }else{
                  if(treeItems[i]["children"][j]["Status"] > 1){
                    chartList.push(treeItems[i]["children"][j]);
                    childDict.push({
                      Title:treeItems[i]["children"][j]["Title"],
                      Assembly:treeItems[i]["children"][j]["AssemblyID"],
                      Value:treeItems[i]["children"][j]["Value"]
                    })
                  }
                }
              }
            }else{
              childDict = [{
                Title:treeItems[i]["Title"],
                Assembly:treeItems[i]["AssemblyID"],
                Value:treeItems[i]["Value"]
              }]
            }
            items.push({Item:treeItems[i], Child:childDict});            
          }
        }
        
        return { items, chartList };
      };
  
      // === 설비 진단 데이터 가져오기 ===

      // const fetchLastReportData = async() =>{
      //   const chName = channel.value == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;
      //   console.log('Asset:', chName);
      //   try {
      //     const response = await axios.get(`/report/lastReportData/diagnosis/${chName}`);
      //     console.log(response.data);
      //   }catch (error) {
      //     console.log("설비 진단 데이터 가져오기 실패:", error);
      //   }
  
      // }
      const fetchLastReportData = async () => {
  equipmentItems.value = [];
  equipmentChartOptions.value = [];
  const chName = channel.value == 'Main' ? asset.value.assetName_main : asset.value.assetName_sub;
  
  try {
    const response = await axios.get(`/report/lastReportData/diagnosis/${chName}`);
    
    if (response.data.success) {
      const { main, detail, timestamp } = response.data.data;
      
      // 1. 바 그래프용 데이터 변환
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
      equipmentChartData.value = { "Names": itemlist, "Values": valuelist, "Titles": datalist };

      // main을 item_name으로 인덱싱 (공백 제거 - detail 매칭용)
      const mainByName = {};
      for (let i = 0; i < main.length; i++) {
        const key = main[i].item_name.replace(/\s/g, '');
        mainByName[key] = main[i];
      }

      // 2. 세부항목 데이터 변환 (parent_name으로 그룹핑)
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

      // 3. equipmentItems 형식으로 변환
      const items = [];
      const chartList = [];
      
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
      
      equipmentItems.value = items;

      // 4. 차트 옵션 설정
      if (chartList.length > 0) {
        const effectiveIds = await setParamIds(chName, chartList, 'diagnostic');
        let idxList = [], idList = [];
        for (let i = 0; i < effectiveIds.length; i++) {
          if (idxList.includes(effectiveIds[i].idx)) {
            continue;
          } else {
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
      
      console.log('📊 Report Data 로드 완료:', timestamp);
    } else {
      console.log('No Report Data');
    }
  } catch (error) {
    console.log("설비 진단 데이터 가져오기 실패:", error);
  }
};
      const fetchEquipmentData = async () => {
        equipmentItems.value = [];
        equipmentChartOptions.value = [];
        const chName = channel.value == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;
        
        try {
          const response = await axios.get(`/api/getDiagnosisDetail/${chName}`);
  
          if (response.data.success) {
            let itemlist = [], valuelist=[], datalist=[];
            for(let i = 0; i < response.data.data_status.length;i++){
              itemlist.push(response.data.data_status[i]["Titles"][locale.value]);
              valuelist.push(response.data.data_status[i]["Status"]);
              datalist.push(response.data.data_status[i]["Titles"])
            }
            equipmentChartData.value = {"Names" : itemlist, "Values" : valuelist, "Titles": datalist};
  
            const treeItems = response.data.data_tree;
            const { items, chartList } = processTreeData(treeItems);
            equipmentItems.value = items;
  
            if(chartList.length > 0){
              const effectiveIds = await setParamIds(chName, chartList, 'diagnostic');
              let idxList=[],idList=[];
              for (let i = 0 ; i < effectiveIds.length;i++){
                if (idxList.includes(effectiveIds[i].idx)){
                  continue;
                }else{
                  idList.push(effectiveIds[i])
                  idxList.push(effectiveIds[i].idx)
                }
              }
              for (let i = 0 ; i < idList.length;i++){
                const titleName = '['+idList[i].Assembly + ']' + idList[i].title;
                const chartValue = await setChartData(idList[i].idx, titleName);
                equipmentChartOptions.value.push(chartValue);
              }
            }
          }else{
            console.log('No Equipment Data');
          }
        }catch (error) {
          console.log("설비 진단 데이터 가져오기 실패:", error);
        }
      };
  
      // === 전력품질 진단 데이터 가져오기 ===
      const fetchPQData = async () => {
        pqItems.value = [];
        pqChartOptions.value = [];
        const chName = channel.value == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;
        
        try {
          const response = await axios.get(`/api/getDiagPQ/${chName}`);
  
          if (response.data.success) {
            let itemlist = [], valuelist=[], datalist=[];
            for(let i = 0; i < response.data.data_status.length;i++){
              itemlist.push(response.data.data_status[i]["Titles"][locale.value]);
              valuelist.push(response.data.data_status[i]["Status"]);
              datalist.push(response.data.data_status[i]["Titles"])
            }
            pqChartData.value = {"Names" : itemlist, "Values" : valuelist, "Titles": datalist};
  
            const treeItems = response.data.data_tree;
            const { items, chartList } = processTreeData(treeItems);
            pqItems.value = items;
  
            if(chartList.length > 0){
              const effectiveIds = await setParamIds(chName, chartList, 'powerquality');
              let idxList=[],idList=[];
              for (let i = 0 ; i < effectiveIds.length;i++){
                if (idxList.includes(effectiveIds[i].idx)){
                  continue;
                }else{
                  idList.push(effectiveIds[i])
                  idxList.push(effectiveIds[i].idx)
                }
              }
              for (let i = 0 ; i < idList.length;i++){
                const titleName = '['+idList[i].Assembly + ']' + idList[i].title;
                const chartValue = await setChartData(idList[i].idx, titleName);
                pqChartOptions.value.push(chartValue);
              }
            }
          }else{
            console.log('No PQ Data');
          }
        }catch (error) {
          console.log("전력품질 진단 데이터 가져오기 실패:", error);
        }
      };
  
      // === 이벤트/결함 데이터 가져오기 (설비 진단용) ===
      const fetchEventData = async () => {
        const chName = channel.value == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;
        
        try {
          const response = await axios.get(`/api/getEvents/${chName}`);
          if (response.data.success) {
            const eventList = response.data.data_tree;
            for(let i = 0; i < eventList.length ; i++){
              if(eventList[i]["Status"] > 1){
                equipmentEventData.value.push(eventList[i]);
              }
            }
          }
        }catch (error) {
          console.log("이벤트 데이터 가져오기 실패:", error);
        }
  
        try {
          const response = await axios.get(`/api/getFaults/${chName}`);
          if (response.data.success) {
            const faultList = response.data.data_tree;
            for(let i = 0; i < faultList.length ; i++){
              if(faultList[i]["Status"] > 1){
                equipmentEventData.value.push(faultList[i]);
              }
            }
          }
        }catch (error) {
          console.log("결함 데이터 가져오기 실패:", error);
        }
      };
  
      onMounted(async () => {
        await Promise.all([
          //fetchLastReportData(),
          fetchEquipmentData(),
          fetchPQData(),
          fetchEventData()
        ]);
      });
  
      watch(() => route.params.channel, async(newChannel) => {
        channel.value = newChannel
        equipmentEventData.value = [];
        await Promise.all([
          //fetchLastReportData(),
          fetchEquipmentData(),
          fetchPQData(),
          fetchEventData()
        ]);
      });
  
      return {
        channel,
        asset,
        // 설비 진단
        equipmentChartData,
        equipmentItems,
        equipmentChartOptions,
        equipmentEventData,
        // 전력품질 진단
        pqChartData,
        pqItems,
        pqChartOptions,
        // 공통
        t,
        locale,
      }  
    }
  }
  </script>
  