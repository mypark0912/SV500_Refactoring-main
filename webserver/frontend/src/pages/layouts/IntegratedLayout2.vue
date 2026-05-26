<template>
  <div class="grid grid-cols-12 gap-x-4 gap-y-4">
    <!-- 로딩 중 표시 -->
    <div v-if="isLoading" class="col-span-12 flex justify-center items-center h-64">
      <div class="flex flex-col items-center gap-3">
        <svg class="animate-spin h-10 w-10 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span class="text-gray-600 dark:text-gray-400">{{ t('dashboard.loading') }}...</span>
      </div>
    </div>

    
    <!-- 로딩 완료 후 표시 -->
    <template v-else>
      <DashboardCard04 
        v-if="channelState.MainDiagnosis" 
        :channel="assetChannel" 
      />

      <DashboardCard_Meter_Integrated 
        v-if="channelState.MainEnable && mainDataReady" 
        :channel="'main'"
        :diagData="diagData_main"
      />

      <DashboardCard_Meter_Integrated 
        v-if="channelState.SubEnable && subDataReady" 
        :channel="'sub'"
        :diagData="diagData_sub"
      />
    </template>
  </div>
</template>

<script>
import { ref, computed, watch, onUnmounted } from 'vue'; 
import DashboardCard_Meter_Integrated from '../../partials/inners/dashboard/DashboardCard_Meter_Integrated_total.vue'
import DashboardCard04 from '../../partials/inners/dashboard/DashboardCard_New2.vue'
import { useSetupStore } from '@/store/setup';
import axios from 'axios';
import { useI18n } from 'vue-i18n'

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
}
</script>