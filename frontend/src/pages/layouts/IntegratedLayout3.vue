<template>
  <div class="grid grid-cols-12 gap-x-2 gap-y-6">
    <!-- 메인 채널 카드 - 6칸 -->
    <Dashboard_MeterCard 
      v-if="channelState.MainEnable" 
      :channel="'main'" 
      class="col-span-6"
    />

    <!-- 진단 현황 카드 - 6칸, 세로 2줄 차지 -->
    <DashboardCard_Meter_Integrated
      class="col-span-6 row-span-2"
      :channel="'sub'"
      :diagData="diagData_sub"
    />

    <!-- 서브 채널 카드 - 6칸 -->
    <Dashboard_MeterCard 
      v-if="channelState.SubEnable" 
      :channel="'sub'" 
      class="col-span-6"
    />
  </div>
</template>

<script>
  import { ref, computed, watch, onUnmounted } from 'vue'; 
import Dashboard_MeterCard from "../../partials/inners/dashboard/DashboardCard_Meter_Ch3.vue";
import DashboardCard04 from "../../partials/inners/dashboard/DashboardCard_New.vue";
import DashboardCard_Meter_Integrated from '../../partials/inners/dashboard/DashboardCard_Meter_Integrated_total2.vue'
import { useSetupStore } from '@/store/setup';
import axios from 'axios';
import { useI18n } from 'vue-i18n'
export default {
  name: "DualChannelLayout",
  components: {
    Dashboard_MeterCard,
    DashboardCard04,
    DashboardCard_Meter_Integrated,
  },
  props: {
    channelState: {
      type: Object,
      required: true,
    },
  },
    setup(props){
    const setupStore = useSetupStore();
    const asset = computed(() => setupStore.getAssetConfig);
    const { t } = useI18n()
    const assetChannel = computed(() => {
      if(asset.value.assetType_main == 'Transformer')
        return 'main';
      else
        return 'sub';
    });

    const diagData_main = ref(null);
    const diagData_sub = ref(null);
    const mainDataReady = ref(false);
    const subDataReady = ref(false);
    const isLoading = ref(true);  // ✅ 초기값 true
    
    let updateInterval = null;

    const fetchDiagData = async (showLoading = false) => {
      if (!asset.value?.assetName_main && !asset.value?.assetName_sub) {
        console.log("⏳ asset 준비 안됨. fetchDiagData 대기중");
        return;
      }

      const assetName_main = asset.value.assetName_main;
      const assetName_sub = asset.value.assetName_sub;

      if (showLoading) {
        isLoading.value = true;
      }

      //console.log('🚀 진단 데이터 병렬 로드 시작');
      const startTime = performance.now();

      try {
        const promises = [];
        
        if (props.channelState.MainEnable && assetName_main) {
          const mainPromise = axios.get(`/api/getDashSatatus/${assetName_main}/Main`)
            .then(res => {
              diagData_main.value = res.data;
              mainDataReady.value = true;
              //console.log(`✅ [Main] 진단 데이터 로드 완료`);
            })
            .catch(err => {
              console.error('❌ [Main] 진단 데이터 로드 실패:', err);
            });
          promises.push(mainPromise);
        }

        if (props.channelState.SubEnable && assetName_sub) {
          const subPromise = axios.get(`/api/getDashSatatus/${assetName_sub}/Sub`)
            .then(res => {
              diagData_sub.value = res.data;
              subDataReady.value = true;
              //console.log(`✅ [Sub] 진단 데이터 로드 완료`);
            })
            .catch(err => {
              console.error('❌ [Sub] 진단 데이터 로드 실패:', err);
            });
          promises.push(subPromise);
        }

        await Promise.all(promises);
        
        const endTime = performance.now();
        //console.log(`✅ 전체 진단 데이터 로드 완료: ${(endTime - startTime).toFixed(0)}ms`);

      } catch (error) {
        console.error('❌ 진단 데이터 로드 실패:', error);
      } finally {
        isLoading.value = false;  // ✅ 로딩 완료
      }
    };

    watch(
      asset,
      (newVal) => {
        if (newVal && (newVal.assetName_main || newVal.assetName_sub)) {
          fetchDiagData(true);  // ✅ 초기 로드시 로딩 표시

          if (updateInterval) {
            clearInterval(updateInterval);
            updateInterval = null;
          }

          updateInterval = setInterval(() => {
            fetchDiagData(false);  // ✅ 갱신시 로딩 표시 안함
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
      isLoading,
      t,
    }
  }
};
</script>
