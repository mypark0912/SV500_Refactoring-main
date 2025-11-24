<template>
  <div class="grid grid-cols-12 gap-6">
    <!-- 1채널 전용 레이아웃 - 카드들이 더 크게 표시 -->
    <DashboardCard_Meter_Single v-if="channelState.MainEnable" :channel="channel" />
    <DashboardCard_Meter_Single v-else-if="channelState.SubEnable" :channel="channel" />
    
    <DashboardCard_PQ_Claude 
      v-if="channelState.MainEnable" 
      :channel="computedChannel"  
    />
    <DashboardCard_PQ_Claude 
      v-else-if="channelState.SubEnable" 
      :channel="computedChannel"  
    />
    
    <Dashboard_TransInfo_final v-if="computedType === 'Transformer' && channelState.MainDiagnosis"
      :channel="channel" 
    />
    <Dashboard_TransInfo_final v-else-if="computedType === 'Transformer' && channelState.Diagnosis"
      :channel="channel" 
    />
    
    <Dashboard_Single v-if="computedType !== 'Transformer' && channelState.MainDiagnosis"
      :channel="computedChannel" 
    />
    <Dashboard_Single v-else-if="computedType !== 'Transformer' && channelState.SubDiagnosis"
      :channel="computedChannel" 
    />
    
    <DashboardCard_kwh v-if="channelState.MainEnable"
      :channel="computedChannel" 
    />
    <DashboardCard_kwh v-else-if="channelState.SubEnable"
      :channel="computedChannel" 
    />
    
    <DashboardCard_Diagnosis v-if="channelState.MainEnable && channelState.MainDiagnosis"
      :channel="computedChannel" 
    />
    <DashboardCard_Diagnosis v-else-if="channelState.SubEnable && channelState.SubDiagnosis"
      :channel="computedChannel" 
    />
  </div>
</template>

<script>
import DashboardCard_Meter_Single from '../../partials/inners/dashboard/DashboardCard_Meter_Single.vue'
import DashboardCard_PQ_Claude from '../../partials/inners/dashboard/DashboardCard_PQ_Claude2.vue'
import Dashboard_TransInfo_final from '../../partials/inners/dashboard/Dashboard_TransInfo_final.vue'
//import Dashboard_Single_Info from '../../partials/inners/dashboard/Dashboard_Single_Info.vue'
import Dashboard_Single from '../../partials/inners/dashboard/Dashboard_Single.vue'
import DashboardCard_kwh from '../../partials/inners/dashboard/DashboardCard_kwh_realtime.vue'
import DashboardCard_Diagnosis from '../../partials/inners/dashboard/DashboardCard_Diagnosis.vue'
import { useSetupStore } from '@/store/setup'
import { computed, inject } from 'vue'

export default {
  name: 'SingleChannelLayout',
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
      console.log(props.channel);
      if (props.channel == 'Main' || props.channel == 'main')
        return 'Main'
      else
        return 'Sub'
    })
    console.log(computedChannel.value);
    const computedType = computed(()=> computedChannel.value == 'Main' ? AssetInfo.value.assetType_main: AssetInfo.value.assetType_sub)
    //const mainData = inject('meterDictMain');
    //const subData = inject('meterDictSub');
    return {
      //opMode,
      //mainData,
      //subData,
      computedType,
      computedChannel,
      AssetInfo,
    }
  }
}
</script>