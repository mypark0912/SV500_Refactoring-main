<template>
    <div class="grid grid-cols-12 gap-x-4 gap-y-4">
      <!-- 2채널 레이아웃 - 메인과 서브 채널 모두 표시 -->
      
      <DashboardCard04 
        v-if="channelState.MainDiagnosis" 
        :channel="assetChannel" 
      />
  
      <!-- 메인 채널 카드 -->
      <DashboardCard_Meter_Integrated 
        v-if="channelState.MainEnable && mainDataReady" 
        :channel="'main'"
        :diagData="diagData_main"
      />
  
      <!-- 서브 채널 카드 -->
      <DashboardCard_Meter_Integrated 
        v-if="channelState.SubEnable && subDataReady" 
        :channel="'sub'"
        :diagData="diagData_sub"
      />
    </div>
  </template>
  
  <script>
  import { ref, computed, watch, onUnmounted } from 'vue'; 
  import DashboardCard_Meter_Integrated from '../../partials/inners/dashboard/DashboardCard_Meter_Integrated_total.vue'
  import DashboardCard04 from '../../partials/inners/dashboard/DashboardCard_New2.vue'
  import { useSetupStore } from '@/store/setup';
  import axios from 'axios';
  
  export default {
    name: 'DualChannelLayout',
    components: {
      DashboardCard_Meter_Integrated,
      DashboardCard04,
    },
    props: {
      mainData: {
        type: Object,
        required: true
      },
      subData: {
        type: Object,
        required: true
      },
      channelState: {
        type: Object,
        required: true
      }
    },
    setup(props){
      const setupStore = useSetupStore();
      const asset = computed(() => setupStore.getAssetConfig);
      const assetChannel = computed(() => {
        if(asset.value.assetType_main == 'Transformer')
          return 'main';
        else
          return 'sub';
      });
  
      // ✅ 진단 데이터 상태
      const diagData_main = ref(null);
      const diagData_sub = ref(null);
      const mainDataReady = ref(false);
      const subDataReady = ref(false);
      
      let updateInterval = null;
  
      // ✅ 진단 데이터 병렬 로드
      const fetchDiagData = async () => {
        if (!asset.value?.assetName_main && !asset.value?.assetName_sub) {
          console.log("⏳ asset 준비 안됨. fetchDiagData 대기중");
          return;
        }
  
        const assetName_main = asset.value.assetName_main;
        const assetName_sub = asset.value.assetName_sub;
  
        console.log('🚀 진단 데이터 병렬 로드 시작');
        const startTime = performance.now();
  
        try {
          const promises = [];
          
          // Main 채널 데이터 로드
          if (props.channelState.MainEnable && assetName_main) {
            const mainPromise = axios.get(`/api/getDashSatatus/${assetName_main}/Main`)
              .then(res => {
                diagData_main.value = res.data;
                mainDataReady.value = true;
                console.log(`✅ [Main] 진단 데이터 로드 완료`);
              })
              .catch(err => {
                console.error('❌ [Main] 진단 데이터 로드 실패:', err);
              });
            promises.push(mainPromise);
          }
  
          // Sub 채널 데이터 로드
          if (props.channelState.SubEnable && assetName_sub) {
            const subPromise = axios.get(`/api/getDashSatatus/${assetName_sub}/Sub`)
              .then(res => {
                diagData_sub.value = res.data;
                subDataReady.value = true;
                console.log(`✅ [Sub] 진단 데이터 로드 완료`);
              })
              .catch(err => {
                console.error('❌ [Sub] 진단 데이터 로드 실패:', err);
              });
            promises.push(subPromise);
          }
  
          // ✅ 병렬 실행 - Main과 Sub가 동시에 시작
          await Promise.all(promises);
          
          const endTime = performance.now();
          console.log(`✅ 전체 진단 데이터 로드 완료: ${(endTime - startTime).toFixed(0)}ms`);
  
        } catch (error) {
          console.error('❌ 진단 데이터 로드 실패:', error);
        }
      };
  
      // ✅ asset이 준비되면 데이터 로드 시작
      watch(
        asset,
        (newVal) => {
          if (newVal && (newVal.assetName_main || newVal.assetName_sub)) {
            // 초기 로드
            fetchDiagData();
  
            // 기존 인터벌 정리
            if (updateInterval) {
              clearInterval(updateInterval);
              updateInterval = null;
            }
  
            // ✅ 60초마다 갱신
            updateInterval = setInterval(() => {
              fetchDiagData();
            }, 60000);
          }
        },
        { immediate: true }
      );
  
      onUnmounted(() => {
        if (updateInterval) {
          clearInterval(updateInterval);
          updateInterval = null;
        }
      });
  
      return {
        asset,
        assetChannel,
        diagData_main,
        diagData_sub,
        mainDataReady,
        subDataReady,
      }
    }
  }
  </script>