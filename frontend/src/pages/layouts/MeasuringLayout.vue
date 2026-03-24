<template>
  <div class="grid grid-cols-12 gap-x-4 gap-y-4">
    <!-- Row 1: 전압(2) / 전류(2) / 주파수(2) / 역률·유효전력(3) / 불평형률·고조파(3) -->
    <MeasCard_Voltage
      v-if="channelState.MainEnable || channelState.SubEnable"
      :channel="computedChannel"
    />
    <MeasCard_Current
      v-if="channelState.MainEnable || channelState.SubEnable"
      :channel="computedChannel"
    />
    <MeasCard_Frequency
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

    <!-- Row 2: 전력량(7) / 알람·이벤트 로그(5) -->
    <MeasCard_Energy
      v-if="channelState.MainEnable || channelState.SubEnable"
      :channel="computedChannel"
    />
    <MeasCard_EventLog
      v-if="channelState.MainEnable || channelState.SubEnable"
      :channel="computedChannel"
    />
  </div>
</template>

<script>
import { computed } from 'vue'
import MeasCard_Voltage from '../../partials/modeview/dashboard2/MeasCard_Voltage.vue'
import MeasCard_Current from '../../partials/modeview/dashboard2/MeasCard_Current.vue'
import MeasCard_Frequency from '../../partials/modeview/dashboard2/MeasCard_Frequency.vue'
import MeasCard_PowerFactor from '../../partials/modeview/dashboard2/MeasCard_PowerFactor.vue'
import MeasCard_PQ from '../../partials/modeview/dashboard2/MeasCard_PQ.vue'
import MeasCard_Energy from '../../partials/modeview/dashboard2/MeasCard_Energy.vue'
import MeasCard_EventLog from '../../partials/modeview/dashboard2/MeasCard_EventLog.vue'

export default {
  name: 'MeasuringLayout',
  components: {
    MeasCard_Voltage,
    MeasCard_Current,
    MeasCard_Frequency,
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
