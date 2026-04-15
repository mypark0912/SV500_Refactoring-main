<template>
  <div class="grid grid-cols-12 gap-x-4 gap-y-4">
    <!-- 메인 채널 -->
    <DualMeasCard_Meter
      v-if="channelState.MainEnable"
      :channel="'main'"
    />
    <DualMeasCard_Diagnosis
      v-if="channelState.MainDiagnosis"
      :channel="'main'"
    />

    <!-- 서브 채널 -->
    <DualMeasCard_Meter
      v-if="channelState.SubEnable"
      :channel="'sub'"
    />
    <DualMeasCard_Diagnosis
      v-if="channelState.SubDiagnosis"
      :channel="'sub'"
    />
  </div>
</template>

<script>
<<<<<<< Updated upstream
import DualMeasCard_Meter from '../../partials/modeview/dashboard2/DualMeasCard_Meter.vue'
import DualMeasCard_Diagnosis from '../../partials/modeview/dashboard2/DualMeasCard_Diagnosis.vue'
=======
import DualMeasCard_Meter from '../../partials/modeview/dashboard2/DualMeasCard_Meter_v2.vue'
import DualMeasCard_Diagnosis from '../../partials/modeview/dashboard2/DualMeasCard_Diagnosis_v2.vue'
>>>>>>> Stashed changes

export default {
  name: 'DualChannel_NewCSS',
  components: {
    DualMeasCard_Meter,
    DualMeasCard_Diagnosis,
  },
  props: {
    channelState: {
      type: Object,
      required: true,
    },
  },
}
</script>
