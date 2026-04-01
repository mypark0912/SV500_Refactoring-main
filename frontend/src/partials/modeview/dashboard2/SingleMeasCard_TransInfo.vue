<template>
  <div class="card-wrap">
    <!-- Header -->
    <div class="card-header">
      <h3 class="card-title meter-accent-emerald">{{ t('dashboard.singleinfo.title') }}</h3>
      <span class="card-channel">
        {{ channel == 'main' ? t('dashboard.diagnosis.subtitle_main') : t('dashboard.diagnosis.subtitle_sub') }}
      </span>
    </div>

    <div class="card-body">
      <!-- Equipment Info -->
      <div class="equipment-info">
        <div class="equipment-avatar">
          <img class="avatar-image" :src="motorImageSrc" alt="Equipment" />
        </div>
        <div class="equipment-details">
          <h3 class="equipment-name">
            {{ channel == 'main' ? AssetInfo.assetNickname_main : AssetInfo.assetNickname_sub }}
          </h3>
          <p class="equipment-type">
            {{ channel == 'main' ? AssetInfo.assetType_main : AssetInfo.assetType_sub }}
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

      <!-- Status Cards -->
      <div class="data-section">
        <div class="status-cards">
          <!-- Temperature -->
          <div v-if="displayData.Temp && displayData.Temp.length > 0" class="status-card">
            <div class="status-value">
              <div class="temp-grid">
                <div v-for="(temp, index) in displayData.Temp" :key="index" class="temp-row">
                  <span class="phase-label">{{ ['R', 'S', 'T'][index] }}</span>
                  <span class="value-number">{{ Number(temp) < -900 ? '-': Number(temp).toFixed(2) }}</span>
                  <span class="value-unit">&#8451;</span>
                </div>
              </div>
            </div>
            <div class="status-label">{{ t('dashboard.transDiag.Temperature') }}</div>
          </div>

          <!-- Load Factor -->
          <div class="status-card">
            <div class="status-value" :class="getLoadRateClass(LoadRate)">
              <span class="value-number">{{ LoadRate }}</span>
              <span class="value-unit">%</span>
            </div>
            <div class="status-label">{{ t('dashboard.transDiag.LoadFactor') }}</div>
          </div>

          <!-- Power Factor -->
          <div class="status-card">
            <div class="status-value">
              <span class="value-number">{{ displayData.PF }}</span>
              <span class="value-unit">%</span>
            </div>
            <div class="status-label">{{ t('dashboard.transDiag.PowerFactor') }}</div>
          </div>
        </div>

        <!-- Equipment Specs Table -->
        <div class="data-table">
          <div class="table-header">
            <h4 class="table-title">{{ t('dashboard.singleinfo.EquipmentInformation') }}</h4>
          </div>
          <div class="table-content">
            <div v-for="item in rawdata" :key="item.Name" class="data-row">
              <span class="data-label">{{ t(`dashboard.transDiag.${item.Name}`) }}</span>
              <span class="data-value">
                {{ item.Value }} <span class="data-unit">{{ item.Unit }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import sampleImg from '@/images/trans.png'
import { useSetupStore } from '@/store/setup'
import { useRealtimeStore } from '@/store/realtime'
import axios from 'axios'

export default {
  name: 'SingleMeasCard_TransInfo',
  props: {
    channel: String,
  },
  setup(props) {
    const { t } = useI18n()
    const setupStore = useSetupStore()
    const realtimeStore = useRealtimeStore()
    let updateInterval = null;
    // 반응형 데이터
    const LoadFactor = ref(-1)
    const rawdata = ref([])
    const isRunning = ref(0);
    // 계산된 속성
    const AssetInfo = computed(() => setupStore.getAssetConfig)
    const motorImageSrc = computed(() => sampleImg)

    // Store에서 실시간 데이터 가져오기
    const channelName = computed(() =>
      props.channel?.toLowerCase() === 'main' ? 'Main' : 'Sub'
    )

    const realtimeData = computed(() =>
      realtimeStore.getChannelData(channelName.value) || {}
    )

    // 화면 표시용 데이터 (설비 타입에 따라 매핑)
    const displayData = computed(() => {
      const data = realtimeData.value;
      console.log(data);
      if (!data || Object.keys(data).length === 0) {
        return { Temp: [], Ig: '-', Stotal: 0, PF: '-' }
      }

      const chType = props.channel?.toLowerCase() === 'main'
        ? AssetInfo.value?.assetType_main
        : AssetInfo.value?.assetType_sub

      if (chType === 'Transformer') {
        return {
          Temp: data.Temp2 ?? [],
          Ig: data.Ig ?? '-',
          Stotal: data.S4 ?? 0,
          PF: data.PF4 ?? '-',
        }
      }

      // 다른 설비 타입 처리
      return {
        Temp: data.Temp2 ?? [],
        Ig: data.Ig ?? '-',
        Stotal: data.Stotal ?? 0,
        PF: data.PF ?? '-',
      }
    })

    // 부하율 계산
    const LoadRate = computed(() => {
      if (LoadFactor.value > 0 && displayData.value.Stotal > 0) {
        return (((displayData.value.Stotal/1000) / LoadFactor.value) * 100).toFixed(2)
      }
      return 0
    })

    // 상태 클래스 함수들
    const getLoadRateClass = (rate) => {
      if (rate >= 90) return 'text-red-600 font-bold'
      if (rate >= 80) return 'text-orange-500 font-semibold'
      if (rate >= 60) return 'text-yellow-600 font-semibold'
      return 'text-green-600'
    }

    const getTemperatureStatus = (temp) => {
      if (temp >= 80) return 'status-critical'
      if (temp >= 60) return 'status-warning'
      return 'status-normal'
    }

    const getLoadStatus = (load) => {
      if (load >= 90) return 'status-critical'
      if (load >= 80) return 'status-warning'
      return 'status-normal'
    }

    const getPowerFactorStatus = (pf) => {
      if (pf < 80) return 'status-warning'
      if (pf < 90) return 'status-caution'
      return 'status-normal'
    }

    // 설비 정보 가져오기 (한 번만 호출)
    const fetchAsset = async () => {
      if (!AssetInfo.value) {
        await setupStore.checkSetting()
      }

      const chName = props.channel?.toLowerCase() === 'main'
        ? AssetInfo.value?.assetName_main
        : AssetInfo.value?.assetName_sub

      if (!chName || chName === '') {
        console.log('등록된 설비가 없습니다.')
        return
      }

      try {
        const response = await axios.get(`/api/getAsset/${chName}`)

        if (response.data.success) {
          rawdata.value = response.data.data

          // RatedKVA 찾기
          const ratedKVAItem = rawdata.value.find(item => item.Name === 'RatedKVA')
          if (ratedKVAItem) {
            LoadFactor.value = parseFloat(ratedKVAItem.Value)
          }
        } else {
          console.log('No Data')
        }
      } catch (error) {
        console.log('데이터 가져오기 실패:', error)
      }
    }

    const getStatus = async() => {
      const chName = props.channel?.toLowerCase() === 'main' ? 'Main' : 'Sub'
      const response = await axios.get(`/api/getEquipStatus/${chName}`);
      if (response.data.success) {
        isRunning.value = response.data.status;
      }
    }

    // 마운트 시 설비 정보 로드
    onMounted(async() => {
      await fetchAsset()
      await getStatus();
      updateInterval = setInterval(async () => {
        await fetchAsset()
        await getStatus();
      }, 300000);  // 5분
    });

    onUnmounted(() => {
      if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
      }
    });

    return {
      // 데이터
      motorImageSrc,
      AssetInfo,
      displayData,
      LoadRate,
      LoadFactor,
      rawdata,
      isRunning,
      // 함수
      t,
      getLoadRateClass,
      getTemperatureStatus,
      getLoadStatus,
      getPowerFactorStatus,
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

/* Equipment info */
.equipment-info {
  @apply flex items-center gap-3 mb-3;
}
.equipment-avatar {
  @apply relative flex-shrink-0;
}
.avatar-image {
  @apply w-12 h-12 rounded-xl object-cover;
  @apply shadow-sm border border-gray-200 dark:border-gray-600;
}
.equipment-details {
  @apply flex flex-col gap-1;
}
.equipment-name {
  @apply text-sm font-bold text-gray-800 dark:text-gray-100 leading-tight;
}
.equipment-type {
  @apply text-xs font-medium;
  @apply bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300;
  @apply px-2 py-0.5 rounded-md inline-block;
}
.equipment-status {
  @apply flex items-center flex-shrink-0 ml-auto;
}
.status-badge {
  @apply flex items-center gap-2 px-3 py-1.5;
  @apply rounded-full font-semibold text-xs;
  @apply border-2 shadow-sm whitespace-nowrap;
}
.status-indicator {
  @apply w-2 h-2 rounded-full;
}
.status-running {
  @apply bg-green-50 dark:bg-green-900/30;
  @apply border-green-500 dark:border-green-600;
  @apply text-green-700 dark:text-green-300;
}
.status-running .status-indicator {
  @apply bg-green-500 animate-pulse;
}
.status-stopped {
  @apply bg-gray-50 dark:bg-gray-700/30;
  @apply border-gray-400 dark:border-gray-500;
  @apply text-gray-700 dark:text-gray-300;
}
.status-stopped .status-indicator {
  @apply bg-gray-400;
}

/* Data section */
.data-section {
  @apply flex flex-row gap-4 items-stretch;
}

/* Status cards */
.status-cards {
  @apply flex flex-wrap gap-3 flex-1;
}
.status-card {
  @apply bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3;
  @apply border border-gray-200 dark:border-gray-600;
  @apply text-center flex flex-col justify-center;
  @apply flex-1 min-w-[80px];
}
.status-value {
  @apply flex items-baseline justify-center gap-1 mb-1;
}
.value-number {
  @apply text-2xl font-bold text-gray-800 dark:text-gray-100;
}
.value-unit {
  @apply text-sm font-semibold text-gray-500 dark:text-white;
}
.status-label {
  @apply text-sm font-medium text-gray-600 dark:text-white leading-tight;
}

/* Temperature grid */
.temp-grid {
  @apply flex flex-col gap-1;
}
.temp-row {
  @apply flex items-center justify-center gap-1;
}
.phase-label {
  @apply text-xs font-semibold text-gray-500 dark:text-gray-400 min-w-[16px];
}
.temp-row .value-number {
  @apply text-lg;
}
.temp-row .value-unit {
  @apply text-xs;
}

/* Data table */
.data-table {
  @apply bg-gray-50 dark:bg-gray-700/50 rounded-lg overflow-hidden;
  @apply border border-gray-200 dark:border-gray-600;
  @apply w-[240px] flex-shrink-0;
}
.table-header {
  @apply bg-gray-100 dark:bg-gray-600 px-3 py-2 border-b border-gray-200 dark:border-gray-500;
}
.table-title {
  @apply text-sm font-bold text-gray-700 dark:text-gray-200;
}
.table-content {
  @apply p-3;
}
.data-row {
  @apply flex justify-between items-center;
  @apply py-1 border-b border-gray-200/50 dark:border-gray-600/50 last:border-b-0;
  @apply rounded px-2 -mx-2 min-h-[2rem];
}
.data-label {
  @apply text-sm font-medium text-gray-600 dark:text-white flex-1;
}
.data-value {
  @apply text-sm font-bold text-gray-800 dark:text-gray-100 flex items-baseline gap-1;
}
.data-unit {
  @apply text-xs font-semibold text-gray-500 dark:text-white;
}

/* Responsive */
@media (max-width: 768px) {
  .equipment-info {
    @apply flex-col text-center gap-2;
  }
  .data-section {
    @apply flex-col;
  }
  .status-cards {
    @apply w-full;
  }
  .data-table {
    @apply w-full;
  }
}
</style>
