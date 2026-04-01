<template>
  <div class="card-wrap">
    <div class="card-header">
      <h3 class="card-title meter-accent-violet">{{ t('dashboard.diagnosis.title') }}</h3>
      <div class="header-right">
        <div v-if="isModule" class="module-badges">
          <div
            v-for="mod in moduleStatuses"
            :key="mod.devId"
            class="module-badge"
            :class="mod.online ? 'badge-on' : 'badge-off'"
            :title="`DevID: ${mod.devId}`"
          >
            <span class="module-dot"></span>
            <span class="module-name">{{ mod.mtype == 0 ? 'DO' : mod.mtype == 1 ? 'P300-C' : mod.m_name }}</span>
          </div>
        </div>
        <span class="card-channel">
          {{ channel.toLowerCase() == 'main' ? t('dashboard.diagnosis.subtitle_main') : t('dashboard.diagnosis.subtitle_sub') }}
        </span>
      </div>
    </div>
    <div class="card-body">
      <div class="diag-grid">
        <StatusItem :channel="channel" :data="stData" mode="diagnosis" />
        <StatusItem :channel="channel" :data="pqData" mode="pq" />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watchEffect, onMounted, onUnmounted, watch, inject } from 'vue'
import StatusItem from '../../inners/dashboard/StatusItem_Trans_Claude.vue'
import StatusItem2 from '../../inners/dashboard/StatusItem2.vue'
import { useSetupStore } from '@/store/setup'
import axios from 'axios'
import { useI18n } from 'vue-i18n'


export default {
  name: 'SingleMeasCard_Diagnosis',
  props: {
    channel: String
  },
  components: {
    StatusItem,
    StatusItem2,
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
      updateTime:'',
    });
    const pqData = ref({
      devName:'',
      devStatus: -2,
      updateTime:'',
    });
    const isModule = ref(false);
    const moduleStatuses = ref([]);
    const setupStore = useSetupStore();
    const channelStatus = computed(() => setupStore.getChannelSetting);
    const asset = computed(() => setupStore.getAssetConfig);
    const assetTypes = ref('');
    const status = ref('Normal');
    const data = ref([]);
    let updateInterval = null;

    const transData = ref({});

    const fetchModuleStatus = async () => {
      const chName = channel.value.toLowerCase() == 'main' ? 'Main' : 'Sub';
      try {
        const response = await axios.get(`/api/getModuleStatus/${chName}`);
        console.log(response.data);
        if(response.data.exist){
          isModule.value = true;
          if (Array.isArray(response.data.data)) {
            // devId 중복 제거
            const seen = new Set();
            moduleStatuses.value = response.data.data.filter(m => {
              if (seen.has(m.devId)) return false;
              seen.add(m.devId);
              return true;
            });
            console.log(moduleStatuses.value);
          }
        }else{
          isModule.value = false;
        }
      } catch (error) {
        isModule.value = false;
        console.log("모듈 상태 가져오기 실패:", error);
      }
    };

     const fetchDashData = async () => {
          if (!asset.value || (!asset.value.assetName_main && !asset.value.assetName_sub)) {
            console.log("⏳ asset 준비 안됨. fetchData 대기중");
            console.log(asset.value);
            return;
          }
        const channelName = (channel.value == 'main' || channel.value == 'Main') ? 'Main' : 'Sub';
         const chName = channelName == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;
         const chType = channelName == 'Main'? asset.value.assetType_main : asset.value.assetType_sub;
         const chNick = channelName == 'Main'? asset.value.assetNickname_main : asset.value.assetNickname_sub;

         try {
             const response = await axios.get(`/api/getDashSatatus/${chName}/${channelName}`);
             if (response.data.status >= 0) {
                stData.value.devName = chName;
                stData.value.devType = chType;
                stData.value.devStatus = response.data.data["Diagnostic"]["status"];
                stData.value.devNickname = chNick;
                stData.value.runhour = response.data.runhours;

                pqData.value.devName = response.data.data["PQ"]["item"];
                pqData.value.devStatus =response.data.data["PQ"]["status"];
             }else{
               console.log('No Data');
             }
           }catch (error) {
             console.log("데이터 가져오기 실패:", error);
           }
    };


    watch(asset, (newVal, oldVal) => {
  if (newVal) {
    if(channel.value == 'main')
      assetTypes.value = newVal.assetType_main;
    else
      assetTypes.value = newVal.assetType_sub;

    fetchDashData();
    fetchModuleStatus();

    // 타이머 재설정
    if (updateInterval) {
      clearInterval(updateInterval);
      updateInterval = null;
    }

    // 새 타이머 설정
    updateInterval = setInterval(async () => {
      await fetchDashData();
      await fetchModuleStatus();
    }, 60000);
  }
}, { immediate: true });


     onUnmounted(() => {
       if (updateInterval) {
         clearInterval(updateInterval);
         updateInterval = null;
       }
     });


     return {
       channel,
       stData,
       channelStatus,
       fetchDashData,
       asset,
       status,
       data,
       pqData,
       assetTypes,
       t,
       moduleStatuses,
       isModule,
     }
   }
 }
</script>

<style scoped>
.card-wrap {
  @apply col-span-full sm:col-span-6 xl:col-span-5;
  @apply bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900;
  @apply shadow-lg rounded-xl border border-gray-200/50 dark:border-gray-700/50;
  @apply overflow-hidden;
}
.card-header {
  @apply flex justify-between items-center px-4 py-2.5;
}
.card-title {
  @apply text-base font-bold text-gray-800 dark:text-white flex items-center gap-2;
}
.card-title::before {
  content: '';
  @apply w-1 h-4 rounded-full inline-block flex-shrink-0;
}
.meter-accent-violet::before {
  @apply bg-violet-500;
}
.header-right {
  @apply flex items-center gap-2;
}
.card-channel {
  @apply text-gray-500 dark:text-gray-500;
  font-size: 10px;
}
.card-body {
  @apply px-4 py-3;
}

/* Module badges */
.module-badges {
  @apply flex items-center gap-1;
}
.module-badge {
  @apply inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full;
  @apply text-xs font-medium border;
}
.badge-on {
  @apply border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20;
}
.badge-off {
  @apply border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800;
}
.badge-on .module-dot {
  @apply w-1.5 h-1.5 rounded-full bg-green-500;
}
.badge-off .module-dot {
  @apply w-1.5 h-1.5 rounded-full bg-gray-400;
}
.module-name {
  @apply text-gray-600 dark:text-gray-400;
}

/* Diagnosis grid */
.diag-grid {
  @apply grid grid-cols-12 gap-3;
}

/* Responsive */
@media (max-width: 640px) {
  .card-wrap {
    @apply col-span-full;
  }
}
</style>
