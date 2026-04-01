<template>
  <div class="card-wrap">
    <div class="card-header">
      <h3 class="card-title meter-accent-emerald">{{ t('dashboard.singleinfo.title') }}</h3>
      <span class="card-channel">
        {{ computedChannel == 'Main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>

    <!-- 설비 정보 -->
    <div class="equipment-info">
      <div class="equipment-avatar">
        <img class="avatar-image" :src="motorImageSrc" />
      </div>
      <div class="equipment-details">
        <h3 class="equipment-name">
          {{ computedChannel == 'Main' ? AssetInfo.assetNickname_main : AssetInfo.assetNickname_sub }}
        </h3>
        <p class="equipment-type">
          {{ computedChannel == 'Main' ? AssetInfo.assetType_main : AssetInfo.assetType_sub }}
        </p>
      </div>
      <div class="equipment-status">
        <span
          class="status-badge"
          :class="isRunning ? 'status-running' : 'status-stopped'"
        >
          <span class="status-indicator"></span>
          <span class="status-text">
            {{ isRunning ? t('dashboard.singleinfo.running') : t('dashboard.singleinfo.stopped') }}
          </span>
        </span>
      </div>
    </div>

    <!-- 데이터 테이블 -->
    <div class="card-body">
      <div class="data-grid">
        <Dash_InnerSingle :channel="computedChannel"/>
        <Dash_InnerEquipment :channel="computedChannel" />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSetupStore } from '@/store/setup'
import motorImg from '@/images/motor_m.png'
import fanImg from '@/images/fan_m.png'
import pumpImg from '@/images/pump_m.png'
import compImg from '@/images/comp_m.png'
import powerImg from '@/images/power_m.png'
import defaultImg from '@/images/cleaned_logo.png'
import transImg from '@/images/trans.png'
import Dash_InnerSingle from '../../inners/dashboard/Dash_InnerSingle.vue'
import Dash_InnerEquipment from '../../inners/dashboard/Dash_InnerEquipment.vue'
import axios from 'axios'
export default {
  name: 'SingleMeasCard_Equip',
  components:{
      Dash_InnerSingle,
      Dash_InnerEquipment,
  },
  props: {
    channel: String,   // 채널 정보
  },
  setup(props) {
    const { t } = useI18n()
    const setupStore = useSetupStore()
    const AssetInfo = computed(() => setupStore.getAssetConfig)
    // 반응형 데이터
    const channel = ref(props.channel)
    const isRunning = ref(false)
    let updateInterval = null;
    // 채널 정보 계산
    const computedChannel = computed(() => {
      if (channel.value == 'Main' || channel.value == 'main')
        return 'Main'
      else
        return 'Sub'
    })
    const computedType = computed(()=> computedChannel.value == 'Main' ? AssetInfo.value.assetType_main: AssetInfo.value.assetType_sub)

    // Transformer 타입 체크
    const isTransformer = computed(() => {
      return computedType.value === 'Transformer' ||
             computedType.value === 'PrimaryTransformer'
    })

    const getStatus = async() =>{
      const response = await axios.get(`/api/getEquipStatus/${computedChannel.value}`);
      if (response.data.success){
        isRunning.value = response.data.status;
      }
    }

    onMounted(async()=>{
      await getStatus();
      updateInterval = setInterval(async () => {
        await getStatus();
      }, 300000);  // 5분
    })

    onUnmounted(() => {
      if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
      }
    });

    // 설비 이미지 결정
    const motorImageSrc = computed(() => {
      switch (computedType.value) {
        case 'Motor':
          return motorImg;
        case 'MotorFeed':
          return motorImg;
        case 'Pump':
          return pumpImg;
        case 'Fan':
          return fanImg;
        case 'Compressor':
          return compImg;
        case 'PSupply':
          return powerImg;
        case 'PowerSupply':
          return powerImg;
        case 'PrimaryTransformer':
          return transImg;
        case 'Transformer':
          return transImg;
        default:
          return defaultImg;
      }
    })

    return {
      // 데이터
      computedChannel,
      isRunning,
      isTransformer,
      // 계산된 속성
      motorImageSrc,
      AssetInfo,
      channel,
      computedType,
      // 함수
      t,
    }
  }
}
</script>

<style scoped>
.card-wrap {
  @apply flex flex-col col-span-full sm:col-span-6 xl:col-span-5;
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

.meter-accent-emerald::before {
  @apply bg-emerald-500;
}

.card-channel {
  @apply text-gray-500 dark:text-gray-500;
  font-size: 10px;
}

.card-body {
  @apply px-4 py-3;
}

/* 설비 정보 */
.equipment-info {
  @apply flex items-center gap-3 px-4 py-3;
  @apply justify-between;
}

.equipment-avatar {
  @apply relative;
}

.avatar-image {
  @apply w-12 h-12 rounded-xl object-cover;
  @apply shadow-sm border border-white dark:border-gray-600;
}

.equipment-details {
  @apply flex flex-col gap-1;
  @apply flex-shrink-0;
}

.equipment-name {
  @apply text-sm font-bold text-gray-800 dark:text-gray-100;
  @apply leading-tight;
}

.equipment-type {
  @apply text-xs font-medium;
  @apply bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300;
  @apply px-2 py-1 rounded-md;
  @apply inline-block w-auto;
}

/* 상태 배지 */
.equipment-status {
  @apply flex items-center;
  @apply flex-shrink-0 ml-auto;
}

.status-badge {
  @apply flex items-center gap-2 px-3 py-1.5;
  @apply rounded-full font-semibold text-xs;
  @apply border-2;
  @apply shadow-sm;
  @apply whitespace-nowrap;
}

.status-indicator {
  @apply w-2 h-2 rounded-full;
  @apply animate-pulse;
}

.status-running {
  @apply bg-green-50 dark:bg-green-900/30;
  @apply border-green-500 dark:border-green-600;
  @apply text-green-700 dark:text-green-300;
}

.status-running .status-indicator {
  @apply bg-green-500;
}

.status-stopped {
  @apply bg-gray-50 dark:bg-gray-700/30;
  @apply border-gray-400 dark:border-gray-500;
  @apply text-gray-700 dark:text-gray-300;
}

.status-stopped .status-indicator {
  @apply bg-gray-400;
  @apply animate-none;
}

/* 데이터 그리드 */
.data-grid {
  @apply grid grid-cols-1 lg:grid-cols-2 gap-4;
  @apply items-start;
}

/* 반응형 */
@media (max-width: 768px) {
  .equipment-info {
    @apply flex-wrap;
  }

  .equipment-status {
    @apply w-full justify-end;
  }

  .data-grid {
    @apply grid-cols-1;
  }
}

@media (max-width: 480px) {
  .status-badge {
    @apply px-2 py-1 text-[10px];
  }

  .status-indicator {
    @apply w-1.5 h-1.5;
  }
}
</style>
