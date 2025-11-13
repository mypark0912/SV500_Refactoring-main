<template>
    <div class="premium-dashboard-card">
     <div class="card-header">
     <header class="header-content">
       <h2 class="card-title">{{ t('dashboard.diagnosis.title') }}</h2>
       <div align="right" class="channel-info">
         <span class="channel-text">
           {{ channel == 'main' ? t('dashboard.diagnosis.subtitle_main'):t('dashboard.diagnosis.subtitle_sub') }}
         </span>
       </div>
     </header>
     </div>
     <div class="summary-section">
           <div v-if="DiagEnable" class="mb-4">
           <!--0StatusItem v-if="assetTypes !== 'Transformer'" :channel="channel" :data="stData" :mode="'diagnosis'" />
           <StatusItem2 v-if="assetTypes == 'Transformer' && Object.keys(transData).length > 0" :channel="channel" :data="stData" :transData="transData" /-->
           <StatusItem2 v-if="Object.keys(transData).length > 0" :channel="channel" :data="stData" :transData="transData" />
          </div>
          <div class="grid grid-cols-12 gap-4">
                <StatusItem v-if="DiagEnable" :channel="channel" :data="stData" :mode="'diagnosis'" />
                <StatusItem v-if="DiagEnable" :channel="channel" :data="pqData" :mode="'pq'" />
          </div>
     </div>
   </div>
 </template>
 
 <script>
 import { ref, computed,watchEffect, onMounted, onUnmounted, watch, inject } from 'vue'
 //import Notification from '../../components/Notification.vue'
 import StatusItem from './StatusItem_Claude2.vue'
 import StatusItem2 from './EquipItem.vue'
  //import AlarmItem from '../job/AlarmItem.vue'
 //import DashboardCard_NotFound from './DashboardCard_NotFound.vue'
 import { useSetupStore } from '@/store/setup'; // ✅ Pinia Store 사용
 import axios from 'axios'
 import { useI18n } from 'vue-i18n'  // ✅ 추가
 import { useRealtimeStore } from '@/store/realtime' 
 export default {
   name: 'DashboardCard04',
   props: {
     channel: String
   },
   components: {
     //Notification,
     StatusItem,
     StatusItem2,
     //AlarmItem,
     //DashboardCard_NotFound,
   },
   setup(props) {
     const { t } = useI18n();
     
     const channel = ref(props.channel);
     
     const stData = ref({
       devName:'',
       devType:'',
       devStatus: -2,
       devNickname : '',
       Ig: 0,
       runhour: 0,
     });
     const pqData = ref({
       devName:'',
       devStatus: -2
     });
     const DiagEnable = ref(false);
     const setupStore = useSetupStore();
     const channelStatus = computed(() => setupStore.getChannelSetting);
     const asset = computed(() => setupStore.getAssetConfig);
     const assetTypes = ref('');
     const status = ref('Normal');
     const alarmContext = ref('');
     const store = useRealtimeStore()
     const data = ref([]);

     const meterDictMain = computed(() => {          
      return store.getChannelData('Main') || {}
     })
     const meterDictSub = computed(() => {
      return store.getChannelData('Sub') || {}
     })
 
     


     //const alarmEnable = ref(false);
     let updateInterval = null;

     const transData = ref({});
 
     const fetchData = async () => {
          if (!asset.value || (!asset.value.assetName_main && !asset.value.assetName_sub)) {
            console.log("⏳ asset 준비 안됨. fetchData 대기중");
            console.log(asset.value);
            return;
          }
         const chName = channel.value == 'main'? asset.value.assetName_main : asset.value.assetName_sub;
         const chType = channel.value == 'main'? asset.value.assetType_main : asset.value.assetType_sub;
         const chNick = channel.value == 'main'? asset.value.assetNickname_main : asset.value.assetNickname_sub;
         if(chName != ''){

           try {
             const response = await axios.get(`/api/getStatus/${chName}/${channel.value}`);
              //console.log(response.data.status);
             if (response.data.status >= 0) {
                stData.value.devName = chName;
                stData.value.devType = chType;
                stData.value.devStatus = response.data.status;
                stData.value.devNickname = chNick;
                stData.value.runhour = response.data.runhours;
                if(assetTypes.value.includes('Transformer')){                 
                    if (channel.value === 'main') {
                      transData.value = { Temp: meterDictMain.value.Temp, Ig: meterDictMain.value.Ig, Stotal:meterDictMain.value.S4 }
                    } else {
                      transData.value = { Temp: meterDictSub.value.Temp, Ig: meterDictSub.value.Ig, Stotal:meterDictSub.value.S4 }
                    }
                }else{
                  stData.value.Ig = channel.value === 'main' ? meterDictMain.value.Ig : meterDictSub.value.Ig;
                }
             }else{
               console.log('No Data');
             }
           }catch (error) {
             console.log("데이터 가져오기 실패:", error);
           } 
         }
     };

     
     const fetchRealData = async () => {
          if (!asset.value || (!asset.value.assetName_main && !asset.value.assetName_sub)) {
            console.log("⏳ asset 준비 안됨. fetchData 대기중");
            console.log(asset.value);
            return;
          }
         const chName = channel.value == 'main'? asset.value.assetName_main : asset.value.assetName_sub;
         const chType = channel.value == 'main'? asset.value.assetType_main : asset.value.assetType_sub;
         if(chName != ''){

           try {
            const response = await axios.get(`/api/getRealTime/${chType}/${chName}`);

             if (response.data.success) {
                transData.value = response.data.data;
             }else{
               console.log('No Data');
             }
           }catch (error) {
             console.log("데이터 가져오기 실패:", error);
           } 
         }
     };

    const fetchPQData = async () => {
          if (!asset.value || (!asset.value.assetName_main && !asset.value.assetName_sub)) {
            console.log("⏳ asset 준비 안됨. fetchData 대기중");
            console.log(asset.value);
            return;
          }
         const chName = channel.value == 'main'? asset.value.assetName_main : asset.value.assetName_sub;
         const chType = channel.value == 'main'? asset.value.assetType_main : asset.value.assetType_sub;
         if(chName != ''){
           try {
            const response = await axios.get(`/api/getPQStatus/${chName}`);
             if (response.data.status >= 0) {
                pqData.value.devName = response.data.item;
                pqData.value.devStatus = response.data.status;
             }else{
               console.log('No Data');
             }
           }catch (error) {
             console.log("데이터 가져오기 실패:", error);
           } 
         }
     };

    const fecthImmediate = async()=>{
      try {
        const response = await axios.get(`/api/setImdAPI`);
        if(response.data.success){
          console.log('진단 API CALL')
        }
      }catch (error) {
        console.log("데이터 가져오기 실패:", error);
      } 
    }

    

    watch(asset, (newVal) => {
      if (newVal) {
        if(channel.value == 'main')
          assetTypes.value = newVal.assetType_main;
        else
          assetTypes.value = newVal.assetType_sub;
        fetchData();
        if(!assetTypes.value.includes('Transformer')){
          fetchRealData();
        }
        fetchPQData();
        //fetchAlarmData();

        // 그리고 나서 주기 업데이트 걸어
        if (updateInterval) {
          console.log(`[${channel.value}] 🛑 기존 폴링 정리:`, updateInterval);
          clearInterval(updateInterval);
          updateInterval = null;  // ✅ 반드시 null로!
        }
        console.log(`[${channel.value}] ✅ 새 폴링 시작`);
          updateInterval = setInterval(async () => {
            console.log(`[${channel.value}] ⏰ 5분 폴링 실행`);
            await fetchData();
            if(!assetTypes.value.includes('Transformer')){
              await fetchRealData();
            }
            await fetchPQData();
          }, 60000);
        // if (!updateInterval) {
        //   updateInterval = setInterval(async () => {
        //     await fetchData();
        //      if(!assetTypes.value.includes('Transformer')){
        //         await fetchRealData();
        //       }
        //     await fetchPQData();
        //     //await fetchAlarmData();
        //   }, 300000);  //5 x 60 × 1000 : 5min
        // }
      }
    }, { immediate: true }); // <-- 바로 실행 시도
 
    onMounted(async () => {     
        await setupStore.checkSetting();   // ✅ setupStore에서 서버 데이터 다시 가져오기
        await fecthImmediate();
      });

 
     onUnmounted(() => {
        console.log(`[${channel.value}] 🧹 컴포넌트 언마운트 - 폴링 정리`);
        if (updateInterval) {
          clearInterval(updateInterval);
          updateInterval = null;
        }
     });
 
     watchEffect(() => {
       if(channel.value == 'main')
         DiagEnable.value = channelStatus.value.MainDiagnosis
       else
         DiagEnable.value = channelStatus.value.SubDiagnosis
     });
 
     return {
       channel,
       stData,
       channelStatus,
       DiagEnable,
       fetchData,
       asset,
       status,
       data,
       pqData,
       alarmContext,
       assetTypes,
       transData,
       fetchRealData,
       //alarmEnable,
       t,
     }    
   }
 }
 </script>

