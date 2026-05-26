<template>
    <div class="col-span-full xl:col-span-12 mt-1 p-2">
        <BarChart v-if="mode == 'Status'" :data="chartData" width="450" height="360" />
        <BarChart v-else-if="mode == 'PowerQuality'" :data="chartData" width="450" height="360" />
    </div>
</template>

<script>
import { ref, watch, computed } from 'vue'
import BarChart from '../../../charts/connect/BatteryCharger_Compact.vue'
import { tailwindConfig } from '../../../utils/Utils'
import { useI18n } from 'vue-i18n'

export default {
  name: 'Diagnosis_BarChart_Compact',
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
    }
  },
  components: {
    BarChart,
  },
  setup(props) {
    const { t } = useI18n()
    const channel = ref('');
    channel.value = props.channel;
    const mode = ref(props.mode);

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
      }
    }, { immediate: true, deep: true })

    return {
      chartData,
      channel,
      mode,
      t,
    }
  }
}
</script>
