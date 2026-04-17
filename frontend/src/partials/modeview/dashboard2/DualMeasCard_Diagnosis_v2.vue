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
          {{ channel == 'main' ? t('dashboard.diagnosis.subtitle_main') : t('dashboard.diagnosis.subtitle_sub') }}
        </span>
      </div>
    </div>

    <div class="card-body" v-if="DiagEnable">
      <!-- 1) 풀폭 Equipment 헤더 -->
      <div class="equip-header">
        <div class="equip-avatar">
          <img class="avatar-image" :src="motorImageSrc" :alt="stData.devType" />
        </div>
        <div class="equip-info">
          <h3 class="equip-name">{{ stData.devNickname }}</h3>
          <span class="equip-type">{{ stData.devType }}</span>
        </div>
        <span class="run-badge" :class="isRunning ? 'run-on' : 'run-off'">
          <span class="run-dot"></span>
          {{ isRunning ? t('dashboard.singleinfo.running') : t('dashboard.singleinfo.stopped') }}
        </span>
      </div>

      <!-- 2) 좌우 2컬럼 -->
      <div class="body-split">
        <!-- 좌: 운용 현황 (리스트) -->
        <div class="metric-card">
          <div class="metric-rows">
            <template v-if="stData.devType.includes('Transformer')">
              <div v-if="hasTempData" v-for="(label, index) in ['R', 'S', 'T']" :key="`temp-${index}`" class="metric-row">
                <span class="metric-label">Temp {{ label }}</span>
                <span class="metric-value">
                  {{ Number(transData.Temp?.[index]) < -900 ? '-' : Number(transData.Temp?.[index]).toFixed(2) }}
                  <span class="metric-unit">℃</span>
                </span>
              </div>
              <div class="metric-row">
                <span class="metric-label">{{ t('dashboard.transDiag.LoadFactor') }}</span>
                <span class="metric-value">{{ LoadRate }} <span class="metric-unit">%</span></span>
              </div>
              <div class="metric-row">
                <span class="metric-label">{{ t('dashboard.transDiag.Ig') }}</span>
                <span class="metric-value">{{ transData.Ig?.toFixed(1) || 0 }} <span class="metric-unit">A</span></span>
              </div>
            </template>
            <template v-else>
              <div class="metric-row">
                <span class="metric-label">{{ t('dashboard.singleinfo.Operatingtime') }}</span>
                <span class="metric-value">{{ stData.runhour }} <span class="metric-unit">hrs</span></span>
              </div>
              <template v-if="transData.length > 0">
                <div class="metric-row">
                  <span class="metric-label">{{ t('dashboard.transDiag.Ig') }}</span>
                  <span class="metric-value">{{ stData.Ig }} <span class="metric-unit">A</span></span>
                </div>
                <div v-for="(item, idx) in transData.slice(0, 3)" :key="`td-${idx}`" class="metric-row">
                  <span class="metric-label">{{ item.Assembly }} : {{ item.Title }}</span>
                  <span class="metric-value">
                    {{ (parseFloat(item?.Value) || 0).toFixed(1) }}
                    <span class="metric-unit">{{ item?.Unit || '' }}</span>
                  </span>
                </div>
              </template>
            </template>
          </div>
        </div>

        <!-- 우: 상태 2개 (신호등) 인라인 컴팩트 -->
        <div class="status-stack">
          <div class="status-row">
            <span class="status-title">{{ t('dashboard.diagnosis.diagnostic') }}</span>
            <div class="status-dots">
              <div
                v-for="(item, idx) in diagStatuses"
                :key="`d-${idx}`"
                class="status-dot-item"
                :class="{ 'is-active': stData.devStatus === idx + 1 }"
              >
                <span
                  class="dot"
                  :class="stData.devStatus === idx + 1 ? item.fill : 'dot-inactive'"
                ></span>
                <span class="dot-label">{{ item.text }}</span>
              </div>
            </div>
          </div>
          <div class="status-row">
            <span class="status-title">{{ t('dashboard.diagnosis.pq') }}</span>
            <div class="status-dots">
              <div
                v-for="(item, idx) in pqStatuses"
                :key="`p-${idx}`"
                class="status-dot-item"
                :class="{ 'is-active': pqData.devStatus === idx + 1 }"
              >
                <span
                  class="dot"
                  :class="pqData.devStatus === idx + 1 ? item.fill : 'dot-inactive'"
                ></span>
                <span class="dot-label">{{ item.text }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import motorImg from '@/images/motor_m.png'
import fanImg from '@/images/fan_m.png'
import pumpImg from '@/images/pump_m.png'
import compImg from '@/images/comp_m.png'
import powerImg from '@/images/power_m.png'
import defaultImg from '@/images/cleaned_logo.png'
import transImg from '@/images/trans.png'
import { ref, computed, watchEffect, onMounted, onUnmounted, watch } from 'vue'
import { useSetupStore } from '@/store/setup'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { useRealtimeStore } from '@/store/realtime'

export default {
  name: 'DualMeasCard_Diagnosis_v2',
  props: {
    channel: String,
  },
  setup(props) {
    const { t } = useI18n()
    const channel = ref(props.channel)

    const stData = ref({
      devName: '',
      devType: '',
      devStatus: -2,
      devNickname: '',
      Ig: 0,
      runhour: 0,
    })
    const pqData = ref({
      devName: '',
      devStatus: -2,
    })
    const DiagEnable = ref(false)
    const isModule = ref(false)
    const moduleStatuses = ref([])
    const isRunning = ref(false)
    const LoadRate = ref(0)
    const setupStore = useSetupStore()
    const channelStatus = computed(() => setupStore.getChannelSetting)
    const asset = computed(() => setupStore.getAssetConfig)
    const assetTypes = ref('')
    const store = useRealtimeStore()

    const meterDictMain = computed(() => store.getChannelData('Main') || {})
    const meterDictSub = computed(() => store.getChannelData('Sub') || {})

    let updateInterval = null
    let runningInterval = null
    const transData = ref({})

    const computedChannel = computed(() => channel.value == 'main' || channel.value == 'Main' ? 'Main' : 'Sub')

    const motorImageSrc = computed(() => {
      switch (stData.value.devType) {
        case 'Motor':
        case 'MotorFeed': return motorImg
        case 'Pump': return pumpImg
        case 'Fan': return fanImg
        case 'Compressor': return compImg
        case 'PSupply':
        case 'PowerSupply': return powerImg
        case 'PrimaryTransformer':
        case 'Transformer': return transImg
        default: return defaultImg
      }
    })

    const hasTempData = computed(() => transData.value?.Temp?.length > 0)

    const LoadFactor = computed(() => {
      let kva = -1
      if (computedChannel.value == 'Main' && stData.value.devType?.includes('Transformer')) {
        kva = setupStore.getMkva
      }
      if (computedChannel.value == 'Sub' && stData.value.devType?.includes('Transformer')) {
        kva = setupStore.getSkva
      }
      return kva
    })

    watch(
      () => LoadFactor.value,
      (newVal) => {
        if (newVal > 0 && transData.value?.Stotal) {
          LoadRate.value = (((transData.value.Stotal / 1000) / newVal) * 100).toFixed(1)
        }
      },
      { immediate: true }
    )

    const fetchModuleStatus = async () => {
      const chName = channel.value.toLowerCase() == 'main' ? 'Main' : 'Sub'
      try {
        const response = await axios.get(`/api/getModuleStatus/${chName}`)
        if (response.data.exist) {
          isModule.value = true
          if (Array.isArray(response.data.data)) {
            const seen = new Set()
            moduleStatuses.value = response.data.data.filter(m => {
              if (seen.has(m.devId)) return false
              seen.add(m.devId)
              return true
            })
          }
        } else {
          isModule.value = false
        }
      } catch (error) {
        isModule.value = false
      }
    }

    const fetchDashData = async () => {
      if (!asset.value || (!asset.value.assetName_main && !asset.value.assetName_sub)) return
      const chName = channel.value == 'main' ? asset.value.assetName_main : asset.value.assetName_sub
      const chType = channel.value == 'main' ? asset.value.assetType_main : asset.value.assetType_sub
      const chNick = channel.value == 'main' ? asset.value.assetNickname_main : asset.value.assetNickname_sub
      const channelName = channel.value == 'main' ? 'Main' : 'Sub'
      try {
        const response = await axios.get(`/api/getDashSatatus/${chName}/${channelName}`)
        if (response.data.status >= 0) {
          stData.value.devName = chName
          stData.value.devType = chType
          stData.value.devStatus = response.data.data['Diagnostic']['status']
          stData.value.devNickname = chNick
          stData.value.runhour = response.data.runhours
          if (assetTypes.value.includes('Transformer')) {
            if (channelName == 'Main') {
              transData.value = { Temp: meterDictMain.value.Temp2, Ig: meterDictMain.value.Ig, Stotal: meterDictMain.value.S4 }
            } else {
              transData.value = { Temp: meterDictSub.value.Temp2, Ig: meterDictSub.value.Ig, Stotal: meterDictSub.value.S4 }
            }
          } else {
            stData.value.Ig = channelName === 'Main' ? meterDictMain.value.Ig : meterDictSub.value.Ig
          }
          pqData.value.devName = response.data.data['PQ']['item']
          pqData.value.devStatus = response.data.data['PQ']['status']
        }
      } catch (error) {
        console.log('데이터 가져오기 실패:', error)
      }
    }

    const fetchRealData = async () => {
      if (!asset.value || (!asset.value.assetName_main && !asset.value.assetName_sub)) return
      const chName = channel.value == 'main' ? asset.value.assetName_main : asset.value.assetName_sub
      const chType = channel.value == 'main' ? asset.value.assetType_main : asset.value.assetType_sub
      if (chName !== '') {
        try {
          const response = await axios.get(`/api/getRealTime/${chType}/${chName}`)
          if (response.data.success) {
            transData.value['realtime'] = response.data.data
          }
        } catch (error) {
          console.log('데이터 가져오기 실패:', error)
        }
      }
    }

    const fetchRunning = async () => {
      try {
        const response = await axios.get(`/api/getEquipStatus/${computedChannel.value}`)
        if (response.data.success) {
          isRunning.value = response.data.status
        }
      } catch (error) {
        // noop
      }
    }

    watch(asset, (newVal) => {
      if (newVal) {
        assetTypes.value = channel.value == 'main' ? newVal.assetType_main : newVal.assetType_sub
        fetchDashData()
        fetchModuleStatus()
        if (!assetTypes.value.includes('Transformer')) {
          fetchRealData()
        }
        if (updateInterval) {
          clearInterval(updateInterval)
          updateInterval = null
        }
        updateInterval = setInterval(async () => {
          await fetchDashData()
          await fetchModuleStatus()
          if (!assetTypes.value.includes('Transformer')) {
            await fetchRealData()
          }
        }, 60000)
      }
    }, { immediate: true })

    onMounted(async () => {
      await setupStore.checkSetting()
      await fetchRunning()
      runningInterval = setInterval(fetchRunning, 300000)
    })

    onUnmounted(() => {
      if (updateInterval) {
        clearInterval(updateInterval)
        updateInterval = null
      }
      if (runningInterval) {
        clearInterval(runningInterval)
        runningInterval = null
      }
    })

    watchEffect(() => {
      if (channel.value == 'main')
        DiagEnable.value = channelStatus.value.MainDiagnosis
      else
        DiagEnable.value = channelStatus.value.SubDiagnosis
    })

    // transData for non-transformer uses realtime array, otherwise transformer object
    const resolvedTransData = computed(() => {
      if (!transData.value) return []
      if (stData.value.devType?.includes('Transformer')) return transData.value
      return transData.value.realtime || []
    })

    const fills = ['bg-emerald-500', 'bg-amber-400', 'bg-orange-500', 'bg-red-500']
    const diagStatuses = computed(() => [
      { text: t('dashboard.diagnosis.st1'), fill: fills[0] },
      { text: t('dashboard.diagnosis.st2'), fill: fills[1] },
      { text: t('dashboard.diagnosis.st3'), fill: fills[2] },
      { text: t('dashboard.diagnosis.st4'), fill: fills[3] },
    ])
    const pqStatuses = computed(() => [
      { text: t('dashboard.diagnosis.st1'), fill: fills[0] },
      { text: t('dashboard.diagnosis.st2'), fill: fills[1] },
      { text: t('dashboard.diagnosis.st3'), fill: fills[2] },
      { text: t('dashboard.diagnosis.st4'), fill: fills[3] },
    ])

    return {
      channel, stData, pqData, DiagEnable, transData: resolvedTransData, t,
      isModule, moduleStatuses, asset,
      motorImageSrc, hasTempData, isRunning, LoadRate,
      diagStatuses, pqStatuses,
    }
  },
}
</script>

<style scoped>
.card-wrap {
  @apply col-span-full sm:col-span-6 xl:col-span-6;
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
  @apply text-xs text-gray-500 dark:text-gray-400;
}
.card-body {
  @apply px-4 py-3 space-y-3;
}

/* Module badges */
.module-badges { @apply flex items-center gap-1; }
.module-badge {
  @apply inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full;
  @apply text-xs font-medium border;
}
.badge-on { @apply border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20; }
.badge-off { @apply border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800; }
.badge-on .module-dot { @apply w-1.5 h-1.5 rounded-full bg-green-500; }
.badge-off .module-dot { @apply w-1.5 h-1.5 rounded-full bg-gray-400; }
.module-name { @apply text-gray-600 dark:text-gray-400; }

/* Equipment header - 풀폭 */
.equip-header {
  @apply flex items-center gap-3 p-3 rounded-lg;
  @apply bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm;
}
.equip-avatar { @apply flex-shrink-0; }
.avatar-image {
  @apply w-10 h-10 rounded-lg object-contain;
  @apply shadow-sm border border-gray-200 dark:border-gray-600;
}
.equip-info { @apply flex flex-col min-w-0 flex-1; }
.equip-name {
  @apply text-base font-bold text-gray-800 dark:text-white leading-tight truncate;
}
.equip-type {
  @apply text-xs font-semibold text-blue-500 dark:text-blue-400;
  @apply bg-blue-100 dark:bg-blue-700 px-2 py-0.5 rounded-md;
  @apply inline-block w-fit mt-0.5;
}
.run-badge {
  @apply flex items-center gap-1.5 px-2.5 py-1 rounded-full;
  @apply font-semibold text-xs border-2 whitespace-nowrap flex-shrink-0;
}
.run-dot { @apply w-1.5 h-1.5 rounded-full animate-pulse; }
.run-on {
  @apply bg-green-50 dark:bg-green-900/30 border-green-500 dark:border-green-600;
  @apply text-green-700 dark:text-green-300;
}
.run-on .run-dot { @apply bg-green-500; }
.run-off {
  @apply bg-gray-50 dark:bg-gray-700/30 border-gray-400 dark:border-gray-500;
  @apply text-gray-700 dark:text-gray-300;
}
.run-off .run-dot { @apply bg-gray-400 animate-none; }

/* Body split : 좌 metric 좁게, 우 status 넓게 */
.body-split {
  @apply grid grid-cols-1 gap-3;
}
@media (min-width: 1024px) {
  .body-split {
    grid-template-columns: minmax(180px, 0.7fr) 1.3fr;
  }
}

/* Metric list card (운용 현황) */
.metric-card {
  @apply bg-white dark:bg-gray-800 rounded-lg overflow-hidden;
  @apply border border-gray-200 dark:border-gray-700;
}
.metric-rows {
  @apply divide-y divide-gray-100 dark:divide-gray-700;
}
.metric-row {
  @apply flex justify-between items-center px-3 py-2;
}
.metric-label {
  @apply text-sm text-gray-600 dark:text-gray-300;
}
.metric-value {
  @apply text-sm font-bold text-gray-900 dark:text-white tabular-nums;
}
.metric-unit {
  @apply text-xs font-medium text-gray-500 dark:text-gray-400 ml-0.5;
}

/* Status stack : 각 신호등을 독립 카드처럼 */
.status-stack {
  @apply flex flex-col gap-2;
}
.status-row {
  @apply flex items-center gap-3 px-3 pt-6 pb-5 flex-1;
  @apply bg-white dark:bg-gray-800 rounded-lg;
  @apply border border-gray-200 dark:border-gray-700;
}
.status-title {
  @apply text-[13px] font-bold text-gray-700 dark:text-white flex-shrink-0;
  @apply w-16;
}
.status-dots {
  @apply grid grid-cols-4 gap-2 flex-1;
}
.status-dot-item {
  @apply flex flex-col items-center gap-2 transition-transform duration-200;
}
.status-dot-item.is-active {
  @apply scale-110;
}
.dot {
  @apply w-5 h-5 rounded-full shadow-sm transition-all duration-200;
}
.dot-inactive {
  @apply bg-gray-300 dark:bg-gray-600;
}
.status-dot-item.is-active .dot {
  @apply shadow-md;
}
.dot-label {
  @apply text-[11px] font-medium text-gray-500 dark:text-gray-400 leading-none;
}
.status-dot-item.is-active .dot-label {
  @apply text-gray-900 dark:text-white font-semibold;
}

@media (max-width: 640px) {
  .card-wrap { @apply col-span-full; }
}
</style>