<style scoped>
.premium-dashboard-card {
  @apply col-span-full sm:col-span-6 xl:col-span-6;
  @apply bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900;
  @apply shadow-lg rounded-xl border border-gray-200/50 dark:border-gray-700/50;
  @apply backdrop-blur-sm;
  @apply transition-all duration-300 hover:shadow-xl;
}

/* 헤더 섹션 */
.card-header {
  @apply p-3 border-b border-gray-200/50 dark:border-gray-700/50;
  @apply bg-gradient-to-r from-blue-50/50 to-purple-50/50 dark:from-blue-900/20 dark:to-purple-900/20;
  @apply rounded-t-xl;
}

.header-content {
  @apply flex justify-between items-center;
}

.card-title {
  @apply text-lg font-bold text-gray-900 dark:text-white;
  @apply bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent;
}

.channel-info {
  @apply flex items-center;
}

.channel-text {
  @apply text-xs font-semibold text-gray-400 dark:text-gray-300 uppercase;
}

.summary-section {
  @apply p-3 gap-2;
}

.summary-container {
  @apply grid grid-cols-5 gap-3;
}

/* 추가적인 다크모드 개선 사항들 */

/* 상태 표시기 개선 */
.status-indicator {
  @apply text-gray-800 dark:text-white;
}

