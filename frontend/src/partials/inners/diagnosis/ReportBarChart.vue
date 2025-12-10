<template>
    <div 
      class="col-span-full xl:col-span-12 mt-1 p-1"
      :class="isPdfMode ? 'bg-white' : 'bg-white dark:bg-gray-800'"
    >
        <BarChart v-if="mode == 'Status'" :data="chartData" :width="chartWidth" :height="chartHeight" />
        <BarChart_PQ v-else-if="mode == 'PowerQuality'" :data="chartData" :mode="mode" :width="chartWidth" :height="chartHeight" />
        <BarChart_PQ v-else-if="mode == 'DiagnosisDetail'" :data="chartData" :mode="mode" :width="chartWidth" :height="chartHeight" />
        <BarChart_FaultEvent v-else-if="mode == 'Fault'" :data="chartData" :width="chartWidth" :height="chartHeight" />
        <BarChart_Event_Claude v-else :data="chartData" :width="chartWidth" :height="chartHeight" />
    </div>
</template>

<script>
import { ref, watch, computed, inject } from 'vue'
import BarChart from '../../../charts/connect/BatteryCharger.vue'
import BarChart_PQ from '../../../charts/connect/BarChart_PQ_Report.vue'
import BarChart_FaultEvent from '../../../charts/connect/BarChart_FaultEvent.vue'
import BarChart_Event_Claude from '../../../charts/connect/BarChart_Event_Claude.vue'

// Import utilities
import { tailwindConfig } from '../../../utils/Utils'

export default {
  name: 'Diagnosis_BarChart2',
  props: {
    data: {
      type: Object,
      default: () => {} 
    },
    channel: {
      type: String,
      default: ''
    },
    mode: {
      type: String,
      default: ''
    },
    width: {
      type: [Number, String],
      default: 450
    },
    height: {
      type: [Number, String],
      default: 250  // 기본값을 250으로 줄임
    }
  },
  components: {
    BarChart,
    BarChart_PQ,
    BarChart_FaultEvent,
    BarChart_Event_Claude
  },
  setup(props) {
    const isPdfMode = inject('isPdfMode', false)
    
    const channel = ref('');
    channel.value = props.channel;
    const mode = ref(props.mode);
    
    // 차트 크기 computed
    const chartWidth = computed(() => props.width)
    const chartHeight = computed(() => props.height)
    
    const chartData = ref({
      labels: [],
      datasets: [
        {
          label: 'Direct',
          data: [],
          backgroundColor: tailwindConfig().theme.colors.sky[500],
          hoverBackgroundColor: tailwindConfig().theme.colors.sky[600],
          barPercentage: 0.7,
          categoryPercentage: 0.7,
          borderRadius: 4,
        },
      ],
      titles: []
    })

    const isDataValid = computed(() => {
      return props.data && 
             props.data.Names && 
             Array.isArray(props.data.Names) &&
             props.data.Values && 
             Array.isArray(props.data.Values) &&
             props.data.Names.length > 0 &&
             props.data.Values.length > 0
    })

    watch(() => props.data, (newData) => {
      if (isDataValid.value) {
        chartData.value = {
          labels: newData.Names,
          datasets: [
            {
              label: 'Direct',
              data: newData.Values,
              backgroundColor: tailwindConfig().theme.colors.sky[500],
              hoverBackgroundColor: tailwindConfig().theme.colors.sky[600],
              barPercentage: 0.7,
              categoryPercentage: 0.7,
              borderRadius: 4,
            },
          ],
          titles: newData.Titles || []
        }
        console.log('Chart data updated:', chartData.value)
      }
    }, { immediate: true, deep: true })

    return {
      chartData,
      channel,
      mode,
      isPdfMode,
      chartWidth,
      chartHeight,
    }    
  }
}
</script>