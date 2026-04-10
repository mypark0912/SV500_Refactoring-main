<template>
  <div class="card-wrap">
    <div class="card-header">
      <h3 class="card-title meter-accent-blue">
        {{ t('report.cardTitle.Channel') }}
      </h3>
    </div>
    <div class="card-body">
      <!-- 첫 번째 줄: 장비 정보 -->
      <div class="info-row">
        <img :src="equipImageSrc" alt="장비 이미지" class="equip-image" />

        <div class="info-block">
          <span class="info-label">{{ assetType }}</span>
          <span class="info-value">{{ assetNickname }}</span>
        </div>

        <div v-if="!assetType?.includes('Transformer')" class="info-block">
          <span class="info-label">{{ t('diagnosis.info.drivetype') }}</span>
          <span class="info-value">
            {{ drType == 'DOL' ? t('diagnosis.info.dr1') : t('diagnosis.info.dr2') }}
          </span>
        </div>

        <div v-if="devLocation != ''" class="info-block">
          <span class="info-label">{{ t('report.cardTitle.installation') }}</span>
          <span class="info-value">{{ devLocation }}</span>
        </div>
      </div>

      <!-- 두 번째 줄: 측정 데이터들 -->
      <div class="data-row">
        <div
          v-for="item in rawdata"
          :key="item.Name"
          class="info-block"
        >
          <span class="info-label">{{ t(`dashboard.transDiag.${item.Name}`) }}</span>
          <span class="info-value">{{ item.Value }} {{ item.Unit }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import axios from 'axios'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useSetupStore } from '@/store/setup'
import motorImg from '@/images/motor_m.png'
import fanImg from '@/images/fan_m.png'
import pumpImg from '@/images/pump_m.png'
import compImg from '@/images/comp_m.png'
import powerImg from '@/images/power_m.png'
import defaultImg from '@/images/cleaned_logo.png'
import transImg from '@/images/trans.png'

export default {
  name: 'Report_Info',
  props: {
    channel: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const { t } = useI18n()
    const channel = ref(props.channel)
    const setupStore = useSetupStore()
    const route = useRoute()
    const rawdata = ref([])
    const drType = ref('')
    const assetType = computed(() => {
      return channel.value == 'Main' ? AssetInfo.value.assetType_main : AssetInfo.value.assetType_sub
    })
    const assetNickname = computed(() => {
      return channel.value == 'Main' ? AssetInfo.value.assetNickname_main : AssetInfo.value.assetNickname_sub
    })

    const AssetInfo = computed(() => {
      return setupStore.getAssetConfig
    })

    const devLocation = computed(() => {
      return setupStore.getDevLocation
    })

    const equipImageSrc = computed(() => {
      const eqType = channel.value.toLowerCase() == 'main' ? AssetInfo.value.assetType_main : AssetInfo.value.assetType_sub
      switch (eqType) {
        case 'Motor': return motorImg
        case 'MotorFeed': return motorImg
        case 'Pump': return pumpImg
        case 'Fan': return fanImg
        case 'Compressor': return compImg
        case 'PSupply': return powerImg
        case 'PowerSupply': return powerImg
        case 'PrimaryTransformer': return transImg
        case 'Transformer': return transImg
        default: return defaultImg
      }
    })

    const fetchAsset = async () => {
      if (!AssetInfo.value)
        await setupStore.checkSetting()
      const chName = channel.value.toLowerCase() == 'main' ? AssetInfo.value.assetName_main : AssetInfo.value.assetName_sub

      if (chName != '') {
        try {
          const response = await axios.get(`/api/getAsset/${chName}`)
          if (response.data.success) {
            rawdata.value = response.data.data
            drType.value = response.data.driveType
          } else {
            console.log('No Data')
          }
        } catch (error) {
          console.log('데이터 가져오기 실패:', error)
        }
      } else {
        alert('There are no registered Asset.')
      }
    }

    onMounted(() => {
      fetchAsset()
    })

    watch(() => route.params.channel, async (newChannel) => {
      channel.value = newChannel
      await fetchAsset()
    })

    return {
      channel,
      rawdata,
      t,
      AssetInfo,
      equipImageSrc,
      fetchAsset,
      devLocation,
      drType,
      assetType,
      assetNickname,
    }
  }
}
</script>

<style scoped>
.card-wrap {
  @apply col-span-full xl:col-span-12;
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
.meter-accent-blue::before {
  @apply bg-blue-500;
}
.card-body {
  @apply px-4 py-3 space-y-4;
}

/* 정보 행 */
.info-row {
  @apply flex gap-6 items-start;
}
.data-row {
  @apply flex gap-6 overflow-x-auto;
}
.info-block {
  @apply min-w-[120px] flex flex-col space-y-1 flex-shrink-0;
}
.info-label {
  @apply text-xs font-bold text-gray-500 dark:text-gray-400 uppercase whitespace-nowrap;
}
.info-value {
  @apply text-lg font-bold text-gray-800 dark:text-gray-100;
}
.equip-image {
  @apply w-14 h-14 object-cover rounded-lg shadow-md border border-gray-300 dark:border-gray-600;
}

/* 반응형 */
@media (max-width: 640px) {
  .info-row {
    @apply flex-wrap;
  }
  .data-row {
    @apply flex-wrap;
  }
}
</style>
