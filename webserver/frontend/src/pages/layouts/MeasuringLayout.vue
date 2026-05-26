<template>
  <div class="grid grid-cols-12 gap-x-4 gap-y-4">
    <!-- 상단 카드들: [Meter 4] [Power 4] [PQ 4] -->
    <MeasCard_Voltage
      v-if="channelState.MainEnable || channelState.SubEnable"
      :channel="computedChannel"
    />
    <MeasCard_PowerFactor
      v-if="channelState.MainEnable || channelState.SubEnable"
      :channel="computedChannel"
    />
    <MeasCard_PQ
      v-if="channelState.MainEnable || channelState.SubEnable"
      :channel="computedChannel"
    />

    <!-- 하단 카드들: [Energy 7] [EventLog 5] -->
    <div
      v-if="channelState.MainEnable || channelState.SubEnable"
      class="col-span-full grid grid-cols-12 gap-x-4 gap-y-4 items-stretch"
    >
      <div class="col-span-full lg:col-span-7 flex">
        <MeasCard_Energy :channel="computedChannel" class="w-full" />
      </div>
      <div class="col-span-full lg:col-span-5 flex">
        <MeasCard_EventLog :channel="computedChannel" class="w-full" />
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import MeasCard_Voltage from '../../partials/modeview/dashboard2/MeasCard_Voltage.vue'
import MeasCard_PowerFactor from '../../partials/modeview/dashboard2/MeasCard_PowerFactor.vue'
import MeasCard_PQ from '../../partials/modeview/dashboard2/MeasCard_PQ.vue'
import MeasCard_Energy from '../../partials/modeview/dashboard2/MeasCard_Energy.vue'
import MeasCard_EventLog from '../../partials/modeview/dashboard2/MeasCard_EventLog.vue'

export default {
  name: 'MeasuringLayout',
  components: {
    MeasCard_Voltage,
    MeasCard_PowerFactor,
    MeasCard_PQ,
    MeasCard_Energy,
    MeasCard_EventLog,
  },
  props: {
    channelState: {
      type: Object,
      required: true,
    },
    channel: {
      type: String,
      required: true,
    },
  },
  setup(props) {
    const computedChannel = computed(() => {
      if (props.channel === 'Main' || props.channel === 'main')
        return 'Main'
      else
        return 'Sub'
    })

    return {
      computedChannel,
    }
  },
}
</script>
