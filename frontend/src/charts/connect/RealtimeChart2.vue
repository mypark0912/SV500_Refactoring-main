<template>
  <div class="grow">
    <canvas ref="canvas" :width="width" :height="height"></canvas>
  </div>
</template>

<script>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useDark } from '@vueuse/core'
import { chartColors } from '../ChartjsConfig'

import {
  Chart, LineController, LineElement, PointElement, LinearScale, TimeScale, Tooltip,
} from 'chart.js'
import 'chartjs-adapter-moment'

// Import utilities
import { tailwindConfig, hexToRGB, formatValue } from '../../utils/Utils'

Chart.register(LineController, LineElement, PointElement, LinearScale, TimeScale, Tooltip)

export default {
  name: 'RealtimeChart',
  props: ['data', 'width', 'height'],
  setup(props) {

    const canvas = ref(null)
    const chartValue = ref(null)
    const chartDeviation = ref(null)
    let chart = null
    const darkMode = useDark()
    const { textColor, gridColor, tooltipTitleColor, tooltipBodyColor, tooltipBgColor, tooltipBorderColor } = chartColors

    // function that updates header values
    const handleHeaderValues = (data, chartValue, chartDeviation) => {
      const currentValue = data.datasets[0].data[data.datasets[0].data.length - 1]
      const previousValue = data.datasets[0].data[data.datasets[0].data.length - 2]
      const diff = ((currentValue - previousValue) / previousValue) * 100
      chartValue.value.innerHTML = data.datasets[0].data[data.datasets[0].data.length - 1]
      if (diff < 0) {
        chartDeviation.value.style.backgroundColor = `rgba(${hexToRGB(tailwindConfig().theme.colors.red[500])}, 0.2)`
        chartDeviation.value.style.color = tailwindConfig().theme.colors.red[700];
      } else {
        chartDeviation.value.style.backgroundColor = `rgba(${hexToRGB(tailwindConfig().theme.colors.green[500])}, 0.2)`
        chartDeviation.value.style.color = tailwindConfig().theme.colors.green[700];
      }      
      chartDeviation.value.innerHTML = `${diff > 0 ? '+' : ''}${diff.toFixed(2)}%`
    }    

    // 데이터 값의 범위를 체크하여 적절한 포맷 결정
    const getTickFormat = (value, allValues) => {
      // 데이터가 없거나 빈 배열인 경우 기본 포맷 반환
      if (!allValues || allValues.length === 0) {
        return value.toFixed(2)
      }
      
      // 숫자 값만 필터링 (객체인 경우 y 값 추출)
      const numericValues = allValues.map(v => {
        if (typeof v === 'number') return v
        if (v && typeof v === 'object' && 'y' in v) return v.y
        return 0
      }).filter(v => typeof v === 'number' && !isNaN(v))
      
      if (numericValues.length === 0) {
        return value.toFixed(2)
      }
      
      const maxValue = Math.max(...numericValues.map(v => Math.abs(v)))
      
      // 매우 작은 값들 (0.0001 미만)
      if (maxValue < 0.0001) {
        return value.toExponential(2)
      }
      // 작은 값들 (0.01 미만)
      else if (maxValue < 0.01) {
        return value.toFixed(4)
      }
      // 소수점 값들 (1 미만)
      else if (maxValue < 1) {
        return value.toFixed(3)
      }
      // 작은 정수 값들 (100 미만)
      else if (maxValue < 100) {
        return value.toFixed(2)
      }
      // 중간 값들 (10000 미만)
      else if (maxValue < 10000) {
        return value.toFixed(1)
      }
      // 큰 값들
      else {
        return value.toFixed(0)
      }
    }
    
    onMounted(() => {
      const ctx = canvas.value
      chart = new Chart(ctx, {
        type: 'line',
        data: props.data,
        options: {
          layout: {
            padding: 20,
          },
          scales: {
            y: {
              border: {
                display: false,
              },
              // suggestedMin, suggestedMax 제거 - 자동 스케일링 사용
              ticks: {
                maxTicksLimit: 5,
                callback: function(value) {
                  // 차트 데이터가 있는지 확인
                  if (!this.chart || !this.chart.data || !this.chart.data.datasets || 
                      !this.chart.data.datasets[0] || !this.chart.data.datasets[0].data ||
                      this.chart.data.datasets[0].data.length === 0) {
                    return value.toFixed(2)
                  }
                  const allValues = this.chart.data.datasets[0].data
                  return getTickFormat(value, allValues)
                },
                color: darkMode.value ? textColor.dark : textColor.light,
              },
              grid: {
                color: darkMode.value ? gridColor.dark : gridColor.light,
              },              
            },
            x: {
              type: 'time',
              time: {
                parser: 'hh:mm:ss',
                unit: 'second',
                tooltipFormat: 'MMM DD, H:mm:ss a',
                displayFormats: {
                  second: 'H:mm:ss',
                },
              },
              border: {
                display: false,
              },
              grid: {
                display: false,
              },
              ticks: {
                autoSkipPadding: 48,
                maxRotation: 0,
                color: darkMode.value ? textColor.dark : textColor.light,
              },
            },
          },
          plugins: {
            legend: {
              display: false,
            },
            datalabels: {
              display: false  // ✅ 표시 비활성화
            },
            tooltip: {
              titleFont: {
                weight: 600,
              },
              callbacks: {
                label: (context) => {
                  const value = context.parsed.y
                  const allValues = context.chart.data.datasets[0].data
                  return getTickFormat(value, allValues)
                },
              },
              titleColor: darkMode.value ? tooltipTitleColor.dark : tooltipTitleColor.light,
              bodyColor: darkMode.value ? tooltipBodyColor.dark : tooltipBodyColor.light,
              backgroundColor: darkMode.value ? tooltipBgColor.dark : tooltipBgColor.light,
              borderColor: darkMode.value ? tooltipBorderColor.dark : tooltipBorderColor.light,               
            },
          },
          interaction: {
            intersect: false,
            mode: 'nearest',
          },
          animation: false,
          maintainAspectRatio: false,
        },
      })
      // output header values
      //handleHeaderValues(props.data, chartValue, chartDeviation)
    })

    onUnmounted(() => chart.destroy())

    watch(
      () => props.data,
      (data) => {
        // update chart
        chart.data = data
        chart.update()
        // update header values
        //handleHeaderValues(data, chartValue, chartDeviation)        
      }
    )

    watch(
      () => darkMode.value,
      () => {
        if (darkMode.value) {
          chart.options.scales.x.ticks.color = textColor.dark
          chart.options.scales.y.ticks.color = textColor.dark
          chart.options.scales.y.grid.color = gridColor.dark
          chart.options.plugins.tooltip.titleColor = tooltipTitleColor.dark
          chart.options.plugins.tooltip.bodyColor = tooltipBodyColor.dark
          chart.options.plugins.tooltip.backgroundColor = tooltipBgColor.dark
          chart.options.plugins.tooltip.borderColor = tooltipBorderColor.dark
        } else {
          chart.options.scales.x.ticks.color = textColor.light
          chart.options.scales.y.ticks.color = textColor.light
          chart.options.scales.y.grid.color = gridColor.light
          chart.options.plugins.tooltip.titleColor = tooltipTitleColor.light
          chart.options.plugins.tooltip.bodyColor = tooltipBodyColor.light
          chart.options.plugins.tooltip.backgroundColor = tooltipBgColor.light
          chart.options.plugins.tooltip.borderColor = tooltipBorderColor.light
        }
        chart.update('none')
      })    

    return {
      canvas,
      chartValue,
      chartDeviation,
    }
  }
}
</script>