.status-normal {
  @apply text-green-600 dark:text-green-400;
}

.status-warning {
  @apply text-yellow-600 dark:text-yellow-400;
}

.status-error {
  @apply text-red-600 dark:text-red-400;
}

.status-offline {
  @apply text-gray-500 dark:text-gray-400;
}

/* 진단 데이터 텍스트 */
.diagnosis-label {
  @apply text-sm font-medium text-gray-600 dark:text-gray-300;
}

.diagnosis-value {
  @apply text-lg font-bold text-gray-800 dark:text-white;
}

.diagnosis-unit {
  @apply text-sm font-medium text-gray-500 dark:text-gray-300;
}

/* 알람 관련 스타일 */
.alarm-text {
  @apply text-red-600 dark:text-red-400;
}

.normal-text {
  @apply text-green-600 dark:text-green-400;
}

.warning-text {
  @apply text-yellow-600 dark:text-yellow-400;
}

/* 디바이스 정보 텍스트 */
.device-name {
  @apply text-gray-800 dark:text-white font-semibold;
}

.device-type {
  @apply text-gray-600 dark:text-gray-300 text-sm;
}

.device-nickname {
  @apply text-gray-500 dark:text-gray-400 text-sm italic;
}

/* 그리드 컨테이너 개선 */
.grid-container {
  @apply bg-white dark:bg-gray-800 rounded-lg;
}

.grid-item {
  @apply p-3 border border-gray-200 dark:border-gray-600 rounded-lg;
  @apply bg-gray-50 dark:bg-gray-700/50;
  @apply transition-all duration-200 hover:shadow-sm;
}

/* 진단 카드 스타일 */
.diagnosis-card {
  @apply bg-white dark:bg-gray-800 rounded-lg p-4;
  @apply border border-gray-200 dark:border-gray-600;
  @apply shadow-sm hover:shadow-md transition-all duration-200;
}

.diagnosis-header {
  @apply flex justify-between items-center mb-3;
  @apply border-b border-gray-200 dark:border-gray-600 pb-2;
}

.diagnosis-title {
  @apply text-lg font-semibold text-gray-800 dark:text-white;
}

.diagnosis-subtitle {
  @apply text-sm text-gray-600 dark:text-gray-300;
}

/* 트랜스포머 데이터 스타일 */
.transformer-data {
  @apply space-y-2;
}

.data-row {
  @apply flex justify-between items-center;
  @apply py-1 border-b border-gray-100 dark:border-gray-700;
}

.data-label {
  @apply text-sm font-medium text-gray-600 dark:text-gray-300;
}

.data-value {
  @apply text-sm font-bold text-gray-800 dark:text-white;
}

/* 상태 배지 */
.status-badge {
  @apply px-2 py-1 rounded-full text-xs font-medium;
}

.status-badge.normal {
  @apply bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400;
}

.status-badge.warning {
  @apply bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400;
}

.status-badge.error {
  @apply bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400;
}

.status-badge.offline {
  @apply bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300;
}

/* 로딩 상태 */
.loading-text {
  @apply text-gray-500 dark:text-gray-400 animate-pulse;
}

/* 에러 상태 */
.error-text {
  @apply text-red-600 dark:text-red-400;
}

/* 빈 상태 */
.empty-state {
  @apply text-gray-500 dark:text-gray-400 text-center py-8;
}

/* 반응형 개선 */
@media (max-width: 768px) {
  .diagnosis-card {
    @apply p-3;
  }
  
  .diagnosis-title {
    @apply text-base;
  }
  
  .data-row {
    @apply flex-col items-start gap-1;
  }
}
</style>