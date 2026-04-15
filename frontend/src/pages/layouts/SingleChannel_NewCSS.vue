<template>
  <div class="grid grid-cols-12 gap-x-4 gap-y-4">
    <!-- 1채널 전용 레이아웃 - 카드들이 더 크게 표시 -->
    <DashboardCard_Meter_Single v-if="channelState.MainEnable" :channel="channel" />
    <DashboardCard_Meter_Single v-else-if="channelState.SubEnable" :channel="channel" />

    <DashboardCard_PQ_Claude
      v-if="channelState.MainEnable" :asset="computedAssetName"
      :channel="computedChannel"
    />
    <DashboardCard_PQ_Claude
      v-else-if="channelState.SubEnable" :asset="computedAssetName"
      :channel="computedChannel"
    />

    <Dashboard_TransInfo_final v-if="computedType === 'Transformer' && channelState.MainDiagnosis"
      :channel="channel"
    />
    <Dashboard_TransInfo_final v-else-if="computedType === 'Transformer' && channelState.SubDiagnosis"
      :channel="channel"
    />

    <Dashboard_Single v-if="computedType !== 'Transformer' && channelState.MainDiagnosis"
      :channel="computedChannel"
    />
    <Dashboard_Single v-else-if="computedType !== 'Transformer' && channelState.SubDiagnosis"
      :channel="computedChannel"
    />

    <!-- 하단 카드들 -->
    <div
      v-if="channelState.MainEnable || channelState.SubEnable"
      class="col-span-full grid grid-cols-12 gap-x-4 gap-y-4 items-stretch"
    >
      <div class="col-span-full lg:col-span-7 flex">
        <DashboardCard_kwh :channel="computedChannel" class="w-full" />
      </div>
      <div class="col-span-full lg:col-span-5 flex">
        <DashboardCard_Diagnosis
          v-if="channelState.MainDiagnosis || channelState.SubDiagnosis"
          :channel="computedChannel"
          class="w-full"
        />
      </div>
    </div>
  </div>
</template>

<script>
import DashboardCard_Meter_Single from '../../partials/modeview/dashboard2/SingleMeasCard_Meter.vue'
import DashboardCard_PQ_Claude from '../../partials/modeview/dashboard2/SingleMeasCard_PQ.vue'
import Dashboard_TransInfo_final from '../../partials/modeview/dashboard2/SingleMeasCard_TransInfo.vue'
import Dashboard_Single from '../../partials/modeview/dashboard2/SingleMeasCard_Equip.vue'
import DashboardCard_kwh from '../../partials/modeview/dashboard2/SingleMeasCard_Energy.vue'
import DashboardCard_Diagnosis from '../../partials/modeview/dashboard2/SingleMeasCard_Diagnosis.vue'
import { useSetupStore } from '@/store/setup'
import { computed } from 'vue'

export default {
  name: 'SingleChannel_NewCSS',
  components: {
    DashboardCard_Meter_Single,
    DashboardCard_PQ_Claude,
    Dashboard_TransInfo_final,
    DashboardCard_kwh,
    DashboardCard_Diagnosis,
    Dashboard_Single,
  },
  props: {
    channelState: {
      type: Object,
      required: true
    },
    channel: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const setupStore = useSetupStore()
    const AssetInfo = computed(() => setupStore.getAssetConfig)

    const computedChannel = computed(() => {
      if (props.channel == 'Main' || props.channel == 'main')
        return 'Main'
      else
        return 'Sub'
    })

    const computedType = computed(() => computedChannel.value == 'Main' ? AssetInfo.value.assetType_main : AssetInfo.value.assetType_sub)
    const computedAssetName = computed(() => computedChannel.value == 'Main' ? AssetInfo.value.assetName_main : AssetInfo.value.assetName_sub)

    return {
      computedType,
      computedChannel,
      AssetInfo,
      computedAssetName,
    }
  }
}
</script>
